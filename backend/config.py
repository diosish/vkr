"""Конфигурация для тестирования с ngrok"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent.parent

# База данных (SQLite для простоты)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./volunteer.db")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://0a02-62-197-45-18.ngrok-free.app")

# Безопасность
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-change-in-production")

# API настройки
API_HOST = "0.0.0.0"
API_PORT = 8000
DEBUG = True

# CORS для ngrok
ALLOWED_ORIGINS = [
    "https://0a02-62-197-45-18.ngrok-free.app",
    "http://localhost:3000",
    "https://web.telegram.org",
    "https://k.web.telegram.org"
]

# Отладочная информация
print(f"🌐 WEBAPP_URL: {WEBAPP_URL}")
print(f"🤖 BOT TOKEN: {'✅ Set (' + TELEGRAM_BOT_TOKEN[:10] + '...)' if TELEGRAM_BOT_TOKEN else '❌ Not set'}")
print(f"📁 Loading .env from: {Path('.env').absolute()}")

if not TELEGRAM_BOT_TOKEN:
    print("⚠️  ВНИМАНИЕ: Создайте файл .env в корне проекта с содержимым:")
    print("TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather")
    print("WEBAPP_URL=https://0a02-62-197-45-18.ngrok-free.app")