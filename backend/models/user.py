"""Упрощенная модель пользователя"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

class UserRole(enum.Enum):
    VOLUNTEER = "volunteer"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(Integer, unique=True, index=True, nullable=False)
    telegram_username = Column(String(255), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.VOLUNTEER)

    # Профиль
    bio = Column(Text)
    avatar_url = Column(String(500))
    location = Column(String(255))
    birth_date = Column(DateTime)

    # Статус
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Связи - правильно настроенная связь с профилем волонтера
    volunteer_profile = relationship(
        "VolunteerProfile",
        uselist=False,  # Это важно! Указываем что это один объект, а не список
        back_populates="user"
    )

    @property
    def full_name(self):
        """Полное имя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def display_name(self):
        """Отображаемое имя"""
        if self.telegram_username:
            return f"@{self.telegram_username}"
        return self.full_name

    def has_role(self, role: UserRole) -> bool:
        """Проверка роли"""
        return self.role == role

    def is_admin(self) -> bool:
        """Является ли админом"""
        return self.role == UserRole.ADMIN

    def is_organizer(self) -> bool:
        """Является ли организатором"""
        return self.role in [UserRole.ORGANIZER, UserRole.ADMIN]

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.full_name}', role='{self.role.value}')>"