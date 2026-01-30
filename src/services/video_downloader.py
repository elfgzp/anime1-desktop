"""Video downloader for anime episodes.

This module provides functionality to download video files from anime1.me.
It supports:
- Async download with progress tracking
- Multiple download strategies
- Resume partial downloads
- Concurrent download limiting
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from urllib.parse import urlencode, parse_qs, urlparse, unquote

import requests
from bs4 import BeautifulSoup

from src.config import HEADERS, DEFAULT_TIMEOUT
from src.utils.http import HttpClient

logger = logging.getLogger(__name__)


@dataclass
class DownloadProgress:
    """Download progress information."""
    episode_id: str
    total_bytes: int = 0
    downloaded_bytes: int = 0
    speed_bytes_per_sec: float = 0.0
    status: str = "pending"  # pending, downloading, completed, failed, cancelled
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    file_path: Optional[str] = None

    @property
    def percent(self) -> float:
        """Get download percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
            "speed_bytes_per_sec": self.speed_bytes_per_sec,
            "status": self.status,
            "error_message": self.error_message,
            "percent": round(self.percent, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "file_path": self.file_path,
        }


class VideoDownloader:
    """Video downloader with progress tracking."""

    def __init__(self, download_dir: Path, max_concurrent: int = 2):
        """Initialize the video downloader.

        Args:
            download_dir: Directory to save downloaded files
            max_concurrent: Maximum number of concurrent downloads
        """
        self.download_dir = download_dir
        self.max_concurrent = max_concurrent
        self._http = HttpClient()
        self._progress: Dict[str, DownloadProgress] = {}
        self._progress_callbacks: List[Callable[[DownloadProgress], None]] = []
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_concurrent)

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _get_video_info(self, episode_url: str) -> Optional[Dict[str, Any]]:
        """Get video information from episode page.

        Args:
            episode_url: URL of the episode page

        Returns:
            Dictionary with video info or None
        """
        try:
            # Fetch episode page
            html = self._http.get(episode_url)
            soup = BeautifulSoup(html, "html.parser")

            # Find video tag
            video = soup.find("video")
            if not video:
                logger.error(f"No video tag found in {episode_url}")
                return None

            # Extract data attributes
            api_req_raw = video.get("data-apireq", "")
            vid = video.get("data-vid", "")

            # Parse api_req JSON - contains all API parameters: c, e, t, p, s
            # Note: data-apireq is URL-encoded, need to decode first
            if api_req_raw:
                try:
                    api_req = unquote(api_req_raw)
                    api_data = json.loads(api_req)
                    return {
                        "vid": api_data.get("v", vid),
                        "category_id": api_data.get("c", ""),
                        "episode_num": api_data.get("e", ""),
                        # API signature parameters (required for v.anime1.me/api)
                        "t": api_data.get("t", ""),
                        "p": api_data.get("p", ""),
                        "s": api_data.get("s", ""),
                    }
                except json.JSONDecodeError:
                    pass

            # Fallback: try to extract from vid attribute
            if vid:
                return {"vid": vid, "category_id": "", "episode_num": "", "t": "", "p": "", "s": ""}

            return None

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None

    def _get_video_url(self, video_info: Dict[str, Any]) -> Optional[tuple[str, dict]]:
        """Get the actual video URL and cookies from the anime1.me API.

        Args:
            video_info: Video info dict with category_id, episode_num, t, p, s

        Returns:
            Tuple of (video_url, cookies) or None
        """
        try:
            # Use anime1.me video API: https://v.anime1.me/api
            # Requires parameters from data-apireq: c, e, t, p, s
            api_url = "https://v.anime1.me/api"

            # Build API request data from video_info
            api_data = {
                "c": video_info.get("category_id", ""),
                "e": video_info.get("episode_num", ""),
                "t": video_info.get("t", ""),
                "p": video_info.get("p", ""),
                "s": video_info.get("s", ""),
            }

            # If we don't have the signature params (t, p, s), we can't call the API
            # Note: p can be 0, so we need to check for None explicitly
            if not api_data["t"] or api_data["p"] is None or api_data["p"] == "" or not api_data["s"]:
                logger.error(f"Missing required API parameters (t, p, s) from data-apireq: t={api_data.get('t')}, p={api_data.get('p')}, s={api_data.get('s')}")
                return None

            # Encode data as JSON wrapped in 'd' parameter
            payload = {"d": json.dumps(api_data)}
            encoded_data = urlencode(payload)

            headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://anime1.me/",
                "Origin": "https://anime1.me/",
                "Accept": "application/json",
            }

            response = requests.post(
                api_url,
                data=encoded_data,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()

            # Parse cookies from response headers (needed for video download)
            cookies = self._parse_cookies(response.headers)

            data = response.json()

            # New format: {"s": [{"src": "//host/path/file.mp4", "type": "video/mp4"}]}
            video_sources = data.get("s", [])
            if video_sources and len(video_sources) > 0:
                src = video_sources[0].get("src", "")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    return (src, cookies)

            # Old format fallback
            if data.get("success") and "file" in data:
                return (data["file"], cookies)
            if data.get("success") and "stream" in data:
                return (data["stream"], cookies)

            if "error" in data:
                logger.error(f"API error: {data['error']}")
                return None

            return None

        except Exception as e:
            logger.error(f"Error getting video URL: {e}")
            return None

    def _parse_cookies(self, headers: dict) -> dict:
        """Parse cookies from Set-Cookie header.

        Args:
            headers: Response headers dict

        Returns:
            Dictionary of cookie name -> value
        """
        cookies = {}
        set_cookie = headers.get("set-cookie", "")
        if set_cookie:
            # Handle comma-separated Set-Cookie headers (multiple cookies in one header)
            for cookie_part in set_cookie.replace("\n", ",").split(","):
                cookie_part = cookie_part.strip()
                # Each cookie is like: "name=value; expires=...; path=..."
                if "=" in cookie_part:
                    # Find the first "=" to get the cookie name
                    first_eq_idx = cookie_part.index("=")
                    name = cookie_part[:first_eq_idx].strip()
                    value = cookie_part[first_eq_idx + 1:].strip()
                    # Extract just the value (before the first semicolon if present)
                    if ";" in value:
                        value = value[:value.index(";")].strip()
                    if name and value:
                        cookies[name] = value

        # Also check for multiple Set-Cookie headers (requests puts them in a list)
        for header_name, header_value in headers.items():
            if header_name.lower() == "set-cookie":
                for cookie_part in header_value.replace("\n", ",").split(","):
                    cookie_part = cookie_part.strip()
                    if "=" in cookie_part:
                        first_eq_idx = cookie_part.index("=")
                        name = cookie_part[:first_eq_idx].strip()
                        value = cookie_part[first_eq_idx + 1:].strip()
                        if ";" in value:
                            value = value[:value.index(";")].strip()
                        if name and value and name not in cookies:
                            cookies[name] = value

        return cookies

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200 - len(ext)] + ext

        return filename.strip()

    def _get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """Get file extension from URL or content type.

        Args:
            url: Video URL
            content_type: HTTP Content-Type header

        Returns:
            File extension (including dot)
        """
        # Try to get from URL
        parsed = urlparse(url)
        path = parsed.path
        if path:
            ext = os.path.splitext(path)[1]
            if ext:
                return ext

        # Try to get from content type
        if content_type:
            if "mp4" in content_type:
                return ".mp4"
            elif "webm" in content_type:
                return ".webm"
            elif "mpeg" in content_type or "mpg" in content_type:
                return ".mpg"
            elif "x-matroska" in content_type:
                return ".mkv"

        # Default
        return ".mp4"

    def download(
        self,
        episode_id: str,
        episode_url: str,
        anime_title: str,
        episode_num: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> DownloadProgress:
        """Download a video episode.

        Args:
            episode_id: Unique episode ID
            episode_url: URL of the episode page
            anime_title: Title of the anime
            episode_num: Episode number
            progress_callback: Optional callback for progress updates

        Returns:
            DownloadProgress object
        """
        # Acquire semaphore for concurrent limit
        acquired = self._semaphore.acquire(timeout=30)
        if not acquired:
            progress = DownloadProgress(
                episode_id=episode_id,
                status="failed",
                error_message="Could not acquire download slot (too many concurrent downloads)",
            )
            return progress

        try:
            return self._do_download(
                episode_id, episode_url, anime_title, episode_num, progress_callback
            )
        finally:
            self._semaphore.release()

    def _do_download(
        self,
        episode_id: str,
        episode_url: str,
        anime_title: str,
        episode_num: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> DownloadProgress:
        """Internal download implementation."""
        progress = DownloadProgress(
            episode_id=episode_id,
            start_time=time.time(),
            status="downloading",
        )

        with self._lock:
            self._progress[episode_id] = progress

        def update_progress():
            """Update progress and call callbacks."""
            with self._lock:
                self._progress[episode_id] = progress
            if progress_callback:
                try:
                    progress_callback(progress)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
            for callback in self._progress_callbacks:
                try:
                    callback(progress)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

        try:
            # Step 1: Get video info
            logger.info(f"Getting video info for {anime_title} episode {episode_num}")
            video_info = self._get_video_info(episode_url)
            if not video_info or not video_info.get("vid"):
                progress.status = "failed"
                progress.error_message = "Could not extract video information"
                progress.end_time = time.time()
                update_progress()
                return progress

            # Step 2: Get video URL and cookies
            logger.info(f"Getting video URL for vid={video_info['vid']}")
            video_url_result = self._get_video_url(video_info)
            if not video_url_result:
                progress.status = "failed"
                progress.error_message = "Could not get video URL from API"
                progress.end_time = time.time()
                update_progress()
                return progress

            video_url, video_cookies = video_url_result

            # Step 3: Prepare download
            # Create anime subdirectory
            safe_title = self._sanitize_filename(anime_title)
            anime_dir = self.download_dir / safe_title
            anime_dir.mkdir(parents=True, exist_ok=True)

            # Determine filename
            ext = self._get_file_extension(video_url)
            filename = f"{safe_title}_EP{episode_num}{ext}"
            file_path = anime_dir / filename

            # Check if file already exists
            if file_path.exists():
                logger.info(f"File already exists: {file_path}")
                progress.status = "completed"
                progress.file_path = str(file_path)
                progress.total_bytes = file_path.stat().st_size
                progress.downloaded_bytes = progress.total_bytes
                progress.end_time = time.time()
                update_progress()
                return progress

            # Step 4: Download file
            logger.info(f"Downloading to {file_path}")
            headers = {
                **HEADERS,
                "Referer": "https://anime1.me/",
            }

            response = requests.get(
                video_url, headers=headers, cookies=video_cookies if video_cookies else None, stream=True, timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()

            # Get total size
            progress.total_bytes = int(response.headers.get("Content-Length", 0))
            update_progress()

            # Download with progress tracking
            downloaded = 0
            last_update_time = time.time()
            last_downloaded = 0

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress.downloaded_bytes = downloaded

                        # Update speed every second
                        current_time = time.time()
                        if current_time - last_update_time >= 1.0:
                            elapsed = current_time - last_update_time
                            bytes_diff = downloaded - last_downloaded
                            progress.speed_bytes_per_sec = bytes_diff / elapsed if elapsed > 0 else 0

                            last_update_time = current_time
                            last_downloaded = downloaded
                            update_progress()

            # Complete
            progress.status = "completed"
            progress.file_path = str(file_path)
            progress.downloaded_bytes = downloaded
            progress.end_time = time.time()
            update_progress()

            logger.info(f"Download completed: {file_path}")
            return progress

        except requests.RequestException as e:
            logger.error(f"Network error downloading {episode_id}: {e}")
            progress.status = "failed"
            progress.error_message = f"Network error: {str(e)}"
            progress.end_time = time.time()
            update_progress()
            return progress

        except Exception as e:
            logger.error(f"Error downloading {episode_id}: {e}")
            progress.status = "failed"
            progress.error_message = str(e)
            progress.end_time = time.time()
            update_progress()
            return progress

    def get_progress(self, episode_id: str) -> Optional[DownloadProgress]:
        """Get download progress for an episode.

        Args:
            episode_id: Episode ID

        Returns:
            DownloadProgress or None
        """
        with self._lock:
            return self._progress.get(episode_id)

    def get_all_progress(self) -> Dict[str, DownloadProgress]:
        """Get all download progress.

        Returns:
            Dictionary of episode_id -> DownloadProgress
        """
        with self._lock:
            return dict(self._progress)

    def cancel_download(self, episode_id: str) -> bool:
        """Cancel a download.

        Args:
            episode_id: Episode ID to cancel

        Returns:
            True if cancelled
        """
        with self._lock:
            progress = self._progress.get(episode_id)
            if progress and progress.status == "downloading":
                progress.status = "cancelled"
                progress.end_time = time.time()
                return True
        return False

    def register_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """Register a callback for all download progress updates."""
        self._progress_callbacks.append(callback)

    def unregister_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """Unregister a progress callback."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    def close(self):
        """Close the downloader and cleanup."""
        self._http.close()


# Global downloader instance
_downloader: Optional[VideoDownloader] = None
_downloader_lock = threading.Lock()


def get_video_downloader(download_dir: Optional[Path] = None, max_concurrent: int = 2) -> VideoDownloader:
    """Get or create the global video downloader instance.

    Args:
        download_dir: Download directory (uses default if None)
        max_concurrent: Maximum concurrent downloads

    Returns:
        VideoDownloader instance
    """
    global _downloader
    with _downloader_lock:
        if _downloader is None:
            if download_dir is None:
                from src.utils.app_dir import get_download_dir
                download_dir = get_download_dir()
            _downloader = VideoDownloader(download_dir, max_concurrent)
        return _downloader


def reset_video_downloader():
    """Reset the global downloader instance."""
    global _downloader
    with _downloader_lock:
        if _downloader:
            _downloader.close()
        _downloader = None
