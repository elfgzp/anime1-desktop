"""Tests for playback history model and service."""
import pytest
import os
import tempfile
import shutil
from datetime import datetime
from peewee import SqliteDatabase

from src.models.database import init_database, get_database, close_database, BaseModel
from src.models.playback_history import PlaybackHistory
from src.services.playback_history_service import PlaybackHistoryService, get_playback_history_service


@pytest.fixture(scope="module")
def db():
    """Initialize database for tests."""
    init_database()
    yield get_database()
    # Cleanup after tests
    PlaybackHistory.delete().execute()
    close_database()


@pytest.fixture
def history_service(db):
    """Create a fresh history service for each test."""
    PlaybackHistory.delete().execute()
    return PlaybackHistoryService()


@pytest.mark.integration
class TestPlaybackHistoryModel:
    """Test PlaybackHistory model operations."""

    def test_create_history_entry(self, history_service):
        """Test creating a playback history entry."""
        success, entry = history_service.update_progress(
            anime_id="test_anime_001",
            anime_title="测试动画",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=120.5,
            total_seconds=1440.0,
            cover_url="http://example.com/cover.jpg"
        )

        assert success is True
        assert entry is not None
        assert entry.anime_id == "test_anime_001"
        assert entry.anime_title == "测试动画"
        assert entry.episode_id == "ep_001"
        assert entry.episode_num == 1
        assert entry.position_seconds == 120.5
        assert entry.total_seconds == 1440.0

    def test_update_existing_entry(self, history_service):
        """Test updating an existing playback history entry."""
        # First create
        history_service.update_progress(
            anime_id="test_anime_001",
            anime_title="测试动画",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=120.5,
            total_seconds=1440.0
        )

        # Then update
        success, entry = history_service.update_progress(
            anime_id="test_anime_001",
            anime_title="测试动画",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=300.0,
            total_seconds=1440.0
        )

        assert success is True
        assert entry.position_seconds == 300.0

    def test_get_episode_progress(self, history_service):
        """Test getting progress for a specific episode."""
        # Create entry
        history_service.update_progress(
            anime_id="test_anime_002",
            anime_title="测试动画2",
            episode_id="ep_005",
            episode_num=5,
            position_seconds=600.0,
            total_seconds=1200.0
        )

        # Get progress
        entry = history_service.get_episode_progress("test_anime_002", "ep_005")

        assert entry is not None
        assert entry.position_seconds == 600.0
        assert entry.episode_num == 5

    def test_get_nonexistent_progress(self, history_service):
        """Test getting progress for nonexistent episode returns None."""
        entry = history_service.get_episode_progress("nonexistent", "ep_001")
        assert entry is None

    def test_get_history_by_anime(self, history_service):
        """Test getting all history entries for an anime."""
        # Create multiple entries
        history_service.update_progress(
            anime_id="test_anime_003",
            anime_title="测试动画3",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=100.0
        )
        history_service.update_progress(
            anime_id="test_anime_003",
            anime_title="测试动画3",
            episode_id="ep_002",
            episode_num=2,
            position_seconds=200.0
        )
        history_service.update_progress(
            anime_id="test_anime_003",
            anime_title="测试动画3",
            episode_id="ep_003",
            episode_num=3,
            position_seconds=300.0
        )

        # Get history
        entries = history_service.get_history_by_anime("test_anime_003")

        assert len(entries) == 3

    def test_get_history_list(self, history_service):
        """Test getting history list ordered by most recent."""
        # Create entries with different times
        history_service.update_progress(
            anime_id="history_test_001",
            anime_title="历史测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=100.0
        )

        entries = history_service.get_history(limit=10)
        assert len(entries) >= 1

    def test_delete_history(self, history_service):
        """Test deleting playback history."""
        # Create entry
        history_service.update_progress(
            anime_id="delete_test_001",
            anime_title="删除测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=100.0
        )

        # Verify exists
        entry = history_service.get_episode_progress("delete_test_001", "ep_001")
        assert entry is not None

        # Delete
        success = history_service.delete_history(anime_id="delete_test_001", episode_id="ep_001")
        assert success is True

        # Verify deleted
        entry = history_service.get_episode_progress("delete_test_001", "ep_001")
        assert entry is None

    def test_get_count(self, history_service):
        """Test getting history count."""
        initial_count = history_service.get_count()

        # Add entry
        history_service.update_progress(
            anime_id="count_test_001",
            anime_title="计数测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=100.0
        )

        assert history_service.get_count() == initial_count + 1

    def test_format_position(self, history_service):
        """Test position formatting."""
        # Create entry
        history_service.update_progress(
            anime_id="format_test_001",
            anime_title="格式测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=3661.0  # 1:01:01
        )

        entry = history_service.get_episode_progress("format_test_001", "ep_001")
        assert entry is not None
        assert entry.format_position() == "01:01:01"

        # Test seconds only
        entry.position_seconds = 125.0
        assert entry.format_position() == "02:05"

    def test_get_progress_percent(self, history_service):
        """Test progress percentage calculation."""
        entry = PlaybackHistory(
            id="percent_test_001",
            anime_id="percent_test",
            anime_title="百分比测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=500.0,
            total_seconds=1000.0
        )

        assert entry.get_progress_percent() == 50

        # Test with zero total
        entry.total_seconds = 0.0
        assert entry.get_progress_percent() == 0


