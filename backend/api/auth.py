# backend/api/auth.py
"""
Улучшенная система аутентификации с rate limiting
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
import hashlib
import hmac
import json
import jwt
from urllib.parse import unquote
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from backend.database import get_db
from backend.config import TELEGRAM_BOT_TOKEN, SECRET_KEY
from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.core.logging import get_logger
from backend.middleware.rate_limit import auth_rate_limiter, rate_limit

router = APIRouter()
logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)

# Константы
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
TELEGRAM_AUTH_EXPIRE_HOURS = 24


class TelegramAuthError(Exception):
    """Ошибка аутентификации Telegram"""
    pass


class UserRegistrationRequest(BaseModel):
    # Основные данные
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    role: str = "volunteer"

    # Профиль волонтера
    middle_name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None

    # Экстренные контакты
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Организационные данные
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    org_contact_name: Optional[str] = None
    org_phone: Optional[str] = None
    org_email: Optional[EmailStr] = None
    org_address: Optional[str] = None

    # Профессиональные данные
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None
    experience_description: Optional[str] = None

    # Доступность
    travel_willingness: Optional[bool] = None
    max_travel_distance: Optional[int] = None
    preferred_activities: Optional[list] = []

    @validator('role')
    def validate_role(cls, v):
        if v not in ['volunteer', 'organizer', 'admin']:
            raise ValueError('Invalid role')
        return v

    @validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['male', 'female']:
            raise ValueError('Invalid gender')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Убираем все кроме цифр и +
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise ValueError('Invalid phone number')
        return v

    @validator('inn')
    def validate_inn(cls, v):
        if v:
            if not v.isdigit() or len(v) not in [10, 12]:
                raise ValueError('INN must be 10 or 12 digits')
        return v


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

    # Организационные поля
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    org_contact_name: Optional[str] = None
    org_phone: Optional[str] = None
    org_email: Optional[str] = None
    org_address: Optional[str] = None

    # Профиль волонтера
    profile_completed: Optional[bool] = None
    completion_percentage: Optional[int] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    is_new_user: bool
    requires_registration: bool = False


def verify_telegram_data(init_data: str) -> Dict:
    """
    Строгая проверка данных Telegram WebApp
    """
    if not init_data:
        raise TelegramAuthError("Missing Telegram init data")

    if not TELEGRAM_BOT_TOKEN:
        raise TelegramAuthError("Bot token not configured")

    try:
        # Парсим параметры
        parsed_data = {}
        for item in init_data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                parsed_data[key] = unquote(value)

        # Проверяем наличие обязательных полей
        if 'hash' not in parsed_data:
            raise TelegramAuthError("Missing hash in init data")

        if 'user' not in parsed_data:
            raise TelegramAuthError("Missing user data")

        # Извлекаем хеш
        received_hash = parsed_data.pop('hash')

        # Создаем строку для проверки (параметры должны быть отсортированы)
        check_string = '\n'.join([
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        ])

        # Вычисляем HMAC
        secret_key = hmac.new(
            "WebAppData".encode(),
            TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        expected_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Сравниваем хеши
        if not hmac.compare_digest(received_hash, expected_hash):
            logger.warning(f"Hash mismatch: expected {expected_hash}, got {received_hash}")
            raise TelegramAuthError("Invalid hash signature")

        # Проверяем время создания данных
        auth_date = int(parsed_data.get('auth_date', 0))
        if datetime.utcnow().timestamp() - auth_date > TELEGRAM_AUTH_EXPIRE_HOURS * 3600:
            raise TelegramAuthError("Auth data expired")

        # Парсим данные пользователя
        user_data = json.loads(parsed_data['user'])

        logger.info(f"Successfully verified Telegram auth for user {user_data.get('id')}")

        return {
            "user_id": user_data.get("id"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "username": user_data.get("username"),
            "photo_url": user_data.get("photo_url"),
            "language_code": user_data.get("language_code", "ru"),
            "is_premium": user_data.get("is_premium", False),
            "auth_date": auth_date
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse user data: {e}")
        raise TelegramAuthError("Invalid user data format")
    except Exception as e:
        logger.error(f"Auth verification failed: {e}")
        raise TelegramAuthError(f"Authentication failed: {str(e)}")


def create_access_token(user_id: int, telegram_user_id: int) -> str:
    """Создание JWT токена"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "telegram_user_id": telegram_user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_or_create_user(db: Session, telegram_data: Dict) -> tuple[User, bool]:
    """Получить или создать пользователя"""
    telegram_user_id = telegram_data.get('user_id')
    if not telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Telegram user ID"
        )

    # Ищем существующего пользователя
    user = db.query(User).filter(
        User.telegram_user_id == telegram_user_id
    ).first()

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
            role=UserRole.VOLUNTEER,
            bio=f"Пользователь Telegram (@{telegram_data.get('username', 'unknown')})",
            location=telegram_data.get('language_code', 'ru').upper(),
            is_verified=bool(telegram_data.get('is_premium')),
            last_activity=datetime.utcnow()
        )

        db.add(user)
        db.flush()
        is_new_user = True

        # Создаем профиль волонтера для новых пользователей
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
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        x_telegram_init_data: Optional[str] = Header(None),
        db: Session = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя через JWT или Telegram auth
    """
    # Приоритет: JWT токен -> Telegram auth

    # Попытка аутентификации через JWT
    if credentials and credentials.credentials:
        try:
            payload = verify_token(credentials.credentials)
            user = db.query(User).filter(User.id == payload["user_id"]).first()
            if user:
                # Обновляем время последней активности
                user.last_activity = datetime.utcnow()
                db.commit()
                return user
        except HTTPException:
            pass  # Переходим к Telegram auth

    # Попытка аутентификации через Telegram
    if x_telegram_init_data:
        try:
            telegram_data = verify_telegram_data(x_telegram_init_data)
            user, _ = get_or_create_user(db, telegram_data)
            return user
        except TelegramAuthError as e:
            logger.warning(f"Telegram auth failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


def get_volunteer_profile_safely(user: User, db: Session) -> Optional[VolunteerProfile]:
    """Безопасное получение профиля волонтера"""
    if user.role != UserRole.VOLUNTEER:
        return None

    profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == user.id
    ).first()

    return profile


@router.post("/verify", response_model=AuthResponse)
@rate_limit(auth_rate_limiter)
async def verify_auth(
        request: Request,
        x_telegram_init_data: str = Header(...),
        db: Session = Depends(get_db)
):
    """Верификация пользователя Telegram с выдачей JWT токена"""
    client_ip = auth_rate_limiter.get_client_ip(request)

    try:
        # Проверяем данные Telegram
        telegram_data = verify_telegram_data(x_telegram_init_data)

        # Получаем или создаем пользователя
        user, is_new_user = get_or_create_user(db, telegram_data)

        # Создаем JWT токен
        access_token = create_access_token(user.id, user.telegram_user_id)

        # Сброс счетчика неудачных попыток при успешной аутентификации
        auth_rate_limiter.reset_failed_attempts(client_ip)

        # Проверяем нужна ли дополнительная регистрация
        requires_registration = False
        profile_completed = False
        completion_percentage = 0

        if user.role == UserRole.VOLUNTEER:
            requires_registration = not user.email or not user.phone
            volunteer_profile = get_volunteer_profile_safely(user, db)
            if volunteer_profile:
                profile_completed = volunteer_profile.profile_completed or False
                completion_percentage = volunteer_profile.completion_percentage or 0
                requires_registration = requires_registration or completion_percentage < 70
            else:
                requires_registration = True
        elif user.role == UserRole.ORGANIZER:
            requires_registration = (not user.organization_name or
                                     not user.org_contact_name or
                                     not user.org_phone or
                                     not user.org_email)

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
            organization_name=user.organization_name,
            inn=user.inn,
            ogrn=user.ogrn,
            org_contact_name=user.org_contact_name,
            org_phone=user.org_phone,
            org_email=user.org_email,
            org_address=user.org_address,
            profile_completed=profile_completed,
            completion_percentage=completion_percentage
        )

        return AuthResponse(
            success=True,
            user=user_data,
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            is_new_user=is_new_user,
            requires_registration=requires_registration
        )

    except TelegramAuthError as e:
        # Записываем неудачную попытку
        auth_rate_limiter.record_failed_attempt(client_ip)
        logger.error(f"Telegram auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        auth_rate_limiter.record_failed_attempt(client_ip)
        logger.error(f"Auth verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение информации о текущем пользователе"""
    # Обновляем время последней активности
    current_user.last_activity = datetime.utcnow()
    db.commit()

    # Получаем профиль волонтера если есть
    profile_completed = False
    completion_percentage = 0
    if current_user.role == UserRole.VOLUNTEER:
        volunteer_profile = get_volunteer_profile_safely(current_user, db)
        if volunteer_profile:
            profile_completed = volunteer_profile.profile_completed or False
            completion_percentage = volunteer_profile.completion_percentage or 0

    return UserResponse(
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
        organization_name=current_user.organization_name,
        inn=current_user.inn,
        ogrn=current_user.ogrn,
        org_contact_name=current_user.org_contact_name,
        org_phone=current_user.org_phone,
        org_email=current_user.org_email,
        org_address=current_user.org_address,
        profile_completed=profile_completed,
        completion_percentage=completion_percentage
    )


