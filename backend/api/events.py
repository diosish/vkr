from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.database import get_db
from backend.api.auth import get_current_user
from backend.models.user import User, UserRole
from backend.models.event import Event, EventStatus, EventCategory
from backend.models.registration import Registration, RegistrationStatus

router = APIRouter()


class EventCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: EventCategory
    tags: Optional[List[str]] = []

    location: Optional[str] = None
    address: Optional[str] = None
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None

    max_volunteers: int = 0
    min_volunteers: int = 1

    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    requirements_description: Optional[str] = None

    what_to_bring: Optional[str] = None
    dress_code: Optional[str] = None
    meal_provided: bool = False
    transport_provided: bool = False

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[EventCategory] = None
    tags: Optional[List[str]] = None

    location: Optional[str] = None
    address: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None

    max_volunteers: Optional[int] = None
    min_volunteers: Optional[int] = None

    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    requirements_description: Optional[str] = None

    what_to_bring: Optional[str] = None
    dress_code: Optional[str] = None
    meal_provided: Optional[bool] = None
    transport_provided: Optional[bool] = None

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    status: Optional[EventStatus] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    short_description: Optional[str]
    category: str
    tags: List[str]

    location: Optional[str]
    address: Optional[str]
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime]

    max_volunteers: int
    min_volunteers: int
    current_volunteers_count: int
    available_slots: int
    progress_percentage: int

    required_skills: List[str]
    preferred_skills: List[str]
    min_age: Optional[int]
    max_age: Optional[int]
    requirements_description: Optional[str]

    what_to_bring: Optional[str]
    dress_code: Optional[str]
    meal_provided: bool
    transport_provided: bool

    contact_person: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]

    status: str
    is_featured: bool
    views_count: int

    creator_name: str
    created_at: datetime
    updated_at: datetime

    # Флаги для текущего пользователя
    can_register: bool
    user_registration_status: Optional[str]

    class Config:
        orm_mode = True


@router.get("/", response_model=List[EventResponse])
async def get_events(
        status: Optional[EventStatus] = Query(None),
        category: Optional[EventCategory] = Query(None),
        search: Optional[str] = Query(None),
        upcoming_only: bool = Query(True),
        limit: int = Query(50, le=100),
        offset: int = Query(0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить список мероприятий"""

    query = db.query(Event)

    # Фильтры
    if status:
        query = query.filter(Event.status == status)
    else:
        # По умолчанию показываем только опубликованные
        query = query.filter(Event.status == EventStatus.PUBLISHED)

    if category:
        query = query.filter(Event.category == category)

    if upcoming_only:
        query = query.filter(Event.start_date > datetime.utcnow())

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term)
            )
        )

    # Сортировка
    query = query.order_by(Event.start_date.asc())

    # Пагинация
    events = query.offset(offset).limit(limit).all()

    # Получаем статусы регистрации пользователя
    user_registrations = {}
    if current_user.role == UserRole.VOLUNTEER:
        registrations = db.query(Registration).filter(
            Registration.user_id == current_user.id,
            Registration.event_id.in_([e.id for e in events])
        ).all()
        user_registrations = {reg.event_id: reg.status.value for reg in registrations}

    # Формируем ответ
    result = []
    for event in events:
        event_data = {
            **event.__dict__,
            "category": event.category.value,
            "status": event.status.value,
            "tags": event.tags or [],
            "required_skills": event.required_skills or [],
            "preferred_skills": event.preferred_skills or [],
            "creator_name": event.creator.full_name if event.creator else "Неизвестно",
            "can_register": event.can_register(current_user),
            "user_registration_status": user_registrations.get(event.id),
            "available_slots": event.available_slots,
            "progress_percentage": event.progress_percentage
        }
        result.append(EventResponse(**event_data))

    return result


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить мероприятие по ID"""

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Увеличиваем счетчик просмотров
    event.views_count += 1
    db.commit()

    # Проверяем регистрацию пользователя
    user_registration = None
    if current_user.role == UserRole.VOLUNTEER:
        user_registration = db.query(Registration).filter(
            and_(
                Registration.user_id == current_user.id,
                Registration.event_id == event_id
            )
        ).first()

    event_data = {
        **event.__dict__,
        "category": event.category.value,
        "status": event.status.value,
        "tags": event.tags or [],
        "required_skills": event.required_skills or [],
        "preferred_skills": event.preferred_skills or [],
        "creator_name": event.creator.full_name if event.creator else "Неизвестно",
        "can_register": event.can_register(current_user),
        "user_registration_status": user_registration.status.value if user_registration else None,
        "available_slots": event.available_slots,
        "progress_percentage": event.progress_percentage
    }

    return EventResponse(**event_data)


@router.post("/", response_model=EventResponse)
async def create_event(
        event_data: EventCreateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Создать новое мероприятие"""

    # Только организаторы и админы могут создавать мероприятия
    if not current_user.is_organizer():
        raise HTTPException(
            status_code=403,
            detail="Only organizers and admins can create events"
        )

    # Валидация дат
    if event_data.start_date >= event_data.end_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    if event_data.registration_deadline and event_data.registration_deadline >= event_data.start_date:
        raise HTTPException(
            status_code=400,
            detail="Registration deadline must be before event start date"
        )

    # Создание мероприятия
    event = Event(
        creator_id=current_user.id,
        **event_data.dict()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return await get_event(event.id, current_user, db)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
        event_id: int,
        event_data: EventUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновить мероприятие"""

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Проверка прав доступа
    if not (current_user.is_admin() or event.creator_id == current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own events"
        )

    # Обновление полей
    update_data = event_data.dict(exclude_unset=True)

    # Валидация дат если они обновляются
    start_date = update_data.get('start_date', event.start_date)
    end_date = update_data.get('end_date', event.end_date)

    if start_date >= end_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    for field, value in update_data.items():
        setattr(event, field, value)

    event.updated_at = datetime.utcnow()

    # Если меняем статус на опубликованный
    if update_data.get('status') == EventStatus.PUBLISHED and not event.published_at:
        event.published_at = datetime.utcnow()

    db.commit()
    db.refresh(event)

    return await get_event(event.id, current_user, db)


@router.delete("/{event_id}")
async def delete_event(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Удалить мероприятие"""

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Проверка прав доступа
    if not (current_user.is_admin() or event.creator_id == current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own events"
        )

    # Мягкое удаление - меняем статус
    event.status = EventStatus.CANCELLED
    event.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Event cancelled successfully"}


@router.get("/my/created", response_model=List[EventResponse])
async def get_my_events(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить мероприятия созданные пользователем"""

    if not current_user.is_organizer():
        raise HTTPException(
            status_code=403,
            detail="Only organizers can view created events"
        )

    events = db.query(Event).filter(
        Event.creator_id == current_user.id
    ).order_by(Event.created_at.desc()).all()

    result = []
    for event in events:
        event_data = {
            **event.__dict__,
            "category": event.category.value,
            "status": event.status.value,
            "tags": event.tags or [],
            "required_skills": event.required_skills or [],
            "preferred_skills": event.preferred_skills or [],
            "creator_name": current_user.full_name,
            "can_register": False,  # Создатель не может регистрироваться
            "user_registration_status": None,
            "available_slots": event.available_slots,
            "progress_percentage": event.progress_percentage
        }
        result.append(EventResponse(**event_data))

    return result