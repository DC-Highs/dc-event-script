import io
import logging
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageFont

from dc_core import ConfigLanguage
from dc_localization import Localization

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def hermetic_environment(monkeypatch):
    """Keeps the tests independent from the developer's .env file and credentials."""
    monkeypatch.setattr("src.common.config_manager.load_dotenv", lambda *args, **kwargs: False)

    for name in ("DC_USER_ID", "DC_AUTH_TOKEN", "DC_GAME_CONFIG_URL"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


@pytest.fixture(autouse=True)
def default_font(monkeypatch):
    """Arial only exists on Windows; the default Pillow font renders the same code paths."""
    monkeypatch.setattr(ImageFont, "truetype", lambda *args, **kwargs: ImageFont.load_default_imagefont())


@pytest.fixture
def project_dir(monkeypatch):
    """Runs the test from the repository root, where the real templates live."""
    monkeypatch.chdir(PROJECT_ROOT)
    return PROJECT_ROOT


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    """Runs the test from an empty directory (no templates, no settings, logs and output stay inside it)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def close_log_handlers():
    yield

    for logger in list(logging.Logger.manager.loggerDict.values()):
        if isinstance(logger, logging.Logger):
            for handler in list(logger.handlers):
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)


def png_bytes(mode="RGBA", size=(8, 8), color=(10, 20, 30, 255)) -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def localization(**entries) -> Localization:
    return Localization(ConfigLanguage.ENGLISH, dict(entries))


def make_app(tmp_path, **overrides) -> SimpleNamespace:
    """A stand-in for DragonCityEventApp with only the state the island scripts read."""
    app = SimpleNamespace(
        data_view={},
        event_number=0,
        event_fp=str(tmp_path),
        chests_desired=[],
        chests_desired_names=[],
        chest_ids={},
        dragon_info={},
        asset_versioning={"chests": {}},
        asset_zip_fp=["/mobile/ui/", "/HD/dxt5/"],
        localization=localization(),
        image_formats={"CHEST": "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/chests/ui_"},
    )
    app.__dict__.update(overrides)
    return app


def rgba_array(width=4, height=4, alpha=255) -> np.ndarray:
    array = np.zeros((height, width, 4), dtype=np.uint8)
    array[:, :, :3] = 100
    array[:, :, 3] = alpha
    return array


@pytest.fixture
def listdir():
    return lambda path: sorted(os.listdir(path))
