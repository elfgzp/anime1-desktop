"""Anime data models."""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Anime:
    """Anime model representing an anime entry."""

    id: str
    title: str
    detail_url: str
    episode: int
    cover_url: str = ""
    year: str = ""
    season: str = ""
    subtitle_group: str = ""
    match_score: int = 0
    match_source: str = ""

    def to_dict(self) -> Dict:
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
            "match_score": self.match_score,
            "match_source": self.match_source,
        }

    @classmethod
    def create(
        cls,
        id: str,
        title: str,
        detail_url: str,
        episode: int,
        cover_url: str = "",
        year: str = "",
        season: str = "",
        subtitle_group: str = "",
        match_score: int = 0,
        match_source: str = "",
    ) -> "Anime":
        """Factory method to create an Anime instance."""
        return cls(
            id=id,
            title=title,
            detail_url=detail_url,
            episode=episode,
            cover_url=cover_url,
            year=year,
            season=season,
            subtitle_group=subtitle_group,
            match_score=match_score,
            match_source=match_source,
        )


@dataclass
class AnimePage:
    """Page model for anime listings."""

    anime_list: List[Anime]
    current_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "anime_list": [a.to_dict() for a in self.anime_list],
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }

    @classmethod
    def create(
        cls,
        anime_list: List[Anime],
        current_page: int,
        total_pages: int,
    ) -> "AnimePage":
        """Factory method to create an AnimePage instance."""
        return cls(
            anime_list=anime_list,
            current_page=current_page,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_prev=current_page > 1,
        )
