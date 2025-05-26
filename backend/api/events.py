from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
import logging

from backend.database import get_db
from backend.api.auth import get_current_user
from backend.models.user import User, UserRole
from backend.models.event import Event, EventStatus, EventCategory, EventLog, EventActionType
from backend.models.registration import Registration, RegistrationStatus
from backend.services.event_service import notify_volunteers_on_new_event, notify_organizer_on_full

router = APIRouter()
logger = logging.getLogger(__name__)


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

    # Новые поля для статистики заявок
    total_registrations: Optional[int] = 0
    approved_registrations: Optional[int] = 0
    pending_registrations: Optional[int] = 0

    class Config:
        from_attributes = True


class RegistrationUserInfo(BaseModel):
    id: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    status: str


class EventStatusUpdateRequest(BaseModel):
    status: str


class BulkEventActionRequest(BaseModel):
    event_ids: list[int]


class EventLogResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    action: str
    timestamp: datetime
    details: str | None = None


# Вспомогательная функция для логирования
async def log_event_action(db, event_id, user_id, action: EventActionType, details: str = None):
    log = EventLog(event_id=event_id, user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()


@router.get("", response_model=List[EventResponse])
async def get_events_alias(
        status: Optional[EventStatus] = Query(None),
        category: Optional[EventCategory] = Query(None),
        search: Optional[str] = Query(None),
        upcoming_only: bool = Query(True),
        limit: int = Query(50, le=100),
        offset: int = Query(0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return await get_events(status, category, search, upcoming_only, limit, offset, current_user, db)


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
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "short_description": event.short_description,
            "category": event.category.value,
            "tags": event.tags or [],
            "location": event.location,
            "address": event.address,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "registration_deadline": event.registration_deadline,
            "max_volunteers": event.max_volunteers,
            "min_volunteers": event.min_volunteers,
            "current_volunteers_count": len(event.registrations) if hasattr(event, 'registrations') else 0,
            "available_slots": event.available_slots if hasattr(event, 'available_slots') else 0,
            "progress_percentage": event.progress_percentage if hasattr(event, 'progress_percentage') else 0,
            "required_skills": event.required_skills or [],
            "preferred_skills": event.preferred_skills or [],
            "min_age": event.min_age,
            "max_age": event.max_age,
            "requirements_description": event.requirements_description,
            "what_to_bring": event.what_to_bring,
            "dress_code": event.dress_code,
            "meal_provided": event.meal_provided if event.meal_provided is not None else False,
            "transport_provided": event.transport_provided if event.transport_provided is not None else False,
            "contact_person": event.contact_person,
            "contact_phone": event.contact_phone,
            "contact_email": event.contact_email,
            "status": event.status.value,
            "is_featured": event.is_featured if hasattr(event, 'is_featured') else False,
            "views_count": event.views_count if hasattr(event, 'views_count') else 0,
            "creator_name": event.creator.full_name if event.creator else "Неизвестно",
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "can_register": event.can_register(current_user) if hasattr(event, 'can_register') else False,
            "user_registration_status": user_registrations.get(event.id),
            "total_registrations": 0,
            "approved_registrations": 0,
            "pending_registrations": 0,
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

    # Статистика по заявкам для организатора и админа
    total_registrations = 0
    approved_registrations = 0
    pending_registrations = 0
    if current_user.is_admin() or event.creator_id == current_user.id:
        regs = db.query(Registration).filter(Registration.event_id == event_id).all()
        total_registrations = len(regs)
        approved_registrations = sum(1 for r in regs if r.status == RegistrationStatus.APPROVED)
        pending_registrations = sum(1 for r in regs if r.status == RegistrationStatus.PENDING)

    event_data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "short_description": event.short_description,
        "category": event.category.value,
        "tags": event.tags or [],
        "location": event.location,
        "address": event.address,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "registration_deadline": event.registration_deadline,
        "max_volunteers": event.max_volunteers,
        "min_volunteers": event.min_volunteers,
        "current_volunteers_count": len(event.registrations) if hasattr(event, 'registrations') else 0,
        "available_slots": event.available_slots if hasattr(event, 'available_slots') else 0,
        "progress_percentage": event.progress_percentage if hasattr(event, 'progress_percentage') else 0,
        "required_skills": event.required_skills or [],
        "preferred_skills": event.preferred_skills or [],
        "min_age": event.min_age,
        "max_age": event.max_age,
        "requirements_description": event.requirements_description,
        "what_to_bring": event.what_to_bring,
        "dress_code": event.dress_code,
        "meal_provided": event.meal_provided if event.meal_provided is not None else False,
        "transport_provided": event.transport_provided if event.transport_provided is not None else False,
        "contact_person": event.contact_person,
        "contact_phone": event.contact_phone,
        "contact_email": event.contact_email,
        "status": event.status.value,
        "is_featured": event.is_featured if hasattr(event, 'is_featured') else False,
        "views_count": event.views_count if hasattr(event, 'views_count') else 0,
        "creator_name": event.creator.full_name if event.creator else "Неизвестно",
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "can_register": event.can_register(current_user) if hasattr(event, 'can_register') else False,
        "user_registration_status": user_registration.status.value if user_registration else None,
        "total_registrations": total_registrations,
        "approved_registrations": approved_registrations,
        "pending_registrations": pending_registrations,
    }
    return EventResponse(**event_data)


@router.post("", response_model=EventResponse)
async def create_event_alias(
        event_data: EventCreateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return await create_event(event_data, current_user, db)


@router.post("/", response_model=EventResponse)
async def create_event(
        event_data: EventCreateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Создать новое мероприятие (только для организаторов и админов)"""
    logger.info(f"Попытка создания мероприятия пользователем {current_user.id} (роль: {current_user.role})")
    
    if not (current_user.role == UserRole.ORGANIZER or current_user.role == UserRole.ADMIN):
        logger.warning(f"Отказано в доступе: пользователь {current_user.id} не является организатором или админом")
        raise HTTPException(
            status_code=403,
            detail="Only organizers and admins can create events"
        )

    # Валидация дат
    if event_data.start_date >= event_data.end_date:
        logger.warning(f"Некорректные даты: start_date={event_data.start_date}, end_date={event_data.end_date}")
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    if event_data.registration_deadline and event_data.registration_deadline >= event_data.start_date:
        logger.warning(f"Некорректная дата регистрации: deadline={event_data.registration_deadline}, start_date={event_data.start_date}")
        raise HTTPException(
            status_code=400,
            detail="Registration deadline must be before event start date"
        )

    try:
        # Создание мероприятия
        logger.info(f"Создание мероприятия с данными: {event_data.dict()}")
        event = Event(
            creator_id=current_user.id,
            status=EventStatus.DRAFT,  # Устанавливаем начальный статус
            **event_data.dict()
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Мероприятие успешно создано с ID: {event.id}")
        
        await log_event_action(db, event.id, current_user.id, EventActionType.CREATE)

        event_data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "short_description": event.short_description,
            "category": event.category.value,
            "tags": event.tags or [],
            "location": event.location,
            "address": event.address,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "registration_deadline": event.registration_deadline,
            "max_volunteers": event.max_volunteers,
            "min_volunteers": event.min_volunteers,
            "current_volunteers_count": 0,
            "available_slots": event.available_slots if hasattr(event, 'available_slots') else 0,
            "progress_percentage": event.progress_percentage if hasattr(event, 'progress_percentage') else 0,
            "required_skills": event.required_skills or [],
            "preferred_skills": event.preferred_skills or [],
            "min_age": event.min_age,
            "max_age": event.max_age,
            "requirements_description": event.requirements_description,
            "what_to_bring": event.what_to_bring,
            "dress_code": event.dress_code,
            "meal_provided": event.meal_provided if event.meal_provided is not None else False,
            "transport_provided": event.transport_provided if event.transport_provided is not None else False,
            "contact_person": event.contact_person,
            "contact_phone": event.contact_phone,
            "contact_email": event.contact_email,
            "status": event.status.value,
            "is_featured": event.is_featured if hasattr(event, 'is_featured') else False,
            "views_count": event.views_count if hasattr(event, 'views_count') else 0,
            "creator_name": current_user.full_name,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "can_register": False,
            "user_registration_status": None,
            "total_registrations": 0,
            "approved_registrations": 0,
            "pending_registrations": 0,
        }
        logger.info(f"Мероприятие успешно создано и возвращено: {event_data}")
        return EventResponse(**event_data)
    except Exception as e:
        logger.error(f"Ошибка при создании мероприятия: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create event: {str(e)}"
        )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
        event_id: int,
        event_data: EventUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    # Проверяем, является ли пользователь создателем мероприятия
    if event.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="У вас нет прав на редактирование этого мероприятия")

    # Обновляем поля мероприятия
    for field, value in event_data.dict(exclude_unset=True).items():
        setattr(event, field, value)

    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)

    # Логируем действие
    await log_event_action(db, event.id, current_user.id, EventActionType.UPDATE)

    return event


@router.delete("/{event_id}", response_model=EventResponse)
async def delete_event(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Проверяем, является ли пользователь создателем мероприятия
    if event.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого мероприятия")

    event.status = EventStatus.DELETED
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)

    # Логируем действие
    await log_event_action(db, event.id, current_user.id, EventActionType.DELETE)

    return event


@router.get("/my/created", response_model=List[EventResponse])
async def get_my_events(
        status: Optional[EventStatus] = Query(None),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить мероприятия созданные пользователем (с фильтрацией по статусу)"""
    print(f"DEBUG: Запрос списка созданных мероприятий от пользователя {current_user.id} (роль: {current_user.role})")

    if not current_user.is_organizer():
        print(f"DEBUG: Отказано в доступе: пользователь {current_user.id} не является организатором")
        raise HTTPException(
            status_code=403,
            detail="Only organizers can view created events"
        )

    # Базовый запрос - все события пользователя
    query = db.query(Event).filter(Event.creator_id == current_user.id)
    print(f"DEBUG: Базовый запрос для пользователя {current_user.id}")
    
    # Если статус не указан, показываем все события, кроме удаленных
    if not status:
        query = query.filter(Event.status != EventStatus.CANCELLED)
        print("DEBUG: Фильтр: все события, кроме удаленных")
    else:
        query = query.filter(Event.status == status)
        print(f"DEBUG: Фильтр по статусу: {status}")
        
    events = query.order_by(Event.created_at.desc()).all()
    print(f"DEBUG: Найдено {len(events)} мероприятий")
    
    for event in events:
        print(f"DEBUG: Мероприятие {event.id}: {event.title} (статус: {event.status.value}, создатель: {event.creator_id})")

    result = []
    for event in events:
        event_data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "short_description": event.short_description,
            "category": event.category.value,
            "tags": event.tags or [],
            "location": event.location,
            "address": event.address,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "registration_deadline": event.registration_deadline,
            "max_volunteers": event.max_volunteers,
            "min_volunteers": event.min_volunteers,
            "current_volunteers_count": len(event.registrations) if hasattr(event, 'registrations') else 0,
            "available_slots": event.available_slots if hasattr(event, 'available_slots') else 0,
            "progress_percentage": event.progress_percentage if hasattr(event, 'progress_percentage') else 0,
            "required_skills": event.required_skills or [],
            "preferred_skills": event.preferred_skills or [],
            "min_age": event.min_age,
            "max_age": event.max_age,
            "requirements_description": event.requirements_description,
            "what_to_bring": event.what_to_bring,
            "dress_code": event.dress_code,
            "meal_provided": event.meal_provided if event.meal_provided is not None else False,
            "transport_provided": event.transport_provided if event.transport_provided is not None else False,
            "contact_person": event.contact_person,
            "contact_phone": event.contact_phone,
            "contact_email": event.contact_email,
            "status": event.status.value,
            "is_featured": event.is_featured if hasattr(event, 'is_featured') else False,
            "views_count": event.views_count if hasattr(event, 'views_count') else 0,
            "creator_name": event.creator.full_name if event.creator else "Неизвестно",
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "can_register": event.can_register(current_user) if hasattr(event, 'can_register') else False,
            "user_registration_status": None,
            "total_registrations": 0,
            "approved_registrations": 0,
            "pending_registrations": 0,
        }
        result.append(EventResponse(**event_data))
        print(f"DEBUG: Добавлено мероприятие в результат: {event.id} - {event.title}")

    print(f"DEBUG: Возвращаем {len(result)} мероприятий")
    return result


@router.get("/{event_id}/registrations", response_model=List[RegistrationUserInfo])
async def get_event_registrations(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not (current_user.is_admin() or event.creator_id == current_user.id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    result = []
    for reg in registrations:
        user = reg.user
        result.append(RegistrationUserInfo(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            status=reg.status.value
        ))
    return result


@router.patch("/{event_id}/status", response_model=EventResponse)
async def update_event_status(
    event_id: int,
    data: EventStatusUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Проверяем, является ли пользователь создателем мероприятия
    if event.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="У вас нет прав на изменение статуса этого мероприятия")

    try:
        new_status = EventStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Недопустимый статус мероприятия")

    event.status = new_status
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)

    # Логируем действие
    await log_event_action(db, event.id, current_user.id, EventActionType.STATUS_CHANGE, f"Статус изменен на {new_status}")

    return event


@router.post("/{event_id}/restore", response_model=EventResponse)
async def restore_event(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Восстановить отменённое мероприятие (перевести из cancelled в draft). Организатор — только свои, админ — любые."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != EventStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Можно восстановить только отменённое мероприятие")
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.ORGANIZER:
        if event.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Organizers can only restore their own events")
    else:
        raise HTTPException(status_code=403, detail="Only organizers and admins can restore events")
    event.status = EventStatus.DRAFT
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    await log_event_action(db, event.id, current_user.id, EventActionType.RESTORE)
    return await get_event(event_id, current_user, db)


@router.delete("/{event_id}/hard", response_model=dict)
async def hard_delete_event(
        event_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Жёсткое удаление мероприятия (только для администратора)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Only admin can hard delete events")
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    await log_event_action(db, event_id, current_user.id, EventActionType.DELETE)
    return {"message": "Event permanently deleted"}


@router.post("/bulk/publish", response_model=list[EventResponse])
async def bulk_publish_events(
    data: BulkEventActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = []
    for event_id in data.event_ids:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            continue
        if not (current_user.is_admin() or event.creator_id == current_user.id):
            continue
        event.status = EventStatus.PUBLISHED
        if not event.published_at:
            event.published_at = datetime.utcnow()
        event.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(event)
        await log_event_action(db, event.id, current_user.id, EventActionType.PUBLISH, "bulk")
        result.append(await get_event(event_id, current_user, db))
    return result


@router.post("/bulk/cancel", response_model=list[EventResponse])
async def bulk_cancel_events(
    data: BulkEventActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = []
    for event_id in data.event_ids:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            continue
        if not (current_user.is_admin() or event.creator_id == current_user.id):
            continue
        event.status = EventStatus.CANCELLED
        event.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(event)
        await log_event_action(db, event.id, current_user.id, EventActionType.CANCEL, "bulk")
        result.append(await get_event(event_id, current_user, db))
    return result


@router.post("/bulk/delete", response_model=list[dict])
async def bulk_delete_events(
    data: BulkEventActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Only admin can bulk delete events")
    result = []
    for event_id in data.event_ids:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            continue
        db.delete(event)
        db.commit()
        await log_event_action(db, event_id, current_user.id, EventActionType.DELETE, "bulk")
        result.append({"id": event_id, "deleted": True})
    return result


@router.get("/export")
async def export_events(
    status: Optional[EventStatus] = Query(None),
    category: Optional[EventCategory] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if status:
        query = query.filter(Event.status == status)
    if category:
        query = query.filter(Event.category == category)
    if start_date:
        query = query.filter(Event.start_date >= start_date)
    if end_date:
        query = query.filter(Event.end_date <= end_date)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term)
            )
        )
    events = query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "status", "category", "start_date", "end_date", "location", "max_volunteers", "current_volunteers_count"
    ])
    for event in events:
        writer.writerow([
            event.id, event.title, event.status.value, event.category.value,
            event.start_date, event.end_date, event.location,
            event.max_volunteers, len(event.registrations) if hasattr(event, 'registrations') else 0
        ])
    output.seek(0)
    # Логируем экспорт
    for event in events:
        await log_event_action(db, event.id, None, EventActionType.EXPORT, "export events.csv")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=events.csv"})


@router.get("/{event_id}/registrations/export")
async def export_event_registrations(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not (current_user.is_admin() or event.creator_id == current_user.id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "full_name", "email", "phone", "status"])
    for reg in registrations:
        user = reg.user
        writer.writerow([
            user.id, user.full_name, user.email, user.phone, reg.status.value
        ])
    output.seek(0)
    await log_event_action(db, event_id, current_user.id, EventActionType.EXPORT, "export registrations.csv")
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=event_{event_id}_registrations.csv"})