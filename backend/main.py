"""
Полное приложение с отдачей React фронтенда + ДИАГНОСТИКА
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import sys

print("=" * 60)
print("🔍 ДИАГНОСТИКА ИМПОРТОВ")
print("=" * 60)

# Исправленные импорты - используем абсолютные пути с префиксом backend
try:
    from backend.database import init_db, get_db
    print("✅ database импортирован")
except ImportError as e:
    print(f"❌ database ОШИБКА: {e}")

try:
    from backend.config import ALLOWED_ORIGINS, WEBAPP_URL, TELEGRAM_BOT_TOKEN
    print("✅ config импортирован")
except ImportError as e:
    print(f"❌ config ОШИБКА: {e}")

try:
    from backend.models.user import User, UserRole
    print("✅ User model импортирован")
except ImportError as e:
    print(f"❌ User model ОШИБКА: {e}")

try:
    from backend.models.volunteer_profile import VolunteerProfile
    print("✅ VolunteerProfile model импортирован")
except ImportError as e:
    print(f"❌ VolunteerProfile model ОШИБКА: {e}")

try:
    from backend.models.event import Event, EventStatus, EventCategory
    print("✅ Event model импортирован")
except ImportError as e:
    print(f"❌ Event model ОШИБКА: {e}")

try:
    from backend.models.registration import Registration, RegistrationStatus
    print("✅ Registration model импортирован")
except ImportError as e:
    print(f"❌ Registration model ОШИБКА: {e}")

print("=" * 60)
print("🔍 ПРОВЕРКА ФАЙЛОВ")
print("=" * 60)

# Проверяем наличие файлов
files_to_check = [
    "backend/__init__.py",
    "backend/api/__init__.py",
    "backend/api/auth.py",
    "backend/models/__init__.py",
    "backend/services/__init__.py"
]

for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"✅ {file_path} существует")
    else:
        print(f"❌ {file_path} НЕ НАЙДЕН!")

print(f"📁 Python path: {sys.path}")
print(f"📁 Current working directory: {Path('.').absolute()}")

# Путь к собранному фронтенду
FRONTEND_BUILD = Path("frontend/build")

# Lifecycle событие
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Запуск сервера...")
    print(f"🌐 Webapp URL: {WEBAPP_URL}")
    print(f"📁 Frontend: {'✅ Найден' if FRONTEND_BUILD.exists() else '❌ Не найден'}")
    init_db()
    create_test_data()
    yield
    # Shutdown
    print("🛑 Остановка сервера...")

def create_test_data():
    """Создание тестовых данных"""
    print("📊 Создание тестовых данных...")

    db = next(get_db())

    try:
        # Проверяем есть ли уже пользователи
        existing_user = db.query(User).first()
        if existing_user:
            print("  ℹ️ Тестовые данные уже существуют")
            db.close()
            return

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

    except Exception as e:
        print(f"  ❌ Ошибка создания тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

# Создание приложения
app = FastAPI(
    title="Volunteer Registration System",
    description="Полная система регистрации волонтеров для Telegram",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=" * 60)
print("🔌 ПОДКЛЮЧЕНИЕ API РОУТЕРОВ")
print("=" * 60)

# Подключение API роутеров - ИСПРАВЛЕНО
try:
    print("🔍 Попытка импорта backend.api.auth...")
    from backend.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    print("✅ Auth API подключен успешно!")
except ImportError as e:
    print(f"❌ Auth API НЕ НАЙДЕН: {e}")
    print("📝 Создайте файл backend/api/auth.py")
except Exception as e:
    print(f"❌ Auth API ОШИБКА: {e}")

try:
    from backend.api.events import router as events_router
    app.include_router(events_router, prefix="/api/events", tags=["Events"])
    print("✅ Events API подключен")
except ImportError as e:
    print(f"⚠️ Events API не найден: {e}")
except Exception as e:
    print(f"❌ Events API ошибка: {e}")

try:
    from backend.api.registrations import router as registrations_router
    app.include_router(registrations_router, prefix="/api/registrations", tags=["Registrations"])
    print("✅ Registrations API подключен")
except ImportError as e:
    print(f"⚠️ Registrations API не найден: {e}")
except Exception as e:
    print(f"❌ Registrations API ошибка: {e}")

print("=" * 60)

# Статические файлы фронтенда
if FRONTEND_BUILD.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD / "static"), name="static")

# API Routes
@app.get("/health")
async def health_check():
    """Проверка здоровья"""
    return {
        "status": "healthy",
        "service": "volunteer-registration-system",
        "version": "2.0.0",
        "webapp_url": WEBAPP_URL,
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
        "frontend": FRONTEND_BUILD.exists()
    }

# Простой тестовый endpoint для проверки
@app.post("/api/test-auth")
async def test_auth():
    """Тестовый endpoint аутентификации"""
    return {
        "success": True,
        "message": "Test auth endpoint works!",
        "user": {
            "id": 1,
            "first_name": "Тест",
            "role": "volunteer"
        }
    }

# Отдача React приложения для всех остальных маршрутов
if FRONTEND_BUILD.exists():
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Отдача React приложения"""
        # Исключаем API маршруты и статические файлы
        if (full_path.startswith("api/") or
            full_path.startswith("docs") or
            full_path.startswith("health") or
            full_path.startswith("static/") or
            full_path.startswith("test/")):
            raise HTTPException(status_code=404, detail="Not found")

        index_file = FRONTEND_BUILD / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding='utf-8'))

        raise HTTPException(status_code=404, detail="Frontend not found")
else:
    # Если фронтенд не собран, показываем информационную страницу
    @app.get("/")
    async def root():
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Volunteer System - Development</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: system-ui; padding: 20px; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .status {{ padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .success {{ background: #d4edda; color: #155724; }}
                .warning {{ background: #fff3cd; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Volunteer Registration System</h1>
                
                <div class="status success">
                    <strong>Backend:</strong> ✅ Работает на порту 8000
                </div>
                
                <div class="status warning">
                    <strong>Frontend:</strong> ⚠️ Не собран
                </div>
                
                <h2>Для разработки:</h2>
                <ol>
                    <li>Запустите фронтенд: <code>cd frontend && npm start</code></li>
                    <li>Откройте: <a href="http://localhost:3000">http://localhost:3000</a></li>
                </ol>
                
                <h2>Для продакшена:</h2>
                <ol>
                    <li>Соберите фронтенд: <code>cd frontend && npm run build</code></li>
                    <li>Перезапустите сервер</li>
                </ol>
                
                <h2>API:</h2>
                <ul>
                    <li><a href="/docs">📖 Документация</a></li>
                    <li><a href="/health">🔍 Здоровье</a></li>
                    <li><a href="/api/test-auth">🧪 Тест авторизации</a></li>
                </ul>
                
                <p><strong>WebApp URL:</strong> {WEBAPP_URL}</p>
            </div>
        </body>
        </html>
        """)

print("🎯 Main.py загружен успешно!")
print("=" * 60)