"""Anime data cache service for background preloading.

This service preloads anime data on startup and periodically refreshes
the cache to speed up application loading while ensuring data freshness.

The service performs the following in background:
1. Fetch anime list from anime1.me
2. For each anime, fetch its detail page to get year/season/subtitle_group
3. Fetch Bangumi info for covers and metadata
4. Continuously update episode counts as new episodes are released
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from src.config import CACHE_REFRESH_INTERVAL, PAGE_SIZE
from src.models.anime import Anime
from src.parser.anime1_parser import Anime1Parser
from src.parser.cover_finder import CoverFinder
from src.services.cover_cache_service import get_cover_cache_service

logger = logging.getLogger(__name__)

# Cache configuration constants
CONCURRENT_WORKERS = 5  # Number of concurrent workers for fetching details
BATCH_DELAY = 2  # seconds delay between batches
VERSION_SAMPLE_SIZE = 10  # Number of anime IDs to use for version string
EMPTY_CACHE_WAIT = 5  # seconds to wait when cache is empty

# Global cache state
_anime_list_cache: List[Anime] = []
_anime_map_cache: Dict[str, Anime] = {}
_last_refresh_time: Optional[datetime] = None
_last_data_version: Optional[str] = None
_cache_lock = threading.Lock()
_refresh_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_initial_load_complete = threading.Event()

# Progress tracking
_fetch_progress = {
    "current_page": 0,
    "total_pages": 0,
    "current_index": 0,
    "total_anime": 0,
    "is_fetching": False,
}
_progress_lock = threading.Lock()


def get_anime_list_cache() -> List[Anime]:
    """Get the cached anime list.

    Returns:
        List of cached Anime objects.
    """
    global _anime_list_cache
    with _cache_lock:
        if not _anime_list_cache:
            _load_anime_list_sync()
        return _anime_list_cache.copy()


def get_anime_map_cache() -> Dict[str, Anime]:
    """Get the cached anime map (id -> Anime).

    Returns:
        Dictionary mapping anime ID to Anime object.
    """
    global _anime_map_cache
    with _cache_lock:
        if not _anime_map_cache:
            _load_anime_list_sync()
        return _anime_map_cache.copy()


def _fetch_fresh_data() -> Tuple[List[Anime], str]:
    """Fetch fresh anime list from anime1.me.

    Returns:
        Tuple of (anime_list, version_string).
    """
    parser = Anime1Parser()
    anime_list = parser.parse_page(1)
    parser.close()

    # Create version string from first N anime IDs
    version = "|".join(sorted([a.id for a in anime_list[:VERSION_SAMPLE_SIZE]]))

    return anime_list, version


def _load_anime_list_sync():
    """Load anime list synchronously (blocking).

    This is called on first access if cache is empty.
    """
    global _anime_list_cache, _anime_map_cache, _last_refresh_time, _last_data_version

    try:
        logger.info("[Cache] Loading anime list from anime1.me...")

        anime_list, version = _fetch_fresh_data()

        _anime_list_cache = anime_list
        _anime_map_cache = {a.id: a for a in anime_list}
        _last_refresh_time = datetime.now()
        _last_data_version = version
        _initial_load_complete.set()

        # Log first few anime IDs
        sample_ids = [a.id for a in anime_list[:5]]
        logger.info(f"[Cache] Initial load complete: {len(anime_list)} anime entries (sample: {sample_ids}...)")

    except Exception as e:
        logger.error(f"[Cache] Failed to load anime list: {e}")
        raise


def _is_adult_content(anime: Anime) -> bool:
    """Check if anime is 18x content.

    Args:
        anime: The anime to check.

    Returns:
        True if this is 18x content.
    """
    return "🔞" in anime.title or "anime1.pw" in anime.detail_url


def _fetch_anime_details(anime: Anime, parser: Anime1Parser, finder: CoverFinder, cache_service) -> bool:
    """Fetch details for a single anime.

    Args:
        anime: The anime to fetch details for.
        parser: The Anime1Parser instance.
        finder: The CoverFinder instance.
        cache_service: The cover cache service.

    Returns:
        True if any update was made.
    """
    anime_id = anime.id
    anime_title = anime.title[:20] if anime.title else "Unknown"

    try:
        logger.info(f"[Cache] Fetching details for [{anime_id}] {anime_title}...")

        # Fetch detail page from anime1.me
        html = parser.client.get(anime.detail_url)
        detail_info = parser.parse_anime_detail(html)

        # Update if we got new info
        updated = False
        bangumi_info = None

        if detail_info.get("year") and not anime.year:
            anime.year = detail_info.get("year", "")
            updated = True
            logger.debug(f"[Cache] [{anime_id}] Set year: {anime.year}")
        if detail_info.get("season") and not anime.season:
            anime.season = detail_info.get("season", "")
            updated = True
            logger.debug(f"[Cache] [{anime_id}] Set season: {anime.season}")
        if detail_info.get("subtitle_group") and not anime.subtitle_group:
            anime.subtitle_group = detail_info.get("subtitle_group", "")
            updated = True
            logger.debug(f"[Cache] [{anime_id}] Set subtitle_group: {anime.subtitle_group}")

        # Get full Bangumi info (rate limited)
        if not anime.cover_url:
            try:
                logger.debug(f"[Cache] [{anime_id}] Fetching Bangumi info...")
                bangumi_info = finder.get_bangumi_info(anime, update_anime=True)
                if bangumi_info:
                    if bangumi_info.get("cover_url"):
                        anime.cover_url = bangumi_info["cover_url"]
                        updated = True
                        logger.info(f"[Cache] [{anime_id}] Got cover from Bangumi")
                    # Store full Bangumi info for later use
                    cache_service.set_bangumi_info(anime.id, bangumi_info)
            except Exception as e:
                logger.debug(f"[Cache] [{anime_id}] Bangumi info fetch failed: {e}")

        # Update cache if anything changed
        if updated:
            anime_dict = anime.to_dict()
            cache_service.set_covers({anime.id: anime_dict})
            logger.info(f"[Cache] [{anime_id}] Updated cache")
        else:
            logger.debug(f"[Cache] [{anime_id}] No updates needed")

        return True

    except Exception as e:
        logger.debug(f"[Cache] [{anime_id}] Failed: {e}")
        return False


def _background_fetch_details():
    """Background thread that fetches anime details for all anime.

    This runs continuously in the background, fetching details for each anime
    in batches with concurrent workers. It will complete a full pass through
    all anime, then start over.
    """
    global _anime_list_cache, _fetch_progress

    parser = Anime1Parser()
    cache_service = get_cover_cache_service()
    finder = CoverFinder()

    logger.info("[Cache] Detail fetch thread started")

    while not _stop_event.is_set():
        try:
            with _cache_lock:
                anime_list = list(_anime_list_cache)

            if not anime_list:
                logger.debug("[Cache] No anime list, waiting...")
                _stop_event.wait(EMPTY_CACHE_WAIT)
                continue

            # Filter out adult content
            normal_anime = [a for a in anime_list if not _is_adult_content(a)]
            skipped_list = [a for a in anime_list if _is_adult_content(a)]
            skipped_count = len(skipped_list)

            # Log skipped adult content
            if skipped_count > 0:
                skipped_titles = [a.id for a in skipped_list[:5]]
                logger.info(f"[Cache] Skipping {skipped_count} adult entries: {skipped_titles}...")

            total_anime = len(normal_anime)

            with _progress_lock:
                _fetch_progress["total_anime"] = total_anime
                _fetch_progress["total_pages"] = (total_anime + CONCURRENT_WORKERS - 1) // CONCURRENT_WORKERS
                _fetch_progress["is_fetching"] = True

            logger.info(f"[Cache] === Starting batch fetch: {total_anime} anime, {CONCURRENT_WORKERS} workers ===")

            # Process anime in batches with concurrent workers
            completed_count = 0
            with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
                for page_idx in range(0, total_anime, CONCURRENT_WORKERS):
                    if _stop_event.is_set():
                        break

                    batch = normal_anime[page_idx:page_idx + CONCURRENT_WORKERS]
                    batch_start = page_idx + 1
                    batch_end = min(page_idx + CONCURRENT_WORKERS, total_anime)

                    with _progress_lock:
                        _fetch_progress["current_page"] = page_idx // CONCURRENT_WORKERS + 1
                        _fetch_progress["current_index"] = page_idx

                    logger.info(f"[Cache] Batch {batch_start}-{batch_end}/{total_anime}: Submitting {len(batch)} tasks...")

                    # Submit all tasks in the batch
                    futures = {
                        executor.submit(_fetch_anime_details, anime, parser, finder, cache_service): anime
                        for anime in batch
                    }

                    # Collect results
                    batch_success = 0
                    for future in as_completed(futures):
                        if _stop_event.is_set():
                            break
                        try:
                            result = future.result()
                            if result:
                                batch_success += 1
                        except Exception as ex:
                            logger.debug(f"[Cache] Task error: {ex}")

                        with _progress_lock:
                            _fetch_progress["current_index"] += 1
                            completed_count += 1

                    logger.info(f"[Cache] Batch {batch_start}-{batch_end}/{total_anime}: Completed {batch_success}/{len(batch)}")

            # Final summary
            logger.info(f"[Cache] === Batch fetch complete: {completed_count}/{total_anime} ===")

            # Update version after full pass
            with _cache_lock:
                _last_refresh_time = datetime.now()

            with _progress_lock:
                _fetch_progress["is_fetching"] = False
                _fetch_progress["current_page"] = 0
                _fetch_progress["current_index"] = 0

            logger.info(f"[Cache] Waiting {CACHE_REFRESH_INTERVAL}s before next pass...")
            # Wait before starting next pass
            _stop_event.wait(CACHE_REFRESH_INTERVAL)

        except Exception as e:
            logger.error(f"[Cache] Detail fetch error: {e}")
            _stop_event.wait(5)

    parser.close()
    logger.info("[Cache] Detail fetch thread stopped")


def _check_for_updates():
    """Check if there's new anime or episode updates.

    Returns:
        True if new data was detected.
    """
    global _anime_list_cache, _anime_map_cache, _last_refresh_time, _last_data_version

    try:
        anime_list, version = _fetch_fresh_data()

        # Check if version changed (new anime added)
        if version != _last_data_version:
            logger.info(f"[Cache] New anime detected, updating list...")

            with _cache_lock:
                _anime_list_cache = anime_list
                _anime_map_cache = {a.id: a for a in anime_list}
                _last_refresh_time = datetime.now()
                _last_data_version = version

            return True

        # Update episode counts for existing anime
        new_map = {a.id: a for a in anime_list}
        updated_count = 0

        with _cache_lock:
            for anime in _anime_list_cache:
                if anime.id in new_map:
                    new_anime = new_map[anime.id]
                    if new_anime.episode != anime.episode:
                        anime.episode = new_anime.episode
                        updated_count += 1

        if updated_count > 0:
            logger.info(f"[Cache] Updated episode counts for {updated_count} anime")

        return False

    except Exception as e:
        logger.error(f"[Cache] Update check failed: {e}")
        return False


def _background_refresh_loop():
    """Background thread that periodically checks for updates."""
    logger.info("[Cache] Background refresh thread started")

    # Wait for initial load
    _initial_load_complete.wait(timeout=30)

    # Start the detail fetch thread
    _stop_event.clear()
    detail_thread = threading.Thread(target=_background_fetch_details, daemon=True)
    detail_thread.start()

    while not _stop_event.is_set():
        try:
            # Wait between update checks
            if _stop_event.wait(CACHE_REFRESH_INTERVAL):
                break

            # Quick check for updates
            _check_for_updates()

        except Exception as e:
            logger.error(f"[Cache] Refresh cycle error: {e}")

    logger.info("[Cache] Background refresh thread stopped")


def start_cache_service():
    """Start the background cache service.

    Call this during application startup.
    """
    global _refresh_thread

    if _refresh_thread is not None and _refresh_thread.is_alive():
        logger.warning("[Cache] Service already running")
        return

    logger.info("=" * 50)
    logger.info("[Cache] Starting cache service...")
    logger.info(f"[Cache] Config: workers={CONCURRENT_WORKERS}, interval={CACHE_REFRESH_INTERVAL}s")

    # Load anime list immediately (blocking but ensures data exists)
    _load_anime_list_sync()

    # Start background threads
    _stop_event.clear()
    _refresh_thread = threading.Thread(target=_background_refresh_loop, daemon=True)
    _refresh_thread.start()

    logger.info("[Cache] Cache service started")
    logger.info("=" * 50)


def stop_cache_service():
    """Stop the background cache service.

    Call this during application shutdown.
    """
    global _refresh_thread

    logger.info("[Cache] Stopping cache service...")
    _stop_event.set()

    if _refresh_thread is not None:
        _refresh_thread.join(timeout=10)
        _refresh_thread = None

    logger.info("[Cache] Cache service stopped")


def get_cache_status() -> dict:
    """Get the current cache status.

    Returns:
        Dictionary with cache status information.
    """
    cache_service = get_cover_cache_service()

    with _cache_lock:
        anime_count = len(_anime_list_cache)
        map_ids = set(_anime_map_cache.keys())

    with _progress_lock:
        progress = dict(_fetch_progress)

    cached_covers = cache_service.get_cached_ids()
    covers_count = len([a_id for a_id in cached_covers if a_id in map_ids])

    return {
        "anime_count": anime_count,
        "covers_cached": covers_count,
        "last_refresh": _last_refresh_time.isoformat() if _last_refresh_time else None,
        "is_refreshing": _refresh_thread is not None and _refresh_thread.is_alive(),
        "initial_load_complete": _initial_load_complete.is_set(),
        "progress": progress,
    }


def refresh_cache_now() -> bool:
    """Trigger an immediate cache refresh.

    Returns:
        True if refresh was triggered.
    """
    if _refresh_thread is None or not _refresh_thread.is_alive():
        return False

    def _do_refresh():
        _check_for_updates()

    thread = threading.Thread(target=_do_refresh, daemon=True)
    thread.start()
    return True


def force_refresh_cache() -> bool:
    """Force a full cache refresh.

    Returns:
        True if refresh succeeded.
    """
    try:
        logger.info("[Cache] Force refreshing cache...")

        anime_list, version = _fetch_fresh_data()

        with _cache_lock:
            _anime_list_cache = anime_list
            _anime_map_cache = {a.id: a for a in anime_list}
            _last_refresh_time = datetime.now()
            _last_data_version = version
            _initial_load_complete.set()

        logger.info(f"[Cache] Force refresh complete: {len(anime_list)} anime entries")

        return True

    except Exception as e:
        logger.error(f"[Cache] Force refresh failed: {e}")
        return False
