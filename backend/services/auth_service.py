"""Сервис аутентификации"""

import hashlib
import hmac
import json
from urllib.parse import unquote
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.config import TELEGRAM_BOT_TOKEN


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_telegram_auth(self, init_data: str) -> dict:
        """Проверка аутентификации Telegram Web App"""
        try:
            # Парсим данные
            parsed_data = {}
            for item in init_data.split('&'):
                if '=' in item:
                    key, value = item.split('=', 1)
                    parsed_data[key] = unquote(value)

            # Извлекаем хеш
            received_hash = parsed_data.pop('hash', '')

            # Создаем строку для проверки
            data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])

            # Вычисляем ожидаемый хеш
            secret_key = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
            expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

            # Проверяем хеш
            if not hmac.compare_digest(received_hash, expected_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication data"
                )

            # Парсим пользовательские данные
            user_data = json.loads(parsed_data.get('user', '{}'))

            # Проверяем актуальность (не старше 1 часа)
            auth_date = int(parsed_data.get('auth_date', 0))
            if datetime.utcnow().timestamp() - auth_date > 3600:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication data expired"
                )

            return user_data

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user data format"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

    def get_or_create_user(self, telegram_data: dict) -> User:
        """Получить или создать пользователя"""
        telegram_user_id = telegram_data.get('id')
        if not telegram_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Telegram user ID"
            )

        # Ищем существующего пользователя
        user = self.db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()

        if user:
            # Обновляем данные пользователя
            user.first_name = telegram_data.get('first_name', user.first_name)
            user.last_name = telegram_data.get('last_name', user.last_name)
            user.telegram_username = telegram_data.get('username', user.telegram_username)
            user.avatar_url = telegram_data.get('photo_url', user.avatar_url)
            user.last_activity = datetime.utcnow()

            self.db.commit()
            self.db.refresh(user)
        else:
            # Создаем нового пользователя
            user = User(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_data.get('username'),
                first_name=telegram_data.get('first_name', 'Пользователь'),
                last_name=telegram_data.get('last_name'),
                avatar_url=telegram_data.get('photo_url'),
                role=UserRole.VOLUNTEER  # По умолчанию все волонтеры
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # Создаем профиль волонтера
            if user.role == UserRole.VOLUNTEER:
                volunteer_profile = VolunteerProfile(user_id=user.id)
                self.db.add(volunteer_profile)
                self.db.commit()

        return user

    def change_user_role(self, user_id: int, new_role: UserRole, admin_user: User) -> User:
        """Изменить роль пользователя (только админ)"""
        if not admin_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change user roles"
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        # Создаем профиль волонтера если нужно
        if new_role == UserRole.VOLUNTEER and not user.volunteer_profile:
            volunteer_profile = VolunteerProfile(user_id=user.id)
            self.db.add(volunteer_profile)

        self.db.commit()
        self.db.refresh(user)

        return user