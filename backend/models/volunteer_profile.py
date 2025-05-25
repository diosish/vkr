"""Упрощенный профиль волонтера"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
from backend.database import Base

class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Личные данные
    middle_name = Column(String(100))
    birth_date = Column(DateTime)
    gender = Column(String(10))

    # Контакты для экстренной связи
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relation = Column(String(100))

    # Профессиональные данные
    education = Column(String(255))
    occupation = Column(String(255))
    organization = Column(String(255))

    # Волонтерский опыт
    skills = Column(JSON)
    interests = Column(JSON)
    experience_description = Column(Text)
    languages = Column(JSON)

    # Доступность
    availability_schedule = Column(JSON)
    preferred_activities = Column(JSON)
    travel_willingness = Column(Boolean, default=False)
    max_travel_distance = Column(Integer)

    # Метаданные
    profile_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", backref="volunteer_profile")

    @property
    def age(self):
        """Возраст"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    @property
    def completion_percentage(self):
        """Процент заполнения профиля"""
        fields = [
            self.middle_name, self.birth_date, self.user.phone if self.user else None,
            self.user.email if self.user else None, self.emergency_contact_name,
            self.emergency_contact_phone, self.education, self.skills, self.experience_description
        ]
        filled = sum(1 for field in fields if field)
        return int((filled / len(fields)) * 100) if fields else 0

    def __repr__(self):
        return f"<VolunteerProfile(user_id={self.user_id}, completed={self.profile_completed})>"