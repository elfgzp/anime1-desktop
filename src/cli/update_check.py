"""Shared update checking CLI module.

This module provides update checking functionality that can be used by:
- Main application entry points (app.py, desktop.py)
- CLI test scripts (tests/test_update_check_cli.py)

All imports are at module level to avoid issues with PyInstaller onefile builds.
"""
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

import requests

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import at module level (avoid imports inside functions for PyInstaller compatibility)
from src.constants.app import (
    PLATFORM_DARWIN,
    PLATFORM_WIN32,
    SHELL_BASH,
    EXT_DMG,
    EXT_ZIP,
    UPDATE_LOG_PREFIX,
    UPDATE_DOWNLOAD_PREFIX,
    UPDATE_CHECK_PREFIX,
    UPDATE_FILE_PREFIX,
    UPDATE_TEMP_PREFIX,
    MACOS_APP_NAME,
    MACOS_APP_PATH,
    MACOS_UPDATER_SCRIPT,
    MACOS_UPDATER_SHELL,
    MACOS_UPDATER_TEMPLATE,
    MACOS_STRUCTURE_DEPTH,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_TIMEOUT,
)
from src.services.update_checker import UpdateChecker, UpdateChannel, UpdateInfo
from src.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME
from src.utils.app_dir import get_download_dir, get_install_dir
from src.utils import get_project_root

logger = logging.getLogger(__name__)


def print_update_result(update_info: UpdateInfo, current_version: str):
    """Print update check result in a formatted way."""
    print(f"\n{UPDATE_CHECK_PREFIX} Mode: checking for updates...")
    print(f"{UPDATE_CHECK_PREFIX} Current version: {current_version}")

    print("\n" + "=" * 60)
    print("Update Check Result")
    print("=" * 60)
    print(f"  Current Version: {update_info.current_version}")
    print(f"  Has Update:      {update_info.has_update}")
    print(f"  Latest Version:  {update_info.latest_version or 'unknown'}")
    print(f"  Is Prerelease:   {update_info.is_prerelease}")

    if update_info.has_update:
        print(f"\n  [UPDATE AVAILABLE] v{update_info.latest_version}")
        if update_info.download_url:
            print(f"  Download URL:    {update_info.download_url}")
        if update_info.asset_name:
            print(f"  Asset:           {update_info.asset_name}")
        if update_info.download_size:
            print(f"  Size:            {update_info.download_size:,} bytes")
        if update_info.release_notes:
            print(f"\n  Release Notes:")
            for line in update_info.release_notes.split('\n')[:10]:
                print(f"    {line}")
            if len(update_info.release_notes.split('\n')) > 10:
                print("    ...")
    else:
        if update_info.latest_version:
            print(f"\n  [UP TO DATE] Already at latest version v{update_info.latest_version}")
        else:
            print(f"\n  [UNKNOWN] Could not determine latest version")

    print("=" * 60 + "\n")


def check_update(
    current_version: str,
    channel: str = "stable",
    repo_owner: str = GITHUB_REPO_OWNER,
    repo_name: str = GITHUB_REPO_NAME,
) -> UpdateInfo:
    """Check for updates with given parameters.

    Args:
        current_version: Current version to compare against
        channel: Update channel (stable or test)
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name

    Returns:
        UpdateInfo with update check results
    """
    update_channel = UpdateChannel.TEST if channel == "test" else UpdateChannel.STABLE

    checker = UpdateChecker(
        repo_owner=repo_owner,
        repo_name=repo_name,
        current_version=current_version,
        channel=update_channel
    )

    return checker.check_for_update()


def run_check_update(current_version: str, channel: str = "stable") -> int:
    """Run update check and print results.

    Args:
        current_version: Current version to compare against
        channel: Update channel (stable or test)

    Returns:
        Exit code: 0 = no update, 1 = update available, 2 = error
    """
    print(f"{UPDATE_CHECK_PREFIX} Mode: checking for updates...")
    print(f"{UPDATE_CHECK_PREFIX} Current version: {current_version}")
    print(f"{UPDATE_CHECK_PREFIX} Channel: {channel}")

    try:
        update_info = check_update(
            current_version=current_version,
            channel=channel,
        )

        print_update_result(update_info, current_version)

        print(f"\n{'='*50}")
        print(f"Update Check Result:")
        print(f"  Current Version: {update_info.current_version}")
        print(f"  Has Update: {update_info.has_update}")
        if update_info.has_update:
            print(f"  Latest Version: {update_info.latest_version}")
        else:
            print(f"  Latest Version: {update_info.latest_version or 'unknown'}")
        print(f"{'='*50}\n")

        return 0 if not update_info.has_update else 1

    except Exception as e:
        print(f"{UPDATE_CHECK_PREFIX} Error: {e}")
        import traceback
        traceback.print_exc()
        return 2


