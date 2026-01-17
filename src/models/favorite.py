"""Favorite anime model."""
from peewee import TextField, IntegerField, TimestampField

from src.models.database import BaseModel


class FavoriteAnime(BaseModel):
    """Model for storing favorite anime (追番)."""

    id = TextField(primary_key=True)
    title = TextField()
    detail_url = TextField()
    episode = IntegerField(default=0)
    cover_url = TextField(default="")
    year = TextField(default="")
    season = TextField(default="")
    subtitle_group = TextField(default="")
    last_episode = IntegerField(default=0)
    added_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        table_name = "favorites"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "detail_url": self.detail_url,
            "episode": self.episode,
            "cover_url": self.cover_url,
            "year": self.year,
            "season": self.season,
            "subtitle_group": self.subtitle_group,
            "last_episode": self.last_episode,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
