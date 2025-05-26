#!/usr/bin/env python3
"""
🚀 Единый запуск полного проекта Telegram Mini App
Система регистрации волонтеров - Полная версия
"""

import os
import sys
import time
import subprocess
import threading
import signal
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
npm_path = r"C:\Program Files\nodejs\npm.cmd"

# Глобальные процессы для управления
processes = []
build_mode = False


def print_banner():
    """Красивый баннер"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            🤝 TELEGRAM VOLUNTEER MINI APP                    ║
║                 Полная система v2.0                         ║
║            Backend + Frontend + Telegram Bot                 ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_requirements():
    """Проверка требований"""
    print("🔍 Проверка системных требований...")

    # Проверка Python
    if sys.version_info < (3, 9):
        print("❌ Требуется Python 3.9+")
        return False
    print("  ✅ Python версия OK")

    # Проверка Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ Node.js {version}")
        else:
            print("  ❌ Node.js не установлен")
            return False
    except FileNotFoundError:
        print("  ❌ Node.js не найден. Установите с https://nodejs.org")
        return False

    # Проверка npm
    try:
        result = subprocess.run([npm_path, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✅ npm {version}")
        else:
            print("  ❌ npm не установлен")
            return False
    except FileNotFoundError:
        print("  ❌ npm не найден")
        return False

    # Проверка .env файла
    if not Path(".env").exists():
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env с содержимым:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_от_botfather")
        print("WEBAPP_URL=https://your-ngrok-url.ngrok-free.app")
        return False

    # Проверка токена
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не указан в .env файле")
        return False
    print("  ✅ Telegram Bot Token настроен")

    # Проверка структуры проекта
    required_dirs = ['backend', 'frontend', 'bot']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"❌ Папка {dir_name} не найдена")
            return False
    print("  ✅ Структура проекта корректна")

    print("✅ Все требования выполнены")
    return True


def install_dependencies():
    """Установка зависимостей"""
    print("📦 Установка и проверка зависимостей...")

    try:
        # Backend зависимости
        print("  📦 Backend зависимости...")
        if Path("requirements.txt").exists():
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, capture_output=True)
            print("    ✅ Python зависимости установлены")

        # Frontend зависимости
        print("  📦 Frontend зависимости...")
        if Path("frontend").exists():
            os.chdir("frontend")

            # Проверяем package.json
            if not Path("package.json").exists():
                print("    ❌ package.json не найден в frontend/")
                return False

            # Устанавливаем зависимости если нужно
            if not Path("node_modules").exists():
                print("    📥 Установка npm зависимостей...")
                subprocess.run([npm_path, "install"], check=True, capture_output=True)
                print("    ✅ npm зависимости установлены")
            else:
                print("    ✅ npm зависимости уже установлены")

            os.chdir("..")

        print("✅ Все зависимости готовы")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def build_frontend():
    """Сборка фронтенда для продакшена"""
    print("⚛️  Сборка React фронтенда...")

    try:
        os.chdir("frontend")

        # Проверяем что есть исходники
        if not Path("src").exists():
            print("    ❌ Папка src не найдена")
            return False

        # Удаляем старую сборку
        if Path("build").exists():
            shutil.rmtree("build")
            print("    🗑️ Удалена старая сборка")

        # Собираем
        print("    🔨 Сборка фронтенда... (это может занять минуту)")
        result = subprocess.run([
            npm_path, "run", "build"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"    ❌ Ошибка сборки: {result.stderr}")
            return False

        if Path("build").exists():
            print("    ✅ Фронтенд собран успешно")

            # Показываем размер сборки
            build_size = sum(f.stat().st_size for f in Path("build").rglob('*') if f.is_file())
            print(f"    📊 Размер сборки: {build_size / 1024 / 1024:.1f} MB")

            return True
        else:
            print("    ❌ Папка build не создана")
            return False

    except Exception as e:
        print(f"    ❌ Ошибка сборки фронтенда: {e}")
        return False
    finally:
        os.chdir("..")


def run_backend():
    """Запуск backend сервера"""
    print("🌐 Запуск backend сервера...")

    try:
        # Запускаем сервер через uvicorn с правильным путем к модулю
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path('.').absolute())
        env['UVICORN_LOG_LEVEL'] = 'debug'  # Включаем подробное логирование

        print(f"    🔧 PYTHONPATH: {env['PYTHONPATH']}")

        # Создаем процесс с перенаправлением вывода
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1",  # Используем localhost вместо 0.0.0.0
            "--port", "8000",
            "--reload",
            "--log-level", "debug"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, cwd=Path('.').absolute())

        processes.append(("Backend", process))

        # Читаем вывод в отдельном потоке
        def read_output():
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line.strip():
                    print(f"[BACKEND] {line.strip()}")

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

        # Даем серверу время на запуск
        time.sleep(2)

        # Проверяем, что процесс все еще работает
        if process.poll() is not None:
            print("❌ Backend процесс завершился сразу после запуска")
            return None

        print("✅ Backend процесс запущен")
        return process

    except Exception as e:
        print(f"❌ Ошибка запуска backend: {e}")
        return None


def run_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")

    try:
        os.chdir("bot")

        # Запускаем бота
        process = subprocess.Popen([
            sys.executable, "bot.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        processes.append(("Bot", process))

        # Читаем вывод в отдельном потоке
        def read_output():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[BOT] {line.rstrip()}")

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

        os.chdir("..")
        return process

    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return None


def run_frontend_dev():
    """Запуск фронтенда в режиме разработки"""
    print("⚛️  Запуск React dev сервера...")

    try:
        os.chdir("frontend")

        # Запускаем dev сервер
        env = os.environ.copy()
        env['BROWSER'] = 'none'  # Не открываем браузер автоматически

        process = subprocess.Popen([
            npm_path, "start"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)

        processes.append(("Frontend", process))

        # Читаем вывод в отдельном потоке
        def read_output():
            for line in iter(process.stdout.readline, ''):
                if line.strip() and not line.startswith("webpack compiled"):
                    print(f"[FRONTEND] {line.rstrip()}")

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

        os.chdir("..")
        return process

    except Exception as e:
        print(f"❌ Ошибка запуска frontend: {e}")
        return None


def cleanup():
    """Остановка всех процессов"""
    print("\n🛑 Остановка сервисов...")

    for name, process in processes:
        try:
            print(f"  🔸 Остановка {name}...")
            process.terminate()

            # Ждем завершения
            try:
                process.wait(timeout=5)
                print(f"    ✅ {name} остановлен")
            except subprocess.TimeoutExpired:
                print(f"    ⚡ Принудительная остановка {name}...")
                process.kill()
                process.wait()
                print(f"    ✅ {name} принудительно остановлен")

        except Exception as e:
            print(f"    ⚠️  Ошибка остановки {name}: {e}")

    print("✅ Все сервисы остановлены")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректной остановки"""
    cleanup()
    sys.exit(0)


