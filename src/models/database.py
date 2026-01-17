"""Database connection and Peewee models for anime1-desktop."""
import logging
from pathlib import Path
from typing import Optional

from peewee import (
    SqliteDatabase,
    Model,
    TextField,
    IntegerField,
    TimestampField,
    BooleanField,
)

from src.utils.app_dir import ensure_app_data_dir

logger = logging.getLogger(__name__)

# Database file name
DB_FILE_NAME = "anime1.db"

# Global database instance
_db: Optional[SqliteDatabase] = None


def get_database_path() -> Path:
    """Get the path to the database file."""
    app_dir = ensure_app_data_dir()
    return app_dir / DB_FILE_NAME


def get_database() -> SqliteDatabase:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        db_path = get_database_path()
        _db = SqliteDatabase(str(db_path), pragmas={
            "journal_mode": "wal",
            "cache_size": -64000,  # 64MB cache
            "foreign_keys": 1,
        })
        logger.info(f"Database initialized at: {db_path}")
    return _db


def close_database():
    """Close the database connection."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
        logger.info("Database connection closed")


class BaseModel(Model):
    """Base model class with common functionality."""

    class Meta:
        database = get_database()


def init_database():
    """Initialize the database and create tables if they don't exist.

    This function:
    1. Creates the database connection
    2. Creates all tables if they don't exist
    3. Runs any pending migrations
    """
    db = get_database()
    db.connect()

    # Import models to register them
    from src.models.favorite import FavoriteAnime
    from src.models.cover_cache import CoverCache
    from src.models.playback_history import PlaybackHistory

    # Create tables
    db.create_tables([
        FavoriteAnime,
        CoverCache,
        PlaybackHistory,
    ])

    # Run migrations
    from src.models.migration import run_migrations
    run_migrations()

    logger.info("Database initialized successfully")
