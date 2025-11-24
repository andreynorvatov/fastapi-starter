import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FILE_PATH = "logs/app.log"
LOG_FORMAT = (
    "%(asctime)s %(levelname)s - [%(module)s - %(funcName)s - %(lineno)d] - "
    "[%(processName)s (pid=%(process)d) - %(threadName)s (tid=%(thread)d)] - %(message)s"
)

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

logger.setLevel(logging.INFO)
