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


def get_download_dir() -> Path:
    """Get download directory for different platforms.

    Returns:
        Path to download directory:
        - Windows: %USERPROFILE%/Downloads
        - macOS: ~/Downloads
        - Linux: ~/Downloads or XDG download dir
    """
    if sys.platform == PLATFORM_WIN32:
        # Windows
        downloads = os.getenv('USERPROFILE') or Path.home()
        return Path(downloads) / 'Downloads'
    elif sys.platform == PLATFORM_DARWIN:
        # macOS
        return Path.home() / 'Downloads'
    else:
        # Linux
        xdg_download = os.getenv('XDG_DOWNLOAD_DIR')
        if xdg_download:
            return Path(xdg_download)
        else:
            return Path.home() / 'Downloads'


def ensure_download_dir() -> Path:
    """Ensure download directory exists and return it."""
    download_dir = get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def get_current_executable_path() -> Path:
    """Get the path of the currently running executable.

    Returns:
        Path to the current executable
    """
    import sys

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        # Use the executable path, not the temp extraction dir
        if sys.platform == PLATFORM_WIN32:
            # On Windows, sys.executable points to the actual exe
            return Path(sys.executable)
        elif sys.platform == PLATFORM_DARWIN:
            # On macOS, need to find the actual .app, not inside _MEIPASS
            return Path(sys.executable)
        else:
            return Path(sys.executable)
    else:
        # Running as Python script
        return Path(sys.executable)


def get_install_dir() -> Path:
    """Get the installation directory of the application.

    Returns:
        Path to the installation directory where the app files are located
    """
    exe_path = get_current_executable_path()

    if sys.platform == PLATFORM_DARWIN:
        # macOS: exe is inside Anime1.app/Contents/MacOS/
        # Installation directory is the parent of Contents
        app_path = exe_path.parent.parent.parent  # Go up from MacOS to app bundle root
        if app_path.suffix == '.app':
            return app_path
        return exe_path.parent.parent  # Fallback
    elif sys.platform == PLATFORM_WIN32:
        # Windows: exe is directly in the install directory
        return exe_path.parent
    else:
        # Linux: exe is directly in the install directory
        return exe_path.parent


def get_restart_command() -> list:
    """Get the command to restart the application.

    Returns:
        List of command arguments to restart the app
    """
    exe_path = get_current_executable_path()
    return [str(exe_path)]
