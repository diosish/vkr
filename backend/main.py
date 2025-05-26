"""
Главный файл приложения с улучшенной архитектурой
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import time
import uuid
from pathlib import Path

# Импорты конфигурации и логирования
from backend.config import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION, WEBAPP_URL,
    get_cors_config, get_logging_config, print_config_info,
    FRONTEND_BUILD_DIR, IS_DEVELOPMENT, IS_PRODUCTION
)
from backend.core.logging import setup_logging, get_logger
from backend.database import init_db, check_db_connection, get_db_info

# Настройка логирования при запуске
logging_config = get_logging_config()
setup_logging(**logging_config)
logger = get_logger(__name__)

# Middleware для добавления request ID
class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request_id = str(uuid.uuid4())
            scope["request_id"] = request_id

            # Добавляем в headers для ответа
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append([b"x-request-id", request_id.encode()])
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Lifecycle событие
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Запуск приложения...")
    print_config_info()

    # Проверяем подключение к БД
    if not check_db_connection():
        logger.error("💥 Не удалось подключиться к базе данных!")
        raise Exception("Database connection failed")

    # Инициализируем БД
    try:
        init_db()
        db_info = get_db_info()
        logger.info(f"📊 Статистика БД: {db_info}")
    except Exception as e:
        logger.error(f"💥 Ошибка инициализации БД: {e}")
        raise

    # Проверяем наличие фронтенда
    if FRONTEND_BUILD_DIR.exists():
        logger.info("✅ Frontend build найден")
    else:
        logger.warning("⚠️ Frontend build не найден - работает только API")

    logger.info("✅ Приложение успешно запущено!")

    yield

    # Shutdown
    logger.info("🛑 Остановка приложения...")
    logger.info("✅ Приложение остановлено")

# Создание приложения
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Добавляем middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestIDMiddleware)

# CORS middleware
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = getattr(request.scope, "request_id", "unknown")

    # Логируем входящий запрос
    logger.info(
        f"📥 {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "ip": request.client.host if request.client else "unknown"
        }
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Логируем ответ
        logger.info(
            f"📤 {response.status_code} {request.url.path} ({process_time:.3f}s)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"💥 500 {request.url.path} ({process_time:.3f}s): {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e),
                "process_time": process_time
            },
            exc_info=True
        )
        raise

# Обработчик ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.scope, "request_id", "unknown")

    logger.warning(
        f"🚫 HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.scope, "request_id", "unknown")

    logger.error(
        f"💥 Unhandled error: {str(exc)}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error" if IS_PRODUCTION else str(exc),
            "status_code": 500,
            "request_id": request_id
        }
    )

# Подключение API роутеров
logger.info("🔌 Подключение API роутеров...")

try:
    from backend.api import auth, events, registrations, admin

    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(events.router, prefix="/api/events", tags=["Events"])
    app.include_router(registrations.router, prefix="/api/registrations", tags=["Registrations"])
    app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

    logger.info("✅ API роутеры подключены")

except ImportError as e:
    logger.error(f"❌ Ошибка импорта API роутеров: {e}")
    raise

# Статические файлы фронтенда
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")
    logger.info("✅ Статические файлы фронтенда подключены")

# API endpoints
@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    db_info = get_db_info()

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": "production" if IS_PRODUCTION else "development",
        "webapp_url": WEBAPP_URL,
        "frontend_available": FRONTEND_BUILD_DIR.exists(),
        "database": db_info,
        "timestamp": time.time()
    }

@app.get("/api/config")
async def get_config():
    """Получить публичную конфигурацию"""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "webapp_url": WEBAPP_URL,
        "is_development": IS_DEVELOPMENT,
        "features": {
            "notifications": True,  # Можно вынести в config
            "file_upload": True,
        }
    }

# Простой тестовый endpoint
@app.get("/api/ping")
async def ping():
    """Простой ping endpoint"""
    return {"message": "pong", "timestamp": time.time()}

# Отдача React приложения
if FRONTEND_BUILD_DIR.exists():
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Отдача React приложения для всех маршрутов"""

        # Исключаем API маршруты
        if (full_path.startswith("api/") or
            full_path.startswith("docs") or
            full_path.startswith("redoc") or
            full_path.startswith("health") or
            full_path.startswith("static/")):
            raise HTTPException(status_code=404, detail="Not found")

        # Отдаем index.html для всех остальных маршрутов
        index_file = FRONTEND_BUILD_DIR / "index.html"
        if index_file.exists():
            content = index_file.read_text(encoding='utf-8')
            return HTMLResponse(content=content)

        raise HTTPException(status_code=404, detail="Frontend not found")

