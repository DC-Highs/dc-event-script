import json
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration, credentials from .env, and settings."""
    
    def __init__(self, settings_file: str = 'settings.json'):
        self.settings_path: str = settings_file

        load_dotenv()
        
        self.settings: Dict[str, Any] = self.load_settings(settings_file)

    def load_settings(self, path: str) -> Dict[str, Any]:
        """Loads settings from a JSON file."""
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            logger.warning(f"Settings file {path} not found. Using defaults.")
            return self._get_default_settings()
        except Exception as e:
            logger.error(f"Error loading settings from {path}: {e}")
            return self._get_default_settings()

    def save_settings(self) -> None:
        """Saves current settings to the JSON file."""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully.")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _get_default_settings(self) -> Dict[str, Any]:
        """Returns default settings structure."""
        return {
            "app": {
                "module_onboarding_check": 1,
                "default_event_number": 1,
                "event_date_order": 1,
                "chest_selection_status": 1
            },
            "ui": {
                "window_mode": "Light Mode",
                "themes": {
                    "Dark Mode": {
                        "menu_background": "black",
                        "menu_foreground": "white",
                        "window_background": "black",
                        "window_foreground": "white"
                    },
                    "Light Mode": {
                        "menu_background": "white",
                        "menu_foreground": "black",
                        "window_background": "white",
                        "window_foreground": "black"
                    }
                }
            }
        }

    def _stored_credentials(self) -> Dict[str, str]:
        return self.settings.get('credentials', {})

    def get_credentials(self) -> Dict[str, str]:
        """Returns the user credentials, preferring the environment variables over settings.json."""
        stored = self._stored_credentials()
        return {
            'userId': os.getenv('DC_USER_ID', '') or stored.get('userId', ''),
            'authToken': os.getenv('DC_AUTH_TOKEN', '') or stored.get('authToken', '')
        }

    def get_game_config_url(self) -> str:
        """Returns the game configuration endpoint, preferring the environment variable over settings.json."""
        return os.getenv('DC_GAME_CONFIG_URL', '') or self._stored_credentials().get('gameConfigUrl', '')

    def set_credentials(self, user_id: str, auth_token: str, game_config_url: Optional[str] = None) -> None:
        """Updates the session and persists the credentials (and the endpoint, when given) in settings.json."""
        os.environ['DC_USER_ID'] = user_id
        os.environ['DC_AUTH_TOKEN'] = auth_token
        stored = self.settings.setdefault('credentials', {})
        stored['userId'] = user_id
        stored['authToken'] = auth_token

        if game_config_url is not None:
            os.environ['DC_GAME_CONFIG_URL'] = game_config_url
            stored['gameConfigUrl'] = game_config_url

        self.save_settings()
        logger.info("Credentials persisted to settings.json")

    @property
    def app_config(self) -> Dict[str, Any]:
        return self.settings.get("app", {})

    @property
    def ui_config(self) -> Dict[str, Any]:
        return self.settings.get("ui", {})
