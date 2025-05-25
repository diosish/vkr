# reset_db.py
"""Скрипт для пересоздания базы данных"""

import os
from pathlib import Path
from backend.database import engine, Base, SessionLocal
from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.models.event import Event, EventStatus, EventCategory
from backend.models.registration import Registration, RegistrationStatus
from datetime import datetime


def reset_database():
    """Пересоздать базу данных с нуля"""
    print("🗑️ Удаление старой базы данных...")

    # Удаляем файл базы данных
    db_file = Path("volunteer.db")
    if db_file.exists():
        db_file.unlink()
        print("  ✅ Старая база данных удалена")

    print("🔨 Создание новой базы данных...")

    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("  ✅ Таблицы созданы")

    # Создаем тестовые данные
    create_test_data()

    print("✅ База данных пересоздана успешно!")


def create_test_data():
    """Создание тестовых данных"""
    print("📊 Создание тестовых данных...")

    db = SessionLocal()

    try:
        # Создаем тестовых пользователей
        admin_user = User(
            telegram_user_id=123456789,
            telegram_username="admin_test",
            first_name="Админ",
            last_name="Тестовый",
            email="admin@test.com",
            phone="+7 (999) 111-11-11",
            role=UserRole.ADMIN
        )

        organizer_user = User(
            telegram_user_id=987654321,
            telegram_username="organizer_test",
            first_name="Организатор",
            last_name="Тестовый",
            email="organizer@test.com",
            phone="+7 (999) 222-22-22",
            role=UserRole.ORGANIZER
        )

        volunteer_user = User(
            telegram_user_id=111222333,
            telegram_username="volunteer_test",
            first_name="Волонтер",
            last_name="Тестовый",
            email="volunteer@test.com",
            phone="+7 (999) 333-33-33",
            role=UserRole.VOLUNTEER
        )

        db.add_all([admin_user, organizer_user, volunteer_user])
        db.commit()
        db.refresh(organizer_user)
        db.refresh(volunteer_user)

        # Создаем профиль для волонтера
        volunteer_profile = VolunteerProfile(
            user_id=volunteer_user.id,
            middle_name="Тестович",
            birth_date=datetime(1990, 1, 1),
            gender="male",
            emergency_contact_name="Родитель Тестовый",
            emergency_contact_phone="+7 (999) 444-44-44",
            emergency_contact_relation="parent",
            education="Высшее",
            skills=["Организаторские способности", "Работа с детьми"],
            interests=["Экология", "Социальная помощь"],
            experience_description="Опыт работы волонтером 2 года",
            languages=["ru", "en"],
            travel_willingness=True,
            max_travel_distance=100,
            preferred_activities=["Разовые мероприятия", "Работа в команде"],
            profile_completed=True
        )

        db.add(volunteer_profile)

        # Создаем тестовые мероприятия
        events_data = [
            {
                "creator_id": organizer_user.id,
                "title": "Уборка парка",
                "description": "Экологическая акция по уборке городского парка. Приглашаем всех неравнодушных граждан принять участие в улучшении экологической обстановки нашего города.",
                "short_description": "Помогите сделать наш город чище!",
                "category": EventCategory.ENVIRONMENTAL,
                "tags": ["экология", "уборка", "парк", "природа"],
                "location": "Центральный парк",
                "address": "ул. Парковая, 1",
                "start_date": datetime(2024, 12, 15, 10, 0),
                "end_date": datetime(2024, 12, 15, 16, 0),
                "max_volunteers": 20,
                "required_skills": ["Физическая выносливость"],
                "what_to_bring": "Перчатки, удобная одежда, питьевая вода",
                "meal_provided": True,
                "contact_person": "Иван Петров",
                "contact_phone": "+7 (999) 222-22-22",
                "status": EventStatus.PUBLISHED,
                "published_at": datetime.utcnow()
            },
            {
                "creator_id": organizer_user.id,
                "title": "Помощь в детском доме",
                "description": "Проведение мастер-классов и игр для детей в детском доме. Подарите детям радость творчества и общения!",
                "short_description": "Подарите детям радость творчества!",
                "category": EventCategory.SOCIAL,
                "tags": ["дети", "творчество", "помощь"],
                "location": "Детский дом №5",
                "address": "ул. Детская, 10",
                "start_date": datetime(2024, 12, 20, 14, 0),
                "end_date": datetime(2024, 12, 20, 18, 0),
                "max_volunteers": 10,
                "required_skills": ["Работа с детьми", "Творческие навыки"],
                "what_to_bring": "Хорошее настроение",
                "meal_provided": False,
                "contact_person": "Мария Петрова",
                "contact_phone": "+7 (999) 333-33-33",
                "status": EventStatus.PUBLISHED,
                "published_at": datetime.utcnow()
            }
        ]

        for event_data in events_data:
            event = Event(**event_data)
            db.add(event)

        db.commit()

        print("  ✅ Тестовые данные созданы:")
        print(f"    👤 Пользователи: 3")
        print(f"    📅 Мероприятия: {len(events_data)}")
        print(f"    👨‍💼 Профили волонтеров: 1")

    except Exception as e:
        print(f"  ❌ Ошибка создания тестовых данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()