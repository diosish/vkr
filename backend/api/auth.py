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
from pydantic import validator
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status

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
    role: Optional[str] = "volunteer"

    # Профиль волонтера
    middle_name: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD format
    gender: Optional[str] = None  # Только 'male' или 'female'

    # Экстренные контакты
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Организация (только для organizer)
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    org_contact_name: Optional[str] = None
    org_phone: Optional[str] = None
    org_email: Optional[EmailStr] = None
    org_address: Optional[str] = None

    # Профессиональные данные (только для volunteer)
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None

    # Опыт (только для volunteer)
    experience_description: Optional[str] = None

    # Доступность (только для volunteer)
    travel_willingness: Optional[bool] = None
    max_travel_distance: Optional[int] = None
    preferred_activities: Optional[list] = []

    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == '':
            return None
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
        
        # Проверяем хеш
        if TELEGRAM_BOT_TOKEN:
            # Сортируем параметры по ключу
            data_check_string = '\n'.join(sorted(f"{k}={v}" for k, v in parsed_data.items()))
            
            # Создаем секретный ключ
            secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
            
            # Вычисляем HMAC-SHA256
            hmac_obj = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
            calculated_hash = hmac_obj.hexdigest()
            
            # В режиме разработки выводим отладочную информацию
            print(f"🔍 Debug auth data:")
            print(f"  Data check string: {data_check_string}")
            print(f"  Received hash: {received_hash}")
            print(f"  Calculated hash: {calculated_hash}")
            
            if calculated_hash != received_hash:
                print(f"❌ Invalid hash: {received_hash} != {calculated_hash}")
                # В режиме разработки пропускаем проверку хеша
                print("⚠️ Development mode: skipping hash verification")
            else:
                print("✅ Hash verification successful")

        # Парсим пользовательские данные
        user_data_str = parsed_data.get('user', '{}')
        if user_data_str:
            user_data = json.loads(user_data_str)
        else:
            raise ValueError("No user data")

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
        # В режиме разработки создаем тестового пользователя
        print("⚠️ Development mode: creating test user")
        return {
            "user_id": 123456789,
            "first_name": "Тест",
            "last_name": "Пользователь",
            "username": "test_user",
            "language_code": "ru",
            "is_premium": False,
            "auth_date": int(datetime.utcnow().timestamp())
        }


def get_or_create_user(db: Session, telegram_data: dict, role: Optional[str] = None, fail_if_exists: bool = False) -> tuple[User, bool]:
    """Получить или создать пользователя, возвращает (user, is_new)"""
    telegram_user_id = telegram_data.get('user_id') or telegram_data.get('id')
    if not telegram_user_id:
        telegram_user_id = 999999999  # ID по умолчанию

    # Ищем существующего пользователя
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    is_new_user = False

    if user:
        if fail_if_exists:
            raise HTTPException(status_code=409, detail="Пользователь с таким Telegram ID уже зарегистрирован")
        # Обновляем данные существующего пользователя
        user.first_name = telegram_data.get('first_name', user.first_name)
        user.last_name = telegram_data.get('last_name', user.last_name)
        user.telegram_username = telegram_data.get('username', user.telegram_username)
        user.avatar_url = telegram_data.get('photo_url', user.avatar_url)
        user.last_activity = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        if telegram_data.get('is_premium'):
            user.is_verified = True
        # Обновляем роль, если явно указана
        if role and user.role.value != role:
            user.role = UserRole(role)
    else:
        from backend.models.user import UserRole
        user_role = UserRole(role) if role else UserRole.VOLUNTEER
        user = User(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_data.get('username'),
            first_name=telegram_data.get('first_name', 'Пользователь'),
            last_name=telegram_data.get('last_name'),
            avatar_url=telegram_data.get('photo_url'),
            role=user_role,
            bio=f"Пользователь Telegram (@{telegram_data.get('username', 'unknown')})",
            location=telegram_data.get('language_code', 'ru').upper(),
            is_verified=True if telegram_data.get('is_premium') else False,
        )
        db.add(user)
        db.flush()  # Получаем ID
        is_new_user = True
        # Создаём профиль волонтёра только если роль volunteer
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


def get_volunteer_profile_safely(user: User, db: Session) -> Optional[VolunteerProfile]:
    """Безопасное получение профиля волонтера"""
    if user.role != UserRole.VOLUNTEER:
        return None

    # Получаем профиль напрямую из БД
    profile = db.query(VolunteerProfile).filter(
        VolunteerProfile.user_id == user.id
    ).first()

    return profile


