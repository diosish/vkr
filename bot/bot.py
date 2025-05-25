"""
Простой Telegram Bot для тестирования
"""

import os
import logging
import asyncio
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://0a02-62-197-45-18.ngrok-free.app")

print(f"🤖 Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Not Set'}")
print(f"🌐 WebApp URL: {WEBAPP_URL}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user

    # Кнопка для запуска Web App
    webapp = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть приложение", web_app=webapp)],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
        [InlineKeyboardButton("🔍 Тест API", callback_data="test_api")]
    ])

    welcome_text = f"""
🤝 *Добро пожаловать в систему регистрации волонтеров!*

Привет, {user.first_name}! 

Это тестовая версия приложения для:
- Регистрации волонтеров
- Управления мероприятиями  
- Записи на участие в событиях

*Для тестирования:*
🌐 WebApp URL: `{WEBAPP_URL}`
🔧 Режим: Разработка

Нажмите "Открыть приложение" для начала!
    """

    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = """
📋 *Помощь по тестированию*

*Доступные команды:*
/start - Запуск приложения
/help - Эта справка
/status - Статус сервисов
/webapp - Прямая ссылка на приложение

*Для разработчиков:*
🔧 API: `https://0a02-62-197-45-18.ngrok-free.app/docs`
🗄️ База данных: SQLite (локальная)
🌐 Frontend: React (если запущен на :3000)

*Тестирование:*
1. Нажмите "Открыть приложение"
2. Проверьте что загружается интерфейс
3. Попробуйте создать тестового волонтера
    """

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка статуса сервисов"""
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WEBAPP_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    status_text = f"""
✅ *Сервисы работают*

🌐 API: {WEBAPP_URL}
📊 Статус: {data.get('status', 'unknown')}
🤖 Bot: {'✅' if data.get('bot_configured') else '❌'}

*Время проверки:* {context.bot.username}
                    """
                else:
                    status_text = f"❌ API недоступен (код: {response.status})"
    except Exception as e:
        status_text = f"❌ Ошибка подключения: {str(e)}"

    await update.message.reply_text(status_text, parse_mode='Markdown')

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Прямая ссылка на Web App"""
    webapp = WebAppInfo(url=WEBAPP_URL)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть", web_app=webapp)]
    ])

    await update.message.reply_text(
        f"🔗 Прямая ссылка на приложение:\n`{WEBAPP_URL}`",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

def main():
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return

    logger.info("🤖 Запуск Telegram бота...")
    logger.info(f"🌐 WebApp URL: {WEBAPP_URL}")

    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавление команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("webapp", webapp_command))

    # Запуск бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()