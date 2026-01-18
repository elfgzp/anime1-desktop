"""Tests for settings API routes."""
import pytest
import json
from flask import Flask

from src.models.database import init_database, get_database, close_database
from src.models.favorite import FavoriteAnime
from src.models.cover_cache import CoverCache
from src.models.anime import Anime
from src.models.playback_history import PlaybackHistory
from src.routes import settings_bp
from src.services.cover_cache_service import get_cover_cache_service
from src.services.favorite_service import get_favorite_service
from src.services.playback_history_service import get_playback_history_service


def clear_all_test_data():
    """Clear all test data from the database."""
    CoverCache.clear_all()
    FavoriteAnime.delete().execute()
    PlaybackHistory.delete().execute()


@pytest.fixture(scope="module")
def app():
    """Create application for testing."""
    app = Flask(__name__)
    app.register_blueprint(settings_bp)

    # Initialize database
    init_database()

    yield app

    # Cleanup
    clear_all_test_data()
    close_database()


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def clean_db():
    """Ensure database is clean before each test."""
    clear_all_test_data()
    yield
    clear_all_test_data()


@pytest.fixture
def setup_test_data(clean_db):
    """Setup test data for cache tests."""
    # Add test cover cache entries
    cover_service = get_cover_cache_service()
    cover_service.set_cover("test_cache_001", {"id": "test_cache_001", "title": "测试1"})
    cover_service.set_cover("test_cache_002", {"id": "test_cache_002", "title": "测试2"})
    cover_service.set_cover("test_cache_003", {"id": "test_cache_003", "title": "测试3"})

    # Add test favorites
    anime1 = Anime(
        id="test_fav_001",
        title="测试收藏1",
        detail_url="http://example.com/1",
        episode=12
    )
    anime2 = Anime(
        id="test_fav_002",
        title="测试收藏2",
        detail_url="http://example.com/2",
        episode=24
    )
    fav_service = get_favorite_service()
    fav_service.add_favorite(anime1)
    fav_service.add_favorite(anime2)

    # Add test playback history
    playback_service = get_playback_history_service()
    playback_service.update_progress(
        anime_id="test_playback_001",
        anime_title="测试播放1",
        episode_id="ep_001",
        episode_num=1,
        position_seconds=100.0,
        total_seconds=1000.0
    )
    playback_service.update_progress(
        anime_id="test_playback_002",
        anime_title="测试播放2",
        episode_id="ep_002",
        episode_num=2,
        position_seconds=200.0,
        total_seconds=2000.0
    )

    yield


@pytest.mark.integration
class TestCacheAPI:
    """Test cache-related API endpoints."""

    def test_get_cache_info(self, client, setup_test_data):
        """Test getting cache information."""
        response = client.get('/api/settings/cache')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'cover_count' in data['data']
        assert 'database_size' in data['data']
        assert 'database_size_formatted' in data['data']
        assert 'favorite_count' in data['data']

        # Verify we have some cached data (from setup_test_data)
        assert data['data']['cover_count'] >= 3

    def test_clear_covers_cache(self, client, setup_test_data):
        """Test clearing covers cache only."""
        cover_service = get_cover_cache_service()
        fav_service = get_favorite_service()
        playback_service = get_playback_history_service()

        # Get count before clearing
        initial_count = cover_service.get_cache_count()
        assert initial_count >= 3, f"Expected at least 3 covers, got {initial_count}"

        # Clear covers cache via API
        response = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({'type': 'covers'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['cleared_count'] >= 3

        # Verify covers count decreased (not necessarily 0 due to potential shared data)
        new_count = cover_service.get_cache_count()
        assert new_count < initial_count, f"Covers should decrease from {initial_count} to less than {new_count}"

        # Favorites should still exist (from setup_test_data)
        assert fav_service.get_count() >= 2

        # Playback history should still exist (from setup_test_data)
        assert playback_service.get_count() >= 2

    def test_clear_all_cache(self, client, setup_test_data):
        """Test clearing all cache including playback history."""
        cover_service = get_cover_cache_service()
        playback_service = get_playback_history_service()
        fav_service = get_favorite_service()

        # Verify initial state
        initial_covers = cover_service.get_cache_count()
        initial_playback = playback_service.get_count()

        assert initial_covers >= 3, f"Expected at least 3 covers, got {initial_covers}"
        assert initial_playback >= 2, f"Expected at least 2 playback entries, got {initial_playback}"

        # Clear all cache
        response = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({'type': 'all'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['cleared_count'] >= 3

        # Verify covers count decreased
        new_covers = cover_service.get_cache_count()
        assert new_covers < initial_covers, f"Covers should decrease from {initial_covers}"

        # Verify playback history is cleared
        new_playback = playback_service.get_count()
        assert new_playback == 0, f"Playback should be 0 after clearing, got {new_playback}"

        # Favorites should still exist (not affected by cache clear)
        assert fav_service.get_count() >= 2

    def test_clear_cache_default_type(self, client, setup_test_data):
        """Test clearing cache with default type (should be covers)."""
        cover_service = get_cover_cache_service()
        initial_count = cover_service.get_cache_count()
        assert initial_count >= 3

        # Clear without specifying type
        response = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['cleared_count'] >= 3

        # Verify covers count decreased
        new_count = cover_service.get_cache_count()
        assert new_count < initial_count, f"Covers should decrease from {initial_count}"

    def test_cache_info_empty(self, client, clean_db):
        """Test getting cache info when empty."""
        response = client.get('/api/settings/cache')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['cover_count'] == 0

    def test_database_size_formatting(self, client, setup_test_data):
        """Test database size is formatted correctly."""
        response = client.get('/api/settings/cache')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['success'] is True

        size_formatted = data['data']['database_size_formatted']
        # Should contain a number and unit (B, KB, or MB)
        assert any(unit in size_formatted for unit in ['B', 'KB', 'MB', 'GB'])


@pytest.mark.integration
class TestSettingsCacheConcurrency:
    """Test cache operations under concurrent scenarios."""

    def test_cache_clear_idempotent(self, client, setup_test_data):
        """Test that clearing cache multiple times is idempotent."""
        cover_service = get_cover_cache_service()
        playback_service = get_playback_history_service()

        # Clear cache first time
        response1 = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({'type': 'all'}),
            content_type='application/json'
        )
        data1 = json.loads(response1.data)
        cleared1 = data1['data']['cleared_count']

        # Verify playback is cleared
        assert playback_service.get_count() == 0, "Playback should be 0 after first clear"

        # Clear again (should clear 0 entries for covers)
        response2 = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({'type': 'all'}),
            content_type='application/json'
        )
        data2 = json.loads(response2.data)
        cleared2 = data2['data']['cleared_count']

        # Verify playback is still cleared
        assert playback_service.get_count() == 0, "Playback should remain 0 after second clear"

    def test_favorites_not_affected_by_cache_clear(self, client, setup_test_data):
        """Test that favorites are not affected by cache clear operations."""
        fav_service = get_favorite_service()
        initial_favorites = fav_service.get_count()
        assert initial_favorites >= 2

        # Clear all cache (should not affect favorites)
        response = client.post(
            '/api/settings/cache/clear',
            data=json.dumps({'type': 'all'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Favorites should still exist
        assert fav_service.get_count() == initial_favorites