@router.post("/verify", response_model=AuthResponse)
async def verify_auth(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
):
    """Верификация пользователя Telegram"""
    try:
        # Если нет данных - создаем гостевого пользователя
        if not x_telegram_init_data:
            print("⚠️ No Telegram auth data, creating guest user")
            telegram_data = {
                "user_id": 999999999,
                "first_name": "Гость",
                "last_name": "Пользователь",
                "username": "guest_user"
            }
        else:
            # Проверяем данные Telegram
            telegram_data = verify_telegram_auth(x_telegram_init_data)

        # Получаем или создаем пользователя
        user, is_new_user = get_or_create_user(db, telegram_data)

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
                completion_percentage = 0
        elif user.role == UserRole.ORGANIZER:
            requires_registration = not user.organization_name or not user.org_contact_name or not user.org_phone or not user.org_email
        elif user.role == UserRole.ADMIN:
            requires_registration = False

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
            message="Authentication successful",
            is_new_user=is_new_user,
            requires_registration=requires_registration
        )

    except Exception as e:
        print(f"❌ Auth error: {e}")
        # В случае ошибки создаем базового пользователя
        user_data = UserResponse(
            id=999,
            telegram_user_id=999999999,
            telegram_username="guest",
            first_name="Гость",
            last_name="Пользователь",
            email=None,
            phone=None,
            role="volunteer",
            bio=None,
            avatar_url=None,
            location=None,
            is_active=True,
            is_verified=False,
            full_name="Гость Пользователь",
            display_name="@guest",
            created_at=datetime.utcnow(),
            last_activity=None,
            organization_name=None,
            inn=None,
            ogrn=None,
            org_contact_name=None,
            org_phone=None,
            org_email=None,
            org_address=None,
            profile_completed=False,
            completion_percentage=0
        )

        return AuthResponse(
            success=True,
            user=user_data,
            message="Guest authentication",
            is_new_user=True,
            requires_registration=True
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение информации о текущем пользователе"""
    try:
        # Обновляем время последней активности
        current_user.last_activity = datetime.utcnow()
        db.commit()
        db.refresh(current_user)

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
    except Exception as e:
        print(f"❌ Get user info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete-registration", response_model=UserResponse)
async def complete_registration(
        registration_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Завершение регистрации пользователя"""
    try:
        # Если явно передан telegram_user_id — ищем пользователя по нему
        telegram_user_id = getattr(registration_data, 'telegram_user_id', None)
        if telegram_user_id:
            user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
            if user:
                current_user = user

        # Проверка уникальности по telegram_user_id (chat_id) при первой регистрации
        if not current_user.id:
            telegram_data = {"user_id": current_user.telegram_user_id}
            get_or_create_user(db, telegram_data, registration_data.role, fail_if_exists=True)

        print("[DEBUG] registration_data:", registration_data.dict())

        # Обновляем основные данные пользователя
        if registration_data.role and current_user.role.value != registration_data.role:
            current_user.role = UserRole(registration_data.role)
        current_user.email = registration_data.email
        current_user.phone = registration_data.phone
        current_user.bio = registration_data.bio
        current_user.location = registration_data.location
        if registration_data.birth_date:
            try:
                current_user.birth_date = datetime.strptime(registration_data.birth_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid birth date format")
        else:
            current_user.birth_date = None

        # --- Разная логика для разных ролей ---
        if current_user.role.value == "organizer":
            # Сохраняем только организационные поля
            current_user.organization_name = registration_data.organization_name
            current_user.inn = registration_data.inn
            current_user.ogrn = registration_data.ogrn
            current_user.org_contact_name = registration_data.org_contact_name
            current_user.org_phone = registration_data.org_phone
            current_user.org_email = registration_data.org_email
            current_user.org_address = registration_data.org_address
            # Не создаём профиль волонтёра
        elif current_user.role.value == "admin":
            # Для админа не создаём профиль вообще
            pass
        else:  # volunteer
            # Обновляем или создаем профиль волонтёра
            volunteer_profile = get_volunteer_profile_safely(current_user, db)
            if not volunteer_profile:
                volunteer_profile = VolunteerProfile(user_id=current_user.id)
                db.add(volunteer_profile)
            # Только нужные поля
            volunteer_profile.middle_name = registration_data.middle_name
            volunteer_profile.gender = registration_data.gender if registration_data.gender in ("male", "female") else None
            volunteer_profile.emergency_contact_name = registration_data.emergency_contact_name
            volunteer_profile.emergency_contact_phone = registration_data.emergency_contact_phone
            volunteer_profile.emergency_contact_relation = registration_data.emergency_contact_relation
            volunteer_profile.education = registration_data.education
            volunteer_profile.occupation = registration_data.occupation
            volunteer_profile.organization = registration_data.organization
            volunteer_profile.experience_description = registration_data.experience_description
            volunteer_profile.travel_willingness = registration_data.travel_willingness
            volunteer_profile.max_travel_distance = registration_data.max_travel_distance
            volunteer_profile.preferred_activities = registration_data.preferred_activities

        # Обновляем время последней активности
        current_user.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(current_user)

        print(f"[DEBUG] После регистрации: id={current_user.id}, role={current_user.role}, email={current_user.email}, phone={current_user.phone}, org_name={getattr(current_user, 'organization_name', None)}")

        # Формируем ответ
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

    except RequestValidationError as ve:
        print(f"[VALIDATION ERROR] {ve.errors()}")
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": ve.errors()})
    except Exception as e:
        db.rollback()
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile", response_model=UserResponse)
async def update_profile(
        profile_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    return await complete_registration(profile_data, current_user, db)


@router.delete("/delete-profile")
async def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить профиль пользователя и все связанные данные"""
    try:
        # Удаляем профиль волонтёра, если есть
        volunteer_profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == current_user.id).first()
        if volunteer_profile:
            db.delete(volunteer_profile)
        # Удаляем все регистрации пользователя
        from backend.models.registration import Registration
        db.query(Registration).filter(Registration.user_id == current_user.id).delete()
        # Удаляем самого пользователя
        db.delete(current_user)
        db.commit()
        return {"success": True, "message": "Профиль и связанные данные удалены"}
    except Exception as e:
        db.rollback()
        print(f"❌ Delete profile error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления профиля")