"""Tests for database models and services."""
import pytest

from src.models.database import init_database, get_database, close_database
from src.models.favorite import FavoriteAnime
from src.models.cover_cache import CoverCache
from src.services.cover_cache_service import get_cover_cache_service
from src.services.favorite_service import get_favorite_service
from src.services.settings_service import get_settings_service
from src.models.anime import Anime


@pytest.fixture(scope="module")
def db():
    """Initialize database for tests."""
    init_database()
    yield get_database()
    # Cleanup after tests
    CoverCache.clear_all()
    FavoriteAnime.delete().execute()
    close_database()


@pytest.fixture
def anime():
    """Create a test anime object."""
    return Anime(
        id="test_anime_001",
        title="测试动画",
        detail_url="http://example.com/anime/1",
        episode=12,
        cover_url="http://example.com/cover.jpg",
        year="2024",
        season="冬季",
        subtitle_group="字幕组"
    )


@pytest.mark.integration
class TestDatabase:
    """Test database connection and models."""

    def test_database_connection(self, db):
        """Test database connection is established."""
        assert db is not None
        assert "favorites" in db.get_tables()
        assert "cover_cache" in db.get_tables()

    def test_cover_cache_operations(self, db):
        """Test CoverCache model operations."""
        # set_cover
        test_data = {
            "id": "test_anime_001",
            "title": "测试动画",
            "cover_url": "http://example.com/cover.jpg"
        }
        assert CoverCache.set_cover("test_anime_001", test_data) is True

        # get_cover
        result = CoverCache.get_cover("test_anime_001")
        assert result is not None
        assert result["title"] == "测试动画"
        assert result["cover_url"] == "http://example.com/cover.jpg"

        # get_covers (batch)
        CoverCache.set_cover("test_anime_002", {"id": "test_anime_002", "title": "测试2"})
        results = CoverCache.get_covers(["test_anime_001", "test_anime_002"])
        assert len(results) == 2

        # delete_cover
        assert CoverCache.delete_by_id("test_anime_001") > 0
        assert CoverCache.get_cover("test_anime_001") is None

        # clear_all
        CoverCache.set_cover("test_3", {"id": "test_3"})
        count = CoverCache.clear_all()
        assert count >= 1
        assert CoverCache.get_count() == 0


@pytest.mark.integration
class TestFavoriteService:
    """Test FavoriteService operations."""

    def test_add_favorite(self, db, anime):
        """Test adding a favorite."""
        fav_service = get_favorite_service()

        # Add favorite
        assert fav_service.add_favorite(anime) is True

        # Check is_favorite
        assert fav_service.is_favorite("test_anime_001") is True

        # Duplicate add should fail
        assert fav_service.add_favorite(anime) is False

    def test_remove_favorite(self, db, anime):
        """Test removing a favorite."""
        fav_service = get_favorite_service()

        # Ensure exists
        fav_service.add_favorite(anime)

        # Remove
        assert fav_service.remove_favorite("test_anime_001") is True
        assert fav_service.is_favorite("test_anime_001") is False

    def test_get_favorites(self, db, anime):
        """Test getting all favorites."""
        fav_service = get_favorite_service()

        # Add multiple
        anime2 = Anime(
            id="test_anime_002",
            title="测试动画2",
            detail_url="http://example.com/anime/2",
            episode=24
        )
        fav_service.add_favorite(anime)
        fav_service.add_favorite(anime2)

        favorites = fav_service.get_favorites()
        assert len(favorites) >= 2

        # Cleanup
        fav_service.remove_favorite("test_anime_001")
        fav_service.remove_favorite("test_anime_002")


@pytest.mark.integration
class TestCoverCacheService:
    """Test CoverCacheService operations."""

    def test_set_and_get_cover(self, db):
        """Test setting and getting a cover."""
        service = get_cover_cache_service()

        test_data = {
            "id": "cache_test_001",
            "title": "缓存测试",
            "cover_url": "http://example.com/cover.jpg",
            "year": "2024"
        }

        assert service.set_cover("cache_test_001", test_data) is True
        result = service.get_cover("cache_test_001")
        assert result is not None
        assert result["title"] == "缓存测试"

    def test_set_covers_batch(self, db):
        """Test setting multiple covers at once."""
        service = get_cover_cache_service()

        covers = {
            "batch_1": {"id": "batch_1", "title": "批量1"},
            "batch_2": {"id": "batch_2", "title": "批量2"},
            "batch_3": {"id": "batch_3", "title": "批量3"},
        }

        count = service.set_covers(covers)
        assert count == 3

        # Verify
        result = service.get_covers(["batch_1", "batch_2", "batch_3"])
        assert len(result) == 3

    def test_cache_info(self, db):
        """Test cache statistics."""
        service = get_cover_cache_service()

        # Set some data
        service.set_cover("info_test", {"id": "info_test"})

        count = service.get_cache_count()
        assert count >= 1

        size = service.get_cache_size()
        assert size > 0

        # Cleanup
        service.clear_all()


@pytest.mark.integration
class TestSettingsService:
    """Test SettingsService operations."""

    def test_get_theme(self, db):
        """Test getting theme setting."""
        service = get_settings_service()
        theme = service.get_theme()
        assert theme in ["dark", "light", "system"]

    def test_set_theme(self, db):
        """Test setting theme."""
        service = get_settings_service()

        # Save original
        original = service.get_theme()

        # Set new theme
        assert service.set_theme("dark") is True
        assert service.get_theme() == "dark"

        assert service.set_theme("light") is True
        assert service.get_theme() == "light"

        # Restore
        service.set_theme(original)
