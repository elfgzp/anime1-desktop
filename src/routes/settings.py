"""Settings API routes."""
import logging
import os
import platform
import signal
import subprocess
import time
import uuid
import zipfile
import shutil
import sys
import tempfile
import requests
from pathlib import Path
from flask import Blueprint, request

from src.services.settings_service import get_settings_service
from src.services.cover_cache_service import get_cover_cache_service
from src.services.favorite_service import get_favorite_service
from src.services.playback_history_service import get_playback_history_service
from src.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME
from src.constants.api import (
    success_response,
    error_response,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM
)
from src.constants.app import (
    PLATFORM_WIN32,
    PLATFORM_DARWIN,
    EXT_DMG,
    EXT_ZIP,
    SHELL_BASH,
    MACOS_APP_PATH,
    MACOS_APP_NAME,
    UPDATE_TEMP_PREFIX,
    UPDATE_FILE_PREFIX,
)
from src.services.constants import (
    PLATFORM_WINDOWS,
    PLATFORM_MACOS,
    PLATFORM_LINUX,
    CMD_BASH,
    CMD_CMD,
    CMD_ARG_C,
    BAT_SCRIPT_EXT,
    UPDATER_TEMP_PREFIX,
    UPDATER_BATCH_NAME,
    RESTART_SCRIPT_NAME,
    RESTART_SCRIPT_FILE,
    RESTART_SCRIPT_PREFIX,
    MACOS_APP_BUNDLE_PATH,
    MACOS_APP_CONTENTS_MACOS,
    LINUX_INSTALL_DIR,
    LINUX_APP_NAME,
    SYSTEM_PLATFORM_WIN32,
    SYSTEM_DARWIN,
    SYSTEM_LINUX,
    SHELL_SHEBANG,
    UPDATE_FILENAME_PREFIX,
    SUBPROCESS_WAIT_INTERVAL,
    SUBPROCESS_WAIT_TIMEOUT,
)
from src.utils.app_dir import get_app_data_dir, get_download_dir, get_install_dir
from src.utils import get_project_root

logger = logging.getLogger(__name__)

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@settings_bp.route("/theme", methods=["GET"])
def get_theme():
    """Get current theme setting."""
    try:
        service = get_settings_service()
        theme = service.get_theme()

        return success_response(data={"theme": theme})
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/theme", methods=["POST"])
def set_theme():
    """Set theme setting.

    Request body:
        theme: Theme value ("dark", "light", or "system")
    """
    try:
        data = request.get_json()
        theme = data.get("theme") if data else None

        if not theme:
            return error_response("theme is required", 400)

        if theme not in [THEME_DARK, THEME_LIGHT, THEME_SYSTEM]:
            return error_response(
                f"Invalid theme. Must be one of: {THEME_DARK}, {THEME_LIGHT}, {THEME_SYSTEM}",
                400
            )

        service = get_settings_service()
        success = service.set_theme(theme)

        if success:
            return success_response(message=f"Theme set to {theme}")
        else:
            return error_response("Failed to set theme", 500)

    except Exception as e:
        logger.error(f"Error setting theme: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/check_update", methods=["GET"])
def check_update():
    """Check for application updates.

    This endpoint delegates to the update API.
    """
    try:
        # Import here to avoid circular dependency
        from src.routes.update import check_update as update_check_update

        # Call the update check endpoint
        response = update_check_update()
        return response

    except Exception as e:
        logger.error(f"Error checking update: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/about", methods=["GET"])
def get_about():
    """Get about information.

    Returns:
        Application information including version, repository, etc.
    """
    try:
        from src import __version__
        from src.routes.update import update_info

        # Get version info
        version_response = update_info()
        version_data = version_response.get_json()

        # Repository URL
        repo_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"

        return success_response(data={
            "version": version_data.get("current_version", "unknown"),
            "channel": version_data.get("channel", "stable"),
            "repository": repo_url,
            "repo_owner": GITHUB_REPO_OWNER,
            "repo_name": GITHUB_REPO_NAME
        })
    except Exception as e:
        logger.error(f"Error getting about info: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/cache", methods=["GET"])
