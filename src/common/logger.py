import logging
import os
from datetime import datetime
from typing import Optional

LOG_DIRECTORY: str = 'logs'
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def _new_log_file_path() -> str:
    """Path of a timestamped log file inside the (created if needed) logs directory."""
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOG_DIRECTORY, f"app_{timestamp}.log")


def _build_handlers(log_file: str) -> list:
    formatter: logging.Formatter = logging.Formatter(LOG_FORMAT)

    file_handler: logging.FileHandler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    stream_handler: logging.StreamHandler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    for handler in (file_handler, stream_handler):
        handler.setFormatter(formatter)

    return [file_handler, stream_handler]


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Sets up a logger that outputs to both a file and the console."""
    logger: logging.Logger = logging.getLogger(name or __name__)
    logger.setLevel(logging.DEBUG)

    for handler in _build_handlers(_new_log_file_path()):
        logger.addHandler(handler)

    return logger