@router.post("/complete-registration", response_model=UserResponse)
async def complete_registration(
        registration_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Завершение регистрации пользователя"""
    try:
        # Проверяем что пользователь не пытается стать админом
        if registration_data.role == 'admin' and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot set admin role"
            )

        # Обновляем роль если изменилась
        if registration_data.role and current_user.role.value != registration_data.role:
            # Проверяем что изменение роли разрешено
            if current_user.role == UserRole.ADMIN and registration_data.role != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin cannot change to non-admin role"
                )
            current_user.role = UserRole(registration_data.role)

        # Обновляем основные данные
        if registration_data.email:
            current_user.email = registration_data.email
        if registration_data.phone:
            current_user.phone = registration_data.phone
        if registration_data.bio:
            current_user.bio = registration_data.bio
        if registration_data.location:
            current_user.location = registration_data.location

        # Обновляем данные в зависимости от роли
        if current_user.role == UserRole.ORGANIZER:
            # Организационные данные
            current_user.organization_name = registration_data.organization_name
            current_user.inn = registration_data.inn
            current_user.ogrn = registration_data.ogrn
            current_user.org_contact_name = registration_data.org_contact_name
            current_user.org_phone = registration_data.org_phone
            current_user.org_email = registration_data.org_email
            current_user.org_address = registration_data.org_address

        elif current_user.role == UserRole.VOLUNTEER:
            # Данные профиля волонтера
            volunteer_profile = get_volunteer_profile_safely(current_user, db)
            if not volunteer_profile:
                volunteer_profile = VolunteerProfile(user_id=current_user.id)
                db.add(volunteer_profile)

            # Обновляем поля профиля
            volunteer_profile.middle_name = registration_data.middle_name
            volunteer_profile.gender = registration_data.gender
            volunteer_profile.emergency_contact_name = registration_data.emergency_contact_name
            volunteer_profile.emergency_contact_phone = registration_data.emergency_contact_phone
            volunteer_profile.emergency_contact_relation = registration_data.emergency_contact_relation
            volunteer_profile.education = registration_data.education
            volunteer_profile.occupation = registration_data.occupation
            volunteer_profile.organization = registration_data.organization
            volunteer_profile.experience_description = registration_data.experience_description
            volunteer_profile.travel_willingness = registration_data.travel_willingness
            volunteer_profile.max_travel_distance = registration_data.max_travel_distance
            volunteer_profile.preferred_activities = registration_data.preferred_activities or []

            # Обновляем дата рождения
            if registration_data.birth_date:
                volunteer_profile.birth_date = datetime.strptime(
                    registration_data.birth_date, "%Y-%m-%d"
                )

        current_user.last_activity = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(current_user)

        # Возвращаем обновленные данные
        return await get_current_user_info(current_user, db)

    except Exception as e:
        logger.error(f"Registration completion failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
        profile_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователе"""
    return await complete_registration(profile_data, current_user, db)


@router.post("/refresh-token")
@rate_limit(auth_rate_limiter)
async def refresh_token(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """Обновление JWT токена"""
    access_token = create_access_token(
        current_user.id,
        current_user.telegram_user_id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.delete("/delete-profile")
async def delete_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Удаление профиля пользователя"""
    try:
        # Удаляем связанные данные
        if current_user.volunteer_profile:
            db.delete(current_user.volunteer_profile)

        # Удаляем пользователя
        db.delete(current_user)
        db.commit()

        return {"message": "Profile deleted successfully"}
    except Exception as e:
        logger.error(f"Profile deletion failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )