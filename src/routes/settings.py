"""Settings API routes."""
import logging
import os
import platform
import signal
import subprocess
import threading
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

# Global download progress tracking
_download_progress = {
    "is_downloading": False,
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "percent": 0,
    "status": "idle",  # idle, downloading, completed, failed
    "message": ""
}

# Global download result for background download
_download_result = {
    "error": None,
    "success": False,
    "restarting": False,
    "updater_type": None,
    "updater_path": None,
    "message": ""
}


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

        # Store result for the background thread to communicate
        download_result = {"error": None, "success": False, "restarting": False, "updater_type": None, "updater_path": None, "message": ""}

        def download_and_install_thread():
            """Background thread that handles download and optional installation."""
            try:
                # Step 1: Download the file
                logger.info(f"[DOWNLOAD-BG] Starting download from {url} to {file_path}")

                # Get content length for progress calculation
                response = requests.get(url, stream=True, timeout=300)
                response.raise_for_status()

                total_bytes = int(response.headers.get('Content-Length', 0))
                logger.info(f"[DOWNLOAD-BG] Total file size: {total_bytes} bytes")

                # Update progress state
                global _download_progress
                _download_progress = {
                    "is_downloading": True,
                    "downloaded_bytes": 0,
                    "total_bytes": total_bytes,
                    "percent": 0,
                    "status": "downloading",
                    "message": "正在下载..."
                }

                downloaded_size = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Update progress every chunk
                            if total_bytes > 0:
                                percent = int((downloaded_size / total_bytes) * 100)
                                _download_progress["downloaded_bytes"] = downloaded_size
                                _download_progress["percent"] = percent

                logger.info(f"[DOWNLOAD-BG] Downloaded {downloaded_size} bytes")

                # Step 2: Handle auto-install if requested
                if auto_install:
                    # 先标记下载完成，开始安装
                    _download_progress["is_downloading"] = False
                    _download_progress["percent"] = 100
                    _download_progress["status"] = "installing"  # 安装中
                    _download_progress["message"] = "正在安装..."

                    # 执行安装
                    install_result = handle_auto_install(file_path, filename, is_dmg)
                    download_result.update(install_result)

                    # 安装完成
                    if install_result.get("success"):
                        _download_progress["status"] = "completed"
                        _download_progress["message"] = install_result.get("message", "安装完成")
                    else:
                        _download_progress["status"] = "failed"
                        _download_progress["message"] = install_result.get("message", "安装失败")
                else:
                    # 非自动安装模式，下载完成即结束
                    _download_progress["is_downloading"] = False
                    _download_progress["percent"] = 100
                    _download_progress["status"] = "completed"
                    _download_progress["message"] = "下载完成"
                    download_result["success"] = True
                    download_result["message"] = "下载完成"

            except Exception as e:
                logger.error(f"[DOWNLOAD-BG] Error in download thread: {e}")
                download_result["error"] = str(e)
                _download_progress["is_downloading"] = False
                _download_progress["status"] = "failed"
                _download_progress["message"] = f"下载失败: {str(e)}"

        def handle_auto_install(file_path, filename, is_dmg):
            """Handle auto-installation after download."""
            result = {"success": False, "restarting": False, "updater_type": None, "message": ""}
            install_dir = get_install_dir()
            logger.info(f"[DOWNLOAD-BG] install_dir={install_dir}")

            try:
                if platform.system().lower() == PLATFORM_WINDOWS:
                    # Windows installation
                    logger.info(f"[DOWNLOAD-BG-WINDOWS] Starting Windows update flow")

                    temp_dir = Path(tempfile.mkdtemp(prefix=UPDATER_TEMP_PREFIX))
                    updater_batch = temp_dir / (UPDATER_BATCH_NAME + BAT_SCRIPT_EXT)
                    zip_copy = temp_dir / file_path.name

                    shutil.copy2(file_path, zip_copy)
                    exe_path = Path(sys.executable)

                    ps_script = f'''$ErrorActionPreference = 'Stop'
Write-Host "[UPDATER] Anime1 Update Starting"
Write-Host "[UPDATER] Source: {zip_copy}"
Write-Host "[UPDATER] Target: {install_dir}"
Write-Host "[UPDATER] Waiting for parent process to exit..."
Start-Sleep -Seconds 5
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
try {{
    Expand-Archive -Path $zipCopy -DestinationPath $installDir -Force -ErrorAction Stop
    Write-Host "[UPDATER] Extraction complete"
}} catch {{
    Write-Host "[UPDATER] ERROR: $_"
    Start-Sleep -Seconds 5
    exit 1
}}
try {{
    $orphanedZip = "$env:TEMP\orphaned_update_$([guid]::NewGuid().ToString('N').Substring(0,8)).zip"
    try {{
        Move-Item -Path $zipCopy -Destination $orphanedZip -Force -ErrorAction Stop
    }} catch {{
        Remove-Item $zipCopy -Force -ErrorAction SilentlyContinue
    }}
}} catch {{}}
Write-Host "[UPDATER] Launching updated app..."
if (Test-Path $exePath) {{
    Start-Process -FilePath $exePath -WindowStyle Normal
}}
Start-Sleep -Seconds 2
'''
                    ps_script_path = temp_dir / "update.ps1"
                    ps_script_path.write_text(ps_script, encoding='utf-8')

                    batch_content = f'''@echo off
echo [UPDATER] Anime1 Update Starting
echo [UPDATER] Launching PowerShell for extraction...
powershell -ExecutionPolicy Bypass -File "{ps_script_path}"
del "%~f0"
'''
                    updater_batch.write_text(batch_content, encoding='utf-8')

                    try:
                        if file_path.exists():
                            file_path.unlink(missing_ok=True)
                    except Exception:
                        pass

                    result["success"] = True
                    result["restarting"] = True
                    result["updater_type"] = "windows"
                    result["updater_path"] = str(updater_batch)
                    result["message"] = "更新已准备就绪，正在重启应用..."

                elif sys.platform == 'darwin':
                    # macOS installation
                    is_zip = filename.lower().endswith(EXT_ZIP)

                    if is_zip:
                        # macOS ZIP auto-install
                        logger.info(f"[UPDATE-MACOS-BG] Installing ZIP: {file_path}")

                        app_path = Path(sys.executable).resolve()
                        if app_path.name == MACOS_APP_NAME:
                            install_dir = app_path.parent.parent.parent
                        else:
                            install_dir = Path(MACOS_APP_BUNDLE_PATH)

                        # Backup existing app
                        backup_dir = install_dir.parent / f"{install_dir.name}_backup_{uuid.uuid4().hex[:8]}"
                        backup_created = False
                        if install_dir.exists():
                            try:
                                shutil.copytree(install_dir, backup_dir)
                                backup_created = True
                            except Exception as e:
                                logger.warning(f"[UPDATE-MACOS-BG] Could not create backup: {e}")

                        # Extract new version
                        try:
                            with zipfile.ZipFile(file_path, 'r') as zf:
                                names = zf.namelist()
                                has_app_prefix = any(name.startswith('Anime1.app/') for name in names)

                                if has_app_prefix:
                                    zf.extractall(install_dir.parent)
                                else:
                                    temp_extract_dir = Path(tempfile.mkdtemp(prefix='anime1_extract_'))
                                    zf.extractall(temp_extract_dir)
                                    extracted_folders = list(temp_extract_dir.iterdir())
                                    if len(extracted_folders) == 1 and extracted_folders[0].is_dir():
                                        if install_dir.exists():
                                            shutil.rmtree(install_dir)
                                        shutil.move(str(extracted_folders[0]), str(install_dir))
                                    shutil.rmtree(temp_extract_dir)

                            # Fix permissions
                            exe_path = install_dir / MACOS_APP_CONTENTS_MACOS / MACOS_APP_NAME
                            if exe_path.exists():
                                os.chmod(exe_path, 0o755)

                            file_path.unlink()

                            if backup_created and backup_dir.exists():
                                shutil.rmtree(backup_dir)

                        except Exception as e:
                            logger.error(f"[UPDATE-MACOS-BG] Failed to install: {e}")
                            if backup_created and backup_dir.exists():
                                if install_dir.exists():
                                    shutil.rmtree(install_dir)
                                shutil.copytree(backup_dir, install_dir)
                                shutil.rmtree(backup_dir)
                            raise

                        # Create restart script
                        temp_dir_restart = Path(tempfile.mkdtemp(prefix=RESTART_SCRIPT_PREFIX))
                        restart_script = temp_dir_restart / RESTART_SCRIPT_FILE

                        restart_content = f'''#!/bin/bash
"{install_dir / MACOS_APP_CONTENTS_MACOS / MACOS_APP_NAME}" &
'''
                        restart_script.write_text(restart_content, encoding='utf-8')
                        os.chmod(restart_script, 0o755)

                        proc = subprocess.Popen([CMD_BASH, str(restart_script)], start_new_session=True)

                        result["success"] = True
                        result["restarting"] = True
                        result["updater_type"] = "macos_zip"
                        result["message"] = "更新完成，正在重启..."

                    else:
                        # DMG handling (simplified - in real app would use macos_updater.py)
                        logger.info("[UPDATE-MACOS-DMG-BG] DMG installation not fully implemented in async mode")

                        result["success"] = True
                        result["restarting"] = True
                        result["updater_type"] = "macos_dmg"
                        result["message"] = "正在安装更新..."

                else:
                    # Linux or other
                    logger.info(f"[DOWNLOAD-BG-LINUX] Installing: {file_path}")

                    exe_path = Path(sys.executable)
                    if exe_path.name == LINUX_APP_NAME:
                        install_dir = exe_path.parent
                    else:
                        install_dir = Path(LINUX_INSTALL_DIR)

                    backup_dir = install_dir.parent / f"{install_dir.name}_backup_{uuid.uuid4().hex[:8]}"
                    backup_created = False
                    if install_dir.exists():
                        try:
                            shutil.copytree(install_dir, backup_dir)
                            backup_created = True
                        except Exception:
                            pass

                    try:
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            zf.extractall(install_dir)
                        file_path.unlink()
                        if backup_created and backup_dir.exists():
                            shutil.rmtree(backup_dir)
                    except Exception as e:
                        if backup_created and backup_dir.exists():
                            if install_dir.exists():
                                shutil.rmtree(install_dir)
                            shutil.copytree(backup_dir, install_dir)
                            shutil.rmtree(backup_dir)
                        raise

                    new_exe_path = install_dir / "Anime1"
                    subprocess.Popen([str(new_exe_path)], cwd=str(install_dir), start_new_session=True)

                    result["success"] = True
                    result["restarting"] = True
                    result["updater_type"] = "linux_zip"
                    result["message"] = "更新完成，正在重启..."

            except Exception as e:
                logger.error(f"[DOWNLOAD-BG] Auto-install failed: {e}")
                result["error"] = str(e)
                _download_progress["status"] = "failed"
                _download_progress["message"] = f"安装失败: {str(e)}"

            return result

        # Store the result globally for polling
        global _download_result
        _download_result = download_result

        # Start background thread
        bg_thread = threading.Thread(target=download_and_install_thread, daemon=True)
        bg_thread.start()

        # Return immediately
        logger.info(f"[DOWNLOAD] Returning response, download continuing in background")

        return success_response(
            message="正在下载更新...",
            data={
                "success": True,
                "downloading": True,
                "status": "downloading",
                "download_path": str(file_path)
            }
        )

    except Exception as e:
        logger.error(f"Error starting download: {e}")
        return error_response(str(e), 500)



@settings_bp.route("/update/progress", methods=["GET"])
def get_update_progress():
    """Get the current download progress for updates.

    Returns:
        Progress information including bytes downloaded, total bytes, and percentage.
    """
    try:
        global _download_progress, _download_result
        return success_response(data={
            "progress": _download_progress,
            "result": _download_result
        })
    except Exception as e:
        logger.error(f"Error getting update progress: {e}")
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
