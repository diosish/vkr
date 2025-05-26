# backend/middleware/rate_limit.py
"""
Rate limiting middleware для защиты от брутфорса и DDoS
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import asyncio
import logging
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Простой in-memory rate limiter.
    Для production рекомендуется использовать Redis.
    """
    
    def __init__(self, requests_per_minute: int = 60, 
                 burst_size: int = 10,
                 lockout_duration: int = 300):  # 5 минут блокировки
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.lockout_duration = lockout_duration
        self.requests: Dict[str, list] = defaultdict(list)
        self.lockouts: Dict[str, datetime] = {}
        self.cleanup_task = None
        
    async def start_cleanup(self):
        """Запуск фоновой задачи очистки старых записей"""
        self.cleanup_task = asyncio.create_task(self._cleanup_old_entries())
        
    async def stop_cleanup(self):
        """Остановка фоновой задачи"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
    async def _cleanup_old_entries(self):
        """Очистка старых записей каждые 5 минут"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 минут
                now = datetime.now()
                
                # Очистка истекших блокировок
                expired_lockouts = [
                    ip for ip, lockout_time in self.lockouts.items()
                    if now > lockout_time
                ]
                for ip in expired_lockouts:
                    del self.lockouts[ip]
                    
                # Очистка старых запросов
                for ip in list(self.requests.keys()):
                    self.requests[ip] = [
                        req_time for req_time in self.requests[ip]
                        if now - req_time < timedelta(minutes=1)
                    ]
                    if not self.requests[ip]:
                        del self.requests[ip]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                
    def get_client_ip(self, request: Request) -> str:
        """Получение IP адреса клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Берем первый IP из списка
            return forwarded_for.split(",")[0].strip()
            
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        # Fallback на IP из соединения
        if request.client:
            return request.client.host
            
        return "unknown"
        
    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[str]]:
        """Проверка, разрешен ли запрос"""
        now = datetime.now()
        
        # Проверяем блокировку
        if client_ip in self.lockouts:
            if now < self.lockouts[client_ip]:
                remaining_seconds = (self.lockouts[client_ip] - now).seconds
                return False, f"Too many requests. Locked out for {remaining_seconds} seconds."
            else:
                # Блокировка истекла
                del self.lockouts[client_ip]
                
        # Очищаем старые запросы
        minute_ago = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Проверяем количество запросов
        request_count = len(self.requests[client_ip])
        
        if request_count >= self.requests_per_minute:
            # Блокируем IP
            self.lockouts[client_ip] = now + timedelta(seconds=self.lockout_duration)
            logger.warning(f"Rate limit exceeded for IP {client_ip}. Locking out for {self.lockout_duration} seconds.")
            return False, f"Rate limit exceeded. Try again in {self.lockout_duration} seconds."
            
        # Проверяем burst
        if request_count >= self.burst_size:
            # Проверяем временной интервал последних запросов
            if len(self.requests[client_ip]) >= self.burst_size:
                time_window = (now - self.requests[client_ip][-self.burst_size]).total_seconds()
                if time_window < 1:  # Burst в течение 1 секунды
                    return False, "Burst limit exceeded. Please slow down."
                    
        # Запрос разрешен
        self.requests[client_ip].append(now)
        return True, None


class RateLimitMiddleware:
    """Middleware для применения rate limiting"""
    
    def __init__(self, app, rate_limiter: RateLimiter,
                 exclude_paths: Optional[list] = None):
        self.app = app
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Проверяем, нужно ли применять rate limiting
            if not any(request.url.path.startswith(path) for path in self.exclude_paths):
                client_ip = self.rate_limiter.get_client_ip(request)
                is_allowed, error_message = self.rate_limiter.is_allowed(client_ip)
                
                if not is_allowed:
                    response = JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Too Many Requests",
                            "detail": error_message
                        },
                        headers={
                            "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                            "Retry-After": str(self.rate_limiter.lockout_duration)
                        }
                    )
                    await response(scope, receive, send)
                    return
                    
        await self.app(scope, receive, send)


# Специальный rate limiter для аутентификации
class AuthRateLimiter(RateLimiter):
    """
    Более строгий rate limiter для эндпоинтов аутентификации
    """
    
    def __init__(self):
        super().__init__(
            requests_per_minute=10,  # Максимум 10 попыток в минуту
            burst_size=3,            # Максимум 3 запроса подряд
            lockout_duration=900     # 15 минут блокировки
        )
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        
    def record_failed_attempt(self, client_ip: str):
        """Записать неудачную попытку аутентификации"""
        self.failed_attempts[client_ip] += 1
        
        # После 5 неудачных попыток - блокировка
        if self.failed_attempts[client_ip] >= 5:
            self.lockouts[client_ip] = datetime.now() + timedelta(seconds=self.lockout_duration)
            logger.warning(f"IP {client_ip} locked out due to {self.failed_attempts[client_ip]} failed auth attempts")
            
    def reset_failed_attempts(self, client_ip: str):
        """Сбросить счетчик неудачных попыток после успешной аутентификации"""
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]


# Создаем глобальные экземпляры
general_rate_limiter = RateLimiter(
    requests_per_minute=120,  # 120 запросов в минуту для обычных эндпоинтов
    burst_size=20,
    lockout_duration=300
)

auth_rate_limiter = AuthRateLimiter()


# Декоратор для применения rate limiting к конкретным эндпоинтам
def rate_limit(limiter: Optional[RateLimiter] = None):
    """
    Декоратор для применения rate limiting к эндпоинту
    
    Пример использования:
    @router.post("/login")
    @rate_limit(auth_rate_limiter)
    async def login(...):
        ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            rate_limiter = limiter or general_rate_limiter
            client_ip = rate_limiter.get_client_ip(request)
            is_allowed, error_message = rate_limiter.is_allowed(client_ip)
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_message,
                    headers={
                        "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                        "Retry-After": str(rate_limiter.lockout_duration)
                    }
                )
                
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator