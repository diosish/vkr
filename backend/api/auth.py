# backend/api/auth.py
"""API для аутентификации и регистрации"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

from backend.database import get_db
from backend.services.telegram_auth_service import TelegramAuthService
from backend.models.user import User, UserRole

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


def get_current_user(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
) -> User:
    """Dependency для получения текущего пользователя"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Authentication required")

    auth_service = TelegramAuthService(db)
    telegram_data = auth_service.verify_telegram_auth(x_telegram_init_data)
    user, _ = auth_service.get_or_create_user(telegram_data)

    return user


@router.post("/verify", response_model=AuthResponse)
async def verify_auth(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
):
    """Верификация пользователя Telegram"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram auth data")

    auth_service = TelegramAuthService(db)

    # Проверяем данные Telegram
    telegram_data = auth_service.verify_telegram_auth(x_telegram_init_data)

    # Получаем или создаем пользователя
    user, is_new_user = auth_service.get_or_create_user(telegram_data)

    # Проверяем нужна ли дополнительная регистрация
    requires_registration = False
    if user.role == UserRole.VOLUNTEER:
        # Для волонтеров проверяем заполненность профиля
        requires_registration = not user.email or not user.phone
        if user.volunteer_profile:
            requires_registration = requires_registration or user.volunteer_profile.completion_percentage < 70

    # Формируем ответ
    user_data = UserResponse.model_validate(user)
    if user.volunteer_profile:
        user_data.profile_completed = user.volunteer_profile.profile_completed
        user_data.completion_percentage = user.volunteer_profile.completion_percentage

    return AuthResponse(
        success=True,
        user=user_data,
        message="Authentication successful",
        is_new_user=is_new_user,
        requires_registration=requires_registration
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    user_data = UserResponse.model_validate(current_user)
    if current_user.volunteer_profile:
        user_data.profile_completed = current_user.volunteer_profile.profile_completed
        user_data.completion_percentage = current_user.volunteer_profile.completion_percentage
    
    return user_data


@router.post("/complete-registration", response_model=UserResponse)
async def complete_registration(
        registration_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Дополнение регистрации пользователя"""
    auth_service = TelegramAuthService(db)
    
    try:
        updated_user = auth_service.complete_user_registration(
            current_user.id, 
            registration_data.model_dump(exclude_unset=True)
        )
        
        user_data = UserResponse.model_validate(updated_user)
        if updated_user.volunteer_profile:
            user_data.profile_completed = updated_user.volunteer_profile.profile_completed
            user_data.completion_percentage = updated_user.volunteer_profile.completion_percentage
        
        return user_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profile", response_model=UserResponse)
async def update_profile(
        profile_data: UserRegistrationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    return await complete_registration(profile_data, current_user, db)


@router.post("/change-role/{user_id}")
async def change_user_role(
        user_id: int,
        new_role: UserRole,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Изменить роль пользователя (только админ)"""
    auth_service = TelegramAuthService(db)
    updated_user = auth_service.change_user_role(user_id, new_role, current_user)

    return {
        "success": True,
        "message": f"User role changed to {new_role.value}",
        "user": UserResponse.model_validate(updated_user)
    }


@router.get("/users", response_model=List[UserResponse])
async def get_users(
        role: Optional[UserRole] = None,
        active_only: bool = True,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить список пользователей (только для админов и организаторов)"""
    if not current_user.is_organizer():
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.order_by(User.created_at.desc()).all()
    
    return [UserResponse.model_validate(user) for user in users]