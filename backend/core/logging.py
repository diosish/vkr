# backend/core/logging.py
"""
Централизованная система логирования
"""

import logging
import logging.config
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import traceback

# Создаем директорию для логов
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """Кастомный форматтер для структурированных логов"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Добавляем дополнительные поля если есть
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address

        # Добавляем traceback для ошибок
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Цветной форматтер для консоли"""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
        log_level: str = "INFO",
        enable_file_logging: bool = True,
        enable_json_logging: bool = False
):
    """
    Настройка системы логирования

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Включить запись в файлы
        enable_json_logging: Использовать JSON формат для файлов
    """

    # Базовая конфигурация
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored_console': {
                '()': ColoredConsoleFormatter,
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'json': {
                '()': StructuredFormatter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored_console',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'backend': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'WARNING',  # Уменьшаем verbose access логи
                'propagate': False
            },
            'sqlalchemy.engine': {
                'handlers': ['console'],
                'level': 'WARNING',  # Только важные SQL логи
                'propagate': False
            }
        }
    }

    # Добавляем файловые хендлеры если нужно
    if enable_file_logging:
        formatter = 'json' if enable_json_logging else 'detailed'

        # Общий лог файл
        config['handlers']['file_all'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': formatter,
            'filename': str(LOGS_DIR / 'volunteer_system.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }

        # Лог файл только для ошибок
        config['handlers']['file_error'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': formatter,
            'filename': str(LOGS_DIR / 'errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'encoding': 'utf8'
        }

        # Добавляем файловые хендлеры к логгерам
        for logger_name in ['', 'backend']:
            config['loggers'][logger_name]['handlers'].extend(['file_all', 'file_error'])

    # Применяем конфигурацию
    logging.config.dictConfig(config)

    # Создаем главный логгер
    logger = logging.getLogger('backend.main')
    logger.info(f"Logging initialized with level: {log_level}")
    logger.info(f"File logging: {'enabled' if enable_file_logging else 'disabled'}")
    logger.info(f"JSON format: {'enabled' if enable_json_logging else 'disabled'}")


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с заданным именем

    Args:
        name: Имя логгера (обычно __name__)

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(f"backend.{name}")


class LoggerMixin:
    """Mixin для добавления логгера в классы"""

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger


def log_function_call(func):
    """Декоратор для логирования вызовов функций"""

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling function {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {e}", exc_info=True)
            raise

    return wrapper


def log_api_request(func):
    """Декоратор для логирования API запросов"""

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # Попытаемся извлечь информацию о запросе
        request_info = "API request"
        if args:
            # Предполагаем что первый аргумент может содержать Request
            try:
                request = args[0]
                if hasattr(request, 'method') and hasattr(request, 'url'):
                    request_info = f"{request.method} {request.url}"
            except:
                pass

        logger.info(f"Processing {request_info}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"Successfully processed {request_info}")
            return result
        except Exception as e:
            logger.error(f"Failed to process {request_info}: {e}", exc_info=True)
            raise

    return wrapper


class RequestContextFilter(logging.Filter):
    """Фильтр для добавления контекста запроса в логи"""

    def filter(self, record):
        # Здесь можно добавить информацию о текущем запросе
        # например, через context variables
        record.request_id = getattr(record, 'request_id', 'unknown')
        record.user_id = getattr(record, 'user_id', 'anonymous')
        return True


# Настройка по умолчанию при импорте
if not logging.getLogger().handlers:
    setup_logging()