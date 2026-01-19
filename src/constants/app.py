"""Application constants."""
import sys
from typing import Final

# Application name
APP_NAME: Final[str] = "Anime1"

# Platform identifiers
PLATFORM_WIN32: Final[str] = "win32"
PLATFORM_DARWIN: Final[str] = "darwin"

# Application state
IS_FROZEN: Final[bool] = getattr(sys, 'frozen', False)

# Environment variable names
ENV_APPDATA: Final[str] = "APPDATA"
ENV_XDG_DATA_HOME: Final[str] = "XDG_DATA_HOME"

# Directory names
DIR_LIBRARY: Final[str] = "Library"
DIR_APPLICATION_SUPPORT: Final[str] = "Application Support"
DIR_APPDATA_ROAMING: Final[str] = "AppData"
DIR_ROAMING: Final[str] = "Roaming"
DIR_LOCAL_SHARE: Final[str] = ".local"
DIR_SHARE: Final[str] = "share"

# Instance lock constants
LOCK_FILE_NAME: Final[str] = "instance.lock"
LOCK_UPDATE_INTERVAL: Final[int] = 10  # seconds
LOCK_TIMEOUT_SECONDS: Final[int] = 30  # seconds

# Instance lock messages
LOCK_MESSAGE_RUNNING: Final[str] = "已在运行"
LOCK_MESSAGE_BODY: Final[str] = "Anime1 桌面应用已经在运行中。\n\n请检查系统托盘或已打开的窗口。"

# Command line argument names
ARG_FLASk_ONLY: Final[str] = "--flask-only"
ARG_SUBPROCESS: Final[str] = "--subprocess"
ARG_PORT: Final[str] = "--port"
ARG_WIDTH: Final[str] = "--width"
ARG_HEIGHT: Final[str] = "--height"
ARG_DEBUG: Final[str] = "--debug"
ARG_REMOTE: Final[str] = "--remote"
ARG_CHECK_UPDATE: Final[str] = "--check-update"
ARG_CHANNEL: Final[str] = "--channel"