@pytest.mark.integration
class TestPlaybackHistoryMigration:
    """Test playback history migration scenarios."""

    def test_migration_from_old_schema_with_title_url(self):
        """Test migration from old schema with title/url columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create old schema database using raw SQLite
            old_db_path = os.path.join(tmpdir, "old_db.db")

            import sqlite3
            conn = sqlite3.connect(old_db_path)
            cursor = conn.cursor()

            # Create old schema
            cursor.execute("""
                CREATE TABLE playback_history (
                    anime_id TEXT,
                    title TEXT,
                    url TEXT,
                    last_watched_at TEXT,
                    progress_seconds REAL
                )
            """)

            # Insert old data
            cursor.execute("""
                INSERT INTO playback_history
                (anime_id, title, url, last_watched_at, progress_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, ("old_anime_001", "旧动画标题", "http://example.com/cover.jpg", datetime.now().isoformat(), 300.0))

            conn.commit()
            conn.close()

            # Create migration helper and test
            from src.models.migration import PeeweeMigrationHelper

            # Close any existing database connection
            close_database()

            # Initialize new database (this will create fresh tables)
            init_database()

            # Create helper with the new database
            helper = PeeweeMigrationHelper(get_database())

            # Run migration data recovery
            from pathlib import Path
            backup_path = Path(old_db_path)

            # The helper should handle the old schema gracefully
            result = helper._migrate_data_from_backup(backup_path, target_version=3)

            # Check if migration handled the old schema
            # (It may fail silently for old schema but shouldn't crash)
            assert result is True

            close_database()

    def test_migration_from_new_schema(self):
        """Test migration from new schema preserves all fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create new schema database using raw SQLite
            old_db_path = os.path.join(tmpdir, "new_db.db")

            import sqlite3
            conn = sqlite3.connect(old_db_path)
            cursor = conn.cursor()

            # Create new schema (matching current model)
            cursor.execute("""
                CREATE TABLE playback_history (
                    id TEXT PRIMARY KEY,
                    anime_id TEXT,
                    anime_title TEXT,
                    episode_id TEXT,
                    episode_num INTEGER,
                    position_seconds REAL,
                    total_seconds REAL,
                    last_watched_at TEXT,
                    cover_url TEXT
                )
            """)

            # Insert data with new schema format
            cursor.execute("""
                INSERT INTO playback_history
                (id, anime_id, anime_title, episode_id, episode_num, position_seconds, total_seconds, last_watched_at, cover_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("new_anime_001_ep_001", "new_anime_001", "新动画标题", "ep_001", 1, 500.0, 1200.0, datetime.now().isoformat(), "http://example.com/new_cover.jpg"))

            conn.commit()
            conn.close()

            # Close any existing database connection
            close_database()

            # Initialize new database
            init_database()

            # Check if data exists in backup before migration
            conn = sqlite3.connect(old_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playback_history")
            backup_data = cursor.fetchall()
            conn.close()
            print(f"[DEBUG] Backup data count: {len(backup_data)}")
            if backup_data:
                print(f"[DEBUG] Backup data: {backup_data[0]}")

            from src.models.migration import PeeweeMigrationHelper
            helper = PeeweeMigrationHelper(get_database())

            from pathlib import Path
            backup_path = Path(old_db_path)
            result = helper._migrate_data_from_backup(backup_path, target_version=3)

            assert result is True

            # Check if data was migrated
            all_entries = list(PlaybackHistory.select())
            print(f"[DEBUG] Migrated entries count: {len(all_entries)}")
            for entry in all_entries:
                print(f"[DEBUG] Entry: id={entry.id}, anime_id={entry.anime_id}, position={entry.position_seconds}")

            # Verify data was migrated
            entry = PlaybackHistory.get_by_id("new_anime_001_ep_001")
            assert entry.anime_id == "new_anime_001"
            assert entry.anime_title == "新动画标题"
            assert entry.position_seconds == 500.0
            assert entry.cover_url == "http://example.com/new_cover.jpg"

            PlaybackHistory.delete().execute()
            close_database()


@pytest.mark.integration
class TestPlaybackHistoryPersistence:
    """Test that playback history persists across sessions."""

    def test_history_persists_in_database(self):
        """Verify history is stored in SQLite database."""
        service = get_playback_history_service()

        # Clear existing data
        PlaybackHistory.delete().execute()

        # Create entry
        service.update_progress(
            anime_id="persist_test_001",
            anime_title="持久化测试",
            episode_id="ep_001",
            episode_num=1,
            position_seconds=123.45,
            total_seconds=600.0,
            cover_url="http://example.com/cover.jpg"
        )

        # Close and reopen database
        close_database()
        init_database()

        # Get new service instance
        new_service = get_playback_history_service()

        # Verify data persists
        entry = new_service.get_episode_progress("persist_test_001", "ep_001")
        assert entry is not None
        assert entry.position_seconds == 123.45
        assert entry.total_seconds == 600.0

        # Cleanup
        PlaybackHistory.delete().execute()
        close_database()
