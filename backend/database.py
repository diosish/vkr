"""Подключение к базе данных с улучшенной конфигурацией"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.config import DATABASE_URL
from backend.core.logging import get_logger
import os

logger = get_logger(__name__)

# Определяем тип БД
is_sqlite = DATABASE_URL.startswith("sqlite")
is_postgres = DATABASE_URL.startswith("postgresql")

# Настройки для разных типов БД
if is_sqlite:
    # SQLite настройки
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20,
        },
        poolclass=StaticPool,
        echo=False  # Отключаем SQL логи по умолчанию
    )

    # Включаем WAL режим для SQLite (лучшая производительность)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Включаем WAL режим
        cursor.execute("PRAGMA journal_mode=WAL")
        # Включаем foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        # Увеличиваем cache размер
        cursor.execute("PRAGMA cache_size=10000")
        # Включаем синхронизацию
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

elif is_postgres:
    # PostgreSQL настройки
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
else:
    # Общие настройки для других БД
    engine = create_engine(DATABASE_URL, echo=False)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """Получить сессию БД с proper error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Инициализация базы данных (создание таблиц)"""
    logger.info("🗄️ Инициализация базы данных...")

    try:
        # Импортируем все модели для создания таблиц
        logger.info("📦 Импорт моделей...")
        from backend.models.user import User, UserRole
        from backend.models.volunteer_profile import VolunteerProfile
        from backend.models.event import Event, EventStatus, EventCategory
        from backend.models.registration import Registration, RegistrationStatus

        logger.info("🔨 Создание таблиц...")
        Base.metadata.create_all(bind=engine)

        logger.info("✅ База данных инициализирована успешно")

        # Создаем тестовые данные если их нет
        create_initial_data()

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise

def create_initial_data():
    """Создание начальных данных если их нет"""
    try:
        db = SessionLocal()

        # Импортируем модели
        from backend.models.user import User, UserRole
        from backend.models.event import Event, EventStatus, EventCategory
        from datetime import datetime, timedelta

        # Проверяем есть ли пользователи
        existing_users = db.query(User).count()

        if existing_users == 0:
            logger.info("📊 Создание тестовых данных...")

            # Создаем тестового админа
            admin_user = User(
                telegram_user_id=123456789,
                telegram_username="admin_test",
                first_name="Админ",
                last_name="Системы",
                email="admin@volunteer-system.local",
                phone="+7 (999) 111-11-11",
                role=UserRole.ADMIN,
                is_verified=True,
                last_activity=datetime.utcnow()
            )

            # Создаем тестового организатора
            organizer_user = User(
                telegram_user_id=987654321,
                telegram_username="organizer_test",
                first_name="Организатор",
                last_name="Тестовый",
                email="organizer@volunteer-system.local",
                phone="+7 (999) 222-22-22",
                role=UserRole.ORGANIZER,
                organization_name="Тестовая НКО",
                org_contact_name="Иван Петров",
                org_phone="+7 (999) 222-22-22",
                org_email="nko@volunteer-system.local",
                last_activity=datetime.utcnow()
            )

            # Создаем тестового волонтера
            volunteer_user = User(
                telegram_user_id=111222333,
                telegram_username="volunteer_test",
                first_name="Волонтер",
                last_name="Тестовый",
                email="volunteer@volunteer-system.local",
                phone="+7 (999) 333-33-33",
                role=UserRole.VOLUNTEER,
                last_activity=datetime.utcnow()
            )

            db.add_all([admin_user, organizer_user, volunteer_user])
            db.commit()

            # Обновляем объекты после commit
            db.refresh(organizer_user)

            # Создаем тестовое мероприятие
            test_event = Event(
                creator_id=organizer_user.id,
                title="Уборка парка «Тестовый»",
                description="Тестовое экологическое мероприятие для проверки системы регистрации волонтеров.",
                short_description="Помогите сделать наш город чище!",
                category=EventCategory.ENVIRONMENTAL,
                tags=["экология", "уборка", "тест"],
                location="Тестовый парк",
                address="ул. Тестовая, 1",
                start_date=datetime.utcnow() + timedelta(days=7),
                end_date=datetime.utcnow() + timedelta(days=7, hours=6),
                max_volunteers=20,
                min_volunteers=5,
                required_skills=["Физическая выносливость"],
                what_to_bring="Перчатки, удобная одежда",
                meal_provided=True,
                contact_person="Иван Петров",
                contact_phone="+7 (999) 222-22-22",
                status=EventStatus.PUBLISHED,
                published_at=datetime.utcnow()
            )

            db.add(test_event)
            db.commit()

            logger.info("  ✅ Созданы тестовые пользователи:")
            logger.info(f"    👤 Админ: admin_test")
            logger.info(f"    👔 Организатор: organizer_test")
            logger.info(f"    🤝 Волонтер: volunteer_test")
            logger.info(f"  ✅ Создано тестовое мероприятие: {test_event.title}")

        else:
            logger.info(f"  ℹ️ База данных содержит {existing_users} пользователей")

    except Exception as e:
        logger.error(f"❌ Ошибка создания тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

def check_db_connection():
    """Проверка подключения к БД"""
    try:
        db = SessionLocal()
        # Простой запрос для проверки соединения
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False

def get_db_info():
    """Получить информацию о БД"""
    try:
        db = SessionLocal()

        info = {
            "database_url": DATABASE_URL.split("://")[0] + "://***",  # Скрываем пароль
            "is_sqlite": is_sqlite,
            "is_postgres": is_postgres,
        }

        # Получаем статистику таблиц если это SQLite
        if is_sqlite:
            from backend.models.user import User
            from backend.models.event import Event
            from backend.models.registration import Registration

            info.update({
                "users_count": db.query(User).count(),
                "events_count": db.query(Event).count(),
                "registrations_count": db.query(Registration).count(),
            })

        db.close()
        return info

    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        return {"error": str(e)}