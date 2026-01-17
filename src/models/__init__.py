"""Models package for anime1-desktop."""
from src.models.database import (
    get_database,
    close_database,
    init_database,
    get_database_path,
    BaseModel,
)
from src.models.favorite import FavoriteAnime
from src.models.cover_cache import CoverCache

__all__ = [
    "get_database",
    "close_database", 
    "init_database",
    "get_database_path",
    "BaseModel",
    "FavoriteAnime",
    "CoverCache",
]
