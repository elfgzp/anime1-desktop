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
        type: Type of cache to clear ("covers", "favorites", or "all")

    Returns:
        Number of entries cleared.
    """
    try:
        data = request.get_json() or {}
        cache_type = data.get("type", "covers")

        cover_service = get_cover_cache_service()
        favorite_service = get_favorite_service()

        cleared_count = 0

        if cache_type in ("covers", "all"):
            cleared_count += cover_service.clear_all()

        if cache_type in ("favorites", "all"):
            # Get all favorites and delete them
            favorites = favorite_service.get_favorites()
            for fav in favorites:
                favorite_service.remove_favorite(fav.id)
            cleared_count += len(favorites)

        return success_response(
            message=f"已清理 {cleared_count} 条缓存",
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
