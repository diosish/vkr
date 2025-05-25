import subprocess
import os

# Запуск frontend
frontend_proc = subprocess.Popen(["npm", "start"], cwd="frontend")

# Запуск backend
backend_proc = subprocess.Popen(["python", "main.py"], cwd="backend/utils")

# Запуск бота
bot_proc = subprocess.Popen(["python", "bot.py"], cwd="backend/bot")

# Ожидаем завершения всех процессов (будут работать параллельно)
frontend_proc.wait()
backend_proc.wait()
bot_proc.wait()
