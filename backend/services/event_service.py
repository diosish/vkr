import requests
from backend.config import settings
from backend.models.user import User, UserRole
from backend.models.event import Event
from backend.models.registration import RegistrationStatus
from sqlalchemy.orm import Session

# URL бота для отправки уведомлений (замените на свой)
BOT_NOTIFY_URL = getattr(settings, 'BOT_NOTIFY_URL', 'http://localhost:8081/bot/notify')


def notify_volunteers_on_new_event(db: Session, event: Event):
    # Получаем всех волонтёров по городу или радиусу
    volunteers = db.query(User).filter(User.role == UserRole.VOLUNTEER).all()
    matched = []
    for v in volunteers:
        if v.location and event.location and v.location.lower() == event.location.lower():
            matched.append(v)
        # Здесь можно добавить проверку по радиусу, если есть координаты
    if not matched:
        return
    payload = {
        "type": "volunteers_new_event",
        "volunteer_ids": [v.telegram_user_id for v in matched if v.telegram_user_id],
        "event": {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "start_date": str(event.start_date),
            "description": event.short_description or event.description or ''
        }
    }
    try:
        requests.post(BOT_NOTIFY_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[Notify] Ошибка отправки уведомления волонтёрам: {e}")


def notify_organizer_on_full(db: Session, event: Event):
    # Проверяем, укомплектован ли штат
    if event.max_volunteers == 0:
        return
    confirmed = [r for r in getattr(event, 'registrations', []) if r.status == RegistrationStatus.APPROVED]
    if len(confirmed) < event.max_volunteers:
        return
    organizer = event.creator
    if not organizer or not organizer.telegram_user_id:
        return
    payload = {
        "type": "organizer_event_full",
        "organizer_id": organizer.telegram_user_id,
        "event": {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "start_date": str(event.start_date)
        }
    }
    try:
        requests.post(BOT_NOTIFY_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[Notify] Ошибка отправки уведомления организатору: {e}")
