"""Auto download API routes."""
import logging
import threading
from pathlib import Path
from typing import Optional

from flask import Blueprint, request

from src.constants.api import success_response, error_response
from src.services.auto_download_service import (
    get_auto_download_service,
    DownloadConfig,
    DownloadFilter,
    DownloadStatus,
)
from src.services.video_downloader import get_video_downloader

logger = logging.getLogger(__name__)

auto_download_bp = Blueprint("auto_download", __name__, url_prefix="/api/auto-download")

# Global download manager
_download_manager: Optional["DownloadManager"] = None


class DownloadManager:
    """Manages active downloads and coordinates between service and downloader."""

    def __init__(self):
        self.auto_service = get_auto_download_service()
        self.downloader: Optional[object] = None
        self._lock = threading.Lock()
        self._active_downloads: set = set()

    def get_downloader(self):
        """Get or create video downloader."""
        if self.downloader is None:
            download_path = self.auto_service.get_download_path()
            config = self.auto_service.get_config()
            self.downloader = get_video_downloader(
                download_path, config.max_concurrent_downloads
            )
            # Register progress callback
            self.downloader.register_progress_callback(self._on_progress_update)
        return self.downloader

    def _on_progress_update(self, progress):
        """Handle download progress updates."""
        # Update record in auto download service
        from src.services.auto_download_service import DownloadRecord

        if progress.status in ["completed", "failed", "cancelled"]:
            with self._lock:
                self._active_downloads.discard(progress.episode_id)

        # Find and update record
        record = DownloadRecord(
            anime_id="",  # Will be filled from existing record
            anime_title="",
            episode_id=progress.episode_id,
            episode_num="",
            status=DownloadStatus(progress.status),
            file_path=progress.file_path,
            error_message=progress.error_message,
        )
        self.auto_service.update_download_record(record)

    def start_download(self, anime: dict, episode: dict) -> dict:
        """Start a new download.

        Args:
            anime: Anime dictionary
            episode: Episode dictionary

        Returns:
            Result dictionary
        """
        episode_id = episode["id"]

        # Check if already downloading
        with self._lock:
            if episode_id in self._active_downloads:
                return {"success": False, "message": "Already downloading"}
            self._active_downloads.add(episode_id)

        # Create download record
        from src.services.auto_download_service import DownloadRecord, DownloadStatus

        record = DownloadRecord(
            anime_id=anime["id"],
            anime_title=anime["title"],
            episode_id=episode_id,
            episode_num=episode["episode"],
            status=DownloadStatus.DOWNLOADING,
        )
        self.auto_service.add_download_record(record)

        # Start download in background
        def do_download():
            downloader = self.get_downloader()
            episode_url = episode.get("url", f"https://anime1.me/{episode_id}")
            downloader.download(
                episode_id=episode_id,
                episode_url=episode_url,
                anime_title=anime["title"],
                episode_num=episode["episode"],
            )

        thread = threading.Thread(target=do_download, daemon=True)
        thread.start()

        return {"success": True, "message": "Download started"}

    def get_progress(self, episode_id: Optional[str] = None) -> dict:
        """Get download progress.

        Args:
            episode_id: Optional episode ID to get specific progress

        Returns:
            Progress information
        """
        if self.downloader is None:
            return {"downloads": []}

        if episode_id:
            progress = self.downloader.get_progress(episode_id)
            if progress:
                return {"download": progress.to_dict()}
            return {"error": "Download not found"}

        all_progress = self.downloader.get_all_progress()
        return {
            "downloads": [p.to_dict() for p in all_progress.values()],
            "active_count": len(self._active_downloads),
        }


def get_download_manager() -> DownloadManager:
    """Get or create the global download manager."""
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager()
    return _download_manager


