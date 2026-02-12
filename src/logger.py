"""Конфигурация логирования приложения в формате JSON для ELK."""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

LOG_FILE_PATH = Path("logs/app.log")


class JsonFormatter(logging.Formatter):
    """Форматтер для вывода логов в JSON формате, совместимом с ELK."""
    
    def __init__(self, **kwargs: Any) -> None:
        """Инициализация JSON форматтера."""
        super().__init__()
        self.default_fields = kwargs
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON."""
        # Базовые поля лога
        log_object: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "level_num": record.levelno,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": {
                "name": record.processName,
                "id": record.process,
            },
            "thread": {
                "name": record.threadName,
                "id": record.thread,
            },
        }
        
        # Добавляем дополнительные поля из record
        for key, value in self.default_fields.items():
            log_object[key] = value
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_object["stack_info"] = self.formatStack(record.stack_info)
        
        # Добавляем любые дополнительные атрибуты, добавленные через LoggerAdapter
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName",
                "exc_info", "exc_text", "stack_info", "taskName",
            ):
                log_object[key] = value
        
        return json.dumps(log_object, ensure_ascii=False)


# Создаем директорию для логов, если она не существует
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger()

json_formatter = JsonFormatter()

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(json_formatter)

file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    mode="a",
    encoding="utf-8",
    maxBytes=10 * 1024 * 1024,  # 10Mb
    backupCount=3,
)
file_handler.setFormatter(json_formatter)

logger.handlers = [stream_handler, file_handler]

# Уровень логирования по умолчанию (может быть переопределен через settings)
logger.setLevel(logging.INFO)


def set_log_level(level: str) -> None:
    """
    Устанавливает уровень логирования.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))
