"""API для аутентификации"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.database import get_db
from backend.services.auth_service import AuthService
from backend.models.user import User, UserRole

router = APIRouter()


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

    class Config:
        orm_mode = True


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse
    message: str
    is_new_user: bool


def get_current_user(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
) -> User:
    """Dependency для получения текущего пользователя"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Authentication required")

    auth_service = AuthService(db)
    telegram_data = auth_service.verify_telegram_auth(x_telegram_init_data)
    user = auth_service.get_or_create_user(telegram_data)

    return user


@router.post("/verify", response_model=AuthResponse)
async def verify_auth(
        x_telegram_init_data: str = Header(None),
        db: Session = Depends(get_db)
):
    """Верификация пользователя Telegram"""
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing Telegram auth data")

    auth_service = AuthService(db)

    # Проверяем данные Telegram
    telegram_data = auth_service.verify_telegram_auth(x_telegram_init_data)

    # Получаем или создаем пользователя
    user = auth_service.get_or_create_user(telegram_data)

    # Определяем новый ли пользователь
    is_new_user = (datetime.utcnow() - user.created_at).total_seconds() < 60

    return AuthResponse(
        success=True,
        user=UserResponse.from_orm(user),
        message="Authentication successful",
        is_new_user=is_new_user
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    return UserResponse.from_orm(current_user)


@router.post("/change-role/{user_id}")
async def change_user_role(
        user_id: int,
        new_role: UserRole,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Изменить роль пользователя (только админ)"""
    auth_service = AuthService(db)
    updated_user = auth_service.change_user_role(user_id, new_role, current_user)

    return {
        "success": True,
        "message": f"User role changed to {new_role.value}",
        "user": UserResponse.from_orm(updated_user)
    }