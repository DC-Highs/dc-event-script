import logging
import os
from datetime import datetime
from typing import Optional

def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Sets up a logger that outputs to both a file and the console."""
    logger: logging.Logger = logging.getLogger(name or __name__)
    logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    log_dir: str = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create filename with timestamp
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file: str = os.path.join(log_dir, f"app_{timestamp}.log")

    # File handler
    file_handler: logging.FileHandler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Stream handler (console)
    stream_handler: logging.StreamHandler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # Formatter
    formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
