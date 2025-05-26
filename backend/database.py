"""Подключение к базе данных с правильными импортами"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL
import sqlite3

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

def auto_migrate_users_table():
    """Добавляет недостающие поля в таблицу users (SQLite)"""
    db_path = 'volunteer.db'
    columns = [
        ('organization_name', 'TEXT'),
        ('inn', 'TEXT'),
        ('ogrn', 'TEXT'),
        ('org_contact_name', 'TEXT'),
        ('org_phone', 'TEXT'),
        ('org_email', 'TEXT'),
        ('org_address', 'TEXT'),
    ]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users);")
        existing = set(row[1] for row in cursor.fetchall())
        for col, col_type in columns:
            if col not in existing:
                print(f"[MIGRATION] Добавляю поле {col} в users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type};")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[MIGRATION ERROR] {e}")

def init_db():
    """Инициализация базы данных (создание таблиц, если их нет)"""
    print("🗄️ Инициализация базы данных...")
    print("📦 Импорт моделей...")
    from backend.models.user import User
    print("  ✅ User model imported")
    from backend.models.volunteer_profile import VolunteerProfile
    print("  ✅ VolunteerProfile model imported")
    from backend.models.event import Event
    print("  ✅ Event model imported")
    from backend.models.registration import Registration
    print("  ✅ Registration model imported")
    print("🔨 Создание таблиц...")
    Base.metadata.create_all(engine)
    auto_migrate_users_table()