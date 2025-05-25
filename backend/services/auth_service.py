# backend/services/telegram_auth_service.py
"""
Сервис аутентификации через Telegram Web App
"""

import hashlib
import hmac
import json
from urllib.parse import unquote
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.config import TELEGRAM_BOT_TOKEN


class TelegramAuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_telegram_auth(self, init_data: str) -> Dict:
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

    def get_or_create_user(self, telegram_data: Dict) -> tuple[User, bool]:
        """Получить или создать пользователя, возвращает (user, is_new)"""
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

        is_new_user = False

        if user:
            # Обновляем данные существующего пользователя
            self._update_user_from_telegram(user, telegram_data)
        else:
            # Создаем нового пользователя
            user = self._create_user_from_telegram(telegram_data)
            is_new_user = True

        self.db.commit()
        self.db.refresh(user)

        return user, is_new_user

    def _create_user_from_telegram(self, telegram_data: Dict) -> User:
        """Создание нового пользователя из данных Telegram"""
        user = User(
            telegram_user_id=telegram_data.get('id'),
            telegram_username=telegram_data.get('username'),
            first_name=telegram_data.get('first_name', 'Пользователь'),
            last_name=telegram_data.get('last_name'),
            avatar_url=telegram_data.get('photo_url'),
            role=UserRole.VOLUNTEER,  # По умолчанию все волонтеры
            # Дополнительные поля из Telegram
            bio=f"Пользователь Telegram (@{telegram_data.get('username', 'unknown')})",
            location=telegram_data.get('language_code', 'ru').upper(),  # Примерно определяем локацию
            is_verified=True if telegram_data.get('is_premium') else False,
        )

        self.db.add(user)
        self.db.flush()  # Получаем ID

        # Создаем профиль волонтера
        if user.role == UserRole.VOLUNTEER:
            volunteer_profile = VolunteerProfile(
                user_id=user.id,
                languages=[telegram_data.get('language_code', 'ru')],
                # Заполняем базовую информацию
                skills=[],
                interests=[],
                preferred_activities=[]
            )
            self.db.add(volunteer_profile)

        return user

    def _update_user_from_telegram(self, user: User, telegram_data: Dict):
        """Обновление данных пользователя из Telegram"""
        # Обновляем основные поля
        user.first_name = telegram_data.get('first_name', user.first_name)
        user.last_name = telegram_data.get('last_name', user.last_name)
        user.telegram_username = telegram_data.get('username', user.telegram_username)
        user.avatar_url = telegram_data.get('photo_url', user.avatar_url)
        user.last_activity = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        # Обновляем статус Premium
        if telegram_data.get('is_premium'):
            user.is_verified = True

    def complete_user_registration(self, user_id: int, registration_data: Dict) -> User:
        """Дополнение регистрации пользователя дополнительными данными"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Обновляем основные данные пользователя
        if 'email' in registration_data:
            # Проверяем уникальность email
            existing_email = self.db.query(User).filter(
                User.email == registration_data['email'],
                User.id != user_id
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="Email уже используется")
            user.email = registration_data['email']

        if 'phone' in registration_data:
            user.phone = registration_data['phone']

        if 'bio' in registration_data:
            user.bio = registration_data['bio']

        if 'location' in registration_data:
            user.location = registration_data['location']

        # Обновляем профиль волонтера если есть
        if user.role == UserRole.VOLUNTEER and user.volunteer_profile:
            profile = user.volunteer_profile

            # Личные данные
            if 'middle_name' in registration_data:
                profile.middle_name = registration_data['middle_name']

            if 'birth_date' in registration_data:
                profile.birth_date = datetime.strptime(registration_data['birth_date'], '%Y-%m-%d')

            if 'gender' in registration_data:
                profile.gender = registration_data['gender']

            # Экстренные контакты
            if 'emergency_contact_name' in registration_data:
                profile.emergency_contact_name = registration_data['emergency_contact_name']

            if 'emergency_contact_phone' in registration_data:
                profile.emergency_contact_phone = registration_data['emergency_contact_phone']

            if 'emergency_contact_relation' in registration_data:
                profile.emergency_contact_relation = registration_data['emergency_contact_relation']

            # Профессиональные данные
            if 'education' in registration_data:
                profile.education = registration_data['education']

            if 'occupation' in registration_data:
                profile.occupation = registration_data['occupation']

            if 'organization' in registration_data:
                profile.organization = registration_data['organization']

            # Навыки и интересы
            if 'skills' in registration_data:
                profile.skills = registration_data['skills']

            if 'interests' in registration_data:
                profile.interests = registration_data['interests']

            if 'languages' in registration_data:
                profile.languages = registration_data['languages']

            if 'experience_description' in registration_data:
                profile.experience_description = registration_data['experience_description']

            # Доступность
            if 'travel_willingness' in registration_data:
                profile.travel_willingness = registration_data['travel_willingness']

            if 'max_travel_distance' in registration_data:
                profile.max_travel_distance = registration_data['max_travel_distance']

            if 'preferred_activities' in registration_data:
                profile.preferred_activities = registration_data['preferred_activities']

            # Обновляем процент заполнения
            profile.updated_at = datetime.utcnow()

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

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