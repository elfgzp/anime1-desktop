"""Application directory utilities for cross-platform support."""
import os
import sys
from pathlib import Path

from src.constants.app import (
    APP_NAME,
    PLATFORM_WIN32,
    PLATFORM_DARWIN,
    ENV_APPDATA,
    ENV_XDG_DATA_HOME,
    DIR_LIBRARY,
    DIR_APPLICATION_SUPPORT,
    DIR_APPDATA_ROAMING,
    DIR_ROAMING,
    DIR_LOCAL_SHARE,
    DIR_SHARE
)


def get_app_data_dir() -> Path:
    """Get application data directory for different platforms.
    
    Returns:
        Path to application data directory:
        - Windows: %APPDATA%/Anime1
        - macOS: ~/Library/Application Support/Anime1
        - Linux: ~/.local/share/Anime1
    """
    if sys.platform == PLATFORM_WIN32:
        # Windows
        app_data = os.getenv(ENV_APPDATA)
        if app_data:
            return Path(app_data) / APP_NAME
        else:
            # Fallback to user home
            return Path.home() / DIR_APPDATA_ROAMING / DIR_ROAMING / APP_NAME
    elif sys.platform == PLATFORM_DARWIN:
        # macOS
        return Path.home() / DIR_LIBRARY / DIR_APPLICATION_SUPPORT / APP_NAME
    else:
        # Linux and others
        xdg_data_home = os.getenv(ENV_XDG_DATA_HOME)
        if xdg_data_home:
            return Path(xdg_data_home) / APP_NAME
        else:
            return Path.home() / DIR_LOCAL_SHARE / DIR_SHARE / APP_NAME


def ensure_app_data_dir() -> Path:
    """Ensure application data directory exists and return it."""
    app_dir = get_app_data_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir
