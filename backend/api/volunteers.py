"""
API для работы с волонтерами
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.volunteer_service import VolunteerService
from backend.api.telegram_auth import get_current_user

router = APIRouter()


class VolunteerCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: EmailStr
    phone: str
    birth_date: date
    address: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    notes: Optional[str] = None


class VolunteerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class VolunteerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    email: str
    phone: str
    birth_date: date
    address: Optional[str]
    skills: List[str]
    experience: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    notes: Optional[str]
    is_active: bool
    age: Optional[int]
    full_name: str

    class Config:
        orm_mode = True


@router.get("/", response_model=List[VolunteerResponse])
async def get_volunteers(
        active_only: bool = Query(True),
        search: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Получить список волонтеров"""
    service = VolunteerService(db)

    if search:
        volunteers = service.search_volunteers(search)
    else:
        volunteers = service.get_all_volunteers(active_only)

    return volunteers


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
async def get_volunteer(
        volunteer_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Получить волонтера по ID"""
    service = VolunteerService(db)
    volunteer = service.get_volunteer(volunteer_id)

    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    return volunteer


@router.post("/", response_model=VolunteerResponse)
async def create_volunteer(
        volunteer_data: VolunteerCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Создать нового волонтера"""
    service = VolunteerService(db)

    try:
        volunteer = service.create_volunteer(volunteer_data.dict())
        return volunteer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{volunteer_id}", response_model=VolunteerResponse)
async def update_volunteer(
        volunteer_id: int,
        volunteer_data: VolunteerUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Обновить данные волонтера"""
    service = VolunteerService(db)

    try:
        # Исключаем None значения
        update_data = {k: v for k, v in volunteer_data.dict().items() if v is not None}
        volunteer = service.update_volunteer(volunteer_id, update_data)
        return volunteer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{volunteer_id}")
async def delete_volunteer(
        volunteer_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """Удалить волонтера (мягкое удаление)"""
    service = VolunteerService(db)

    success = service.delete_volunteer(volunteer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    return {"message": "Volunteer deleted successfully"}