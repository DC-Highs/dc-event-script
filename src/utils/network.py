import urllib.request
import logging
import os
from typing import Union

logger = logging.getLogger(__name__)

def download_file(url: str, destination: str) -> bool:
    """Downloads a file from a URL to a destination path."""
    try:
        urllib.request.urlretrieve(url, destination)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def ensure_directory(path: str) -> None:
    """Ensures that a directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)
