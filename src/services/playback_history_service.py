"""Service for managing playback history using Peewee ORM."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from peewee import fn

from src.models.playback_history import PlaybackHistory as PlaybackHistoryModel
from src.models.anime import Anime

logger = logging.getLogger(__name__)


class PlaybackHistoryService:
    """Service for managing playback history using Peewee ORM."""

    def update_progress(
        self,
        anime_id: str,
        anime_title: str,
        episode_id: str,
        episode_num: int,
        position_seconds: float,
        total_seconds: float = 0.0,
        cover_url: str = ""
    ) -> Tuple[bool, PlaybackHistoryModel]:
        """Update or create playback progress for an episode.

        This method updates the playback position. If the entry already exists,
        it updates the position and timestamp. If not, it creates a new entry.

        Args:
            anime_id: ID of the anime.
            anime_title: Title of the anime.
            episode_id: ID of the episode.
            episode_num: Episode number.
            position_seconds: Current playback position in seconds.
            total_seconds: Total duration of the episode in seconds (optional).
            cover_url: URL of the anime cover (optional).

        Returns:
            Tuple of (success, entry).
        """
        try:
            entry_id = PlaybackHistoryModel.generate_id(anime_id, episode_id)
            now = datetime.now()

            logger.info(f"[PlaybackHistory] 保存进度: anime_id={anime_id}, episode_id={episode_id}, position={position_seconds}s")

            # Upsert: update if exists, otherwise insert
            query = PlaybackHistoryModel.insert(
                id=entry_id,
                anime_id=anime_id,
                anime_title=anime_title,
                episode_id=episode_id,
                episode_num=episode_num,
                position_seconds=position_seconds,
                total_seconds=total_seconds,
                cover_url=cover_url,
                last_watched_at=now
            ).on_conflict(
                conflict_target=("id",),
                preserve=["anime_id", "anime_title", "episode_id", "episode_num", "cover_url"],
                update={
                    "position_seconds": position_seconds,
                    "total_seconds": total_seconds,
                    "last_watched_at": now
                }
            )
            query.execute()

            # Fetch and return the updated entry
            entry = PlaybackHistoryModel.get_by_id(entry_id)
            logger.info(f"[PlaybackHistory] 进度保存成功: {anime_title} 第{episode_num}集 -> {position_seconds}s")
            return True, entry

        except Exception as e:
            logger.error(f"[PlaybackHistory] 保存进度失败: {e}")
            return False, None

    def get_history(self, limit: int = 50) -> List[PlaybackHistoryModel]:
        """Get playback history ordered by most recently watched.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of PlaybackHistoryModel instances, most recent first.
        """
        try:
            return list(
                PlaybackHistoryModel.select()
                .order_by(PlaybackHistoryModel.last_watched_at.desc())
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting playback history: {e}")
            return []

    def get_history_by_anime(self, anime_id: str) -> List[PlaybackHistoryModel]:
        """Get all playback history entries for a specific anime.

        Args:
            anime_id: ID of the anime.

        Returns:
            List of PlaybackHistoryModel instances for the anime.
        """
        try:
            return list(
                PlaybackHistoryModel.select()
                .where(PlaybackHistoryModel.anime_id == anime_id)
                .order_by(PlaybackHistoryModel.episode_num.desc())
            )
        except Exception as e:
            logger.error(f"Error getting playback history for anime {anime_id}: {e}")
            return []

    def get_episode_progress(self, anime_id: str, episode_id: str) -> Optional[PlaybackHistoryModel]:
        """Get playback progress for a specific episode.

        Args:
            anime_id: ID of the anime.
            episode_id: ID of the episode.

        Returns:
            PlaybackHistoryModel instance or None if not found.
        """
        try:
            entry_id = PlaybackHistoryModel.generate_id(anime_id, episode_id)
            return PlaybackHistoryModel.get_by_id(entry_id)
        except PlaybackHistoryModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting episode progress: {e}")
            return None

    def get_latest_for_anime(self, anime_id: str) -> Optional[PlaybackHistoryModel]:
        """Get the most recently watched episode for an anime.

        Args:
            anime_id: ID of the anime.

        Returns:
            PlaybackHistoryModel instance or None if not found.
        """
        try:
            return (
                PlaybackHistoryModel.select()
                .where(PlaybackHistoryModel.anime_id == anime_id)
                .order_by(PlaybackHistoryModel.last_watched_at.desc())
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting latest progress for anime {anime_id}: {e}")
            return None

    def delete_history(self, anime_id: str = None, episode_id: str = None) -> bool:
        """Delete playback history.

        Args:
            anime_id: Optional - delete all history for this anime.
            episode_id: Optional - delete history for specific episode.

        Returns:
            True if deleted successfully.
        """
        try:
            query = PlaybackHistoryModel.delete()

            if anime_id and episode_id:
                query = query.where(
                    (PlaybackHistoryModel.anime_id == anime_id) &
                    (PlaybackHistoryModel.episode_id == episode_id)
                )
            elif anime_id:
                query = query.where(PlaybackHistoryModel.anime_id == anime_id)
            elif episode_id:
                query = query.where(PlaybackHistoryModel.episode_id == episode_id)
            else:
                # Delete all history
                query = query.execute()
                return True

            deleted = query.execute()
            logger.info(f"Deleted {deleted} playback history entries")
            return True

        except Exception as e:
            logger.error(f"Error deleting playback history: {e}")
            return False

    def get_count(self) -> int:
        """Get total count of playback history entries.

        Returns:
            Number of entries.
        """
        try:
            return PlaybackHistoryModel.select().count()
        except Exception as e:
            logger.error(f"Error getting playback history count: {e}")
            return 0

    def cleanup_old_entries(self, keep_count: int = 200) -> int:
        """Remove old playback history entries, keeping the most recent ones.

        Args:
            keep_count: Number of entries to keep.

        Returns:
            Number of deleted entries.
        """
        try:
            # Get the timestamp of the nth most recent entry
            entries = (
                PlaybackHistoryModel.select()
                .order_by(PlaybackHistoryModel.last_watched_at.desc())
                .offset(keep_count)
                .limit(1)
            )

            if not entries:
                return 0

            cutoff_time = entries[0].last_watched_at

            # Delete all entries older than cutoff
            deleted = (
                PlaybackHistoryModel.delete()
                .where(PlaybackHistoryModel.last_watched_at < cutoff_time)
                .execute()
            )

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old playback history entries")

            return deleted

        except Exception as e:
            logger.error(f"Error cleaning up old playback history: {e}")
            return 0


# Global service instance
_playback_history_service: Optional[PlaybackHistoryService] = None


def get_playback_history_service() -> PlaybackHistoryService:
    """Get or create the global playback history service instance."""
    global _playback_history_service
    if _playback_history_service is None:
        _playback_history_service = PlaybackHistoryService()
    return _playback_history_service
