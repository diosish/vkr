"""Подключение к базе данных с правильными импортами"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

# Создаем движок БД (SQLite)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Нужно для SQLite
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация базы данных"""
    print("🗄️ Инициализация базы данных...")

    # ВАЖНО: Импортируем все модели в правильном порядке
    print("📦 Импорт моделей...")

    # Сначала базовые модели без зависимостей
    from backend.models.user import User
    print("  ✅ User model imported")

    # Затем модели с зависимостями
    from backend.models.volunteer_profile import VolunteerProfile
    print("  ✅ VolunteerProfile model imported")

    from backend.models.event import Event
    print("  ✅ Event model imported")

    from backend.models.registration import Registration
    print("  ✅ Registration model imported")

    # Создание таблиц
    print("🔨 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ База данных готова!")