@auto_download_bp.route("/config", methods=["GET"])
def get_config():
    """Get auto download configuration.

    Returns:
        Current configuration including filters and settings.
    """
    try:
        service = get_auto_download_service()
        config = service.get_config()

        return success_response(
            data={
                "enabled": config.enabled,
                "download_path": config.download_path,
                "check_interval_hours": config.check_interval_hours,
                "max_concurrent_downloads": config.max_concurrent_downloads,
                "auto_download_new": config.auto_download_new,
                "auto_download_favorites": config.auto_download_favorites,
                "filters": {
                    "min_year": config.filters.min_year,
                    "max_year": config.filters.max_year,
                    "specific_years": config.filters.specific_years,
                    "seasons": config.filters.seasons,
                    "min_episodes": config.filters.min_episodes,
                    "include_patterns": config.filters.include_patterns,
                    "exclude_patterns": config.filters.exclude_patterns,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting auto download config: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/config", methods=["POST"])
def update_config():
    """Update auto download configuration.

    Request body:
        enabled: bool - Enable/disable auto download
        download_path: str - Custom download path (empty for default)
        check_interval_hours: int - Check interval in hours
        max_concurrent_downloads: int - Max concurrent downloads
        auto_download_new: bool - Auto download new anime
        auto_download_favorites: bool - Auto download favorites
        filters: object - Filter configuration
            min_year: int - Minimum year
            max_year: int - Maximum year
            specific_years: list - Specific years to download
            seasons: list - Seasons to download ["冬季", "春季", "夏季", "秋季"]
            min_episodes: int - Minimum episode count
            include_patterns: list - Regex patterns to include
            exclude_patterns: list - Regex patterns to exclude

    Returns:
        Updated configuration
    """
    try:
        data = request.get_json() or {}
        service = get_auto_download_service()

        # Get current config
        config = service.get_config()

        # Update fields
        if "enabled" in data:
            config.enabled = bool(data["enabled"])
        if "download_path" in data:
            config.download_path = str(data["download_path"])
        if "check_interval_hours" in data:
            config.check_interval_hours = int(data["check_interval_hours"])
        if "max_concurrent_downloads" in data:
            config.max_concurrent_downloads = int(data["max_concurrent_downloads"])
        if "auto_download_new" in data:
            config.auto_download_new = bool(data["auto_download_new"])
        if "auto_download_favorites" in data:
            config.auto_download_favorites = bool(data["auto_download_favorites"])

        # Update filters
        if "filters" in data:
            filters_data = data["filters"]
            if "min_year" in filters_data:
                config.filters.min_year = (
                    int(filters_data["min_year"]) if filters_data["min_year"] else None
                )
            if "max_year" in filters_data:
                config.filters.max_year = (
                    int(filters_data["max_year"]) if filters_data["max_year"] else None
                )
            if "specific_years" in filters_data:
                config.filters.specific_years = [
                    int(y) for y in filters_data["specific_years"]
                ]
            if "seasons" in filters_data:
                config.filters.seasons = list(filters_data["seasons"])
            if "min_episodes" in filters_data:
                config.filters.min_episodes = (
                    int(filters_data["min_episodes"])
                    if filters_data["min_episodes"]
                    else None
                )
            if "include_patterns" in filters_data:
                config.filters.include_patterns = list(filters_data["include_patterns"])
            if "exclude_patterns" in filters_data:
                config.filters.exclude_patterns = list(filters_data["exclude_patterns"])

        # Save config
        if service.update_config(config):
            # Restart scheduler if enabled changed
            if config.enabled:
                service.stop_scheduler()
                service.start_scheduler()
            else:
                service.stop_scheduler()

            return success_response(
                message="Configuration updated",
                data=config.to_dict(),
            )
        else:
            return error_response("Failed to save configuration", 500)

    except Exception as e:
        logger.error(f"Error updating auto download config: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/status", methods=["GET"])
def get_status():
    """Get auto download service status.

    Returns:
        Service status including recent downloads and counts.
    """
    try:
        service = get_auto_download_service()
        status = service.get_status()
        return success_response(data=status)
    except Exception as e:
        logger.error(f"Error getting auto download status: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/history", methods=["GET"])
def get_history():
    """Get download history.

    Query params:
        limit: Maximum number of records (default: 100)
        status: Filter by status (pending, downloading, completed, failed, skipped)

    Returns:
        List of download records
    """
    try:
        service = get_auto_download_service()
        limit = request.args.get("limit", 100, type=int)
        status_str = request.args.get("status", None)

        status = DownloadStatus(status_str) if status_str else None
        history = service.get_history(limit=limit, status=status)

        return success_response(
            data={
                "history": [r.to_dict() for r in history],
                "total": len(history),
            }
        )
    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/download", methods=["POST"])
def start_download():
    """Start a manual download.

    Request body:
        anime_id: str - Anime ID
        episode_id: str - Episode ID
        episode_num: str - Episode number
        title: str - Anime title
        url: str - Episode URL (optional)

    Returns:
        Download start result
    """
    try:
        data = request.get_json() or {}

        anime_id = data.get("anime_id")
        episode_id = data.get("episode_id")
        episode_num = data.get("episode_num")
        title = data.get("title")
        url = data.get("url", f"https://anime1.me/{episode_id}")

        if not all([anime_id, episode_id, title]):
            return error_response("Missing required fields: anime_id, episode_id, title", 400)

        anime = {
            "id": anime_id,
            "title": title,
        }
        episode = {
            "id": episode_id,
            "episode": episode_num or "",
            "url": url,
        }

        manager = get_download_manager()
        result = manager.start_download(anime, episode)

        if result["success"]:
            return success_response(message=result["message"], data=result)
        else:
            return error_response(result["message"], 400)

    except Exception as e:
        logger.error(f"Error starting download: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/progress", methods=["GET"])
def get_progress():
    """Get download progress.

    Query params:
        episode_id: Specific episode ID (optional, returns all if not specified)

    Returns:
        Download progress information
    """
    try:
        episode_id = request.args.get("episode_id")
        manager = get_download_manager()
        progress = manager.get_progress(episode_id)
        return success_response(data=progress)
    except Exception as e:
        logger.error(f"Error getting download progress: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/filter/preview", methods=["POST"])
def preview_filter():
    """Preview which anime would match the given filter.

    Request body:
        filters: Filter configuration object

    Returns:
        List of anime that would match the filter
    """
    try:
        data = request.get_json() or {}
        filters_data = data.get("filters", {})

        # Create temporary filter
        temp_filter = DownloadFilter()
        if "min_year" in filters_data:
            temp_filter.min_year = (
                int(filters_data["min_year"]) if filters_data["min_year"] else None
            )
        if "max_year" in filters_data:
            temp_filter.max_year = (
                int(filters_data["max_year"]) if filters_data["max_year"] else None
            )
        if "specific_years" in filters_data:
            temp_filter.specific_years = [int(y) for y in filters_data["specific_years"]]
        if "seasons" in filters_data:
            temp_filter.seasons = list(filters_data["seasons"])
        if "min_episodes" in filters_data:
            temp_filter.min_episodes = (
                int(filters_data["min_episodes"]) if filters_data["min_episodes"] else None
            )
        if "include_patterns" in filters_data:
            temp_filter.include_patterns = list(filters_data["include_patterns"])
        if "exclude_patterns" in filters_data:
            temp_filter.exclude_patterns = list(filters_data["exclude_patterns"])

        # Get all anime and filter
        from src.services.anime_cache_service import get_anime_list_cache

        all_anime = get_anime_list_cache()
        all_anime_dicts = [a.to_dict() for a in all_anime]

        service = get_auto_download_service()
        filtered = service.filter_anime(all_anime_dicts)

        # Also apply temporary filter
        final_filtered = [a for a in filtered if temp_filter.matches(a)]

        return success_response(
            data={
                "total_anime": len(all_anime_dicts),
                "matched_count": len(final_filtered),
                "matched_anime": final_filtered[:50],  # Limit to 50 for preview
            }
        )

    except Exception as e:
        logger.error(f"Error previewing filter: {e}")
        return error_response(str(e), 500)


@auto_download_bp.route("/test", methods=["POST"])
def test_download():
    """Test download a single episode.

    Request body:
        episode_url: URL of the episode to test

    Returns:
        Test result with video info
    """
    try:
        data = request.get_json() or {}
        episode_url = data.get("episode_url")

        if not episode_url:
            return error_response("episode_url is required", 400)

        # Create temporary downloader to test
        service = get_auto_download_service()
        download_path = service.get_download_path()

        from src.services.video_downloader import VideoDownloader

        downloader = VideoDownloader(download_path, max_concurrent=1)

        try:
            # Get video info
            video_info = downloader._get_video_info(episode_url)
            if not video_info:
                return error_response("Could not extract video information", 400)

            # Get video URL
            video_url = downloader._get_video_url(video_info.get("vid", ""))

            return success_response(
                data={
                    "success": True,
                    "video_info": video_info,
                    "video_url_found": video_url is not None,
                    "message": "Video info extracted successfully",
                }
            )
        finally:
            downloader.close()

    except Exception as e:
        logger.error(f"Error testing download: {e}")
        return error_response(str(e), 500)