def get_cache_info():
    """Get cache information.

    Returns:
        Cache statistics including cover count and database size.
    """
    try:
        cover_service = get_cover_cache_service()
        favorite_service = get_favorite_service()

        cover_count = cover_service.get_cache_count()
        db_size = cover_service.get_cache_size()
        favorite_count = favorite_service.get_count()

        # Format size to human readable
        if db_size >= 1024 * 1024:
            size_str = f"{db_size / (1024 * 1024):.2f} MB"
        elif db_size >= 1024:
            size_str = f"{db_size / 1024:.2f} KB"
        elif db_size >= 0:
            size_str = f"{db_size} B"
        else:
            size_str = "未知"

        return success_response(data={
            "cover_count": cover_count,
            "database_size": db_size,
            "database_size_formatted": size_str,
            "favorite_count": favorite_count,
        })
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Clear the cover cache.

    Request body (optional):
        type: Type of cache to clear ("covers" or "all")
        - "covers": Clear only cover cache (default)
        - "all": Clear cover cache, playback history, and performance data

    Returns:
        Number of entries cleared.
    """
    try:
        data = request.get_json() or {}
        cache_type = data.get("type", "covers")

        cover_service = get_cover_cache_service()
        playback_service = get_playback_history_service()

        cleared_count = 0
        message_parts = []

        if cache_type in ("covers", "all"):
            cover_cleared = cover_service.clear_all()
            cleared_count += cover_cleared
            message_parts.append(f"{cover_cleared} 条封面缓存")

        if cache_type == "all":
            # Clear all playback history
            playback_service.delete_history()
            message_parts.append("播放记录")

            # Clear performance tracking data
            from src.models.performance_trace import clear_performance_traces, clear_performance_stats
            traces_cleared = clear_performance_traces()
            stats_cleared = clear_performance_stats()
            if traces_cleared > 0 or stats_cleared > 0:
                message_parts.append(f"性能追踪数据 ({traces_cleared} 条)")
                cleared_count += traces_cleared + stats_cleared

        # Execute VACUUM to shrink database and WAL checkpoint to release WAL file
        from src.models.database import get_database
        db = get_database()
        try:
            # TRUNCATE checkpoint writes changes and truncates WAL file to 0
            # This is the key to actually release disk space
            db.execute_sql("PRAGMA wal_checkpoint(TRUNCATE)")
            # VACUUM to shrink database
            db.execute_sql("VACUUM")
        except Exception as e:
            logger.error(f"Error shrinking database: {e}")

        message = "已清理 " + " + ".join(message_parts)

        return success_response(
            message=message,
            data={"cleared_count": cleared_count}
        )
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/logs", methods=["GET"])
def get_logs():
    """Get application logs.

    Query params:
        lines: Number of lines to return (default: 100, max: 1000)
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Log entries with timestamp, level, and message.
    """
    try:
        # Get number of lines (default 100, max 1000)
        lines = request.args.get("lines", 100, type=int)
        lines = min(max(lines, 10), 1000)

        # Get log level filter
        level_filter = request.args.get("level", None)

        # Find log file in app data directory
        log_dir = get_app_data_dir() / "logs"
        log_file = log_dir / "app.log"

        logs = []

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                # Read last N lines
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse log line format: "2024-01-15 10:30:45,123 [INFO] message"
                    try:
                        # Simple parsing: extract timestamp, level, and message
                        if " [" in line and "] " in line:
                            timestamp_part, rest = line.split(" [", 1)
                            level_part, message = rest.split("] ", 1)

                            log_entry = {
                                "timestamp": timestamp_part.strip(),
                                "level": level_part.strip(),
                                "message": message.strip()
                            }

                            # Apply level filter if specified
                            if level_filter and log_entry["level"] != level_filter.upper():
                                continue

                            logs.append(log_entry)
                        else:
                            # Non-standard format, just add as-is
                            if not level_filter:
                                logs.append({
                                    "timestamp": "",
                                    "level": "RAW",
                                    "message": line
                                })
                    except ValueError:
                        # Parse failed, add as raw
                        if not level_filter:
                            logs.append({
                                "timestamp": "",
                                "level": "RAW",
                                "message": line
                            })
        else:
            # Try to find logs directory
            if not (log_dir / "logs").exists():
                # Create logs directory if it doesn't exist
                os.makedirs(log_dir / "logs", exist_ok=True)
                return success_response(data={
                    "logs": [],
                    "message": "日志文件不存在，已创建 logs 目录",
                    "total_lines": 0
                })

        return success_response(data={
            "logs": logs,
            "total_lines": len(logs)
        })

    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/logs/clear", methods=["POST"])
def clear_logs():
    """Clear application logs."""
    try:
        log_dir = get_app_data_dir() / "logs"
        log_file = log_dir / "app.log"

        if log_file.exists():
            # Truncate the log file
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")

        return success_response(message="日志已清空")
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/logs/open", methods=["POST"])
def open_logs_folder():
    """Open the logs folder in system file explorer."""
    try:
        log_dir = get_app_data_dir() / "logs"

        # Create directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        log_dir_str = str(log_dir)

        system = platform.system().lower()
        if system == PLATFORM_WINDOWS:
            # Use subprocess to avoid encoding issues with os.startfile
            subprocess.run(
                ["explorer.exe", log_dir_str],
                check=True,
                shell=True,
                capture_output=True
            )
        elif system == PLATFORM_DARWIN:  # macOS (Darwin)
            subprocess.run(
                ["open", log_dir_str],
                check=True,
                capture_output=True
            )
        else:  # Linux
            subprocess.run(
                ["xdg-open", log_dir_str],
                check=True,
                capture_output=True
            )

        return success_response(message=f"已打开日志文件夹: {log_dir}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to open logs folder via subprocess: {e}")
        # Fallback to os.system
        try:
            system = platform.system().lower()
            if system == PLATFORM_WINDOWS:
                os.startfile(str(log_dir))
            else:
                os.system(f'xdg-open "{log_dir}"' if system != PLATFORM_DARWIN else f'open "{log_dir}"')
            return success_response(message=f"已打开日志文件夹: {log_dir}")
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            return error_response(f"无法打开日志文件夹: {str(fallback_error)}", 500)
    except Exception as e:
        logger.error(f"Error opening logs folder: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/update/download", methods=["POST"])
def download_update():
    """Download and optionally auto-install the update.

    Request body:
        url: Download URL for the update (required)
        auto_install: Whether to auto-install after download (optional, default: false)

    Returns:
        Path to the downloaded file or install result.
    """
    logger.info("[DOWNLOAD] download_update called")
    logger.info(f"[DOWNLOAD] Request URL: {request.url}")
    logger.info(f"[DOWNLOAD] Request method: {request.method}")

    try:
        data = request.get_json() or {}
        url = data.get("url")
        auto_install = data.get("auto_install", False)

        logger.info(f"[DOWNLOAD] url={url}, auto_install={auto_install}")

        if not url:
            return error_response("url is required", 400)

        # Get filename from URL
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = f"{UPDATE_FILENAME_PREFIX}{uuid.uuid4().hex[:8]}{EXT_ZIP}"

        logger.info(f"[DOWNLOAD] filename={filename}")

        # Check if it's a DMG file (macOS disk image)
        is_dmg = filename.lower().endswith(EXT_DMG)
        logger.info(f"[DOWNLOAD] is_dmg={is_dmg}")

        # Get download directory
        download_dir = get_download_dir()
        logger.info(f"[DOWNLOAD] download_dir={download_dir}")
        download_dir.mkdir(parents=True, exist_ok=True)
        file_path = download_dir / filename

        # Download the file
        logger.info(f"[DOWNLOAD] Downloading from {url} to {file_path}")

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        downloaded_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

        logger.info(f"[DOWNLOAD] Downloaded {downloaded_size} bytes")

        if auto_install:
            # Auto-install mode
            logger.info(f"[DOWNLOAD] auto_install=true, platform={sys.platform}")

            install_dir = get_install_dir()
            logger.info(f"[DOWNLOAD] install_dir={install_dir}")

            if platform.system().lower() == PLATFORM_WINDOWS:
                # Windows: Create a batch file that handles the update after app exits
                # This is necessary because Windows doesn't allow replacing running files
                logger.info(f"[DOWNLOAD-WINDOWS] Starting Windows update flow")

                # Create a temp directory for the updater
                temp_dir = Path(tempfile.mkdtemp(prefix=UPDATER_TEMP_PREFIX))
                logger.info(f"[DOWNLOAD-WINDOWS] Created temp dir: {temp_dir}")

                updater_batch = temp_dir / (UPDATER_BATCH_NAME + BAT_SCRIPT_EXT)
                zip_copy = temp_dir / file_path.name
                logger.info(f"[DOWNLOAD-WINDOWS] zip_copy: {zip_copy}")

                # Copy the zip to temp location
                shutil.copy2(file_path, zip_copy)
                logger.info(f"[DOWNLOAD-WINDOWS] Copied zip to temp location")

                # Get the executable path
                exe_path = Path(sys.executable)
                logger.info(f"[DOWNLOAD-WINDOWS] exe_path: {exe_path}")

                # Create PowerShell script for update (Windows has built-in PowerShell)
                logger.info(f"[DOWNLOAD-WINDOWS] Creating PowerShell update script...")
                logger.info(f"[DOWNLOAD-WINDOWS] - zip_copy: {zip_copy}")
                logger.info(f"[DOWNLOAD-WINDOWS] - install_dir: {install_dir}")
                logger.info(f"[DOWNLOAD-WINDOWS] - exe_path: {exe_path}")

                # Use PowerShell's Expand-Archive (built-in since PowerShell 5.0 / Windows 10)
                ps_script = f'''$ErrorActionPreference = 'Stop'
Write-Host "[UPDATER] Anime1 Update Starting"
Write-Host "[UPDATER] Source: {zip_copy}"
Write-Host "[UPDATER] Target: {install_dir}"

# Wait for parent process to exit (allow more time)
Write-Host "[UPDATER] Waiting for parent process to exit..."
Start-Sleep -Seconds 5

# Keep waiting until the exe is no longer locked
Write-Host "[UPDATER] Checking if exe is unlocked..."
$exePath = "{exe_path}"
$maxWait = 30
$waited = 0
while (Test-Path $exePath) {{
    try {{
        $lock = [System.IO.File]::Open($exePath, 'Open', 'ReadWrite', 'None')
        $lock.Close()
        break
    }} catch {{
        Start-Sleep -Seconds 1
        $waited += 1
        if ($waited -ge $maxWait) {{
            Write-Host "[UPDATER] WARNING: Exe still locked after {0} seconds, continuing anyway..." -f $maxWait
            break
        }}
    }}
}}

Write-Host "[UPDATER] Extracting update..."
$tempDir = "{temp_dir}"
$zipCopy = "{zip_copy}"
$installDir = "{install_dir}"

# Extract using PowerShell's Expand-Archive (no external Python needed)
try {{
    Expand-Archive -Path $zipCopy -DestinationPath $installDir -Force -ErrorAction Stop
    Write-Host "[UPDATER] Extraction complete"
}} catch {{
    Write-Host "[UPDATER] ERROR: $_"
    Start-Sleep -Seconds 5
    exit 1
}}

# Clean up - use rename then delete to handle locked files
try {{
    # Rename zip first (often works even when delete fails)
    $orphanedZip = "$env:TEMP\orphaned_update_$([guid]::NewGuid().ToString('N').Substring(0,8)).zip"
    try {{
        Move-Item -Path $zipCopy -Destination $orphanedZip -Force -ErrorAction Stop
        Write-Host "[UPDATER] Moved zip to temp"
    }} catch {{
        Write-Host "[UPDATER] Could not move zip, trying delete..."
        Remove-Item $zipCopy -Force -ErrorAction SilentlyContinue
    }}
    Write-Host "[UPDATER] Cleanup complete"
}} catch {{}}

Write-Host "[UPDATER] Launching updated app..."
if (Test-Path $exePath) {{
    Start-Process -FilePath $exePath -WindowStyle Normal
    Write-Host "[UPDATER] Update complete"
}} else {{
    Write-Host "[UPDATER] ERROR: Executable not found: $exePath"
}}

# Self-delete after a delay
Start-Sleep -Seconds 2
'''
                ps_script_path = temp_dir / "update.ps1"
                ps_script_path.write_text(ps_script, encoding='utf-8')
                logger.info(f"[DOWNLOAD-WINDOWS] Created PowerShell script: {ps_script_path}")

                # Create batch file that launches PowerShell script
                batch_content = f'''@echo off
echo [UPDATER] Anime1 Update Starting
echo [UPDATER] Launching PowerShell for extraction...
powershell -ExecutionPolicy Bypass -File "{ps_script_path}"
del "%~f0"
'''
                updater_batch.write_text(batch_content, encoding='utf-8')

                logger.info(f"[DOWNLOAD] Created updater batch at {updater_batch}")

                # Clean up the original download with error handling
                # The file might be locked by browser download or antivirus
                try:
                    if file_path.exists():
                        file_path.unlink(missing_ok=True)
                        logger.info(f"[DOWNLOAD] Deleted original download file: {file_path}")
                except PermissionError as pe:
                    logger.warning(f"[DOWNLOAD] Could not delete download file (locked): {file_path}. Will be cleaned up on next startup.")
                    # Rename instead of delete - some programs hold locks on the original file
                    try:
                        orphaned_path = file_path.parent / f"orphaned_update_{uuid.uuid4().hex[:8]}.zip"
                        file_path.rename(orphaned_path)
                        logger.info(f"[DOWNLOAD] Renamed to orphaned file: {orphaned_path}")
                    except Exception as rename_err:
                        logger.warning(f"[DOWNLOAD] Could not rename file either: {rename_err}")
                except Exception as delete_err:
                    logger.warning(f"[DOWNLOAD] Failed to clean up download file: {delete_err}")

                # Return info that app needs to restart
                return success_response(
                    message="更新已准备就绪，正在重启应用...",
                    data={
                        "success": True,
                        "restarting": True,
                        "updater_type": "windows",
                        "updater_path": str(updater_batch)
                    }
                )
            elif sys.platform == 'darwin':
                # macOS: Prefer ZIP for direct extraction, fall back to DMG
                # ZIP allows in-place replacement without mounting/unmounting
                is_zip = filename.lower().endswith(EXT_ZIP)

                if is_zip:
                    # macOS ZIP auto-install - extract directly (preferred method)
                    logger.info(f"[UPDATE-MACOS] Preparing ZIP auto-install: {file_path}")
                    logger.info(f"[UPDATE-MACOS] Filename: {filename}")

                    # Get app path for macOS
                    app_path = Path(sys.executable).resolve()
                    logger.info(f"[UPDATE-MACOS] Current app path: {app_path}")

                    if app_path.name == MACOS_APP_NAME:
                        install_dir = app_path.parent.parent.parent  # Contents/MacOS -> Contents -> .app
                    else:
                        install_dir = Path(MACOS_APP_BUNDLE_PATH)

                    logger.info(f"[UPDATE-MACOS] Install directory: {install_dir}")
                    logger.info(f"[UPDATE-MACOS] Current app exists: {install_dir.exists()}")

                    # Backup existing app
                    backup_dir = install_dir.parent / f"{install_dir.name}_backup_{uuid.uuid4().hex[:8]}"
                    logger.info(f"[UPDATE-MACOS] Backup directory: {backup_dir}")
                    backup_created = False
                    if install_dir.exists():
                        try:
                            shutil.copytree(install_dir, backup_dir)
                            backup_created = True
                            logger.info(f"[UPDATE-MACOS] Backup created successfully")
                        except Exception as e:
                            logger.warning(f"[UPDATE-MACOS] Could not create backup: {e}")

                    # Extract new version
                    try:
                        logger.info(f"[UPDATE-MACOS] Opening ZIP file: {file_path}")
                        logger.info(f"[UPDATE-MACOS] Extracting to install dir: {install_dir}")
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            # Check ZIP structure to handle both formats:
                            # 1. anime1-macos-0.2.4/Contents/... (portable format)
                            # 2. Anime1.app/Contents/... (app bundle format)
                            names = zf.namelist()
                            logger.info(f"[UPDATE-MACOS] ZIP file count: {len(names)} files")
                            logger.info(f"[UPDATE-MACOS] ZIP contents (first 10): {names[:10]}")

                            # Check if ZIP has Anime1.app/ prefix
                            has_app_prefix = any(name.startswith('Anime1.app/') for name in names)
                            logger.info(f"[UPDATE-MACOS] ZIP has Anime1.app/ prefix: {has_app_prefix}")

                            if has_app_prefix:
                                # ZIP has Anime1.app/ prefix, extract directly
                                logger.info(f"[UPDATE-MACOS] Extracting to {install_dir.parent}...")
                                zf.extractall(install_dir.parent)
                                logger.info(f"[UPDATE-MACOS] Direct extraction complete")
                                logger.info(f"[UPDATE-MACOS] New app exists: {(install_dir.parent / 'Anime1.app').exists()}")
                            else:
                                # ZIP has portable format like anime1-macos-0.2.4/Contents/...
                                # Extract to a temp location first, then move the .app to /Applications/
                                logger.info(f"[UPDATE-MACOS] Using portable format extraction...")
                                temp_extract_dir = Path(tempfile.mkdtemp(prefix='anime1_extract_'))
                                logger.info(f"[UPDATE-MACOS] Temp dir: {temp_extract_dir}")

                                zf.extractall(temp_extract_dir)
                                logger.info(f"[UPDATE-MACOS] Extracted to temp dir")

                                # Find the extracted app folder
                                extracted_folders = list(temp_extract_dir.iterdir())
                                logger.info(f"[UPDATE-MACOS] Extracted folders: {extracted_folders}")

                                if len(extracted_folders) == 1 and extracted_folders[0].is_dir():
                                    extracted_app = extracted_folders[0]
                                    logger.info(f"[UPDATE-MACOS] Moving app: {extracted_app.name}")
                                    # Remove old install_dir if exists (backup already created)
                                    if install_dir.exists():
                                        logger.info(f"[UPDATE-MACOS] Removing old installation...")
                                        shutil.rmtree(install_dir)
                                    # Move the extracted app to /Applications/
                                    shutil.move(str(extracted_app), str(install_dir))
                                    logger.info(f"[UPDATE-MACOS] App moved to {install_dir}")
                                    logger.info(f"[UPDATE-MACOS] New app exists: {install_dir.exists()}")
                                else:
                                    # Fallback: try to find .app folder
                                    logger.info(f"[UPDATE-MACOS] Searching for .app folder...")
                                    for item in temp_extract_dir.rglob('*.app'):
                                        if item.is_dir():
                                            logger.info(f"[UPDATE-MACOS] Found .app: {item}")
                                            if install_dir.exists():
                                                shutil.rmtree(install_dir)
                                            shutil.move(str(item), str(install_dir))
                                            break
                                # Clean up temp dir
                                shutil.rmtree(temp_extract_dir)
                                logger.info(f"[UPDATE-MACOS] Temp dir cleaned up")

                        logger.info(f"[UPDATE-MACOS] Installation to {install_dir} complete")

                        # Ensure executable has proper permissions (zipfile may strip them)
                        exe_path = install_dir / MACOS_APP_CONTENTS_MACOS / MACOS_APP_NAME
                        logger.info(f"[UPDATE-MACOS] Checking executable: {exe_path}")
                        if exe_path.exists():
                            current_mode = oct(os.stat(exe_path).st_mode)[-3:]
                            logger.info(f"[UPDATE-MACOS] Current permissions: {current_mode}")
                            os.chmod(exe_path, 0o755)
                            new_mode = oct(os.stat(exe_path).st_mode)[-3:]
                            logger.info(f"[UPDATE-MACOS] Set execute permissions: {new_mode}")
                        else:
                            logger.error(f"[UPDATE-MACOS] Executable NOT FOUND: {exe_path}")
                    except Exception as e:
                        logger.error(f"Failed to extract update: {e}")
                        if backup_created and backup_dir.exists():
                            logger.info("Restoring from backup...")
                            if install_dir.exists():
                                shutil.rmtree(install_dir)
                            shutil.copytree(backup_dir, install_dir)
                            shutil.rmtree(backup_dir)
                        return error_response(f"安装失败: {str(e)}", 500)

                    if backup_created and backup_dir.exists():
                        shutil.rmtree(backup_dir)

                    file_path.unlink()

                    # 记录安装成功信息
                    logger.info(f"[UPDATE-MACOS] Update installed successfully to {install_dir}")

                    # 获取新版本信息
                    from src import __version__
                    logger.info(f"[UPDATE-MACOS] New version: {__version__}")

                    # Launch the new app
                    exe_path = install_dir / MACOS_APP_CONTENTS_MACOS / MACOS_APP_NAME
                    logger.info(f"[UPDATE-MACOS] Restarting application: {exe_path}")
                    logger.info(f"[UPDATE-MACOS] Executable exists: {exe_path.exists()}")

                    # 创建独立的更新日志文件（更容易追踪更新流程）
                    update_log_path = Path.home() / "Library/Application Support/Anime1/update.log"
                    logger.info(f"[UPDATE-MACOS] Update log path: {update_log_path}")

                    # Create a shell script to restart after exit
                    temp_dir_restart = Path(tempfile.mkdtemp(prefix=RESTART_SCRIPT_PREFIX))
                    restart_script = temp_dir_restart / RESTART_SCRIPT_FILE
                    # 标记文件：重启脚本启动后创建，父进程检查此文件确认脚本已获取控制权
                    ready_marker = temp_dir_restart / "restart_ready"
                    restart_content = f'''{SHELL_SHEBANG}
# 标记文件：表示重启脚本已开始执行
READY_FILE="{ready_marker}"

# 记录重启日志
UPDATE_LOG="$HOME/Library/Application Support/Anime1/update.log"
echo "========================================" >> "$UPDATE_LOG"
echo "[RESTART] $(date): Starting Anime1 restart process" >> "$UPDATE_LOG"
echo "[RESTART] Executable path: {exe_path}" >> "$UPDATE_LOG"
echo "[RESTART] App path: {install_dir}" >> "$UPDATE_LOG"

# 标记脚本已开始执行（让父进程知道可以安全退出了）
touch "$READY_FILE"
echo "[RESTART] $(date): Restart script initialized, ready marker created" >> "$UPDATE_LOG"

# 查找并终止所有 Anime1 进程 - 使用多种方法确保完全终止
echo "[RESTART] $(date): Looking for running Anime1 processes..." >> "$UPDATE_LOG"

# 方法1: 使用 pgrep -a 查找所有包含 Anime1 的进程（-a 确保返回所有匹配）
PIDS=$(pgrep -a -f "Anime1" 2>/dev/null | awk '{{print $1}}' || echo "")
if [ -n "$PIDS" ]; then
    echo "[RESTART] $(date): Found Anime1 processes: $PIDS" >> "$UPDATE_LOG"
    for pid in $PIDS; do
        echo "[RESTART] $(date): Killing process $pid..." >> "$UPDATE_LOG"
        kill -9 "$pid" 2>/dev/null || true
    done
fi

# 方法2: 杀死 /Applications/Anime1.app 相关的进程
APPPIDS=$(pgrep -a -f "/Applications/Anime1" 2>/dev/null | awk '{{print $1}}' || echo "")
if [ -n "$APPPIDS" ]; then
    echo "[RESTART] $(date): Found app bundle processes: $APPPIDS" >> "$UPDATE_LOG"
    for pid in $APPPIDS; do
        echo "[RESTART] $(date): Killing process $pid..." >> "$UPDATE_LOG"
        kill -9 "$pid" 2>/dev/null || true
    done
fi

# 等待进程完全退出
sleep 2

# 再次检查并强制终止
REMAINING=$(pgrep -a -f "Anime1" 2>/dev/null | awk '{{print $1}}' || echo "")
if [ -n "$REMAINING" ]; then
    echo "[RESTART] $(date): WARNING - Some processes still running: $REMAINING" >> "$UPDATE_LOG"
    # 最后一次尝试杀死
    for pid in $REMAINING; do
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 1
fi

# 最终验证
FINAL_CHECK=$(pgrep -a -f "Anime1" 2>/dev/null | awk '{{print $1}}' || echo "")
if [ -z "$FINAL_CHECK" ]; then
    echo "[RESTART] $(date): All Anime1 processes terminated" >> "$UPDATE_LOG"
else
    echo "[RESTART] $(date): WARNING - Some processes may still be running: $FINAL_CHECK" >> "$UPDATE_LOG"
fi

# 清理旧的 _MEIPASS 目录（PyInstaller 临时文件）
# 这些目录可能包含旧的版本文件，需要在启动新版本前清理
echo "[RESTART] $(date): Cleaning up old PyInstaller temp directories..." >> "$UPDATE_LOG"
for meipass_dir in /tmp/_MEI*; do
    if [ -d "$meipass_dir" ]; then
        rm -rf "$meipass_dir" 2>/dev/null || true
        echo "[RESTART] $(date): Cleaned up: $meipass_dir" >> "$UPDATE_LOG"
    fi
done

echo "[RESTART] $(date): Launching updated app..." >> "$UPDATE_LOG"
"{exe_path}" &
APP_PID=$!
echo "[RESTART] $(date): App launched with PID: $APP_PID" >> "$UPDATE_LOG"

# 等待一小段时间确保应用启动
sleep 3

# 检查进程是否在运行
if kill -0 $APP_PID 2>/dev/null; then
    echo "[RESTART] $(date): SUCCESS - Anime1 restarted successfully (PID: $APP_PID)" >> "$UPDATE_LOG"
else
    echo "[RESTART] $(date): WARNING - Process may have exited (PID: $APP_PID)" >> "$UPDATE_LOG"
fi

echo "========================================" >> "$UPDATE_LOG"
'''
                    restart_script.write_text(restart_content, encoding='utf-8')
                    os.chmod(restart_script, 0o755)
                    logger.info(f"[UPDATE-MACOS] Created restart script: {restart_script}")

                    proc = subprocess.Popen(
                        [CMD_BASH, str(restart_script)],
                        start_new_session=True
                    )
                    logger.info(f"[UPDATE-MACOS] Restart script started (PID: {proc.pid})")

                    # 等待重启脚本创建标记文件，确认已获取控制权
                    logger.info(f"[UPDATE-MACOS] Waiting for restart script to initialize...")
                    for _ in range(int(SUBPROCESS_WAIT_TIMEOUT / SUBPROCESS_WAIT_INTERVAL)):
                        if ready_marker.exists():
                            logger.info(f"[UPDATE-MACOS] Restart script initialized successfully")
                            break
                        time.sleep(SUBPROCESS_WAIT_INTERVAL)
                    else:
                        logger.warning(f"[UPDATE-MACOS] Restart script may not have initialized (marker not found)")

                    return success_response(
                        message="更新完成，正在重启...",
                        data={
                            "success": True,
                            "restarting": True,
                            "updater_type": "macos_zip",
                            "download_path": str(file_path)
                        }
                    )
                elif is_dmg:
                    logger.info("[UPDATE-MACOS-DMG] Starting DMG auto-update process")
                    logger.info("[UPDATE-MACOS-DMG] Downloaded file: %s", file_path)
                    logger.info("[UPDATE-MACOS-DMG] File size: %d bytes", downloaded_size)

                    # Get the path to the current app
                    app_path = Path(sys.executable).resolve()
                    logger.info("[UPDATE-MACOS-DMG] Current executable: %s", app_path)

                    # For PyInstaller apps, the executable is inside the .app bundle
                    if app_path.name == MACOS_APP_NAME:
                        app_bundle = app_path.parent.parent.parent  # Contents/MacOS -> Contents -> .app
                        logger.info("[UPDATE-MACOS-DMG] Executable inside .app bundle")
                    else:
                        # Try to find the app bundle
                        app_bundle = Path(MACOS_APP_BUNDLE_PATH)
                        logger.info("[UPDATE-MACOS-DMG] Trying standard path: %s", app_bundle)
                        if not app_bundle.exists():
                            app_bundle = Path.home() / MACOS_APP_BUNDLE_PATH.lstrip('/')
                            logger.info("[UPDATE-MACOS-DMG] Trying home path: %s", app_bundle)
                        if not app_bundle.exists():
                            # Fallback: return manual install
                            logger.warning("[UPDATE-MACOS-DMG] Could not find app bundle, falling back to manual install")
                            return success_response(
                                message="下载完成，请手动打开并安装 DMG 文件",
                                data={
                                    "file_path": str(file_path),
                                    "file_size": downloaded_size,
                                    "open_path": str(file_path),
                                    "manual_install": True,
                                    "asset_type": "dmg"
                                }
                            )

                    logger.info("[UPDATE-MACOS-DMG] App bundle found: %s", app_bundle)
                    logger.info("[UPDATE-MACOS-DMG] App bundle exists: %s", app_bundle.exists())

                    # Create the updater script path
                    root = get_project_root()
                    updater_script = root / "src" / "scripts" / "macos_updater.py"
                    logger.info("[UPDATE-MACOS-DMG] Updater script: %s", updater_script)

                    # Create a temp directory for the updater
                    temp_dir = Path(tempfile.mkdtemp(prefix=UPDATER_TEMP_PREFIX))
                    updater_script_copy = temp_dir / 'macos_updater.py'

                    # Copy the updater script to temp location
                    shutil.copy2(updater_script, updater_script_copy)

                    # Get the real app path
                    real_app_path = app_bundle.resolve()

                    logger.info("[UPDATE-MACOS-DMG] App bundle: %s", real_app_path)
                    logger.info("[UPDATE-MACOS-DMG] Updater script: %s", updater_script_copy)

                    # Create a shell script that runs the updater and then the new app
                    shell_script = temp_dir / 'run_updater.sh'
                    shell_content = f'''#!/bin/bash
cd "{temp_dir}"
"{sys.executable}" "{updater_script_copy}" --dmg "{file_path}" --app "{real_app_path}" --no-cleanup
RESULT=$?
exit $RESULT
'''
                    shell_script.write_text(shell_content, encoding='utf-8')
                    os.chmod(shell_script, 0o755)

                    logger.info(f"[DOWNLOAD] Created shell updater script at {shell_script}")

                    # Release the instance lock BEFORE launching updater
                    # This prevents a race condition where updater tries to acquire the lock
                    # while anime1 is still running
                    logger.info("[DOWNLOAD] Releasing instance lock before launching updater...")
                    from src.desktop import InstanceLock
                    lock = InstanceLock()
                    lock.force_release()
                    logger.info("[DOWNLOAD] Instance lock released")

                    # Launch the updater detached and exit
                    logger.info(f"[DOWNLOAD] Launching updater with subprocess.Popen, platform={sys.platform}")
                    try:
                        if sys.platform == SYSTEM_PLATFORM_WIN32:
                            proc = subprocess.Popen(
                                [CMD_BASH, str(shell_script)],
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                                cwd=str(temp_dir)
                            )
                        else:
                            proc = subprocess.Popen(
                                [CMD_BASH, str(shell_script)],
                                start_new_session=True,
                                cwd=str(temp_dir)
                            )
                        logger.info(f"[DOWNLOAD] subprocess.Popen started successfully, pid={proc.pid}")
                    except Exception as popen_err:
                        logger.error(f"[DOWNLOAD] subprocess.Popen failed: {popen_err}")
                        raise

                    # 等待 updater 进程开始执行
                    logger.info("[DOWNLOAD] Waiting for updater to start...")
                    updater_started = False
                    for _ in range(int(SUBPROCESS_WAIT_TIMEOUT / SUBPROCESS_WAIT_INTERVAL)):
                        try:
                            result = subprocess.run(
                                ['pgrep', '-f', 'macos_updater'],
                                capture_output=True,
                                text=True,
                                timeout=1
                            )
                            if result.returncode == 0:
                                updater_started = True
                                logger.info(f"[DOWNLOAD] Updater is running")
                                break
                        except Exception:
                            pass
                        time.sleep(SUBPROCESS_WAIT_INTERVAL)
                    if not updater_started:
                        logger.warning("[DOWNLOAD] Updater may not have started")

                    logger.info("Launched macOS updater, exiting app...")
                    return success_response(
                        message="正在安装更新...",
                        data={
                            "success": True,
                            "restarting": True,
                            "updater_type": "macos_dmg",
                            "cleanup_delay": 5,
                            "download_path": str(file_path)
                        }
                    )
            else:
                # Linux or other non-Windows, non-macOS platforms
                logger.info(f"Preparing Linux update for {file_path}")

                # Get app path
                exe_path = Path(sys.executable)
                if exe_path.name == LINUX_APP_NAME:
                    install_dir = exe_path.parent  # /opt/anime1 directory
                else:
                    install_dir = Path(LINUX_INSTALL_DIR)

                # Backup existing app
                backup_dir = install_dir.parent / f"{install_dir.name}_backup_{uuid.uuid4().hex[:8]}"
                logger.info(f"Creating backup at {backup_dir}")
                backup_created = False
                if install_dir.exists():
                    try:
                        shutil.copytree(install_dir, backup_dir)
                        backup_created = True
                    except Exception as e:
                        logger.warning(f"Could not create backup: {e}")

                # Extract new version
                try:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.extractall(install_dir)
                    logger.info(f"Extracted update to {install_dir}")
                except Exception as e:
                    logger.error(f"Failed to extract update: {e}")
                    if backup_created and backup_dir.exists():
                        logger.info("Restoring from backup...")
                        if install_dir.exists():
                            shutil.rmtree(install_dir)
                        shutil.copytree(backup_dir, install_dir)
                        shutil.rmtree(backup_dir)
                    return error_response(f"安装失败: {str(e)}", 500)

                if backup_created and backup_dir.exists():
                    shutil.rmtree(backup_dir)

                file_path.unlink()

                # Restart the app
                new_exe_path = install_dir / "Anime1"
                logger.info(f"Restarting application: {new_exe_path}")
                subprocess.Popen(
                    [str(new_exe_path)],
                    cwd=str(install_dir),
                    start_new_session=True
                )

                # 等待新进程启动，避免过早退出
                logger.info(f"Waiting for new app to start...")
                time.sleep(SUBPROCESS_WAIT_TIMEOUT)

                return success_response(
                    message="更新完成，正在重启...",
                    data={
                        "success": True,
                        "restarting": True,
                        "updater_type": "linux_zip",
                        "download_path": str(file_path)
                    }
                )
        else:
            # Manual mode: just download and let user handle it
            return success_response(
                message="下载完成",
                data={
                    "download_path": str(file_path),
                    "file_size": downloaded_size,
                    "open_path": str(file_path)
                }
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading update: {e}")
        return error_response(f"下载失败: {str(e)}", 500)
    except Exception as e:
        logger.error(f"Error downloading update: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/update/run-updater", methods=["POST"])
def run_updater():
    """Run the updater batch file and exit the application.

    This is used on Windows to run the updater after the app has exited.

    Request body:
        updater_path: Path to the updater batch file

    Returns:
        Success message (app will exit after this).
    """
    logger.info("[UPDATER] ============================================")
    logger.info("[UPDATER] run_updater called")
    logger.info("[UPDATER] PID: %d", os.getpid())
    logger.info("[UPDATER] Request URL: %s", request.url)
    logger.info("[UPDATER] ============================================")

    try:
        data = request.get_json() or {}
        updater_path = data.get("updater_path")

        logger.info("[UPDATER] updater_path=%s", updater_path)

        if updater_path:
            updater = Path(updater_path)
            logger.info("[UPDATER] Updater exists: %s", updater.exists())

        if not updater_path:
            return error_response("updater_path is required", 400)

        updater = Path(updater_path)
        logger.info(f"[UPDATER] updater exists={updater.exists()}")

        if not updater.exists():
            return error_response(f"Updater not found: {updater_path}", 404)

        logger.info(f"[UPDATER] Running updater: {updater}, platform={sys.platform}")

        # Release the instance lock BEFORE launching updater
        # This prevents a race condition where updater tries to acquire the lock
        # while anime1 is still running
        logger.info("[UPDATER] Releasing instance lock before launching updater...")
        from src.desktop import InstanceLock
        lock = InstanceLock()
        lock.force_release()
        logger.info("[UPDATER] Instance lock released")

        # Run the updater and exit
        try:
            if sys.platform == SYSTEM_PLATFORM_WIN32:
                proc = subprocess.Popen(
                    [CMD_CMD, CMD_ARG_C, str(updater)],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                proc = subprocess.Popen(
                    [str(updater)],
                    start_new_session=True
                )
            logger.info(f"[UPDATER] subprocess.Popen started successfully, pid={proc.pid}")
        except Exception as popen_err:
            logger.error(f"[UPDATER] subprocess.Popen failed: {popen_err}")
            raise

        # Exit the application
        logger.info("Exiting application for update...")

        # Return success response and exit
        # Note: In tests, sys.exit is mocked so the test can continue
        # In real usage, sys.exit(0) will terminate the process after the response is sent
        response = success_response(data={"success": True}, message="启动更新程序")
        sys.exit(0)
        return response  # Unreachable but needed for type checking

    except Exception as e:
        logger.error(f"Error running updater: {e}")
        return error_response(str(e), 500)


@settings_bp.route("/exit", methods=["POST"])
def exit_app():
    """Exit the application gracefully.

    This is used after an update has been prepared to close the app
    so the updater can replace files.

    Returns:
        Success response (app will exit after this).
    """
    logger.info("[EXIT] ============================================")
    logger.info("[EXIT] exit_app called, shutting down...")
    logger.info("[EXIT] PID: %d", os.getpid())
    logger.info("[EXIT] ============================================")

    # Get parent PID from environment (set by start_flask_server_subprocess)
    parent_pid = os.environ.get('PARENT_PID')
    if parent_pid:
        try:
            parent_pid = int(parent_pid)
            logger.info("[EXIT] Parent PID: %d", parent_pid)

            # Use multiple methods to detect Windows platform
            # sys.platform might not work correctly in some environments (e.g., MSYS2)
            is_windows = (
                sys.platform == SYSTEM_PLATFORM_WIN32 or
                os.name == 'nt' or
                platform.system().lower() == 'windows'
            )

            if is_windows:
                # Windows: Use taskkill to terminate the parent process
                logger.info("[EXIT] Windows platform detected (sys.platform=%s, os.name=%s, platform.system()=%s), using taskkill...",
                           sys.platform, os.name, platform.system())
                try:
                    result = subprocess.run(
                        ['taskkill', '/F', '/PID', str(parent_pid)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info("[EXIT] Sent taskkill to parent process")
                    else:
                        logger.warning(f"[EXIT] taskkill failed: {result.stderr}")
                except Exception as e:
                    logger.warning(f"[EXIT] Failed to kill parent process: {e}")
            else:
                # Unix: Use signals
                # Try to terminate parent process gracefully first
                try:
                    os.kill(parent_pid, signal.SIGTERM)
                    logger.info("[EXIT] Sent SIGTERM to parent process")
                    # Give the parent process a moment to exit gracefully
                    time.sleep(1)
                except ProcessLookupError:
                    logger.info("[EXIT] Parent process already exited")
                except PermissionError:
                    logger.warning("[EXIT] Cannot send SIGTERM to parent (permission denied)")

                # Check if parent is still running, if so, force kill
                try:
                    os.kill(parent_pid, 0)  # This checks if process exists
                    logger.info("[EXIT] Parent still running, sending SIGKILL...")
                    os.kill(parent_pid, signal.SIGKILL)
                    logger.info("[EXIT] Sent SIGKILL to parent process")
                except ProcessLookupError:
                    logger.info("[EXIT] Parent process exited after SIGTERM")
                except PermissionError:
                    logger.warning("[EXIT] Cannot send SIGKILL to parent (permission denied)")
        except (ValueError, TypeError) as e:
            logger.warning(f"[EXIT] Invalid parent PID: {e}")

    # Also kill any child processes
    try:
        import psutil
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                logger.info("[EXIT] Killing child process: %d", child.pid)
                child.kill()
            except Exception as e:
                logger.warning(f"[EXIT] Failed to kill child process {child.pid}: {e}")
        if children:
            psutil.wait_procs(children, timeout=2)
            logger.info("[EXIT] All child processes terminated")
    except ImportError:
        logger.debug("[EXIT] psutil not available, skipping child process cleanup")

    # Calculate lock file path directly (avoiding imports that may fail in PyInstaller)
    try:
        if sys.platform == SYSTEM_PLATFORM_WIN32:
            # Windows: Use APPDATA
            data_dir = Path.home() / "AppData" / "Roaming" / "Anime1"
        else:
            # Unix/Mac: Use Library/Application Support
            data_dir = Path.home() / "Library" / "Application Support" / "Anime1"
        lock_file_path = data_dir / "instance.lock"
        logger.info("[EXIT] Lock file path: %s", lock_file_path)
        logger.info("[EXIT] Lock file exists: %s", lock_file_path.exists())

        if lock_file_path.exists():
            lock_file_path.unlink()
            logger.info("[EXIT] Deleted lock file")
        else:
            logger.info("[EXIT] Lock file doesn't exist, no need to delete")
    except Exception as lock_error:
        logger.warning(f"[EXIT] Could not handle lock file: {lock_error}")

    try:
        # Shutdown services
        from src.app import shutdown_services
        logger.info("[EXIT] Shutting down services...")
        shutdown_services()
        logger.info("[EXIT] Services shutdown complete")
    except Exception as e:
        logger.warning(f"[EXIT] Error shutting down services: {e}")

    # 等待重启脚本执行，避免过早退出导致重启脚本被终止
    # 检查是否有 anime1 restart 相关的进程在运行
    logger.info("[EXIT] Checking for restart script...")
    for _ in range(int(SUBPROCESS_WAIT_TIMEOUT / SUBPROCESS_WAIT_INTERVAL)):
        try:
            restart_running = False
            if sys.platform == SYSTEM_PLATFORM_WIN32:
                # Windows: Use tasklist to check for restart processes
                result = subprocess.run(
                    ['tasklist', '/FI', 'imagename eq cmd.exe'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Check if any cmd.exe is running with "anime1" in the command line
                if 'anime1' in result.stdout.lower():
                    restart_running = True
            else:
                # Unix: Use pgrep
                result = subprocess.run(
                    ['pgrep', '-f', 'anime1.*restart'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    restart_running = True

            if not restart_running:
                # 没有找到重启进程，可以安全退出
                logger.info("[EXIT] No restart script detected, safe to exit")
                break
            logger.info("[EXIT] Restart script still running, waiting...")
            time.sleep(SUBPROCESS_WAIT_INTERVAL)
        except Exception:
            break
    else:
        logger.warning("[EXIT] Restart script may still be running, proceeding with exit")

    # Exit immediately without calling Flask's error handlers
    logger.info("[EXIT] ============================================")
    logger.info("[EXIT] Exiting application (PID: %d)...", os.getpid())
    logger.info("[EXIT] ============================================")
    os._exit(0)


@settings_bp.route("/open_path", methods=["POST"])
def open_path():
    """Open a file or path in the system file explorer/executor.

    Request body:
        path: Path to the file or directory to open

    Returns:
        Success message.
    """
    try:
        data = request.get_json()
        path_str = data.get("path") if data else None

        if not path_str:
            return error_response("path is required", 400)

        path = Path(path_str)

        if not path.exists():
            return error_response(f"Path does not exist: {path_str}", 404)

        path_str = str(path)

        system = platform.system().lower()
        if system == PLATFORM_WINDOWS:
            # Use subprocess to avoid encoding issues
            subprocess.run(
                ["explorer.exe", "/select,", path_str],
                check=True,
                shell=True,
                capture_output=True
            )
        elif system == PLATFORM_DARWIN:  # macOS (Darwin)
            subprocess.run(
                ["open", "-R", path_str],  # -R reveals in Finder
                check=True,
                capture_output=True
            )
            # Also try to open the file directly
            subprocess.run(
                ["open", path_str],
                check=False,  # Don't fail if it's not directly openable
                capture_output=True
            )
        else:  # Linux
            subprocess.run(
                ["xdg-open", path_str],
                check=True,
                capture_output=True
            )

        return success_response(message=f"已打开: {path_str}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to open path via subprocess: {e}")
        # Fallback to os.system
        try:
            system = platform.system().lower()
            if system == PLATFORM_WINDOWS:
                os.startfile(str(path))
            else:
                os.system(f'xdg-open "{path}"' if system != PLATFORM_DARWIN else f'open "{path}"')
            return success_response(message=f"已打开: {path_str}")
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            return error_response(f"无法打开路径: {str(fallback_error)}", 500)
    except Exception as e:
        logger.error(f"Error opening path: {e}")
        return error_response(str(e), 500)
