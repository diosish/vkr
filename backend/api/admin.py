from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
import re

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
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{10,14}$')
    role: Optional[str] = None
    is_active: Optional[bool] = None
    organization_name: Optional[str] = Field(None, min_length=2, max_length=100)
    inn: Optional[str] = Field(None, pattern=r'^\d{10}$|^\d{12}$')
    ogrn: Optional[str] = Field(None, pattern=r'^\d{13}$|^\d{15}$')
    org_contact_name: Optional[str] = Field(None, min_length=2, max_length=100)
    org_phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{10,14}$')
    org_email: Optional[EmailStr] = None
    org_address: Optional[str] = Field(None, max_length=200)

    @validator('role')
    def validate_role(cls, v):
        if v and v not in [role.value for role in UserRole]:
            raise ValueError('Invalid role')
        return v

    @validator('inn')
    def validate_inn(cls, v):
        if v:
            # Проверка контрольной суммы ИНН
            if len(v) == 10:
                coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
                check_sum = sum(int(v[i]) * coefficients[i] for i in range(9)) % 11 % 10
                if check_sum != int(v[9]):
                    raise ValueError('Invalid INN checksum')
            elif len(v) == 12:
                coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
                coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
                check_sum1 = sum(int(v[i]) * coefficients1[i] for i in range(10)) % 11 % 10
                check_sum2 = sum(int(v[i]) * coefficients2[i] for i in range(11)) % 11 % 10
                if check_sum1 != int(v[10]) or check_sum2 != int(v[11]):
                    raise ValueError('Invalid INN checksum')
        return v

    @validator('ogrn')
    def validate_ogrn(cls, v):
        if v:
            # Проверка контрольной суммы ОГРН
            if len(v) == 13:
                check_sum = int(v[:-1]) % 11 % 10
                if check_sum != int(v[-1]):
                    raise ValueError('Invalid OGRN checksum')
            elif len(v) == 15:
                check_sum = int(v[:-1]) % 13 % 10
                if check_sum != int(v[-1]):
                    raise ValueError('Invalid OGRNIP checksum')
        return v

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
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    max_volunteers: Optional[int] = None
    required_skills: Optional[List[str]] = None
    what_to_bring: Optional[str] = Field(None, max_length=1000)
    meal_provided: Optional[bool] = None
    contact_person: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{10,14}$')

    @validator('category')
    def validate_category(cls, v):
        if v and v not in [category.value for category in EventCategory]:
            raise ValueError('Invalid category')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v and v not in [status.value for status in EventStatus]:
            raise ValueError('Invalid status')
        return v

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v

    @validator('max_volunteers')
    def validate_max_volunteers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Max volunteers cannot be negative')
        return v

    @validator('required_skills')
    def validate_skills(cls, v):
        if v:
            if not all(isinstance(skill, str) and len(skill) <= 50 for skill in v):
                raise ValueError('Invalid skills format')
        return v

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
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid role value"
            )
    
    if search:
        # Очищаем поисковый запрос от специальных символов
        search = re.sub(r'[^\w\s\-]', '', search)
        if len(search) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query too short"
            )
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
    
    # Проверяем уникальность email
    if user_data.email and user_data.email != user.email:
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email уже используется другим пользователем"
            )
    
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
    
    try:
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении данных пользователя"
        )

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
        # Очищаем поисковый запрос от специальных символов
        search = re.sub(r'[^\w\s\-]', '', search)
        if len(search) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query too short"
            )
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
    """Получить список мероприятий"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    query = db.query(Event)
    
    if search:
        # Очищаем поисковый запрос от специальных символов
        search = re.sub(r'[^\w\s\-]', '', search)
        if len(search) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query too short"
            )
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
    """Обновить данные мероприятия"""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    # Обновляем только переданные поля
    if event_data.title is not None:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.short_description is not None:
        event.short_description = event_data.short_description
    if event_data.category is not None:
        event.category = EventCategory(event_data.category)
    if event_data.status is not None:
        event.status = EventStatus(event_data.status)
    if event_data.start_date is not None:
        event.start_date = event_data.start_date
    if event_data.end_date is not None:
        event.end_date = event_data.end_date
    if event_data.location is not None:
        event.location = event_data.location
    if event_data.address is not None:
        event.address = event_data.address
    if event_data.max_volunteers is not None:
        event.max_volunteers = event_data.max_volunteers
    if event_data.required_skills is not None:
        event.required_skills = event_data.required_skills
    if event_data.what_to_bring is not None:
        event.what_to_bring = event_data.what_to_bring
    if event_data.meal_provided is not None:
        event.meal_provided = event_data.meal_provided
    if event_data.contact_person is not None:
        event.contact_person = event_data.contact_person
    if event_data.contact_phone is not None:
        event.contact_phone = event_data.contact_phone
    
    try:
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении данных мероприятия"
        )

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