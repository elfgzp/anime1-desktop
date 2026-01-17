"""Playback history model."""
from peewee import TextField, IntegerField, TimestampField, FloatField

from src.models.database import BaseModel


class PlaybackHistory(BaseModel):
    """Model for storing playback history (观看历史).

    Tracks the last played position for each episode of each anime.
    """

    id = TextField(primary_key=True)
    anime_id = TextField(index=True)
    anime_title = TextField()
    episode_id = TextField(index=True)
    episode_num = IntegerField()
    position_seconds = FloatField(default=0.0)  # Playback position in seconds
    total_seconds = FloatField(default=0.0)  # Total duration in seconds (optional)
    last_watched_at = TimestampField()
    cover_url = TextField(default="")

    class Meta:
        table_name = "playback_history"
        # Create indexes for efficient queries
        indexes = (
            (("anime_id", "episode_id"), True),  # Unique index for anime+episode combo
        )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "anime_id": self.anime_id,
            "anime_title": self.anime_title,
            "episode_id": self.episode_id,
            "episode_num": self.episode_num,
            "position_seconds": self.position_seconds,
            "total_seconds": self.total_seconds,
            "position_formatted": self.format_position(),
            "last_watched_at": self.last_watched_at.isoformat() if self.last_watched_at else None,
            "cover_url": self.cover_url,
        }

    def format_position(self):
        """Format position as MM:SS or HH:MM:SS."""
        seconds = int(self.position_seconds)
        if seconds < 0:
            return "00:00"
        hours, mins = divmod(seconds, 3600)
        mins, secs = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def get_progress_percent(self):
        """Get progress percentage (0-100)."""
        if self.total_seconds > 0:
            return min(100, int((self.position_seconds / self.total_seconds) * 100))
        return 0

    @classmethod
    def generate_id(cls, anime_id: str, episode_id: str) -> str:
        """Generate a unique ID for a playback history entry."""
        return f"{anime_id}_{episode_id}"
