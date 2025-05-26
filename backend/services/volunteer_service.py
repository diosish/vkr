from sqlalchemy.orm import Session
from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.models.event import Event
from backend.models.registration import Registration, RegistrationStatus
from typing import List, Optional
from datetime import datetime

class VolunteerService:
    def __init__(self, db: Session):
        self.db = db

    def get_volunteer_profile(self, user_id: int) -> Optional[VolunteerProfile]:
        """Получить профиль волонтера"""
        return self.db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user_id).first()

    def get_volunteer_events(self, user_id: int) -> List[Event]:
        """Получить список мероприятий волонтера"""
        registrations = self.db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.status == RegistrationStatus.APPROVED
        ).all()
        return [reg.event for reg in registrations]

    def get_volunteer_stats(self, user_id: int) -> dict:
        """Получить статистику волонтера"""
        total_events = self.db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.status == RegistrationStatus.APPROVED
        ).count()

        upcoming_events = self.db.query(Registration).join(Event).filter(
            Registration.user_id == user_id,
            Registration.status == RegistrationStatus.APPROVED,
            Event.start_date > datetime.utcnow()
        ).count()

        return {
            "total_events": total_events,
            "upcoming_events": upcoming_events
        }
