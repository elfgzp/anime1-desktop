"""Auto download service for scheduled anime downloads.

This service provides:
1. Configuration management for auto download settings
2. Filtering anime by year, season, and other criteria
3. Background download scheduling
4. Download progress tracking
"""
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from src.utils.app_dir import ensure_app_data_dir

logger = logging.getLogger(__name__)

CONFIG_FILE_NAME = "auto_download_config.json"
DOWNLOAD_HISTORY_FILE_NAME = "auto_download_history.json"


class DownloadStatus(Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DownloadFilter:
    """Filter configuration for auto download."""
    # Year filter
    min_year: Optional[int] = None  # 最小年份，如 2024
    max_year: Optional[int] = None  # 最大年份，如 2025
    specific_years: List[int] = field(default_factory=list)  # 特定年份列表

    # Season filter
    seasons: List[str] = field(default_factory=list)  # ["冬季", "春季", "夏季", "秋季"]

    # Episode filter
    min_episodes: Optional[int] = None  # 最少集数

    # Title filter (regex patterns)
    include_patterns: List[str] = field(default_factory=list)  # 包含这些关键词
    exclude_patterns: List[str] = field(default_factory=list)  # 排除这些关键词

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadFilter":
        return cls(**data)

    def matches(self, anime: Dict[str, Any]) -> bool:
        """Check if an anime matches this filter.

        Args:
            anime: Anime dictionary with keys like year, season, episode, title

        Returns:
            True if the anime matches all filter criteria
        """
        # Year check
        year_str = anime.get("year", "")
        if year_str:
            try:
                year = int(year_str)
                if self.min_year is not None and year < self.min_year:
                    return False
                if self.max_year is not None and year > self.max_year:
                    return False
                if self.specific_years and year not in self.specific_years:
                    return False
            except ValueError:
                pass

        # Season check
        if self.seasons:
            anime_season = anime.get("season", "")
            if anime_season and anime_season not in self.seasons:
                return False

        # Episode count check
        if self.min_episodes is not None:
            episode = anime.get("episode", 0)
            if isinstance(episode, (int, float)) and episode < self.min_episodes:
                return False

        # Title pattern check
        title = anime.get("title", "")
        if self.include_patterns:
            import re
            matched = False
            for pattern in self.include_patterns:
                try:
                    if re.search(pattern, title, re.IGNORECASE):
                        matched = True
                        break
                except re.error:
                    continue
            if not matched:
                return False

        if self.exclude_patterns:
            import re
            for pattern in self.exclude_patterns:
                try:
                    if re.search(pattern, title, re.IGNORECASE):
                        return False
                except re.error:
                    continue

        return True


@dataclass
class DownloadConfig:
    """Auto download configuration."""
    enabled: bool = False  # 是否启用自动下载
    download_path: str = ""  # 下载路径，空字符串使用默认下载目录
    check_interval_hours: int = 24  # 检查间隔（小时）
    max_concurrent_downloads: int = 2  # 最大并发下载数
    filters: DownloadFilter = field(default_factory=DownloadFilter)  # 筛选条件
    auto_download_new: bool = True  # 自动下载新番
    auto_download_favorites: bool = False  # 自动下载追番列表中的番剧

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "download_path": self.download_path,
            "check_interval_hours": self.check_interval_hours,
            "max_concurrent_downloads": self.max_concurrent_downloads,
            "filters": self.filters.to_dict(),
            "auto_download_new": self.auto_download_new,
            "auto_download_favorites": self.auto_download_favorites,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadConfig":
        filters_data = data.pop("filters", {})
        filters = DownloadFilter.from_dict(filters_data) if filters_data else DownloadFilter()
        return cls(filters=filters, **data)


@dataclass
class DownloadRecord:
    """Record of a single download."""
    anime_id: str
    anime_title: str
    episode_id: str
    episode_num: str
    status: DownloadStatus
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anime_id": self.anime_id,
            "anime_title": self.anime_title,
            "episode_id": self.episode_id,
            "episode_num": self.episode_num,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "file_path": self.file_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadRecord":
        data = data.copy()
        data["status"] = DownloadStatus(data.get("status", "pending"))
        return cls(**data)


class AutoDownloadService:
    """Service for managing auto downloads."""

    def __init__(self, config_path: Optional[Path] = None, history_path: Optional[Path] = None):
        """Initialize the auto download service.

        Args:
            config_path: Optional path to config file
            history_path: Optional path to history file
        """
        if config_path is None:
            app_dir = ensure_app_data_dir()
            config_path = app_dir / CONFIG_FILE_NAME

        if history_path is None:
            app_dir = ensure_app_data_dir()
            history_path = app_dir / DOWNLOAD_HISTORY_FILE_NAME

        self.config_path = config_path
        self.history_path = history_path
        self._config: Optional[DownloadConfig] = None
        self._history: List[DownloadRecord] = []
        self._lock = threading.Lock()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._download_callbacks: List[Callable] = []

        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Ensure config and history files exist."""
        if not self.config_path.exists():
            self._save_config(DownloadConfig())
        if not self.history_path.exists():
            self._save_history([])

    def _load_config(self) -> DownloadConfig:
        """Load config from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return DownloadConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading auto download config: {e}")
        return DownloadConfig()

    def _save_config(self, config: DownloadConfig):
        """Save config to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving auto download config: {e}")
            raise

    def _load_history(self) -> List[DownloadRecord]:
        """Load download history from file."""
        try:
            if self.history_path.exists():
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [DownloadRecord.from_dict(r) for r in data]
        except Exception as e:
            logger.error(f"Error loading download history: {e}")
        return []

    def _save_history(self, history: List[DownloadRecord]):
        """Save download history to file."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in history], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving download history: {e}")
            raise

    def get_config(self) -> DownloadConfig:
        """Get current configuration."""
        with self._lock:
            if self._config is None:
                self._config = self._load_config()
            return self._config

    def update_config(self, config: DownloadConfig) -> bool:
        """Update configuration.

        Args:
            config: New configuration

        Returns:
            True if successful
        """
        with self._lock:
            try:
                self._save_config(config)
                self._config = config
                logger.info("Auto download config updated")
                return True
            except Exception as e:
                logger.error(f"Failed to update config: {e}")
                return False

    def get_download_path(self) -> Path:
        """Get the download path from config or default."""
        config = self.get_config()
        if config.download_path:
            path = Path(config.download_path)
            path.mkdir(parents=True, exist_ok=True)
            return path
        else:
            from src.utils.app_dir import get_download_dir
            return get_download_dir()

    def get_history(self, limit: int = 100, status: Optional[DownloadStatus] = None) -> List[DownloadRecord]:
        """Get download history.

        Args:
            limit: Maximum number of records to return
            status: Filter by status

        Returns:
            List of download records
        """
        with self._lock:
            history = self._load_history()
            if status:
                history = [r for r in history if r.status == status]
            return sorted(history, key=lambda r: r.created_at, reverse=True)[:limit]

    def add_download_record(self, record: DownloadRecord):
        """Add a new download record."""
        with self._lock:
            history = self._load_history()
            history.append(record)
            self._save_history(history)
            self._history = history

    def update_download_record(self, record: DownloadRecord):
        """Update an existing download record."""
        with self._lock:
            history = self._load_history()
            for i, r in enumerate(history):
                if r.episode_id == record.episode_id:
                    history[i] = record
                    break
            self._save_history(history)
            self._history = history

    def is_episode_downloaded(self, episode_id: str) -> bool:
        """Check if an episode has been downloaded."""
        with self._lock:
            history = self._load_history()
            for record in history:
                if record.episode_id == episode_id and record.status in [
                    DownloadStatus.COMPLETED, DownloadStatus.DOWNLOADING
                ]:
                    return True
            return False

    def filter_anime(self, anime_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter anime list based on current configuration.

        Args:
            anime_list: List of anime dictionaries

        Returns:
            Filtered list of anime
        """
        config = self.get_config()
        filters = config.filters

        filtered = []
        for anime in anime_list:
            if filters.matches(anime):
                filtered.append(anime)

        return filtered

    def start_scheduler(self):
        """Start the background download scheduler."""
        if self._running:
            logger.warning("Auto download scheduler already running")
            return

        config = self.get_config()
        if not config.enabled:
            logger.info("Auto download is disabled, not starting scheduler")
            return

        self._running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("Auto download scheduler started")

    def stop_scheduler(self):
        """Stop the background download scheduler."""
        if not self._running:
            return

        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=10)
        self._running = False
        logger.info("Auto download scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                config = self.get_config()
                if not config.enabled:
                    logger.info("Auto download disabled, scheduler sleeping...")
                    self._stop_event.wait(3600)  # Check again in 1 hour
                    continue

                logger.info("Running auto download check...")
                self._check_and_download()

                # Wait for next check interval
                wait_seconds = config.check_interval_hours * 3600
                logger.info(f"Next check in {config.check_interval_hours} hours")
                self._stop_event.wait(wait_seconds)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self._stop_event.wait(300)  # Wait 5 minutes on error

    def _check_and_download(self):
        """Check for new episodes and download them."""
        from src.services.anime_cache_service import get_anime_list_cache
        from src.services.favorite_service import get_favorite_service

        config = self.get_config()

        # Get anime to check
        anime_to_check = []

        if config.auto_download_new:
            # Get all anime and filter
            all_anime = get_anime_list_cache()
            all_anime_dicts = [a.to_dict() for a in all_anime]
            filtered = self.filter_anime(all_anime_dicts)
            anime_to_check.extend(filtered)

        if config.auto_download_favorites:
            # Get favorites
            favorite_service = get_favorite_service()
            favorites = favorite_service.get_favorites()
            for fav in favorites:
                anime_dict = {
                    "id": fav.anime_id,
                    "title": fav.title,
                    "year": fav.year,
                    "season": fav.season,
                    "episode": fav.episode,
                }
                if config.filters.matches(anime_dict):
                    anime_to_check.append(anime_dict)

        # Remove duplicates
        seen_ids = set()
        unique_anime = []
        for anime in anime_to_check:
            if anime["id"] not in seen_ids:
                seen_ids.add(anime["id"])
                unique_anime.append(anime)

        logger.info(f"Found {len(unique_anime)} anime to check for downloads")

        # Check each anime for new episodes
        for anime in unique_anime:
            if self._stop_event.is_set():
                break
            self._check_anime_episodes(anime)

    def _check_anime_episodes(self, anime: Dict[str, Any]):
        """Check and download episodes for a specific anime."""
        from src.parser.anime1_parser import Anime1Parser

        parser = Anime1Parser()
        try:
            detail_url = anime.get("detail_url", f"https://anime1.me/?cat={anime['id']}")
            episodes = parser.parse_episode_list(detail_url)

            for episode in episodes:
                if self._stop_event.is_set():
                    break

                episode_id = episode["id"]
                if self.is_episode_downloaded(episode_id):
                    continue

                # Trigger download
                self._download_episode(anime, episode)

        except Exception as e:
            logger.error(f"Error checking episodes for {anime.get('title')}: {e}")
        finally:
            parser.close()

    def _download_episode(self, anime: Dict[str, Any], episode: Dict[str, Any]):
        """Download a single episode.

        This is a placeholder that calls registered callbacks.
        Actual download implementation would be in a separate module.
        """
        record = DownloadRecord(
            anime_id=anime["id"],
            anime_title=anime["title"],
            episode_id=episode["id"],
            episode_num=episode["episode"],
            status=DownloadStatus.PENDING,
        )
        self.add_download_record(record)

        # Notify callbacks
        for callback in self._download_callbacks:
            try:
                callback(anime, episode, record)
            except Exception as e:
                logger.error(f"Error in download callback: {e}")

    def register_download_callback(self, callback: Callable):
        """Register a callback for download events.

        Args:
            callback: Function called with (anime, episode, record) arguments
        """
        self._download_callbacks.append(callback)

    def unregister_download_callback(self, callback: Callable):
        """Unregister a download callback."""
        if callback in self._download_callbacks:
            self._download_callbacks.remove(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        config = self.get_config()
        history = self.get_history(limit=10)

        # Count by status
        all_history = self.get_history(limit=10000)
        status_counts = {
            "pending": 0,
            "downloading": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }
        for record in all_history:
            status_counts[record.status.value] += 1

        return {
            "enabled": config.enabled,
            "running": self._running,
            "download_path": str(self.get_download_path()),
            "check_interval_hours": config.check_interval_hours,
            "filters": config.filters.to_dict(),
            "recent_downloads": [r.to_dict() for r in history],
            "status_counts": status_counts,
        }


# Global service instance
_auto_download_service: Optional[AutoDownloadService] = None


def get_auto_download_service() -> AutoDownloadService:
    """Get or create the global auto download service instance."""
    global _auto_download_service
    if _auto_download_service is None:
        _auto_download_service = AutoDownloadService()
    return _auto_download_service
