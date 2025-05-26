from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.api.auth import get_current_user
from backend.models.event import Event, EventStatus, EventCategory

router = APIRouter()

class UserListItem(BaseModel):
    id: int
    telegram_user_id: int
    first_name: str
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    organization_name: Optional[str]

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    organization_name: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    org_contact_name: Optional[str] = None
    org_phone: Optional[str] = None
    org_email: Optional[str] = None
    org_address: Optional[str] = None

class AdminStats(BaseModel):
    users_total: int
    volunteers_total: int
    organizers_total: int
    admins_total: int
    organizations_total: int
    events_total: int

class EventListItem(BaseModel):
    id: int
    title: str
    category: str
    status: str
    start_date: datetime
    end_date: datetime
    creator_id: int
    location: Optional[str]
    class Config:
        from_attributes = True

class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    address: Optional[str] = None
    max_volunteers: Optional[int] = None
    required_skills: Optional[list] = None
    what_to_bring: Optional[str] = None
    meal_provided: Optional[bool] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

@router.get("/users", response_model=List[UserListItem])
async def get_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список пользователей с фильтрацией"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    query = db.query(User)
    
    if role:
        query = query.filter(User.role == UserRole(role))
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(search)) |
            (User.last_name.ilike(search)) |
            (User.email.ilike(search)) |
            (User.organization_name.ilike(search))
        )
    
    return query.all()

@router.get("/users/{user_id}", response_model=UserListItem)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о пользователе"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить данные пользователя"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновляем только переданные поля
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.role is not None:
        user.role = UserRole(user_data.role)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.organization_name is not None:
        user.organization_name = user_data.organization_name
    if user_data.inn is not None:
        user.inn = user_data.inn
    if user_data.ogrn is not None:
        user.ogrn = user_data.ogrn
    if user_data.org_contact_name is not None:
        user.org_contact_name = user_data.org_contact_name
    if user_data.org_phone is not None:
        user.org_phone = user_data.org_phone
    if user_data.org_email is not None:
        user.org_email = user_data.org_email
    if user_data.org_address is not None:
        user.org_address = user_data.org_address
    
    db.commit()
    return {"success": True}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить пользователя"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db.delete(user)
    db.commit()
    return {"success": True}

@router.get("/organizations", response_model=List[UserListItem])
async def get_organizations(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список организаций"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    query = db.query(User).filter(User.role == UserRole.ORGANIZER)
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            (User.organization_name.ilike(search)) |
            (User.org_contact_name.ilike(search)) |
            (User.org_email.ilike(search))
        )
    
    return query.all()

@router.get("/stats", response_model=AdminStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    users_total = db.query(User).count()
    volunteers_total = db.query(User).filter(User.role == UserRole.VOLUNTEER).count()
    organizers_total = db.query(User).filter(User.role == UserRole.ORGANIZER).count()
    admins_total = db.query(User).filter(User.role == UserRole.ADMIN).count()
    organizations_total = db.query(User).filter(User.role == UserRole.ORGANIZER).count()
    from backend.models.event import Event
    events_total = db.query(Event).count()
    return AdminStats(
        users_total=users_total,
        volunteers_total=volunteers_total,
        organizers_total=organizers_total,
        admins_total=admins_total,
        organizations_total=organizations_total,
        events_total=events_total
    )

@router.get("/events", response_model=List[EventListItem])
async def get_events(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    query = db.query(Event)
    if search:
        search = f"%{search}%"
        query = query.filter(Event.title.ilike(search))
    return query.all()

@router.get("/events/{event_id}", response_model=EventListItem)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event

@router.put("/events/{event_id}")
async def update_event(
    event_id: int,
    event_data: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    for field, value in event_data.dict(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    return {"success": True}

@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    db.delete(event)
    db.commit()
    return {"success": True} 