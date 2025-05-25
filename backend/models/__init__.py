"""Модели для системы регистрации волонтеров"""

# Порядок импорта важен для правильного создания внешних ключей
from .user import User, UserRole
from .volunteer_profile import VolunteerProfile
from .event import Event, EventStatus, EventCategory
from .registration import Registration, RegistrationStatus

__all__ = [
    'User', 'UserRole',
    'VolunteerProfile',
    'Event', 'EventStatus', 'EventCategory',
    'Registration', 'RegistrationStatus'
]