def wait_for_backend():
    """Ожидание запуска backend сервера"""
    print("⏳ Ожидание запуска backend сервера...")
    
    start_time = time.time()
    max_wait = 30  # максимальное время ожидания в секундах
    check_interval = 1  # интервал проверки в секундах
    
    while time.time() - start_time < max_wait:
        try:
            # Проверяем, что процесс backend все еще работает
            for name, process in processes:
                if name == "Backend":
                    if process.poll() is not None:
                        print("❌ Backend сервер остановился")
                        return False
            
            # Проверяем доступность сервера
            import requests
            try:
                # Пробуем разные эндпоинты
                endpoints = [
                    "http://127.0.0.1:8000/health",
                    "http://127.0.0.1:8000/api/ping",
                    "http://127.0.0.1:8000"
                ]
                
                for endpoint in endpoints:
                    try:
                        print(f"Проверка {endpoint}...")
                        response = requests.get(endpoint, timeout=1)
                        if response.status_code == 200:
                            print(f"✅ Backend сервер успешно запущен (проверка через {endpoint})")
                            return True
                    except requests.RequestException as e:
                        print(f"⚠️ Ошибка при проверке {endpoint}: {e}")
                        continue
                
            except Exception as e:
                print(f"⚠️ Ошибка при проверке сервера: {e}")
            
            # Ждем перед следующей проверкой
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"❌ Ошибка при проверке backend: {e}")
            return False
    
    print("❌ Backend сервер не запустился в течение 30 секунд")
    print("Проверьте:")
    print("1. Нет ли ошибок в логах сервера")
    print("2. Не занят ли порт 8000 другим процессом")
    print("3. Доступен ли сервер по адресу http://127.0.0.1:8000")
    return False


