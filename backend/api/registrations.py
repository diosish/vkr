"""API для регистрации на мероприятия"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.database import get_db
from backend.api.auth import get_current_user
from backend.models.user import User, UserRole
from backend.models.event import Event
from backend.models.registration import Registration, RegistrationStatus
from backend.services.event_service import notify_organizer_on_full

router = APIRouter()


class RegistrationCreateRequest(BaseModel):
    event_id: int
    motivation: Optional[str] = None
    relevant_experience: Optional[str] = None
    availability_notes: Optional[str] = None
    special_requirements: Optional[str] = None


class RegistrationUpdateRequest(BaseModel):
    motivation: Optional[str] = None
    relevant_experience: Optional[str] = None
    availability_notes: Optional[str] = None
    special_requirements: Optional[str] = None
    organizer_notes: Optional[str] = None
    status: Optional[RegistrationStatus] = None


class RegistrationResponse(BaseModel):
    id: int
    event_id: int
    event_title: str
    event_start_date: datetime
    event_location: Optional[str]

    status: str
    motivation: Optional[str]
    relevant_experience: Optional[str]
    availability_notes: Optional[str]
    special_requirements: Optional[str]
    organizer_notes: Optional[str]

    registered_at: datetime
    confirmed_at: Optional[datetime]

    volunteer_name: str
    volunteer_phone: Optional[str]
    volunteer_email: Optional[str]

    class Config:
        orm_mode = True


@router.post("/", response_model=RegistrationResponse)
async def register_for_event(
        registration_data: RegistrationCreateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Зарегистрироваться на мероприятие"""

    # Только волонтеры могут регистрироваться
    if current_user.role != UserRole.VOLUNTEER:
        raise HTTPException(
            status_code=403,
            detail="Only volunteers can register for events"
        )

    # Проверяем существование мероприятия
    event = db.query(Event).filter(Event.id == registration_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Проверяем возможность регистрации
    if not event.can_register(current_user):
        raise HTTPException(
            status_code=400,
            detail="Registration is not available for this event"
        )

    # Проверяем что пользователь еще не зарегистрирован
    existing_registration = db.query(Registration).filter(
        and_(
            Registration.user_id == current_user.id,
            Registration.event_id == registration_data.event_id,
            Registration.status.in_([RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED])
        )
    ).first()

    if existing_registration:
        raise HTTPException(
            status_code=400,
            detail="You are already registered for this event"
        )

    # Создаем регистрацию
    registration = Registration(
        user_id=current_user.id,
        event_id=registration_data.event_id,
        motivation=registration_data.motivation,
        relevant_experience=registration_data.relevant_experience,
        availability_notes=registration_data.availability_notes,
        special_requirements=registration_data.special_requirements
    )

    db.add(registration)

    # Увеличиваем счетчик волонтеров (если автоподтверждение)
    # Пока делаем автоподтверждение для простоты
    registration.status = RegistrationStatus.CONFIRMED
    registration.confirmed_at = datetime.utcnow()
    event.current_volunteers_count += 1

    db.commit()
    db.refresh(registration)

    # Проверяем, не укомплектовано ли мероприятие после подтверждения
    if registration.status == RegistrationStatus.CONFIRMED and event.is_full:
        notify_organizer_on_full(db, event)

    # Формируем ответ
    response_data = {
        **registration.__dict__,
        "event_title": event.title,
        "event_start_date": event.start_date,
        "event_location": event.location,
        "status": registration.status.value,
        "volunteer_name": current_user.full_name,
        "volunteer_phone": current_user.phone,
        "volunteer_email": current_user.email
    }

    return RegistrationResponse(**response_data)


@router.get("/my", response_model=List[RegistrationResponse])
async def get_my_registrations(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить свои регистрации"""

    if current_user.role != UserRole.VOLUNTEER:
        raise HTTPException(
            status_code=403,
            detail="Only volunteers can view registrations"
        )

    registrations = db.query(Registration).filter(
        Registration.user_id == current_user.id
    ).order_by(Registration.registered_at.desc()).all()

    result = []
    for reg in registrations:
        response_data = {
            **reg.__dict__,
            "event_title": reg.event.title,
            "event_start_date": reg.event.start_date,
            "event_location": reg.event.location,
            "status": reg.status.value,
            "volunteer_name": current_user.full_name,
            "volunteer_phone": current_user.phone,
            "volunteer_email": current_user.email
        }
        result.append(RegistrationResponse(**response_data))

    return result


@router.put("/{registration_id}", response_model=RegistrationResponse)
async def update_registration(
        registration_id: int,
        update_data: RegistrationUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновить регистрацию"""

    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Проверка прав доступа
    is_owner = registration.user_id == current_user.id
    is_event_creator = registration.event.creator_id == current_user.id
    is_admin = current_user.is_admin()

    if not (is_owner or is_event_creator or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    # Обновление полей
    update_fields = update_data.dict(exclude_unset=True)

    for field, value in update_fields.items():
        # Только организатор может менять статус и заметки организатора
        if field in ['status', 'organizer_notes'] and not (is_event_creator or is_admin):
            continue

        setattr(registration, field, value)

    # Обновляем счетчик волонтеров при изменении статуса
    if 'status' in update_fields:
        old_status = registration.status
        new_status = update_fields['status']

        if old_status == RegistrationStatus.CONFIRMED and new_status != RegistrationStatus.CONFIRMED:
            registration.event.current_volunteers_count -= 1
        elif old_status != RegistrationStatus.CONFIRMED and new_status == RegistrationStatus.CONFIRMED:
            registration.event.current_volunteers_count += 1
            registration.confirmed_at = datetime.utcnow()

        # Проверяем, не укомплектовано ли мероприятие после подтверждения
        if new_status == RegistrationStatus.CONFIRMED and registration.event.is_full:
            notify_organizer_on_full(db, registration.event)

    registration.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(registration)

    # Формируем ответ
    response_data = {
        **registration.__dict__,
        "event_title": registration.event.title,
        "event_start_date": registration.event.start_date,
        "event_location": registration.event.location,
        "status": registration.status.value,
        "volunteer_name": registration.user.full_name,
        "volunteer_phone": registration.user.phone,
        "volunteer_email": registration.user.email
    }

    return RegistrationResponse(**response_data)


@router.delete("/{registration_id}")
async def cancel_registration(
        registration_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Отменить регистрацию"""

    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Проверка прав доступа
    if registration.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="You can only cancel your own registrations"
        )

    # Проверяем возможность отмены
    if not registration.can_cancel():
        raise HTTPException(
            status_code=400,
            detail="This registration cannot be cancelled"
        )

    # Отменяем регистрацию
    if registration.status == RegistrationStatus.CONFIRMED:
        registration.event.current_volunteers_count -= 1

    registration.status = RegistrationStatus.CANCELLED
    registration.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Registration cancelled successfully"}


@router.get("/event/{event_id}", response_model=List[RegistrationResponse])
async def get_event_registrations(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить регистрации на мероприятие (для организаторов)"""

    # Проверяем мероприятие
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Проверка прав доступа
    if not (current_user.is_admin() or event.creator_id == current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only view registrations for your own events"
        )

    registrations = db.query(Registration).filter(
        Registration.event_id == event_id
    ).order_by(Registration.registered_at.desc()).all()

    result = []
    for reg in registrations:
        response_data = {
            **reg.__dict__,
            "event_title": event.title,
            "event_start_date": event.start_date,
            "event_location": event.location,
            "status": reg.status.value,
            "volunteer_name": reg.user.full_name,
            "volunteer_phone": reg.user.phone,
            "volunteer_email": reg.user.email
        }
        result.append(RegistrationResponse(**response_data))

    return result