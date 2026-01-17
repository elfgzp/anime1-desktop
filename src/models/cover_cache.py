"""Cover cache model."""
from datetime import datetime
from peewee import TextField, TimestampField

from src.models.database import BaseModel


class CoverCache(BaseModel):
    """Model for caching anime cover and Bangumi data."""

    anime_id = TextField(primary_key=True)
    cover_data = TextField()  # JSON string containing cover and basic info
    bangumi_info = TextField(null=True)  # JSON string containing Bangumi detailed info
    cached_at = TimestampField(default=datetime.now)

    class Meta:
        table_name = "cover_cache"

    @classmethod
    def get_cover(cls, anime_id: str):
        """Get cached cover data for an anime.

        Returns:
            Dict or None if not cached.
        """
        import json
        record = cls.get_or_none(cls.anime_id == anime_id)
        if record:
            try:
                return json.loads(record.cover_data)
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def get_covers(cls, anime_ids: list) -> dict:
        """Get cached covers for multiple anime.

        Args:
            anime_ids: List of anime IDs.

        Returns:
            Dict mapping anime_id to cover data.
        """
        import json
        result = {}
        query = cls.select().where(cls.anime_id.in_(anime_ids))
        for record in query:
            try:
                result[record.anime_id] = json.loads(record.cover_data)
            except json.JSONDecodeError:
                continue
        return result

    @classmethod
    def get_bangumi_info(cls, anime_id: str):
        """Get cached Bangumi info for an anime.

        Returns:
            Dict or None if not cached.
        """
        import json
        record = cls.get_or_none(cls.anime_id == anime_id)
        if record and record.bangumi_info:
            try:
                return json.loads(record.bangumi_info)
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def get_bangumi_info_batch(cls, anime_ids: list) -> dict:
        """Get cached Bangumi info for multiple anime.

        Args:
            anime_ids: List of anime IDs.

        Returns:
            Dict mapping anime_id to Bangumi info.
        """
        import json
        result = {}
        query = cls.select().where(cls.anime_id.in_(anime_ids))
        for record in query:
            if record.bangumi_info:
                try:
                    result[record.anime_id] = json.loads(record.bangumi_info)
                except json.JSONDecodeError:
                    continue
        return result

    @classmethod
    def set_cover(cls, anime_id: str, cover_data: dict, bangumi_info: dict = None) -> bool:
        """Cache cover data and optionally Bangumi info for an anime.

        Args:
            anime_id: The anime ID.
            cover_data: The cover data to cache.
            bangumi_info: Optional Bangumi info to cache.

        Returns:
            True if cached successfully.
        """
        import json
        try:
            json_data = json.dumps(cover_data, ensure_ascii=False)
            bangumi_json = json.dumps(bangumi_info, ensure_ascii=False) if bangumi_info else None
            # Use upsert pattern: delete then insert
            cls.delete().where(cls.anime_id == anime_id).execute()
            cls.insert(anime_id=anime_id, cover_data=json_data, bangumi_info=bangumi_json).execute()
            return True
        except (TypeError, ValueError):
            return False

    @classmethod
    def set_covers(cls, covers: dict, bangumi_infos: dict = None) -> int:
        """Cache multiple covers at once.

        Args:
            covers: Dict mapping anime_id to cover data.
            bangumi_infos: Optional dict mapping anime_id to Bangumi info.

        Returns:
            Number of covers successfully cached.
        """
        import json
        successful = 0

        if bangumi_infos is None:
            bangumi_infos = {}

        for anime_id, cover_data in covers.items():
            try:
                json_data = json.dumps(cover_data, ensure_ascii=False)
                bangumi_info = bangumi_infos.get(anime_id)
                bangumi_json = json.dumps(bangumi_info, ensure_ascii=False) if bangumi_info else None
                # Use upsert pattern: delete then insert
                cls.delete().where(cls.anime_id == anime_id).execute()
                cls.insert(anime_id=anime_id, cover_data=json_data, bangumi_info=bangumi_json).execute()
                successful += 1
            except (TypeError, ValueError):
                continue
        return successful

    @classmethod
    def set_bangumi_info(cls, anime_id: str, bangumi_info: dict) -> bool:
        """Update Bangumi info for an existing anime cache entry.

        Args:
            anime_id: The anime ID.
            bangumi_info: The Bangumi info to cache.

        Returns:
            True if cached successfully.
        """
        import json
        try:
            bangumi_json = json.dumps(bangumi_info, ensure_ascii=False)
            # Update only the bangumi_info field
            query = cls.update(bangumi_info=bangumi_json).where(cls.anime_id == anime_id)
            query.execute()
            return True
        except (TypeError, ValueError):
            return False

    @classmethod
    def clear_all(cls) -> int:
        """Clear all cached covers.

        Returns:
            Number of entries deleted.
        """
        return cls.delete().execute()

    @classmethod
    def get_count(cls) -> int:
        """Get the number of cached covers."""
        return cls.select().count()
