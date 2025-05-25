"""API для управления профилем"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

from backend.database import get_db
from backend.api.auth import get_current_user
from backend.models.user import User
from backend.models.volunteer_profile import VolunteerProfile

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    # Основные данные пользователя
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    # Данные профиля волонтера
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None

    # Контакты для экстренной связи
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Профессиональные данные
    education: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None

    # Навыки и интересы
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    experience_description: Optional[str] = None

    # Доступность
    travel_willingness: Optional[bool] = None
    max_travel_distance: Optional[int] = None
    preferred_activities: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    # Пользователь
    id: int
    first_name: str
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    avatar_url: Optional[str]
    role: str

    # Профиль волонтера
    middle_name: Optional[str]
    birth_date: Optional[date]
    age: Optional[int]
    gender: Optional[str]

    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relation: Optional[str]

    education: Optional[str]
    occupation: Optional[str]
    organization: Optional[str]

    skills: Optional[List[str]]
    interests: Optional[List[str]]
    languages: Optional[List[str]]
    experience_description: Optional[str]

    travel_willingness: Optional[bool]
    max_travel_distance: Optional[int]
    preferred_activities: Optional[List[str]]

    # Метаданные
    profile_completed: bool
    completion_percentage: int

    class Config:
        orm_mode = True


@router.get("/", response_model=ProfileResponse)
async def get_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить профиль пользователя"""

    # Создаем профиль волонтера если его нет
    if current_user.role.value == "volunteer" and not current_user.volunteer_profile:
        volunteer_profile = VolunteerProfile(user_id=current_user.id)
        db.add(volunteer_profile)
        db.commit()
        db.refresh(current_user)

    profile_data = {
        # Данные пользователя
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "bio": current_user.bio,
        "location": current_user.location,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value,

        # Значения по умолчанию для волонтерского профиля
        "profile_completed": False,
        "completion_percentage": 0,
    }

    # Добавляем данные профиля волонтера если есть
    if current_user.volunteer_profile:
        vp = current_user.volunteer_profile
        profile_data.update({
            "middle_name": vp.middle_name,
            "birth_date": vp.birth_date.date() if vp.birth_date else None,
            "age": vp.age,
            "gender": vp.gender,
            "emergency_contact_name": vp.emergency_contact_name,
            "emergency_contact_phone": vp.emergency_contact_phone,
            "emergency_contact_relation": vp.emergency_contact_relation,
            "education": vp.education,
            "occupation": vp.occupation,
            "organization": vp.organization,
            "skills": vp.skills or [],
            "interests": vp.interests or [],
            "languages": vp.languages or [],
            "experience_description": vp.experience_description,
            "travel_willingness": vp.travel_willingness,
            "max_travel_distance": vp.max_travel_distance,
            "preferred_activities": vp.preferred_activities or [],
            "profile_completed": vp.profile_completed,
            "completion_percentage": vp.completion_percentage,
        })

    return ProfileResponse(**profile_data)


@router.put("/", response_model=ProfileResponse)
async def update_profile(
        profile_data: ProfileUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновить профиль пользователя"""

    # Обновляем данные пользователя
    update_data = profile_data.dict(exclude_unset=True)

    # Поля пользователя
    user_fields = ['first_name', 'last_name', 'email', 'phone', 'bio', 'location']

    for field in user_fields:
        if field in update_data:
            setattr(current_user, field, update_data[field])

    current_user.updated_at = datetime.utcnow()

    # Обновляем профиль волонтера если пользователь - волонтер
    if current_user.role.value == "volunteer":
    # Создаем профиль если его нет
        if not current_user.volunteer_profile:
            volunteer_profile = VolunteerProfile(user_id=current_user.id)
            db.add(volunteer_profile)
            db.flush()  # Чтобы получить ID
            current_user.volunteer_profile = volunteer_profile

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
        if field in update_data:
            setattr(vp, field, update_data[field])

    # Проверяем заполненность профиля
    required_fields = [
        vp.middle_name, vp.birth_date, current_user.phone, current_user.email,
        vp.emergency_contact_name, vp.emergency_contact_phone,
        vp.education, vp.skills, vp.experience_description
    ]

    filled_count = sum(1 for field in required_fields if field)
    vp.profile_completed = filled_count >= 7  # Минимум 7 из 9 полей
    vp.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    # Возвращаем обновленный профиль
    return await get_profile(current_user, db)
