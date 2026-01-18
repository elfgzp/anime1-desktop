"""Settings API routes."""
import logging
import os
import platform
import subprocess
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
from src.utils.app_dir import get_app_data_dir

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

        if platform.system() == "Windows":
            # Use subprocess to avoid encoding issues with os.startfile
            subprocess.run(
                ["explorer.exe", log_dir_str],
                check=True,
                shell=True,
                capture_output=True
            )
        elif platform.system() == "Darwin":  # macOS
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
            if platform.system() == "Windows":
                os.startfile(str(log_dir))
            else:
                os.system(f'xdg-open "{log_dir}"' if platform.system() != "Darwin" else f'open "{log_dir}"')
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
    try:
        import requests
        import uuid
        import zipfile
        import shutil
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        from src.utils.app_dir import get_download_dir, get_install_dir

        data = request.get_json() or {}
        url = data.get("url")
        auto_install = data.get("auto_install", False)

        if not url:
            return error_response("url is required", 400)

        # Get filename from URL
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = f"anime1_update_{uuid.uuid4().hex[:8]}.zip"

        # Get download directory
        download_dir = get_download_dir()
        download_dir.mkdir(parents=True, exist_ok=True)
        file_path = download_dir / filename

        # Download the file
        logger.info(f"Downloading update from {url} to {file_path}")

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        downloaded_size = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

        logger.info(f"Downloaded {downloaded_size} bytes to {file_path}")

        if auto_install:
            # Auto-install mode
            logger.info(f"Auto-installing update from {file_path}")

            install_dir = get_install_dir()
            logger.info(f"Installation directory: {install_dir}")

            if sys.platform == 'win32':
                # Windows: Create a batch file that handles the update after app exits
                # This is necessary because Windows doesn't allow replacing running files

                # Create a temp directory for the updater
                temp_dir = Path(tempfile.mkdtemp(prefix='anime1_update_'))
                updater_batch = temp_dir / 'update.bat'
                zip_copy = temp_dir / file_path.name

                # Copy the zip to temp location
                shutil.copy2(file_path, zip_copy)

                # Get the executable path
                exe_path = Path(sys.executable)

                # Create batch file content
                batch_content = f'''@echo off
timeout /t 3 /nobreak >nul
echo 正在安装更新...
"{sys.executable}" -c "import zipfile; import shutil; import sys; zf=zipfile.ZipFile(r'{zip_copy}'); zf.extractall(r'{install_dir}'); import os; os.remove(r'{zip_copy}'); os.rmdir(r'{temp_dir}')"
if exist r"{exe_path}" start "" "{exe_path}"
del "%~f0"
'''
                updater_batch.write_text(batch_content, encoding='utf-8')

                logger.info(f"Created updater batch at {updater_batch}")

                # Clean up the original download
                file_path.unlink()

                # Return info that app needs to restart
                return success_response(
                    message="更新已准备就绪，正在重启应用...",
                    data={
                        "success": True,
                        "restarting": True,
                        "updater_path": str(updater_batch)
                    }
                )
            else:
                # Non-Windows: Direct update and restart
                # Create backup of current installation
                backup_dir = install_dir.parent / f"{install_dir.name}_backup_{uuid.uuid4().hex[:8]}"
                logger.info(f"Creating backup at {backup_dir}")
                try:
                    shutil.copytree(install_dir, backup_dir)
                    backup_created = True
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")
                    backup_created = False

                # Extract new version
                try:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.extractall(install_dir)
                    logger.info(f"Extracted update to {install_dir}")
                except Exception as e:
                    logger.error(f"Failed to extract update: {e}")
                    # Restore from backup if extraction failed
                    if backup_created and backup_dir.exists():
                        logger.info("Restoring from backup...")
                        shutil.rmtree(install_dir)
                        shutil.copytree(backup_dir, install_dir)
                        shutil.rmtree(backup_dir)
                    return error_response(f"安装失败: {str(e)}", 500)

                # Clean up backup if extraction succeeded
                if backup_created and backup_dir.exists():
                    shutil.rmtree(backup_dir)

                # Clean up downloaded file
                file_path.unlink()

                # Restart the application
                exe_path = Path(sys.executable)
                logger.info(f"Restarting application: {exe_path}")
                subprocess.Popen([str(exe_path)], cwd=str(install_dir))

                return success_response(
                    message="更新完成，正在重启...",
                    data={
                        "success": True,
                        "restarting": True
                    }
                )
        else:
            # Manual mode: just download and let user handle it
            return success_response(
                message="下载完成",
                data={
                    "file_path": str(file_path),
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
    try:
        import os
        import subprocess
        import sys

        data = request.get_json() or {}
        updater_path = data.get("updater_path")

        if not updater_path:
            return error_response("updater_path is required", 400)

        updater = Path(updater_path)
        if not updater.exists():
            return error_response(f"Updater not found: {updater_path}", 404)

        logger.info(f"Running updater: {updater}")

        # Run the updater and exit
        if sys.platform == 'win32':
            subprocess.Popen(['cmd', '/c', str(updater)], detached=True, creationflags=subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen([str(updater)], detached=True)

        # Exit the application
        logger.info("Exiting application for update...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error running updater: {e}")
        return error_response(str(e), 500)


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

        if platform.system() == "Windows":
            # Use subprocess to avoid encoding issues
            subprocess.run(
                ["explorer.exe", "/select,", path_str],
                check=True,
                shell=True,
                capture_output=True
            )
        elif platform.system() == "Darwin":  # macOS
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
            if platform.system() == "Windows":
                os.startfile(str(path))
            else:
                os.system(f'xdg-open "{path}"' if platform.system() != "Darwin" else f'open "{path}"')
            return success_response(message=f"已打开: {path_str}")
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            return error_response(f"无法打开路径: {str(fallback_error)}", 500)
    except Exception as e:
        logger.error(f"Error opening path: {e}")
        return error_response(str(e), 500)
