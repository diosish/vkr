"""
Аутентификация через Telegram Web App
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import hmac
import hashlib
import json
from urllib.parse import unquote
from typing import Optional
import os

router = APIRouter()


class TelegramAuthData(BaseModel):
    auth_date: int
    first_name: str
    id: int
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    hash: str


def verify_telegram_auth(init_data: str) -> dict:
    """Проверка подлинности данных от Telegram"""
    try:
        # Получаем токен бота из переменных окружения
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise HTTPException(status_code=500, detail="Bot token not configured")

        # Парсим данные
        parsed_data = {}
        for item in init_data.split('&'):
            key, value = item.split('=', 1)
            parsed_data[key] = unquote(value)

        # Извлекаем хеш
        received_hash = parsed_data.pop('hash', '')

        # Создаем строку для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])

        # Вычисляем ожидаемый хеш
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        # Проверяем хеш
        if not hmac.compare_digest(received_hash, expected_hash):
            raise HTTPException(status_code=401, detail="Invalid authentication data")

        # Парсим пользовательские данные
        user_data = json.loads(parsed_data.get('user', '{}'))

        return {
            "user_id": user_data.get("id"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "username": user_data.get("username"),
            "photo_url": user_data.get("photo_url"),
            "auth_date": int(parsed_data.get("auth_date", 0))
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post("/verify")
async def verify_auth(x_telegram_init_data: str = Header(None)):
    """Верификация пользователя Telegram"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram auth data")

    user_data = verify_telegram_auth(x_telegram_init_data)

    # Здесь можно сохранить или обновить данные пользователя в БД

    return {
        "success": True,
        "user": user_data,
        "message": "Authentication successful"
    }


def get_current_user(x_telegram_init_data: str = Header(None)) -> dict:
    """Dependency для получения текущего пользователя"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Authentication required")

    return verify_telegram_auth(x_telegram_init_data)