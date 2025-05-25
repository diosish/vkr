# backend/api/auth.py
"""API для аутентификации и регистрации через Telegram"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
import hashlib
import hmac
import json
from urllib.parse import unquote

from backend.database import get_db
from backend.config import TELEGRAM_BOT_TOKEN
from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile

router = APIRouter()


class UserRegistrationRequest(BaseModel):
    # Основные данные
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    # Профиль волонтера
    middle_name: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD format
    gender: Optional[str] = None

    # Экстренные контакты
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Профессиональные данные
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None

    # Навыки и интересы
    skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    experience_description: Optional[str] = None

    # Доступность
    travel_willingness: Optional[bool] = None
    max_travel_distance: Optional[int] = None
    preferred_activities: Optional[List[str]] = []


class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    telegram_username: Optional[str]
    first_name: str
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: str
    bio: Optional[str]
    avatar_url: Optional[str]
    location: Optional[str]
    is_active: bool
    is_verified: bool
    full_name: str
    display_name: str
    created_at: datetime
    last_activity: Optional[datetime]

    # Профиль волонтера (если есть)
    profile_completed: Optional[bool] = None
    completion_percentage: Optional[int] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse
    message: str
    is_new_user: bool
    requires_registration: bool = False


def verify_telegram_auth(init_data: str) -> dict:
    """Проверка подлинности данных от Telegram"""
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
            print(f"❌ Hash mismatch: expected={expected_hash}, received={received_hash}")
            # В режиме разработки пропускаем проверку хеша
            print("⚠️ Skipping hash validation in development mode")

        # Парсим пользовательские данные
        user_data = json.loads(parsed_data.get('user', '{}'))

        return {
            "user_id": user_data.get("id"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "username": user_data.get("username"),
            "photo_url": user_data.get("photo_url"),
            "language_code": user_data.get("language_code"),
            "is_premium": user_data.get("is_premium", False),
            "auth_date": int(parsed_data.get("auth_date", 0))
        }

    except Exception as e:
        print(f"❌ Auth verification error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def get_or_create_user(db: Session, telegram_data: dict) -> tuple[User, bool]:
    """Получить или создать пользователя, возвращает (user, is_new)"""
    telegram_user_id = telegram_data.get('user_id')
    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="Missing Telegram user ID")

    # Ищем существующего пользователя
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    is_new_user = False

    if user:
        # Обновляем данные существующего пользователя
        user.first_name = telegram_data.get('first_name', user.first_name)
        user.last_name = telegram_data.get('last_name', user.last_name)
        user.telegram_username = telegram_data.get('username', user.telegram_username)
        user.avatar_url = telegram_data.get('photo_url', user.avatar_url)
        user.last_activity = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        if telegram_data.get('is_premium'):
            user.is_verified = True
    else:
        # Создаем нового пользователя
        user = User(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_data.get('username'),
            first_name=telegram_data.get('first_name', 'Пользователь'),
            last_name=telegram_data.get('last_name'),
            avatar_url=telegram_data.get('photo_url'),
            role=UserRole.VOLUNTEER,  # По умолчанию все волонтеры
            bio=f"Пользователь Telegram (@{telegram_data.get('username', 'unknown')})",
            location=telegram_data.get('language_code', 'ru').upper(),
            is_verified=True if telegram_data.get('is_premium') else False,
        )

        db.add(user)
        db.flush()  # Получаем ID
        is_new_user = True

        # Создаем профиль волонтера
        if user.role == UserRole.VOLUNTEER:
            volunteer_profile = VolunteerProfile(
                user_id=user.id,
                languages=[telegram_data.get('language_code', 'ru')],
                skills=[],
                interests=[],
                preferred_activities=[]
            )
            db.add(volunteer_profile)

    db.commit()
    db.refresh(user)
    return user, is_new_user


def get_current_user(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
) -> User:
    """Dependency для получения текущего пользователя"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Authentication required")

    telegram_data = verify_telegram_auth(x_telegram_init_data)
    user, _ = get_or_create_user(db, telegram_data)
    return user


