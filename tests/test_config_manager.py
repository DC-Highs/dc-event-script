import json
import logging
import os

import pytest

from src.common.config_manager import ConfigManager
from src.common.logger import setup_logging


def write_settings(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_missing_settings_file_uses_defaults(work_dir, caplog):
    with caplog.at_level(logging.WARNING):
        manager = ConfigManager("missing.json")

    assert manager.app_config["default_event_number"] == 1
    assert manager.ui_config["window_mode"] == "Light Mode"
    assert "not found" in caplog.text


def test_invalid_settings_file_uses_defaults(work_dir, caplog):
    (work_dir / "settings.json").write_text("{not json", encoding="utf-8")

    with caplog.at_level(logging.ERROR):
        manager = ConfigManager()

    assert manager.settings["ui"]["window_mode"] == "Light Mode"
    assert "Error loading settings" in caplog.text


def test_settings_are_loaded_saved_and_exposed(work_dir):
    path = write_settings(work_dir / "custom.json", {"app": {"x": 1}, "ui": {"window_mode": "Dark Mode"}})

    manager = ConfigManager(path)
    assert manager.app_config == {"x": 1}
    assert manager.ui_config == {"window_mode": "Dark Mode"}

    manager.settings["app"]["x"] = 2
    manager.save_settings()
    assert json.loads((work_dir / "custom.json").read_text(encoding="utf-8"))["app"]["x"] == 2


def test_save_settings_logs_failures(work_dir, caplog):
    manager = ConfigManager("missing.json")
    manager.settings_path = str(work_dir / "no-such-dir" / "settings.json")

    with caplog.at_level(logging.ERROR):
        manager.save_settings()

    assert "Error saving settings" in caplog.text


def test_credentials_prefer_the_environment(work_dir, monkeypatch):
    path = write_settings(work_dir / "s.json", {"credentials": {"userId": "from-file", "authToken": "file-token"}})
    manager = ConfigManager(path)

    assert manager.get_credentials() == {"userId": "from-file", "authToken": "file-token"}

    monkeypatch.setenv("DC_USER_ID", "from-env")
    monkeypatch.setenv("DC_AUTH_TOKEN", "env-token")
    assert manager.get_credentials() == {"userId": "from-env", "authToken": "env-token"}


def test_credentials_default_to_empty(work_dir):
    assert ConfigManager("missing.json").get_credentials() == {"userId": "", "authToken": ""}


def test_set_credentials_updates_session_and_file(work_dir):
    manager = ConfigManager(str(work_dir / "s.json"))

    manager.set_credentials("42", "secret")
    manager.set_credentials("43", "secret-2")

    saved = json.loads((work_dir / "s.json").read_text(encoding="utf-8"))
    assert saved["credentials"] == {"userId": "43", "authToken": "secret-2"}
    assert os.environ["DC_USER_ID"] == "43"
    assert manager.get_credentials()["authToken"] == "secret-2"
    os.environ.pop("DC_USER_ID")
    os.environ.pop("DC_AUTH_TOKEN")


def test_game_config_url_comes_from_the_environment(work_dir, monkeypatch):
    manager = ConfigManager("missing.json")
    assert manager.get_game_config_url() == ""

    monkeypatch.setenv("DC_GAME_CONFIG_URL", "https://example.com/config")
    assert manager.get_game_config_url() == "https://example.com/config"


def test_setup_logging_writes_to_the_logs_directory(work_dir):
    logger = setup_logging("tests.logger")
    logger.info("hello")
    logger.debug("details")

    logs = list((work_dir / "logs").glob("app_*.log"))
    assert len(logs) == 1
    assert "hello" in logs[0].read_text(encoding="utf-8")

    anonymous = setup_logging()
    assert anonymous.name == "src.common.logger"
    assert len(list((work_dir / "logs").glob("app_*.log"))) >= 1
