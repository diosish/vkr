"""Упрощенная модель регистрации"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

class RegistrationStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"  # Это правильно
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Статус
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING)

    # Дополнительная информация
    motivation = Column(Text)
    relevant_experience = Column(Text)
    availability_notes = Column(Text)
    special_requirements = Column(Text)

    # Связь с организатором
    organizer_notes = Column(Text)
    rejection_reason = Column(Text)

    # Участие
    attended = Column(Boolean)
    feedback = Column(Text)
    rating = Column(Integer)

    # Временные метки
    registered_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", backref="registrations")
    event = relationship("Event", backref="registrations")

    def can_cancel(self) -> bool:
        """Можно ли отменить регистрацию"""
        return self.status in [RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED]

    def can_confirm(self) -> bool:
        """Можно ли подтвердить регистрацию"""
        return self.status == RegistrationStatus.PENDING

    def __repr__(self):
        return f"<Registration(id={self.id}, user_id={self.user_id}, event_id={self.event_id}, status='{self.status.value}')>"