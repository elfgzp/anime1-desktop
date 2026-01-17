"""Database migration helper for Peewee models.

This module provides schema version tracking and migration capabilities
for the anime1-desktop SQLite database.
"""
import logging
from typing import Callable, Dict, List, Optional
from datetime import datetime

from src.models.database import get_database, BaseModel

logger = logging.getLogger(__name__)

# Current schema version - increment this when making schema changes
SCHEMA_VERSION = 2

# Migration history table name
MIGRATION_TABLE = "migrations"


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: int, description: str, migrate_fn: Callable):
        """Initialize a migration.
        
        Args:
            version: Target schema version.
            description: Description of the migration.
            migrate_fn: Function that performs the migration.
        """
        self.version = version
        self.description = description
        self.migrate_fn = migrate_fn


class PeeweeMigrationHelper:
    """Helper class for managing Peewee database migrations."""

    def __init__(self):
        """Initialize the migration helper."""
        self.db = get_database()
        self.migrations: Dict[int, Migration] = {}

    def register_migration(self, version: int, description: str, migrate_fn: Callable):
        """Register a migration.
        
        Args:
            version: Target schema version.
            description: Description of the migration.
            migrate_fn: Function that performs the migration.
        """
        self.migrations[version] = Migration(version, description, migrate_fn)

    def _ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        # Create a simple migrations table using raw SQL
        self.db.execute_sql(f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def get_applied_migrations(self) -> List[int]:
        """Get list of applied migration versions.
        
        Returns:
            List of applied migration version numbers.
        """
        try:
            cursor = self.db.execute_sql(
                f"SELECT version FROM {MIGRATION_TABLE} ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []

    def apply_migrations(self):
        """Apply all pending migrations."""
        self._ensure_migrations_table()
        
        applied = self.get_applied_migrations()
        current_version = max(applied) if applied else 0
        
        logger.info(f"Current schema version: {current_version}, Latest: {SCHEMA_VERSION}")
        
        if current_version >= SCHEMA_VERSION:
            logger.info("Database schema is up to date")
            return
        
        # Apply migrations in order
        for version in range(current_version + 1, SCHEMA_VERSION + 1):
            if version in self.migrations:
                migration = self.migrations[version]
                logger.info(f"Applying migration {version}: {migration.description}")

                try:
                    # Run migration function
                    migration.migrate_fn(self.db)

                    # Record the migration
                    self.db.execute_sql(
                        f"INSERT OR REPLACE INTO {MIGRATION_TABLE} (version, applied_at) VALUES (?, ?)",
                        (version, datetime.now())
                    )

                    logger.info(f"Migration {version} applied successfully")
                except Exception as e:
                    logger.error(f"Failed to apply migration {version}: {e}")
                    raise
            else:
                logger.warning(f"No migration registered for version {version}")

    def get_schema_version(self) -> int:
        """Get the current schema version.
        
        Returns:
            Current schema version, or 0 if no migrations applied.
        """
        applied = self.get_applied_migrations()
        return max(applied) if applied else 0


# Global migration helper instance
_migration_helper: Optional[PeeweeMigrationHelper] = None


def get_migration_helper() -> PeeweeMigrationHelper:
    """Get or create the global migration helper instance."""
    global _migration_helper
    if _migration_helper is None:
        _migration_helper = PeeweeMigrationHelper()
    return _migration_helper


def register_default_migrations():
    """Register the default migrations for anime1-desktop."""
    helper = get_migration_helper()

    # Migration 1: Create initial tables (favorites and cover_cache)
    helper.register_migration(
        version=1,
        description="Create initial tables (favorites, cover_cache)",
        migrate_fn=lambda m: None  # Tables are created via BaseModel.Meta.table_settings
    )

    # Migration 2: Add bangumi_info column to cover_cache table
    helper.register_migration(
        version=2,
        description="Add bangumi_info column to cover_cache",
        migrate_fn=lambda db: db.execute_sql(
            "ALTER TABLE cover_cache ADD COLUMN bangumi_info TEXT"
        )
    )


def run_migrations():
    """Run all pending migrations."""
    register_default_migrations()
    helper = get_migration_helper()
    helper.apply_migrations()
