"""Service for caching anime covers using Peewee ORM."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from src.models.cover_cache import CoverCache as CoverCacheModel
from src.models.database import get_database_path

logger = logging.getLogger(__name__)


class CoverCacheService:
    """Service for caching anime cover data using Peewee ORM."""

    def get_cover(self, anime_id: str) -> Optional[Dict[str, Any]]:
        """Get cached cover data for an anime.

        Args:
            anime_id: The anime ID.

        Returns:
            Cover data dict, or None if not cached.
        """
        return CoverCacheModel.get_cover(anime_id)

    def get_covers(self, anime_ids: list) -> Dict[str, Dict[str, Any]]:
        """Get cached covers for multiple anime.

        Args:
            anime_ids: List of anime IDs.

        Returns:
            Dict mapping anime_id to cover data.
        """
        if not anime_ids:
            return {}
        return CoverCacheModel.get_covers(anime_ids)

    def set_cover(self, anime_id: str, cover_data: Dict[str, Any], bangumi_info: Dict[str, Any] = None) -> bool:
        """Cache cover data for an anime, optionally with Bangumi info.

        Args:
            anime_id: The anime ID.
            cover_data: The cover data to cache.
            bangumi_info: Optional Bangumi info to cache.

        Returns:
            True if cached successfully, False otherwise.
        """
        return CoverCacheModel.set_cover(anime_id, cover_data, bangumi_info)

    def set_covers(self, covers: Dict[str, Dict[str, Any]], bangumi_infos: Dict[str, Dict[str, Any]] = None) -> int:
        """Cache multiple covers at once.

        Args:
            covers: Dict mapping anime_id to cover data.
            bangumi_infos: Optional dict mapping anime_id to Bangumi info.

        Returns:
            Number of covers successfully cached.
        """
        if not covers:
            return 0
        return CoverCacheModel.set_covers(covers, bangumi_infos)

    def get_bangumi_info(self, anime_id: str) -> Optional[Dict[str, Any]]:
        """Get cached Bangumi info for an anime.

        Args:
            anime_id: The anime ID.

        Returns:
            Bangumi info dict, or None if not cached.
        """
        return CoverCacheModel.get_bangumi_info(anime_id)

    def get_bangumi_info_batch(self, anime_ids: list) -> Dict[str, Dict[str, Any]]:
        """Get cached Bangumi info for multiple anime.

        Args:
            anime_ids: List of anime IDs.

        Returns:
            Dict mapping anime_id to Bangumi info.
        """
        if not anime_ids:
            return {}
        return CoverCacheModel.get_bangumi_info_batch(anime_ids)

    def set_bangumi_info(self, anime_id: str, bangumi_info: Dict[str, Any]) -> bool:
        """Update Bangumi info for an existing anime cache entry.

        Args:
            anime_id: The anime ID.
            bangumi_info: The Bangumi info to cache.

        Returns:
            True if cached successfully, False otherwise.
        """
        return CoverCacheModel.set_bangumi_info(anime_id, bangumi_info)

    def delete_cover(self, anime_id: str) -> bool:
        """Delete cached cover for an anime.

        Args:
            anime_id: The anime ID.

        Returns:
            True if deleted, False if not found.
        """
        try:
            deleted = CoverCacheModel.delete_by_id(anime_id)
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting cover cache for {anime_id}: {e}")
            return False

    def clear_all(self) -> int:
        """Clear all cached covers.

        Returns:
            Number of entries deleted.
        """
        return CoverCacheModel.clear_all()

    def get_cache_count(self) -> int:
        """Get the number of cached covers.

        Returns:
            Number of cached entries.
        """
        return CoverCacheModel.get_count()

    def get_cache_size(self) -> int:
        """Get the total size of cached data in bytes.

        Note: This is an approximation based on the database file size.

        Returns:
            Size in bytes, or -1 if unavailable.
        """
        try:
            db_path = get_database_path()
            if db_path.exists():
                return db_path.stat().st_size
        except OSError as e:
            logger.error(f"Error getting cache size: {e}")
        return -1


# Global service instance
_cover_cache_service: Optional[CoverCacheService] = None


def get_cover_cache_service() -> CoverCacheService:
    """Get or create the global cover cache service instance."""
    global _cover_cache_service
    if _cover_cache_service is None:
        _cover_cache_service = CoverCacheService()
    return _cover_cache_service
