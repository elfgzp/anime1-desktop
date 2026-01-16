"""Favorite anime data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FavoriteAnime:
    """Favorite anime model."""
    
    id: str
    title: str
    detail_url: str
    episode: int
    cover_url: str = ""
    year: str = ""
    season: str = ""
    subtitle_group: str = ""
    last_episode: int = 0
    added_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    has_update: bool = False
    
    def to_dict(self) -> dict:
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
            "has_update": self.has_update
        }
    
    @classmethod
    def from_anime_dict(cls, anime: dict, last_episode: Optional[int] = None) -> "FavoriteAnime":
        """Create FavoriteAnime from anime dictionary."""
        if last_episode is None:
            last_episode = anime.get("episode", 0)
        
        return cls(
            id=anime["id"],
            title=anime["title"],
            detail_url=anime["detail_url"],
            episode=anime.get("episode", 0),
            cover_url=anime.get("cover_url", ""),
            year=anime.get("year", ""),
            season=anime.get("season", ""),
            subtitle_group=anime.get("subtitle_group", ""),
            last_episode=last_episode
        )
