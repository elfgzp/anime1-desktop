"""Service for managing favorite anime (追番) using Peewee ORM."""
import logging
from datetime import datetime
from typing import List, Optional

from peewee import fn

from src.models.favorite import FavoriteAnime as FavoriteAnimeModel
from src.models.anime import Anime

logger = logging.getLogger(__name__)

DEFAULT_EPISODE = 0


class FavoriteService:
    """Service for managing favorite anime using Peewee ORM."""

    def add_favorite(self, anime: Anime) -> bool:
        """Add an anime to favorites.

        Args:
            anime: Anime model instance.

        Returns:
            True if added successfully, False if already exists.
        """
        # Check if already exists
        existing = FavoriteAnimeModel.get_or_none(FavoriteAnimeModel.id == anime.id)
        if existing:
            return False

        now = datetime.now()
        episode = anime.episode if anime.episode > 0 else DEFAULT_EPISODE

        try:
            FavoriteAnimeModel.create(
                id=anime.id,
                title=anime.title,
                detail_url=anime.detail_url,
                episode=episode,
                cover_url=anime.cover_url or "",
                year=anime.year or "",
                season=anime.season or "",
                subtitle_group=anime.subtitle_group or "",
                last_episode=episode,
                added_at=now,
                updated_at=now,
            )
            logger.info(f"Added favorite: {anime.id} - {anime.title}")
            return True
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False

    def remove_favorite(self, anime_id: str) -> bool:
        """Remove an anime from favorites.

        Args:
            anime_id: ID of the anime to remove.

        Returns:
            True if removed successfully, False if not found.
        """
        try:
            deleted = FavoriteAnimeModel.delete_by_id(anime_id)
            if deleted:
                logger.info(f"Removed favorite: {anime_id}")
            return deleted > 0
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False

    def is_favorite(self, anime_id: str) -> bool:
        """Check if an anime is in favorites.

        Args:
            anime_id: ID of the anime to check.

        Returns:
            True if favorite, False otherwise.
        """
        return FavoriteAnimeModel.get_or_none(FavoriteAnimeModel.id == anime_id) is not None

    def get_favorites(self) -> List[FavoriteAnimeModel]:
        """Get all favorites.

        Returns:
            List of FavoriteAnimeModel instances.
        """
        return list(
            FavoriteAnimeModel.select()
            .order_by(FavoriteAnimeModel.added_at.desc())
        )

    def update_episode(self, anime_id: str, current_episode: int) -> bool:
        """Update the current episode for a favorite.

        Args:
            anime_id: ID of the anime.
            current_episode: Current episode number.

        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            now = datetime.now()
            query = FavoriteAnimeModel.update(
                episode=current_episode,
                updated_at=now
            ).where(FavoriteAnimeModel.id == anime_id)
            return query.execute() > 0
        except Exception as e:
            logger.error(f"Error updating episode: {e}")
            return False

    def check_for_updates(self) -> List[FavoriteAnimeModel]:
        """Check which favorites have new episodes.

        This method compares the stored last_episode with the current episode
        from the anime list. Returns favorites that have updates.

        Returns:
            List of favorites with updates (episode > last_episode).
        """
        from src.routes.anime import get_anime_map

        try:
            anime_map = get_anime_map()
            favorites = self.get_favorites()
            updated = []

            for fav in favorites:
                anime_id = fav.id
                if anime_id in anime_map:
                    current_anime = anime_map[anime_id]
                    current_episode = current_anime.episode
                    last_episode = fav.last_episode

                    if current_episode > last_episode:
                        # Update the stored episode
                        self.update_episode(anime_id, current_episode)
                        fav.episode = current_episode
                        fav.has_update = True
                        updated.append(fav)

            return updated
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return []

    def has_updates(self) -> bool:
        """Check if any favorites have updates.

        Returns:
            True if any favorites have new episodes, False otherwise.
        """
        updates = self.check_for_updates()
        return len(updates) > 0

    def get_count(self) -> int:
        """Get the count of favorites.

        Returns:
            Number of favorites.
        """
        return FavoriteAnimeModel.select().count()


# Global service instance
_favorite_service: Optional[FavoriteService] = None


def get_favorite_service() -> FavoriteService:
    """Get or create the global favorite service instance."""
    global _favorite_service
    if _favorite_service is None:
        _favorite_service = FavoriteService()
    return _favorite_service