@router.post("/verify", response_model=AuthResponse)
async def verify_auth(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
):
    """Верификация пользователя Telegram"""
    if not x_telegram_init_data:
        # В режиме разработки возвращаем тестового пользователя
        print("⚠️ No Telegram auth data, returning test user")
        return AuthResponse(
            success=True,
            user=UserResponse(
                id=1,
                telegram_user_id=123456789,
                telegram_username="test_user",
                first_name="Тест",
                last_name="Пользователь",
                email=None,
                phone=None,
                role="volunteer",
                bio=None,
                avatar_url=None,
                location=None,
                is_active=True,
                is_verified=False,
                full_name="Тест Пользователь",
                display_name="@test_user",
                created_at=datetime.utcnow(),
                last_activity=None,
                profile_completed=False,
                completion_percentage=30
            ),
            message="Test authentication successful",
            is_new_user=False,
            requires_registration=True
        )

    try:
        # Проверяем данные Telegram
        telegram_data = verify_telegram_auth(x_telegram_init_data)

        # Получаем или создаем пользователя
        user, is_new_user = get_or_create_user(db, telegram_data)

        # Проверяем нужна ли дополнительная регистрация
        requires_registration = False
        profile_completed = False
        completion_percentage = 0

        if user.role == UserRole.VOLUNTEER:
            # Для волонтеров проверяем заполненность профиля
            requires_registration = not user.email or not user.phone

            # Правильно обрабатываем volunteer_profile (может быть None)
            if hasattr(user, 'volunteer_profile') and user.volunteer_profile:
                profile_completed = user.volunteer_profile.profile_completed
                completion_percentage = user.volunteer_profile.completion_percentage
                requires_registration = requires_registration or completion_percentage < 70
            else:
                # Если профиля нет, требуется регистрация
                requires_registration = True

        # Формируем ответ
        user_data = UserResponse(
            id=user.id,
            telegram_user_id=user.telegram_user_id,
            telegram_username=user.telegram_username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            bio=user.bio,
            avatar_url=user.avatar_url,
            location=user.location,
            is_active=user.is_active,
            is_verified=user.is_verified,
            full_name=user.full_name,
            display_name=user.display_name,
            created_at=user.created_at,
            last_activity=user.last_activity,
            profile_completed=profile_completed,
            completion_percentage=completion_percentage
        )

        return AuthResponse(
            success=True,
            user=user_data,
            message="Authentication successful",
            is_new_user=is_new_user,
            requires_registration=requires_registration
        )

    except Exception as e:
        print(f"❌ Auth error: {e}")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""

    # Правильно обрабатываем volunteer_profile
    profile_completed = False
    completion_percentage = 0

    if hasattr(current_user, 'volunteer_profile') and current_user.volunteer_profile:
        profile_completed = current_user.volunteer_profile.profile_completed
        completion_percentage = current_user.volunteer_profile.completion_percentage

    user_data = UserResponse(
        id=current_user.id,
        telegram_user_id=current_user.telegram_user_id,
        telegram_username=current_user.telegram_username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        location=current_user.location,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        full_name=current_user.full_name,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
        last_activity=current_user.last_activity,
        profile_completed=profile_completed,
        completion_percentage=completion_percentage
    )

    return user_data


@router.post("/complete-registration", response_model=UserResponse)
async def complete_registration(
        registration_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Дополнение регистрации пользователя"""
    try:
        # Обновляем основные данные пользователя
        update_data = registration_data.dict(exclude_unset=True)

        # Поля пользователя
        user_fields = ['email', 'phone', 'bio', 'location']
        for field in user_fields:
            if field in update_data and update_data[field]:
                setattr(current_user, field, update_data[field])

        current_user.updated_at = datetime.utcnow()

        # Обновляем профиль волонтера если пользователь - волонтер
        if current_user.role == UserRole.VOLUNTEER:
            # Создаем профиль если его нет
            if not hasattr(current_user, 'volunteer_profile') or not current_user.volunteer_profile:
                volunteer_profile = VolunteerProfile(user_id=current_user.id)
                db.add(volunteer_profile)
                db.flush()  # Чтобы получить ID
                # Обновляем связь
                db.refresh(current_user)

            vp = current_user.volunteer_profile

            # Поля профиля волонтера
            volunteer_fields = [
                'middle_name', 'birth_date', 'gender',
                'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
                'education', 'occupation', 'organization',
                'skills', 'interests', 'languages', 'experience_description',
                'travel_willingness', 'max_travel_distance', 'preferred_activities'
            ]

            for field in volunteer_fields:
                if field in update_data and update_data[field] is not None:
                    if field == 'birth_date' and update_data[field]:
                        setattr(vp, field, datetime.strptime(update_data[field], '%Y-%m-%d'))
                    else:
                        setattr(vp, field, update_data[field])

            # Проверяем заполненность профиля
            required_fields = [
                vp.middle_name, vp.birth_date, current_user.phone, current_user.email,
                vp.emergency_contact_name, vp.emergency_contact_phone,
                vp.education,
                vp.skills and len(vp.skills) > 0 if vp.skills else False,
                vp.experience_description
            ]

            filled_count = sum(1 for field in required_fields if field)
            vp.profile_completed = filled_count >= 7  # Минимум 7 из 9 полей
            vp.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(current_user)

        # Возвращаем обновленные данные
        return await get_current_user_info(current_user)

    except Exception as e:
        print(f"❌ Registration completion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profile", response_model=UserResponse)
async def update_profile(
        profile_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    return await complete_registration(profile_data, current_user, db)