"""Service for managing application settings."""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.app_dir import ensure_app_data_dir
from src.constants.api import THEME_DARK, THEME_LIGHT, THEME_SYSTEM

logger = logging.getLogger(__name__)

SETTINGS_FILE_NAME = "settings.json"


class SettingsService:
    """Service for managing application settings."""

    def __init__(self, settings_path: Optional[Path] = None):
        """Initialize the settings service.
        
        Args:
            settings_path: Optional path to settings file. If not provided, uses default location.
        """
        if settings_path is None:
            app_dir = ensure_app_data_dir()
            settings_path = app_dir / SETTINGS_FILE_NAME
        
        self.settings_path = settings_path
        self._default_settings = {
            "theme": THEME_SYSTEM
        }
        self._ensure_settings_file()

    def _ensure_settings_file(self):
        """Ensure settings file exists with default values."""
        if not self.settings_path.exists():
            self._save_settings(self._default_settings)

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = {**self._default_settings, **settings}
                    return merged
            return self._default_settings.copy()
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return self._default_settings.copy()

    def _save_settings(self, settings: Dict[str, Any]):
        """Save settings to file."""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def get_theme(self) -> str:
        """Get current theme setting.
        
        Returns:
            Theme value: "dark", "light", or "system"
        """
        settings = self._load_settings()
        return settings.get("theme", THEME_SYSTEM)

    def set_theme(self, theme: str) -> bool:
        """Set theme setting.
        
        Args:
            theme: Theme value ("dark", "light", or "system")
            
        Returns:
            True if set successfully, False otherwise
        """
        if theme not in [THEME_DARK, THEME_LIGHT, THEME_SYSTEM]:
            logger.warning(f"Invalid theme value: {theme}")
            return False
        
        try:
            settings = self._load_settings()
            settings["theme"] = theme
            self._save_settings(settings)
            logger.info(f"Theme set to: {theme}")
            return True
        except Exception as e:
            logger.error(f"Error setting theme: {e}")
            return False

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings.
        
        Returns:
            Dictionary of all settings
        """
        return self._load_settings()

    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            settings = self._load_settings()
            settings[key] = value
            self._save_settings(settings)
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False


# Global service instance
_settings_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    """Get or create the global settings service instance."""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