else:
    # Если фронтенд не собран, показываем dev страницу
    @app.get("/")
    async def development_page():
        """Страница для разработки"""
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <title>{APP_NAME} - Development</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    padding: 40px; 
                    line-height: 1.6; 
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .status {{ 
                    padding: 16px; 
                    border-radius: 8px; 
                    margin: 16px 0; 
                    border-left: 4px solid;
                }}
                .success {{ 
                    background: #d4edda; 
                    color: #155724; 
                    border-color: #28a745;
                }}
                .warning {{ 
                    background: #fff3cd; 
                    color: #856404; 
                    border-color: #ffc107;
                }}
                .info {{
                    background: #d1ecf1;
                    color: #0c5460;
                    border-color: #17a2b8;
                }}
                code {{ 
                    background: #f8f9fa; 
                    padding: 2px 6px; 
                    border-radius: 4px;
                    font-family: 'Monaco', 'Consolas', monospace;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin: 20px 0;
                }}
                .card {{
                    padding: 16px;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    background: white;
                }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>🚀 {APP_NAME}</h1>
            <p>Версия: <strong>{APP_VERSION}</strong> | Режим: <strong>Разработка</strong></p>
            
            <div class="status success">
                <strong>✅ Backend запущен</strong><br>
                API сервер работает на порту 8000
            </div>
            
            <div class="status warning">
                <strong>⚠️ Frontend не собран</strong><br>
                Для работы с интерфейсом необходимо собрать фронтенд
            </div>
            
            <div class="status info">
                <strong>🤖 Telegram Bot</strong><br>
                WebApp URL: <code>{WEBAPP_URL}</code>
            </div>
            
            <h2>🛠️ Для разработки:</h2>
            <ol>
                <li>Запустите фронтенд: <code>cd frontend && npm start</code></li>
                <li>Откройте: <a href="http://localhost:3000">http://localhost:3000</a></li>
            </ol>
            
            <h2>🏗️ Для продакшена:</h2>
            <ol>
                <li>Соберите фронтенд: <code>cd frontend && npm run build</code></li>
                <li>Перезапустите сервер</li>
            </ol>
            
            <h2>📚 API Документация:</h2>
            <div class="grid">
                <div class="card">
                    <h3>🔍 Интерактивная документация</h3>
                    <a href="/docs">Swagger UI (/docs)</a>
                </div>
                <div class="card">
                    <h3>📖 Альтернативная документация</h3>
                    <a href="/redoc">ReDoc (/redoc)</a>
                </div>
                <div class="card">
                    <h3>💓 Проверка здоровья</h3>
                    <a href="/health">Health Check (/health)</a>
                </div>
                <div class="card">
                    <h3>🏓 Простой тест</h3>
                    <a href="/api/ping">Ping API (/api/ping)</a>
                </div>
            </div>
            
            <hr style="margin: 40px 0;">
            <p style="color: #6c757d; font-size: 14px;">
                💡 <strong>Совет:</strong> После сборки фронтенда эта страница заменится на полнофункциональное приложение
            </p>
        </body>
        </html>
        """)

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    from backend.config import API_HOST, API_PORT, DEBUG

    logger.info(f"🌟 Запуск {APP_NAME} v{APP_VERSION}")

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG and IS_DEVELOPMENT,
        log_config=None,  # Используем нашу систему логирования
        access_log=False  # Отключаем встроенный access log
    )