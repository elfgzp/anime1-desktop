"""Database constants."""
from typing import Final

# Database file name
DB_FILE_NAME: Final[str] = "favorites.db"

# Table name
TABLE_FAVORITES: Final[str] = "favorites"

# Column names
COL_ID: Final[str] = "id"
COL_TITLE: Final[str] = "title"
COL_DETAIL_URL: Final[str] = "detail_url"
COL_EPISODE: Final[str] = "episode"
COL_COVER_URL: Final[str] = "cover_url"
COL_YEAR: Final[str] = "year"
COL_SEASON: Final[str] = "season"
COL_SUBTITLE_GROUP: Final[str] = "subtitle_group"
COL_LAST_EPISODE: Final[str] = "last_episode"
COL_ADDED_AT: Final[str] = "added_at"
COL_UPDATED_AT: Final[str] = "updated_at"

# Index name
IDX_FAVORITES_ID: Final[str] = "idx_favorites_id"

# Default values
DEFAULT_EPISODE: Final[int] = 0
DEFAULT_EMPTY_STRING: Final[str] = ""
