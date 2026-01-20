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
ARG_AUTO_UPDATE: Final[str] = "--auto-update"
ARG_CHANNEL: Final[str] = "--channel"

# Auto-update constants
UPDATE_LOG_PREFIX: Final[str] = "[AUTO-UPDATE]"
UPDATE_DOWNLOAD_PREFIX: Final[str] = "[DOWNLOAD]"
UPDATE_UPDATER_PREFIX: Final[str] = "[UPDATER]"
UPDATE_CHECK_PREFIX: Final[str] = "[CHECK-UPDATE]"

# File extensions
EXT_DMG: Final[str] = ".dmg"
EXT_ZIP: Final[str] = ".zip"
EXT_PY: Final[str] = ".py"
EXT_SH: Final[str] = ".sh"

# Update file naming
UPDATE_FILE_PREFIX: Final[str] = "anime1_update_"
UPDATE_TEMP_PREFIX: Final[str] = "anime1_update_"

# macOS app bundle
MACOS_APP_NAME: Final[str] = "Anime1"
MACOS_APP_BUNDLE_NAME: Final[str] = "Anime1.app"
MACOS_APP_PATH: Final[str] = "/Applications/Anime1.app"
MACOS_UPDATER_SCRIPT: Final[str] = "macos_updater.py"
MACOS_UPDATER_SHELL: Final[str] = "run_updater.sh"

# macOS app bundle structure
# Contents/MacOS/executable -> Contents -> .app
MACOS_STRUCTURE_DEPTH: Final[int] = 3  # executable -> MacOS -> Contents -> .app

# Shell script template for macOS updater
MACOS_UPDATER_TEMPLATE: Final[str] = '''#!/bin/bash
cd "{temp_dir}"
"{python_path}" "{updater_script}" --dmg "{dmg_path}" --app "{app_path}" --no-cleanup
RESULT=$?
exit $RESULT
'''

# Shell command
SHELL_BASH: Final[str] = "bash"

# Download constants
DOWNLOAD_CHUNK_SIZE: Final[int] = 8192
DOWNLOAD_TIMEOUT: Final[int] = 300  # seconds
