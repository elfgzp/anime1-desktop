"""Service for managing favorite anime (追番)."""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.utils.app_dir import ensure_app_data_dir
from src.models.favorite import FavoriteAnime
from src.models.anime import Anime
from src.constants.database import (
    DB_FILE_NAME,
    TABLE_FAVORITES,
    COL_ID,
    COL_TITLE,
    COL_DETAIL_URL,
    COL_EPISODE,
    COL_COVER_URL,
    COL_YEAR,
    COL_SEASON,
    COL_SUBTITLE_GROUP,
    COL_LAST_EPISODE,
    COL_ADDED_AT,
    COL_UPDATED_AT,
    IDX_FAVORITES_ID,
    DEFAULT_EPISODE,
    DEFAULT_EMPTY_STRING
)

logger = logging.getLogger(__name__)


class FavoriteService:
    """Service for managing favorite anime."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the favorite service.
        
        Args:
            db_path: Optional path to database file. If not provided, uses default location.
        """
        if db_path is None:
            app_dir = ensure_app_data_dir()
            db_path = app_dir / DB_FILE_NAME
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_FAVORITES} (
                {COL_ID} TEXT PRIMARY KEY,
                {COL_TITLE} TEXT NOT NULL,
                {COL_DETAIL_URL} TEXT NOT NULL,
                {COL_EPISODE} INTEGER NOT NULL,
                {COL_COVER_URL} TEXT DEFAULT '{DEFAULT_EMPTY_STRING}',
                {COL_YEAR} TEXT DEFAULT '{DEFAULT_EMPTY_STRING}',
                {COL_SEASON} TEXT DEFAULT '{DEFAULT_EMPTY_STRING}',
                {COL_SUBTITLE_GROUP} TEXT DEFAULT '{DEFAULT_EMPTY_STRING}',
                {COL_LAST_EPISODE} INTEGER DEFAULT {DEFAULT_EPISODE},
                {COL_ADDED_AT} TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                {COL_UPDATED_AT} TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        create_index_sql = f"""
            CREATE INDEX IF NOT EXISTS {IDX_FAVORITES_ID} ON {TABLE_FAVORITES}({COL_ID})
        """
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            cursor.execute(create_index_sql)
            conn.commit()
        finally:
            conn.close()

    def add_favorite(self, anime: Anime) -> bool:
        """Add an anime to favorites.
        
        Args:
            anime: Anime model instance.
            
        Returns:
            True if added successfully, False if already exists.
        """
        check_sql = f"SELECT {COL_ID} FROM {TABLE_FAVORITES} WHERE {COL_ID} = ?"
        
        insert_sql = f"""
            INSERT INTO {TABLE_FAVORITES} (
                {COL_ID}, {COL_TITLE}, {COL_DETAIL_URL}, {COL_EPISODE}, {COL_COVER_URL},
                {COL_YEAR}, {COL_SEASON}, {COL_SUBTITLE_GROUP}, {COL_LAST_EPISODE}, 
                {COL_ADDED_AT}, {COL_UPDATED_AT}
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        episode = anime.episode if anime.episode > 0 else DEFAULT_EPISODE
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Check if already exists
            cursor.execute(check_sql, (anime.id,))
            if cursor.fetchone():
                return False
            
            # Insert new favorite
            cursor.execute(insert_sql, (
                anime.id,
                anime.title,
                anime.detail_url,
                episode,
                anime.cover_url or DEFAULT_EMPTY_STRING,
                anime.year or DEFAULT_EMPTY_STRING,
                anime.season or DEFAULT_EMPTY_STRING,
                anime.subtitle_group or DEFAULT_EMPTY_STRING,
                episode,  # last_episode initially equals episode
                now,
                now
            ))
            
            conn.commit()
            logger.info(f"Added favorite: {anime.id} - {anime.title}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding favorite: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def remove_favorite(self, anime_id: str) -> bool:
        """Remove an anime from favorites.
        
        Args:
            anime_id: ID of the anime to remove.
            
        Returns:
            True if removed successfully, False if not found.
        """
        delete_sql = f"DELETE FROM {TABLE_FAVORITES} WHERE {COL_ID} = ?"
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(delete_sql, (anime_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Removed favorite: {anime_id}")
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Error removing favorite: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def is_favorite(self, anime_id: str) -> bool:
        """Check if an anime is in favorites.
        
        Args:
            anime_id: ID of the anime to check.
            
        Returns:
            True if favorite, False otherwise.
        """
        check_sql = f"SELECT {COL_ID} FROM {TABLE_FAVORITES} WHERE {COL_ID} = ?"
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(check_sql, (anime_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorites.
        
        Returns:
            List of favorite anime dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, detail_url, episode, cover_url,
                       year, season, subtitle_group, last_episode, added_at, updated_at
                FROM favorites
                ORDER BY added_at DESC
            """)
            
            rows = cursor.fetchall()
            favorites = []
            for row in rows:
                favorites.append({
                    "id": row[0],
                    "title": row[1],
                    "detail_url": row[2],
                    "episode": row[3],
                    "cover_url": row[4],
                    "year": row[5],
                    "season": row[6],
                    "subtitle_group": row[7],
                    "last_episode": row[8],
                    "added_at": row[9],
                    "updated_at": row[10]
                })
            
            return favorites
        finally:
            conn.close()

    def update_episode(self, anime_id: str, current_episode: int) -> bool:
        """Update the current episode for a favorite.
        
        Args:
            anime_id: ID of the anime.
            current_episode: Current episode number.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE favorites
                SET episode = ?, updated_at = ?
                WHERE id = ?
            """, (current_episode, datetime.now(), anime_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating episode: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def check_for_updates(self) -> List[Dict[str, Any]]:
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
                anime_id = fav["id"]
                if anime_id in anime_map:
                    current_anime = anime_map[anime_id]
                    current_episode = current_anime.episode
                    last_episode = fav.get("last_episode", 0)
                    
                    if current_episode > last_episode:
                        # Update the stored episode
                        self.update_episode(anime_id, current_episode)
                        updated.append({
                            **fav,
                            "episode": current_episode,
                            "last_episode": last_episode,
                            "has_update": True
                        })
            
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


# Global service instance
_favorite_service: Optional[FavoriteService] = None


def get_favorite_service() -> FavoriteService:
    """Get or create the global favorite service instance."""
    global _favorite_service
    if _favorite_service is None:
        _favorite_service = FavoriteService()
    return _favorite_service