def show_status():
    """Показать статус и ссылки"""
    webapp_url = os.getenv("WEBAPP_URL", "https://your-ngrok-url.ngrok-free.app")

    status_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                     🎉 ВСЕ ГОТОВО!                         ║
╚══════════════════════════════════════════════════════════════╝

🌐 Backend API:     http://localhost:8000
📖 Документация:    http://localhost:8000/docs
🔍 Проверка:        http://localhost:8000/health

🤖 Telegram Bot:    Запущен и готов к работе
🌍 WebApp URL:      {webapp_url}
"""

    if not build_mode:
        status_text += """
⚛️  React Dev:       http://localhost:3000
🔧 Режим:           Разработка (hot reload)

📱 Для тестирования в браузере:
  → Откройте http://localhost:3000

📱 Для тестирования в Telegram:
  1. Соберите фронтенд: Ctrl+C → python run_all.py --build
  2. Откройте бота в Telegram
  3. Нажмите "Открыть приложение"
"""
    else:
        status_text += """
📱 Telegram Mini App готово!
  1. Откройте своего бота в Telegram
  2. Отправьте /start
  3. Нажмите "Открыть приложение"

🔧 Режим:           Продакшен (оптимизированная сборка)
"""

    status_text += """
⚠️  Для остановки нажмите Ctrl+C
    """

    print(status_text)


def main():
    """Главная функция"""
    global build_mode

    # Проверяем аргументы командной строки
    if "--build" in sys.argv or "--production" in sys.argv:
        build_mode = True
        print("🏗️  Режим: Продакшен (с сборкой фронтенда)")
    else:
        print("🔧 Режим: Разработка (dev серверы)")

    print_banner()

    # Проверки
    if not check_requirements():
        sys.exit(1)

    # Установка зависимостей
    if not install_dependencies():
        sys.exit(1)

    # Сборка фронтенда для продакшена
    if build_mode:
        if not build_frontend():
            print("❌ Не удалось собрать фронтенд")
            sys.exit(1)

    # Регистрация обработчика сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Запуск сервисов
        backend_process = run_backend()
        if not backend_process:
            sys.exit(1)

        # Ждем запуска backend
        if not wait_for_backend():
            cleanup()
            sys.exit(1)

        # Запуск бота
        bot_process = run_bot()
        if not bot_process:
            cleanup()
            sys.exit(1)

        # Запуск фронтенда (только в dev режиме)
        if not build_mode:
            frontend_process = run_frontend_dev()
            # Фронтенд не критичен, можно продолжать без него

        # Показываем статус
        show_status()

        # Ожидание
        while True:
            time.sleep(1)

            # Проверяем что основные процессы еще живы
            if backend_process.poll() is not None:
                print("❌ Backend процесс остановился")
                break

            if bot_process.poll() is not None:
                print("❌ Bot процесс остановился")
                break

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
    finally:
        cleanup()


def show_help():
    """Показать справку"""
    help_text = """
🚀 Система запуска Telegram Mini App

Использование:
  python run_all.py [опции]

Опции:
  --build, --production    Режим продакшена (сборка фронтенда)
  --help, -h              Показать эту справку

Режимы запуска:

🔧 Режим разработки (по умолчанию):
  python run_all.py

  - Backend на http://localhost:8000
  - Frontend dev сервер на http://localhost:3000  
  - Hot reload для быстрой разработки
  - Тестирование в браузере

🏗️  Режим продакшена:
  python run_all.py --build

  - Сборка оптимизированного фронтенда
  - Backend отдает собранные файлы
  - Готово для Telegram Mini App
  - Тестирование только в Telegram

Примеры:
  python run_all.py                 # Разработка
  python run_all.py --build         # Продакшен
  python run_all.py --production     # То же что --build

Требования:
  - Python 3.9+
  - Node.js 16+
  - npm
  - Файл .env с токеном бота
"""
    print(help_text)


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
    else:
        main()