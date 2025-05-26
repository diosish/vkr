"""Улучшенная конфигурация приложения"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

# Загружаем переменные окружения
load_dotenv()

# Определяем окружение
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"
IS_TESTING = ENVIRONMENT == "testing"

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
FRONTEND_BUILD_DIR = BASE_DIR / "frontend" / "build"

# === БАЗА ДАННЫХ ===
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    if IS_TESTING:
        DATABASE_URL = "sqlite:///:memory:"
    elif IS_PRODUCTION:
        # В продакшене требуем явного указания БД
        raise ValueError("DATABASE_URL must be set in production")
    else:
        # Развитие - используем SQLite
        DATABASE_URL = "sqlite:///./volunteer.db"

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-ngrok-url.ngrok-free.app")

if not TELEGRAM_BOT_TOKEN and not IS_TESTING:
    print("⚠️  ВНИМАНИЕ: TELEGRAM_BOT_TOKEN не установлен!")
    print("   Создайте файл .env с токеном от @BotFather")

# === БЕЗОПАСНОСТЬ ===
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ValueError("SECRET_KEY must be set in production")
    else:
        SECRET_KEY = "dev-secret-key-change-in-production"
        if IS_DEVELOPMENT:
            print("⚠️  Используется dev SECRET_KEY. Измените в продакшене!")

# JWT настройки
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 дней

# === API НАСТРОЙКИ ===
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true" if IS_DEVELOPMENT else "false").lower() == "true"

# CORS настройки
ALLOWED_ORIGINS = []

if IS_DEVELOPMENT:
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # FastAPI
        "http://127.0.0.1:8000",
    ])

# Добавляем WEBAPP_URL если указан и это не дефолтное значение
if WEBAPP_URL and WEBAPP_URL != "https://your-ngrok-url.ngrok-free.app":
    ALLOWED_ORIGINS.append(WEBAPP_URL)

# Telegram Web App домены (только официальные)
ALLOWED_ORIGINS.extend([
    "https://web.telegram.org",
    "https://k.web.telegram.org"
])

# Дополнительные origins из переменных окружения (только для production)
if IS_PRODUCTION:
    additional_origins = os.getenv("ALLOWED_ORIGINS", "")
    if additional_origins:
        ALLOWED_ORIGINS.extend([origin.strip() for origin in additional_origins.split(",")])

# Список разрешенных методов
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Список разрешенных заголовков
ALLOWED_HEADERS = [
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "X-Telegram-Init-Data",
    "X-Request-ID"
]

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true" if IS_PRODUCTION else "false").lower() == "true"
LOG_JSON_FORMAT = os.getenv("LOG_JSON_FORMAT", "true" if IS_PRODUCTION else "false").lower() == "true"

# === УВЕДОМЛЕНИЯ ===
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
NOTIFICATION_CHANNELS = os.getenv("NOTIFICATION_CHANNELS", "telegram").split(",")

# === ФАЙЛЫ И МЕДИА ===
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB

# Создаем директории если не существуют
MEDIA_ROOT.mkdir(exist_ok=True)
(MEDIA_ROOT / "avatars").mkdir(exist_ok=True)
(MEDIA_ROOT / "documents").mkdir(exist_ok=True)

# === REDIS (для кэширования и очередей) ===
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ENABLE_REDIS = os.getenv("ENABLE_REDIS", "false").lower() == "true"

# === EMAIL (опционально) ===
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@volunteer-system.local")

# === МОНИТОРИНГ ===
SENTRY_DSN = os.getenv("SENTRY_DSN")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "false").lower() == "true"

# === НАСТРОЙКИ ПРИЛОЖЕНИЯ ===
APP_NAME = "Volunteer Registration System"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Система регистрации волонтеров для Telegram Mini App"

# Лимиты API
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100")  # запросов в минуту
API_BURST_LIMIT = os.getenv("API_BURST_LIMIT", "200")

# URL бота для уведомлений
BOT_NOTIFY_URL = os.getenv("BOT_NOTIFY_URL", "http://localhost:8081/bot/notify")

class Settings:
    """Класс для хранения настроек приложения"""
    def __init__(self):
        self.APP_NAME = APP_NAME
        self.APP_VERSION = APP_VERSION
        self.APP_DESCRIPTION = APP_DESCRIPTION
        self.API_RATE_LIMIT = API_RATE_LIMIT
        self.API_BURST_LIMIT = API_BURST_LIMIT
        self.BOT_NOTIFY_URL = BOT_NOTIFY_URL
        self.DATABASE_URL = DATABASE_URL
        self.SECRET_KEY = SECRET_KEY
        self.JWT_ALGORITHM = JWT_ALGORITHM
        self.JWT_EXPIRE_MINUTES = JWT_EXPIRE_MINUTES
        self.ENVIRONMENT = ENVIRONMENT
        self.IS_DEVELOPMENT = IS_DEVELOPMENT
        self.IS_PRODUCTION = IS_PRODUCTION
        self.IS_TESTING = IS_TESTING
        self.ALLOWED_ORIGINS = ALLOWED_ORIGINS
        self.ALLOWED_METHODS = ALLOWED_METHODS
        self.ALLOWED_HEADERS = ALLOWED_HEADERS
        self.LOG_LEVEL = LOG_LEVEL
        self.LOG_TO_FILE = LOG_TO_FILE
        self.LOG_JSON_FORMAT = LOG_JSON_FORMAT
        self.ENABLE_NOTIFICATIONS = ENABLE_NOTIFICATIONS
        self.NOTIFICATION_CHANNELS = NOTIFICATION_CHANNELS
        self.MEDIA_ROOT = MEDIA_ROOT
        self.MEDIA_URL = MEDIA_URL
        self.MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE
        self.REDIS_URL = REDIS_URL
        self.ENABLE_REDIS = ENABLE_REDIS
        self.EMAIL_HOST = EMAIL_HOST
        self.EMAIL_PORT = EMAIL_PORT
        self.EMAIL_USER = EMAIL_USER
        self.EMAIL_PASSWORD = EMAIL_PASSWORD
        self.EMAIL_USE_TLS = EMAIL_USE_TLS
        self.FROM_EMAIL = FROM_EMAIL
        self.SENTRY_DSN = SENTRY_DSN
        self.ENABLE_METRICS = ENABLE_METRICS

# Создаем экземпляр настроек
settings = Settings()

# === ФУНКЦИИ КОНФИГУРАЦИИ ===

def get_database_config():
    """Получить конфигурацию базы данных"""
    return {
        "url": DATABASE_URL,
        "is_sqlite": DATABASE_URL.startswith("sqlite"),
        "is_postgres": DATABASE_URL.startswith("postgresql"),
        "is_mysql": DATABASE_URL.startswith("mysql"),
    }

def get_cors_config():
    """Получить конфигурацию CORS"""
    return {
        "allow_origins": ALLOWED_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ALLOWED_METHODS,
        "allow_headers": ALLOWED_HEADERS,
        "expose_headers": ["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
        "max_age": 3600,  # 1 час
    }

def get_logging_config():
    """Получить конфигурацию логирования"""
    return {
        "log_level": LOG_LEVEL,
        "enable_file_logging": LOG_TO_FILE,
        "enable_json_logging": LOG_JSON_FORMAT,
    }

def is_feature_enabled(feature: str) -> bool:
    """Проверить включена ли функция"""
    features = {
        "notifications": ENABLE_NOTIFICATIONS,
        "redis": ENABLE_REDIS,
        "metrics": ENABLE_METRICS,
        "email": bool(EMAIL_HOST and EMAIL_USER),
        "sentry": bool(SENTRY_DSN),
    }
    return features.get(feature, False)

def print_config_info():
    """Вывести информацию о конфигурации"""
    print("=" * 60)
    print("🔧 КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ")
    print("=" * 60)
    print(f"🌍 Окружение: {ENVIRONMENT}")
    print(f"🗄️  База данных: {get_database_config()['url'].split('://')[0]}://***")
    print(f"🤖 Telegram Bot: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print(f"📱 Frontend: {'✅' if FRONTEND_BUILD_DIR.exists() else '❌'}")
    print(f"🔐 Secure mode: {'✅' if IS_PRODUCTION else '❌'}")
    print(f"📊 Debug mode: {'✅' if DEBUG else '❌'}")
    print(f"📝 Log level: {LOG_LEVEL}")
    print(f"🔔 Notifications: {'✅' if ENABLE_NOTIFICATIONS else '❌'}")
    print(f"🗃️  Redis: {'✅' if ENABLE_REDIS else '❌'}")
    print(f"📧 Email: {'✅' if is_feature_enabled('email') else '❌'}")
    print(f"🚨 Sentry: {'✅' if is_feature_enabled('sentry') else '❌'}")
    print("=" * 60)

# Валидация критичных настроек
def validate_config():
    """Валидация конфигурации"""
    errors = []

    if IS_PRODUCTION:
        if SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed in production")

        if not TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if WEBAPP_URL == "https://your-ngrok-url.ngrok-free.app":
            errors.append("WEBAPP_URL must be set to actual domain")

    if errors:
        print("❌ ОШИБКИ КОНФИГУРАЦИИ:")
        for error in errors:
            print(f"   • {error}")
        if IS_PRODUCTION:
            raise ValueError("Invalid production configuration")

    return len(errors) == 0

# Автоматическая валидация при импорте
if __name__ != "__main__":
    validate_config()