import os

def ensure_directory(path: str) -> None:
    """Ensures that a directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)
