"""Упрощенная модель мероприятия"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from backend.database import Base
from backend.models.user import User
from enum import Enum

class EventStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class EventCategory(Enum):
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    EDUCATION = "education"
    HEALTH = "health"
    COMMUNITY = "community"
    EMERGENCY = "emergency"
    SPORTS = "sports"
    CULTURE = "culture"
    OTHER = "other"

class EventActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CANCEL = "cancel"
    RESTORE = "restore"
    PUBLISH = "publish"
    EXPORT = "export"
    OTHER = "other"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Основная информация
    title = Column(String(200), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))

    # Категоризация
    category = Column(SAEnum(EventCategory), default=EventCategory.OTHER)
    tags = Column(JSON)

    # Место и время
    location = Column(String(255))
    address = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    registration_deadline = Column(DateTime)

    # Участники
    max_volunteers = Column(Integer, default=0)
    min_volunteers = Column(Integer, default=1)
    current_volunteers_count = Column(Integer, default=0)

    # Требования
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    min_age = Column(Integer)
    max_age = Column(Integer)
    requirements_description = Column(Text)

    # Детали
    what_to_bring = Column(Text)
    dress_code = Column(String(255))
    meal_provided = Column(Boolean, default=False)
    transport_provided = Column(Boolean, default=False)

    # Контакты
    contact_person = Column(String(255))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))

    # Статус и метаданные
    status = Column(SAEnum(EventStatus), default=EventStatus.DRAFT)
    is_featured = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)

    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    # Связи
    creator = relationship("User", backref=backref("created_events", cascade="all, delete-orphan"))
    logs = relationship("EventLog", back_populates="event", cascade="all, delete-orphan")

    # Добавить в класс Event:


    @property
    def available_slots(self):
        """Доступные места"""
        if self.max_volunteers == 0:
            return float('inf')
        return max(0, self.max_volunteers - self.current_volunteers_count)

    @property
    def progress_percentage(self):
        """Процент заполнения"""
        if self.max_volunteers == 0:
            return 0
        return int((self.current_volunteers_count / self.max_volunteers) * 100)

    @property
    def is_active(self):
        """Активно ли мероприятие"""
        return self.status == EventStatus.PUBLISHED and self.start_date > datetime.utcnow()

    @property
    def is_registration_open(self):
        """Открыта ли регистрация"""
        now = datetime.utcnow()
        if self.registration_deadline:
            return self.is_active and now < self.registration_deadline
        return self.is_active and now < self.start_date



    @property
    def is_full(self):
        """Заполнено ли мероприятие"""
        return self.max_volunteers > 0 and self.current_volunteers_count >= self.max_volunteers

    @property
    def progress_percentage(self):
        """Процент заполнения"""
        if self.max_volunteers == 0:
            return 0
        return int((self.current_volunteers_count / self.max_volunteers) * 100)

    def can_register(self, user) -> bool:
        """Может ли пользователь зарегистрироваться"""
        from backend.models.user import UserRole
        return (
            self.is_registration_open and
            not self.is_full and
            user.role == UserRole.VOLUNTEER
        )

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', status='{self.status.value}')>"

    @property
    def current_volunteers_count(self):
        """Текущее количество подтвержденных волонтеров"""
        if hasattr(self, 'registrations'):
            return len([r for r in self.registrations if r.status == RegistrationStatus.CONFIRMED])
        return 0


class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(SAEnum(EventActionType), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)

    event = relationship("Event", back_populates="logs")
    user = relationship("User")