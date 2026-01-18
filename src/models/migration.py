"""Database migration helper for Peewee models.

This module provides schema version tracking and migration capabilities
with automatic recovery on failure.

Migration recovery strategy:
1. Try standard migration (peewee's add_column handles existing columns)
2. If fails: backup old DB, create new schema, migrate data from old DB
3. Last resort: clear problematic table data, keep other data intact
"""
import logging
import shutil
from datetime import datetime
from pathlib import Path

from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator

from src.models.database import get_database

logger = logging.getLogger(__name__)

# Current schema version - increment this when making schema changes
SCHEMA_VERSION = 3

# Migration history table name
MIGRATION_TABLE = "schema_migrations"


class PeeweeMigrationHelper:
    """Helper class for managing Peewee database migrations."""

    def __init__(self, db=None):
        """Initialize the migration helper."""
        self.db = db or get_database()
        self._migrator = None

    @property
    def migrator(self):
        """Get the peewee migrator instance."""
        if self._migrator is None:
            self._migrator = SqliteMigrator(self.db)
        return self._migrator

    def _ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        self.db.execute_sql(f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_applied_versions(self) -> list:
        """Get list of applied migration versions."""
        try:
            cursor = self.db.execute_sql(
                f"SELECT version FROM {MIGRATION_TABLE} ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return []

    def _mark_migration_applied(self, version: int):
        """Mark a migration as applied."""
        self.db.execute_sql(
            f"INSERT OR REPLACE INTO {MIGRATION_TABLE} (version, applied_at) VALUES (?, ?)",
            (version, datetime.now())
        )

    def apply_migrations(self):
        """Apply all pending migrations with automatic recovery on failure."""
        self._ensure_migrations_table()

        applied_versions = self._get_applied_versions()
        current_version = max(applied_versions) if applied_versions else 0

        logger.info(f"Current schema version: {current_version}, Latest: {SCHEMA_VERSION}")

        if current_version >= SCHEMA_VERSION:
            logger.info("Database schema is up to date")
            return

        # Apply migrations in order with recovery
        for version in range(current_version + 1, SCHEMA_VERSION + 1):
            if not self._run_migration_with_recovery(version):
                logger.error(f"All recovery methods failed for migration {version}")
                raise RuntimeError(f"Failed to apply migration {version}")

    def _run_migration_with_recovery(self, version: int) -> bool:
        """Run migration with automatic recovery on failure.

        Recovery strategy:
        1. Try standard migration
        2. If fails: backup DB, recreate schema, migrate data from backup
        3. Last resort: clear problematic table data

        Args:
            version: The migration version to run.

        Returns:
            True if migration succeeded, False otherwise.
        """
        # Strategy 1: Try standard migration
        logger.info(f"Applying migration {version}: {self._get_migration_description(version)}")
        if self._try_standard_migration(version):
            return True

        # Strategy 2: Backup and migrate data from old DB
        logger.warning(f"Standard migration failed, attempting data migration recovery...")
        if self._try_migrate_with_backup(version):
            return True

        # Strategy 3: Last resort - clear problematic table
        logger.warning(f"Data migration failed, attempting table recovery...")
        if self._try_clear_table_recovery(version):
            return True

        return False

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            cursor = self.db.execute_sql(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            if result and result[0]:
                return column_name in result[0]
            return False
        except Exception:
            return False

    def _try_standard_migration(self, version: int) -> bool:
        """Try standard migration using peewee's migrate()."""
        try:
            # Special check for migration 2: skip if column already exists
            if version == 2 and self._column_exists("cover_cache", "bangumi_info"):
                logger.info(f"Migration 2: bangumi_info column already exists, skipping")
                self._mark_migration_applied(version)
                return True

            with self.db.transaction():
                migrate_fn = self._get_migration_func(version)
                migrate_fn(self.migrator)
            self._mark_migration_applied(version)
            logger.info(f"Migration {version} applied successfully")
            return True
        except Exception as e:
            # Check if it's a duplicate column error - if so, mark as applied
            if "duplicate column name" in str(e).lower():
                logger.info(f"Migration {version}: column already exists, marking as applied")
                self._mark_migration_applied(version)
                return True
            logger.warning(f"Standard migration failed: {e}")
            return False

    def _try_migrate_with_backup(self, version: int) -> bool:
        """Backup DB, recreate schema, migrate data from backup.

        This preserves user data (favorites, history) while fixing schema issues.
        """
        try:
            from src.models.database import get_database_path

            db_path = get_database_path()
            if not db_path.exists():
                return False

            # Create backup path
            backup_path = db_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"Backing up database to: {backup_path}")

            # Close current connection and backup
            self.db.close()
            shutil.copy2(db_path, backup_path)

            # Reconnect
            self.db.connect()

            # Recreate tables with correct schema
            logger.info("Recreating database schema...")
            self._recreate_schema()

            # Migrate data from backup
            logger.info("Migrating data from backup...")
            if self._migrate_data_from_backup(backup_path, version):
                logger.info("Data migration successful")
                # Mark migration as applied
                for v in range(version, SCHEMA_VERSION + 1):
                    try:
                        self._mark_migration_applied(v)
                    except:
                        pass
                return True

            logger.warning("Data migration from backup failed")
            return False

        except Exception as e:
            logger.error(f"Backup migration failed: {e}")
            return False

    def _recreate_schema(self):
        """Recreate all tables with current model definitions.

        IMPORTANT: This method now preserves favorites and playback_history tables
        by backing up their data before dropping, then restoring after schema recreation.
        """
        from src.models.favorite import FavoriteAnime
        from src.models.cover_cache import CoverCache
        from src.models.playback_history import PlaybackHistory
        from datetime import datetime
        import json

        # Backup critical data before dropping tables
        favorites_backup = []
        history_backup = []

        try:
            # Backup favorites
            if FavoriteAnime.table_exists():
                for fav in FavoriteAnime.select():
                    favorites_backup.append({
                        "id": fav.id,
                        "title": fav.title,
                        "detail_url": fav.detail_url,
                        "episode": fav.episode,
                        "cover_url": fav.cover_url,
                        "year": fav.year,
                        "season": fav.season,
                        "subtitle_group": fav.subtitle_group,
                        "last_episode": fav.last_episode,
                        "added_at": fav.added_at,
                        "updated_at": fav.updated_at,
                    })
                logger.info(f"Backed up {len(favorites_backup)} favorites")
        except Exception as e:
            logger.warning(f"Failed to backup favorites: {e}")

        try:
            # Backup playback_history
            if PlaybackHistory.table_exists():
                for hist in PlaybackHistory.select():
                    history_backup.append({
                        "id": hist.id,
                        "anime_id": hist.anime_id,
                        "anime_title": hist.anime_title,
                        "episode_id": hist.episode_id,
                        "episode_num": hist.episode_num,
                        "position_seconds": hist.position_seconds,
                        "total_seconds": hist.total_seconds,
                        "last_watched_at": hist.last_watched_at,
                        "cover_url": hist.cover_url,
                    })
                logger.info(f"Backed up {len(history_backup)} history entries")
        except Exception as e:
            logger.warning(f"Failed to backup playback history: {e}")

        # Drop tables (except critical ones - we handle them separately)
        self.db.execute_sql("DROP TABLE IF EXISTS cover_cache")
        self.db.execute_sql("DROP TABLE IF EXISTS performance_trace")
        self.db.execute_sql("DROP TABLE IF EXISTS performance_stat")
        self.db.execute_sql(f"DROP TABLE IF EXISTS {MIGRATION_TABLE}")

        # Recreate tables
        self.db.create_tables([
            FavoriteAnime,
            CoverCache,
            PlaybackHistory,
        ])

        # Restore critical data
        restored_favorites = 0
        if favorites_backup:
            try:
                FavoriteAnime.insert_many(favorites_backup).on_conflict_replace().execute()
                restored_favorites = len(favorites_backup)
                logger.info(f"Restored {restored_favorites} favorites")
            except Exception as e:
                logger.error(f"Failed to restore favorites: {e}")
                # Try one by one
                for fav in favorites_backup:
                    try:
                        FavoriteAnime.get_by_id(fav["id"])
                        restored_favorites += 1
                    except:
                        try:
                            FavoriteAnime.create(**fav)
                            restored_favorites += 1
                        except:
                            pass

        restored_history = 0
        if history_backup:
            try:
                PlaybackHistory.insert_many(history_backup).on_conflict_replace().execute()
                restored_history = len(history_backup)
                logger.info(f"Restored {restored_history} history entries")
            except Exception as e:
                logger.error(f"Failed to restore playback history: {e}")
                # Try one by one
                for hist in history_backup:
                    try:
                        PlaybackHistory.get_by_id(hist["id"])
                        restored_history += 1
                    except:
                        try:
                            PlaybackHistory.create(**hist)
                            restored_history += 1
                        except:
                            pass

        # Recreate migrations table
        self._ensure_migrations_table()
        logger.info("Database schema recreated with data protection")

    def _migrate_data_from_backup(self, backup_path: Path, target_version: int = 3) -> bool:
        """Migrate data from backup database.

        This preserves user data (favorites, history) while fixing schema issues.
        Uses ORM for data insertion where possible.
        """
        import json

        # Import models for ORM operations
        from src.models.favorite import FavoriteAnime
        from src.models.cover_cache import CoverCache
        from src.models.playback_history import PlaybackHistory

        def table_exists(db: SqliteDatabase, table_name: str) -> bool:
            """Check if a table exists using raw SQL (required for PRAGMA)."""
            cursor = db.execute_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (table_name,)
            )
            return cursor.fetchone() is not None

        def get_table_columns(db: SqliteDatabase, table_name: str) -> set:
            """Get column names for a table using raw SQL (PRAGMA doesn't have ORM equivalent)."""
            cursor = db.execute_sql(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}

        try:
            # Connect to backup DB
            backup_db = SqliteDatabase(str(backup_path))

            # Migrate favorites - only if table exists
            if table_exists(backup_db, "favorite_anime"):
                try:
                    columns = get_table_columns(backup_db, "favorite_anime")
                    # Map old column names to new ones
                    column_map = {
                        "anime_id": "anime_id",
                        "title": "title",
                        "url": "url",
                        "cover_image": "cover_image",
                        "added_at": "added_at"
                    }
                    select_cols = [col for col in column_map.keys() if col in columns]
                    if select_cols:
                        cursor = backup_db.execute_sql(
                            f"SELECT {', '.join(select_cols)} FROM favorite_anime"
                        )
                        rows = list(cursor.fetchall())

                        if rows:
                            # Use ORM insert_many
                            insert_data = []
                            for row in rows:
                                item = {}
                                for i, col in enumerate(select_cols):
                                    item[column_map[col]] = row[i]
                                insert_data.append(item)

                            FavoriteAnime.insert_many(insert_data).on_conflict_replace().execute()
                            logger.info(f"Migrated {len(insert_data)} favorite entries")
                except Exception as e:
                    logger.debug(f"Could not migrate favorite data: {e}")

            # Migrate playback_history - handle both old and new schemas
            if table_exists(backup_db, "playback_history"):
                try:
                    columns = get_table_columns(backup_db, "playback_history")

                    if "episode_id" in columns:
                        # New-ish schema - use ORM directly
                        cursor = backup_db.execute_sql(
                            "SELECT id, anime_id, anime_title, episode_id, episode_num, "
                            "position_seconds, total_seconds, last_watched_at, cover_url FROM playback_history"
                        )
                        rows = list(cursor.fetchall())

                        if rows:
                            insert_data = []
                            for row in rows:
                                # Convert last_watched_at to Unix timestamp (handle ISO string or existing timestamp)
                                last_watched = row[7]
                                if isinstance(last_watched, str):
                                    # Parse ISO format string to timestamp
                                    try:
                                        from dateutil.parser import isoparse
                                        last_watched = int(isoparse(last_watched).timestamp())
                                    except ImportError:
                                        # Fallback: try to parse as simple timestamp
                                        try:
                                            last_watched = int(float(last_watched))
                                        except (ValueError, TypeError):
                                            last_watched = int(datetime.now().timestamp())

                                insert_data.append({
                                    "id": row[0],
                                    "anime_id": row[1],
                                    "anime_title": row[2],
                                    "episode_id": row[3],
                                    "episode_num": row[4],
                                    "position_seconds": row[5],
                                    "total_seconds": row[6],
                                    "last_watched_at": last_watched,
                                    "cover_url": row[8] or ""
                                })

                            PlaybackHistory.insert_many(insert_data).on_conflict_replace().execute()
                            logger.info(f"Migrated {len(insert_data)} playback history entries (new schema)")
                    else:
                        # Old schema - map columns dynamically
                        column_mapping = {
                            "anime_id": "anime_id",
                            "title": "anime_title",
                            "episode_id": "episode_id",
                            "episode_num": "episode_num",
                            "position_seconds": "position_seconds",
                            "progress_seconds": "position_seconds",
                            "total_seconds": "total_seconds",
                            "last_watched_at": "last_watched_at",
                            "cover_url": "cover_url",
                            "url": "cover_url"
                        }

                        select_cols = [col for col in column_mapping.keys() if col in columns]
                        if select_cols:
                            cursor = backup_db.execute_sql(
                                f"SELECT {', '.join(select_cols)} FROM playback_history"
                            )
                            rows = list(cursor.fetchall())

                            if rows:
                                insert_data = []
                                for row in rows:
                                    item = {"id": None, "anime_id": "", "anime_title": "", "episode_id": "",
                                           "episode_num": 0, "position_seconds": 0.0, "total_seconds": 0.0,
                                           "last_watched_at": datetime.now(), "cover_url": ""}
                                    for i, col in enumerate(select_cols):
                                        item[column_mapping[col]] = row[i] if row[i] is not None else item.get(column_mapping[col])
                                    # Generate ID if not present
                                    if item["anime_id"] and item.get("episode_id"):
                                        item["id"] = f"{item['anime_id']}_{item['episode_id']}"
                                    insert_data.append(item)

                                PlaybackHistory.insert_many(insert_data).on_conflict_replace().execute()
                                logger.info(f"Migrated {len(insert_data)} playback history entries (old schema)")
                except Exception as e:
                    logger.debug(f"Could not migrate playback_history data: {e}")

            # Migrate cover_cache - only if table exists
            if table_exists(backup_db, "cover_cache"):
                try:
                    if target_version >= 3:
                        # New schema with indexed fields
                        cursor = backup_db.execute_sql(
                            "SELECT anime_id, cover_data, bangumi_info, cached_at FROM cover_cache"
                        )
                        rows = list(cursor.fetchall())

                        if rows:
                            insert_data = []
                            for row in rows:
                                cover_data = json.loads(row[1]) if row[1] else {}
                                insert_data.append({
                                    "anime_id": row[0],
                                    "title": cover_data.get("title", ""),
                                    "year": cover_data.get("year", ""),
                                    "season": cover_data.get("season", ""),
                                    "cover_url": cover_data.get("cover_url") or "",
                                    "episode": cover_data.get("episode", 0),
                                    "cover_data": row[1] or "",
                                    "bangumi_info": row[2] or "",
                                    "cached_at": row[3],
                                    "updated_at": datetime.now()
                                })

                            CoverCache.insert_many(insert_data).on_conflict_ignore().execute()
                            logger.info(f"Migrated {len(insert_data)} cover_cache entries")
                    else:
                        # Old schema without indexed fields
                        cursor = backup_db.execute_sql(
                            "SELECT anime_id, cover_data, bangumi_info, cached_at FROM cover_cache"
                        )
                        rows = list(cursor.fetchall())

                        if rows:
                            insert_data = []
                            for row in rows:
                                insert_data.append({
                                    "anime_id": row[0],
                                    "cover_data": row[1] or "",
                                    "bangumi_info": row[2] or "",
                                    "cached_at": row[3]
                                })

                            CoverCache.insert_many(insert_data).on_conflict_ignore().execute()
                            logger.info(f"Migrated {len(insert_data)} cover_cache entries (old schema)")
                except Exception as e:
                    logger.debug(f"Could not migrate cover_cache data: {e}")

            # Create indexes for version 3+
            if target_version >= 3:
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_title ON cover_cache(title)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_year ON cover_cache(year)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_season ON cover_cache(season)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_cached_at ON cover_cache(cached_at)")

            backup_db.close()

            # Verify critical data was migrated
            self._verify_critical_data()

            logger.info("Data migrated from backup")
            return True

        except Exception as e:
            logger.error(f"Error migrating data from backup: {e}")
            return False

    def _try_clear_table_recovery(self, version: int) -> bool:
        """Last resort: clear problematic table data and retry migration.

        This preserves favorites and playback_history, but loses cover_cache data.
        """
        try:
            logger.warning("Clearing cover_cache table as last resort recovery...")

            # Backup critical data before clearing
            from src.models.favorite import FavoriteAnime
            from src.models.playback_history import PlaybackHistory

            favorites_before = FavoriteAnime.select().count() if FavoriteAnime.table_exists() else 0
            history_before = PlaybackHistory.select().count() if PlaybackHistory.table_exists() else 0

            # Clear the problematic table
            self.db.execute_sql("DELETE FROM cover_cache")

            # Retry the migration
            if self._try_standard_migration(version):
                logger.info("Migration successful after clearing cover_cache")
                # Verify critical data
                favorites_after = FavoriteAnime.select().count() if FavoriteAnime.table_exists() else 0
                history_after = PlaybackHistory.select().count() if PlaybackHistory.table_exists() else 0

                if favorites_before != favorites_after or history_before != history_after:
                    logger.warning(f"Data mismatch: favorites {favorites_before}->{favorites_after}, history {history_before}->{history_after}")
                return True

            # For version 3, try recreating the table completely
            if version >= 3:
                logger.warning("Retrying migration 3 with table recreation...")
                self.db.execute_sql("DROP TABLE IF EXISTS cover_cache")
                if self._try_standard_migration(version):
                    logger.info("Migration successful after table recreation")
                    return True

            return False

        except Exception as e:
            logger.error(f"Table recovery failed: {e}")
            return False

    def _get_migration_description(self, version: int) -> str:
        """Get description for a migration version."""
        descriptions = {
            1: "Create initial tables (favorites, cover_cache)",
            2: "Add bangumi_info column to cover_cache",
            3: "Add indexed fields (title, year, season) to cover_cache for efficient filtering",
        }
        return descriptions.get(version, f"Migration {version}")

    def _get_migration_func(self, version: int):
        """Get the migration function for a version."""
        from src.models.cover_cache import CoverCache

        # Version 3 requires recreating the table due to schema changes
        # This is handled in _try_standard_migration with special logic
        if version == 3:
            return lambda m: None  # Handled specially

        migrations = {
            1: lambda m: None,
            2: lambda m: m.add_column("cover_cache", "bangumi_info", CoverCache.bangumi_info),
        }
        return migrations.get(version, lambda m: None)

    def _try_standard_migration(self, version: int) -> bool:
        """Try standard migration using peewee's migrate()."""
        try:
            # Version 3 requires special handling - table recreation
            if version == 3:
                return self._migrate_version_3()

            # Special check for migration 2: skip if column already exists
            if version == 2 and self._column_exists("cover_cache", "bangumi_info"):
                logger.info(f"Migration 2: bangumi_info column already exists, skipping")
                self._mark_migration_applied(version)
                return True

            with self.db.transaction():
                migrate_fn = self._get_migration_func(version)
                migrate_fn(self.migrator)
            self._mark_migration_applied(version)
            logger.info(f"Migration {version} applied successfully")
            return True
        except Exception as e:
            # Check if it's a duplicate column error - if so, mark as applied
            if "duplicate column name" in str(e).lower():
                logger.info(f"Migration {version}: column already exists, marking as applied")
                self._mark_migration_applied(version)
                return True
            logger.warning(f"Standard migration failed: {e}")
            return False

    def _migrate_version_3(self) -> bool:
        """Migrate to version 3: add indexed fields to cover_cache.

        Since we're adding multiple indexed columns, we recreate the table.
        """
        import json
        from src.models.cover_cache import CoverCache

        try:
            logger.info("Migrating cover_cache to version 3 (adding indexed fields)...")

            # Backup old data first (before any schema changes)
            old_data = []
            try:
                cursor = self.db.execute_sql("SELECT anime_id, cover_data, bangumi_info, cached_at FROM cover_cache")
                for row in cursor.fetchall():
                    old_data.append({
                        "anime_id": row[0],
                        "cover_data": row[1],
                        "bangumi_info": row[2],
                        "cached_at": row[3],
                    })
                logger.info(f"Backed up {len(old_data)} rows from old cover_cache table")
            except Exception as e:
                logger.warning(f"Could not backup cover_cache data (table may not exist): {e}")
                old_data = []

            # Drop old table if exists
            self.db.execute_sql("DROP TABLE IF EXISTS cover_cache")
            logger.info("Dropped old cover_cache table")

            # Create new table with fresh schema
            try:
                # Use Peewee's create_tables on the database, not db.create_table
                from src.models.cover_cache import CoverCache
                self.db.create_tables([CoverCache])
                logger.info("Created new cover_cache table with new schema")
            except Exception as e:
                logger.error(f"Failed to create new cover_cache table: {e}")
                return False

            # Migrate old data to new schema
            from datetime import datetime
            migrated_count = 0
            for row in old_data:
                try:
                    # Extract fields from old cover_data
                    cover_data = json.loads(row["cover_data"]) if row["cover_data"] else {}
                    title = cover_data.get("title", "")
                    year = cover_data.get("year", "")
                    season = cover_data.get("season", "")
                    cover_url = cover_data.get("cover_url")
                    episode = cover_data.get("episode", 0)

                    self.db.execute_sql(
                        """INSERT INTO cover_cache
                           (anime_id, title, year, season, cover_url, episode, cover_data, bangumi_info, cached_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (row["anime_id"], title, year, season, cover_url, episode,
                         row["cover_data"], row["bangumi_info"], row["cached_at"], datetime.now())
                    )
                    migrated_count += 1
                except Exception as e:
                    logger.debug(f"Could not migrate row {row.get('anime_id', 'unknown')}: {e}")
                    continue

            logger.info(f"Migrated {migrated_count} rows to new schema")

            # Create indexes
            try:
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_title ON cover_cache(title)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_year ON cover_cache(year)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_season ON cover_cache(season)")
                self.db.execute_sql("CREATE INDEX IF NOT EXISTS idx_cover_cache_cached_at ON cover_cache(cached_at)")
                logger.info("Created indexes")
            except Exception as e:
                logger.warning(f"Failed to create some indexes: {e}")

            # Verify table exists
            try:
                self.db.execute_sql("SELECT COUNT(*) FROM cover_cache")
                logger.info("Verified cover_cache table exists")
            except Exception as e:
                logger.error(f"Verification failed - table may not exist: {e}")
                return False

            self._mark_migration_applied(3)

            # Verify critical data is intact
            self._verify_critical_data()

            logger.info("Migration 3 applied successfully")
            return True

        except Exception as e:
            logger.error(f"Migration 3 failed: {e}", exc_info=True)
            # Try to recover by recreating the table
            try:
                from src.models.cover_cache import CoverCache
                self.db.execute_sql("DROP TABLE IF EXISTS cover_cache")
                self.db.create_tables([CoverCache])
                logger.info("Recovered by recreating cover_cache table")
                self._mark_migration_applied(3)
                # Verify critical data after recovery
                self._verify_critical_data()
                return True
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
            return False

    def _verify_critical_data(self):
        """Verify that critical data (favorites, playback_history) is intact after migration."""
        from src.models.favorite import FavoriteAnime
        from src.models.playback_history import PlaybackHistory

        try:
            fav_count = FavoriteAnime.select().count()
            hist_count = PlaybackHistory.select().count()
            logger.info(f"Data verification: {fav_count} favorites, {hist_count} history entries")
        except Exception as e:
            logger.warning(f"Could not verify critical data: {e}")


# Global migration helper instance
_migration_helper = None


def get_migration_helper(db=None) -> PeeweeMigrationHelper:
    """Get or create the global migration helper instance."""
    global _migration_helper
    if db is not None:
        # If db is provided, create a new helper with that db
        return PeeweeMigrationHelper(db)
    if _migration_helper is None:
        _migration_helper = PeeweeMigrationHelper()
    return _migration_helper


def run_migrations():
    """Run all pending migrations."""
    helper = get_migration_helper()
    helper.apply_migrations()
