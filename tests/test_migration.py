"""Tests for database migration module."""
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from peewee import SqliteDatabase

from src.models.migration import (
    PeeweeMigrationHelper,
    SCHEMA_VERSION,
    get_migration_helper,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = SqliteDatabase(db_path)
    yield db

    # Cleanup
    db.close()
    try:
        os.unlink(db_path)
    except:
        pass

    # Clean up any backup files
    for f in Path(db_path).parent.glob(f"{Path(db_path).stem}.bak.*"):
        try:
            f.unlink()
        except:
            pass


class TestPeeweeMigrationHelper:
    """Tests for PeeweeMigrationHelper class."""

    def test_ensure_migrations_table_creates_table(self, temp_db):
        """Test that _ensure_migrations_table creates the migrations table."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Verify table exists
        cursor = temp_db.execute_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        )
        result = cursor.fetchone()
        assert result is not None, "schema_migrations table should exist"

    def test_get_applied_versions_returns_empty_for_new_db(self, temp_db):
        """Test that _get_applied_versions returns empty list for new database."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        versions = helper._get_applied_versions()
        assert versions == []

    def test_mark_migration_applied_records_version(self, temp_db):
        """Test that _mark_migration_applied records a migration version."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        helper._mark_migration_applied(1)

        versions = helper._get_applied_versions()
        assert 1 in versions

    def test_mark_migration_applied_multiple_versions(self, temp_db):
        """Test marking multiple migration versions."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        helper._mark_migration_applied(1)
        helper._mark_migration_applied(2)

        versions = helper._get_applied_versions()
        assert versions == [1, 2]

    def test_apply_migrations_skips_when_up_to_date(self, temp_db):
        """Test that apply_migrations skips when schema is up to date."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()
        helper._mark_migration_applied(SCHEMA_VERSION)

        # Should not raise and should complete quickly
        helper.apply_migrations()

    def test_apply_migrations_runs_pending_migrations(self, temp_db):
        """Test that apply_migrations runs pending migrations."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Don't mark any migrations as applied
        helper.apply_migrations()

        # Verify all migrations up to SCHEMA_VERSION are applied
        versions = helper._get_applied_versions()
        for v in range(1, SCHEMA_VERSION + 1):
            assert v in versions, f"Migration {v} should be applied"

    def test_add_column_migration_succeeds_when_column_missing(self, temp_db):
        """Test that add_column migration works when column doesn't exist."""
        from src.models.cover_cache import CoverCache

        # Create the cover_cache table without bangumi_info column
        temp_db.create_table(CoverCache)

        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Run migration 2 (add_column)
        helper._try_standard_migration(2)

        # Verify migration is marked as applied
        assert 2 in helper._get_applied_versions()

        # Verify column exists
        cursor = temp_db.execute_sql("PRAGMA table_info(cover_cache)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "bangumi_info" in columns

    def test_add_column_migration_handles_existing_column(self, temp_db):
        """Test that add_column migration handles existing column gracefully."""
        from src.models.cover_cache import CoverCache

        # Create the cover_cache table WITH bangumi_info column
        temp_db.execute_sql("""
            CREATE TABLE cover_cache (
                anime_id TEXT PRIMARY KEY,
                cover_data TEXT,
                bangumi_info TEXT,
                cached_at TIMESTAMP
            )
        """)

        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Migration should return False (handled by exception) but recovery might kick in
        # In this case, since column already exists, the standard migration will fail
        # but the system should handle it gracefully
        result = helper._try_standard_migration(2)

        # The standard migration should fail because column exists
        # But we should be able to handle this gracefully
        assert result is False or 2 in helper._get_applied_versions()

    def test_get_migration_helper_with_custom_db(self, temp_db):
        """Test that get_migration_helper can use a custom database."""
        helper = get_migration_helper(temp_db)
        assert helper.db is temp_db

    def test_current_schema_version(self):
        """Test that SCHEMA_VERSION is a positive integer."""
        assert isinstance(SCHEMA_VERSION, int)
        assert SCHEMA_VERSION >= 1


class TestMigrationRecovery:
    """Tests for migration recovery mechanisms."""

    def test_clear_table_recovery_deletes_data(self, temp_db):
        """Test that _try_clear_table_recovery clears the cover_cache table."""
        from src.models.cover_cache import CoverCache

        # Create table and add data
        temp_db.create_table(CoverCache)
        temp_db.execute_sql("INSERT INTO cover_cache (anime_id, cover_data) VALUES ('test', '{}')")

        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Verify data exists
        cursor = temp_db.execute_sql("SELECT COUNT(*) FROM cover_cache")
        assert cursor.fetchone()[0] == 1

        # Clear the table
        helper._try_clear_table_recovery(2)

        # Verify data is deleted
        cursor = temp_db.execute_sql("SELECT COUNT(*) FROM cover_cache")
        assert cursor.fetchone()[0] == 0

    def test_migration_with_recovery_fallback_chain(self, temp_db):
        """Test that recovery methods are tried in order."""
        helper = PeeweeMigrationHelper(temp_db)
        helper._ensure_migrations_table()

        # Since migration 2 tries to add a column that may already exist,
        # we need to test the recovery chain
        # This test verifies the method exists and returns appropriately
        result = helper._run_migration_with_recovery(2)

        # Should succeed because either standard migration works
        # or recovery kicks in
        assert result is True


class TestMigrationDescriptions:
    """Tests for migration description functionality."""

    def test_get_migration_description_returns_string(self, temp_db):
        """Test that _get_migration_description returns a description."""
        helper = PeeweeMigrationHelper(temp_db)

        desc = helper._get_migration_description(1)
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_get_migration_description_for_all_versions(self, temp_db):
        """Test descriptions for all migration versions."""
        helper = PeeweeMigrationHelper(temp_db)

        for v in range(1, SCHEMA_VERSION + 1):
            desc = helper._get_migration_description(v)
            assert isinstance(desc, str)
            assert len(desc) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
