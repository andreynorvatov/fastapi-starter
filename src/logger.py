"""Конфигурация логирования приложения."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE_PATH = Path("logs/app.log")
LOG_FORMAT = (
    "%(asctime)s %(levelname)s - [%(module)s - %(funcName)s - %(lineno)d] - "
    "[%(processName)s (pid=%(process)d) - %(threadName)s (tid=%(thread)d)] - %(message)s"
)

# Создаем директорию для логов, если она не существует
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger()

formatter = logging.Formatter(fmt=LOG_FORMAT)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    mode="a",
    encoding="utf-8",
    maxBytes=10 * 1024 * 1024,  # 10Mb
    backupCount=3,
)
file_handler.setFormatter(formatter)

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
