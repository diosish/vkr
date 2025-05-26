"""Инициализация базы данных"""

import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models.user import User, UserRole
from backend.models.volunteer_profile import VolunteerProfile
from backend.models.event import Event
from backend.models.registration import Registration, RegistrationStatus

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./volunteer.db")
BACKUP_DIR = "backups"

def init_db():
    """Инициализация базы данных"""
    print("🔄 Инициализация базы данных...")

    # Создаем бэкап если база существует
    if os.path.exists("volunteer.db"):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        backup_name = f"volunteer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2("volunteer.db", backup_path)
        print(f"✅ Создан бэкап: {backup_path}")

    # Создаем движок и сессию
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")

    # Применяем миграции
    from backend.migrations.add_last_activity import upgrade as add_last_activity
    try:
        add_last_activity()
        print("✅ Миграции применены")
    except Exception as e:
        print(f"⚠️ Ошибка при применении миграций: {e}")

    # Создаем тестового админа если нет пользователей
    db = SessionLocal()
    try:
        if not db.query(User).first():
            admin = User(
                telegram_user_id=123456789,
                telegram_username="admin",
                first_name="Админ",
                last_name="Системы",
                email="admin@example.com",
                phone="+79001234567",
                role=UserRole.ADMIN,
                is_verified=True,
                last_activity=datetime.utcnow()
            )
            db.add(admin)
            db.commit()
            print("✅ Создан тестовый админ")
    except Exception as e:
        print(f"⚠️ Ошибка при создании тестового админа: {e}")
        db.rollback()
    finally:
        db.close()

    print("✅ Инициализация завершена")

if __name__ == "__main__":
    init_db() 