def run_auto_update(current_version: str, channel: str = "stable") -> int:
    """Check for updates and auto-install if available.

    This reuses the same logic as the /api/settings/update/download endpoint.

    Args:
        current_version: Current version to compare against
        channel: Update channel (stable or test)

    Returns:
        Exit code: 0 = no update or update installed, 1 = update available but not installed, 2 = error
    """
    log = f"{UPDATE_LOG_PREFIX}"
    download_log = f"{UPDATE_DOWNLOAD_PREFIX}"

    print(f"\n{log} Mode: check and auto-install updates")
    print(f"{log} Current version: {current_version}")
    print(f"{log} Channel: {channel}")

    try:
        update_info = check_update(
            current_version=current_version,
            channel=channel,
        )

        print_update_result(update_info, current_version)

        if not update_info.has_update:
            print(f"\n{log} No update available. Already at latest version: {update_info.latest_version or current_version}")
            return 0

        # There is an update - download and install it
        if not update_info.download_url:
            print(f"{log} Error: No download URL available")
            return 1

        print(f"\n{log} Downloading and installing update...")
        print(f"{log} URL: {update_info.download_url}")
        print(f"{log} Asset: {update_info.asset_name}")

        # Get filename from URL
        url = update_info.download_url
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = f"{UPDATE_FILE_PREFIX}{uuid.uuid4().hex[:8]}{EXT_DMG}"

        # Get download directory
        download_dir = get_download_dir()
        print(f"{download_log} download_dir={download_dir}")
        download_dir.mkdir(parents=True, exist_ok=True)
        file_path = download_dir / filename

        print(f"{download_log} Downloading from {url} to {file_path}")

        # Download the file
        response = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()

        downloaded_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

        print(f"{download_log} Downloaded {downloaded_size:,} bytes")

        # Check if it's a DMG file
        is_dmg = filename.lower().endswith(EXT_DMG)

        if sys.platform == PLATFORM_DARWIN and is_dmg:
            # macOS DMG auto-install - spawn subprocess and exit immediately
            print(f"{log} Auto-installing DMG on macOS...")

            # Get the path to the current app
            app_path = Path(sys.executable).resolve()
            if app_path.name == MACOS_APP_NAME.replace(EXT_DMG, ''):
                real_app_path = app_path
                for _ in range(MACOS_STRUCTURE_DEPTH):
                    real_app_path = real_app_path.parent
            else:
                real_app_path = Path(MACOS_APP_PATH)

            print(f"{log} App path: {real_app_path}")

            # Create bash script for update process
            temp_dir = Path(tempfile.mkdtemp(prefix=UPDATE_TEMP_PREFIX))
            updater_script = temp_dir / "updater.sh"

            bash_script = f'''#!/bin/bash
# Anime1 Auto-Updater Script
# This runs in a subprocess so the parent can exit before we replace the app

LOG_PREFIX="{log}"
DMG_PATH="{file_path}"
APP_PATH="{real_app_path}"
BACKUP_DIR="{temp_dir}/backup"
MACOS_APP_NAME="{MACOS_APP_NAME}"

log() {{
    echo "$LOG_PREFIX $1"
}}

log "Starting update process..."
log "DMG: $DMG_PATH"
log "App: $APP_PATH"

# Create backup
log "Creating backup..."
cp -R "$APP_PATH" "$BACKUP_DIR"

# Mount DMG
log "Mounting DMG..."
MOUNT_RESULT=$(hdiutil attach -nobrowse "$DMG_PATH" 2>&1)
if [ $? -ne 0 ]; then
    log "Failed to mount DMG: $MOUNT_RESULT"
    exit 1
fi

# Find mount point
MOUNT_POINT=""
for line in $MOUNT_RESULT; do
    if [[ "$line" == *"/Volumes/"* ]]; then
        MOUNT_POINT=$(echo "$line" | awk '{{print $NF}}')
        break
    fi
done

if [ -z "$MOUNT_POINT" ]; then
    log "Could not find mount point"
    exit 1
fi

log "Mounted at: $MOUNT_POINT"

# Find new app
NEW_APP="$MOUNT_POINT/$MACOS_APP_NAME"
if [ ! -d "$NEW_APP" ]; then
    for item in "$MOUNT_POINT"/*.app; do
        if [ -d "$item" ]; then
            NEW_APP="$item"
            break
        fi
    done
fi

if [ ! -d "$NEW_APP" ]; then
    log "Could not find app in DMG"
    hdiutil detach -force "$MOUNT_POINT" 2>/dev/null
    exit 1
fi

log "Found new app: $NEW_APP"

# Replace app
log "Replacing app..."
rm -rf "$APP_PATH"
cp -R "$NEW_APP" "$APP_PATH"

# Fix permissions
chmod 755 "$APP_PATH/Contents/MacOS/Anime1" 2>/dev/null

log "App updated"

# Unmount DMG
log "Unmounting DMG..."
hdiutil detach -force "$MOUNT_POINT" 2>/dev/null

# Clean up backup
rm -rf "$BACKUP_DIR"
rm -rf "{temp_dir}"

# Launch updated app
log "Launching updated app..."
open "$APP_PATH"

log "Update completed successfully!"
'''

            updater_script.write_text(bash_script, encoding='utf-8')
            os.chmod(updater_script, 0o755)

            print(f"{log} Spawning updater subprocess...")

            # Spawn subprocess and exit immediately
            # The subprocess will be adopted by init (pid 1) and continue running
            subprocess.Popen(
                [SHELL_BASH, str(updater_script)],
                start_new_session=True,
                cwd=str(temp_dir)
            )

            print(f"{log} Updater started. Exiting parent process...")
            print(f"{log} Update will complete in the background.")
            return 0

        elif sys.platform == PLATFORM_WIN32 or filename.lower().endswith(EXT_ZIP):
            # Windows or ZIP file - extract to install directory
            print(f"{log} Extracting update...")

            install_dir = get_install_dir()
            print(f"{log} Install directory: {install_dir}")

            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(install_dir)

            print(f"{log} Update extracted to {install_dir}")
            print(f"{log} Update v{update_info.latest_version} installed successfully!")

            # Clean up
            file_path.unlink()
            return 0

        else:
            # Other platforms - just download
            print(f"{log} Download complete: {file_path}")
            print(f"{log} Manual installation required")
            return 0

    except Exception as e:
        print(f"{log} Error: {e}")
        import traceback
        traceback.print_exc()
        return 2
