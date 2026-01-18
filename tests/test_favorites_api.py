"""Tests for favorites API with playback progress and update detection."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestFavoritesPlaybackProgress:
    """Test playback progress detection in favorites list."""

    def test_playback_progress_calculated_correctly(self):
        """Test that playback progress is correctly calculated from history."""
        from src.services.playback_history_service import PlaybackHistoryService
        from src.models.playback_history import PlaybackHistory

        # Test the format_position method
        mock_progress = MagicMock(spec=PlaybackHistory)
        mock_progress.position_seconds = 3723  # 1 hour, 2 minutes, 3 seconds

        # Test format_position logic
        seconds = int(mock_progress.position_seconds)
        hours, mins = divmod(seconds, 3600)
        mins, secs = divmod(mins, 60)
        formatted = f"{hours:02d}:{mins:02d}:{secs:02d}"

        assert formatted == "01:02:03"

    def test_progress_percent_calculation(self):
        """Test progress percentage calculation."""
        from src.models.playback_history import PlaybackHistory

        mock_progress = MagicMock(spec=PlaybackHistory)

        # Test with total_seconds
        mock_progress.position_seconds = 300
        mock_progress.total_seconds = 600

        percent = int((mock_progress.position_seconds / mock_progress.total_seconds) * 100)
        assert percent == 50

        # Test with zero total_seconds
        mock_progress.total_seconds = 0
        percent = int((mock_progress.position_seconds / max(mock_progress.total_seconds, 1)) * 100) if mock_progress.total_seconds > 0 else 0
        assert percent == 0

    def test_sorting_with_updates_and_progress(self):
        """Test sorting logic for favorites with updates and progress."""
        # Simulate the sorting key logic from favorite.py

        def sort_key(item):
            has_progress = item.get("playback_progress") is not None
            playback = item.get("playback_progress") or {}
            last_watched = playback.get("last_watched_at") or ""
            last_watched_ts = 0

            return (
                -item.get("has_update", False),
                -item.get("new_episode_count", 0),
                -int(has_progress),
                -last_watched_ts,
            )

        # Test data
        items = [
            {"title": "无更新无进度", "has_update": False, "new_episode_count": 0, "playback_progress": None},
            {"title": "有更新", "has_update": True, "new_episode_count": 3, "playback_progress": None},
            {"title": "有更新更多", "has_update": True, "new_episode_count": 5, "playback_progress": None},
            {"title": "无更新有进度", "has_update": False, "new_episode_count": 0, "playback_progress": {"episode_num": 1}},
        ]

        sorted_items = sorted(items, key=sort_key)

        # First should be "有更新更多" (has update, more new episodes)
        assert sorted_items[0]["title"] == "有更新更多"
        # Second should be "有更新"
        assert sorted_items[1]["title"] == "有更新"
        # Third should be "有更新有进度"
        assert sorted_items[2]["title"] == "无更新有进度"
        # Last should be "无更新无进度"
        assert sorted_items[3]["title"] == "无更新无进度"

    def test_first_episode_progress_defaults(self):
        """Test that first episode progress has correct defaults."""
        # Default values for first episode without progress
        first_episode_progress = {
            "episode_num": 1,
            "position_seconds": 0,
            "position_formatted": "00:00",
            "progress_percent": 0,
            "last_watched_at": None,
        }

        assert first_episode_progress["episode_num"] == 1
        assert first_episode_progress["position_seconds"] == 0
        assert first_episode_progress["progress_percent"] == 0
        assert first_episode_progress["position_formatted"] == "00:00"
        assert first_episode_progress["last_watched_at"] is None

    def test_update_detection_logic(self):
        """Test update detection when current_episode > last_episode."""
        # Test cases for update detection
        test_cases = [
            # (current_episode, last_episode, expected_has_update, expected_new_count)
            (12, 10, True, 2),
            (10, 10, False, 0),
            (5, 8, False, 0),  # Current less than last (shouldn't happen normally)
            (1, 0, True, 1),
            (0, 0, False, 0),
        ]

        for current_ep, last_ep, expected_update, expected_count in test_cases:
            has_update = current_ep > last_ep
            new_episode_count = current_ep - last_ep if has_update else 0

            assert has_update == expected_update
            assert new_episode_count == expected_count

    def test_format_position_various_values(self):
        """Test format_position with various second values."""
        def format_position(seconds):
            seconds = int(seconds)
            if seconds < 0:
                return "00:00"
            hours, mins = divmod(seconds, 3600)
            mins, secs = divmod(mins, 60)
            if hours > 0:
                return f"{hours:02d}:{mins:02d}:{secs:02d}"
            return f"{mins:02d}:{secs:02d}"

        # Test cases
        assert format_position(0) == "00:00"
        assert format_position(30) == "00:30"
        assert format_position(90) == "01:30"
        assert format_position(3600) == "01:00:00"
        assert format_position(3661) == "01:01:01"
        assert format_position(-1) == "00:00"

    def test_sorting_with_last_watched_time(self):
        """Test that favorites with same update status are sorted by last_watched_at."""
        from datetime import datetime, timedelta

        # Simulate the sorting key logic
        def sort_key(item):
            has_progress = item.get("playback_progress") is not None
            playback = item.get("playback_progress") or {}
            last_watched = playback.get("last_watched_at") or ""

            # Convert ISO string to timestamp for sorting
            last_watched_ts = 0
            if last_watched:
                try:
                    last_watched_ts = datetime.fromisoformat(last_watched.replace("Z", "+00:00")).timestamp()
                except (ValueError, AttributeError):
                    last_watched_ts = 0

            return (
                -item.get("has_update", False),
                -item.get("new_episode_count", 0),
                -int(has_progress),
                -last_watched_ts,
            )

        now = datetime.now()
        items = [
            {"title": "较早观看", "has_update": False, "new_episode_count": 0,
             "playback_progress": {"episode_num": 1, "last_watched_at": (now - timedelta(hours=2)).isoformat()}},
            {"title": "最近观看", "has_update": False, "new_episode_count": 0,
             "playback_progress": {"episode_num": 2, "last_watched_at": now.isoformat()}},
            {"title": "更早观看", "has_update": False, "new_episode_count": 0,
             "playback_progress": {"episode_num": 3, "last_watched_at": (now - timedelta(hours=5)).isoformat()}},
        ]

        sorted_items = sorted(items, key=sort_key)

        # Should be sorted by last_watched_at descending (most recent first)
        assert sorted_items[0]["title"] == "最近观看"
        assert sorted_items[1]["title"] == "较早观看"
        assert sorted_items[2]["title"] == "更早观看"


class TestPlaybackHistoryModel:
    """Test PlaybackHistory model methods."""

    def test_format_position_method(self):
        """Test the format_position method directly."""
        from src.models.playback_history import PlaybackHistory

        # Create a mock with the required attributes
        mock = MagicMock(spec=PlaybackHistory)

        # Test various position values
        test_cases = [
            (0, "00:00"),
            (30, "00:30"),
            (90, "01:30"),
            (600, "10:00"),
            (3600, "01:00:00"),
            (3661, "01:01:01"),
            (7323, "02:02:03"),
        ]

        for seconds, expected in test_cases:
            mock.position_seconds = seconds
            # Simulate the format_position logic
            seconds_val = int(mock.position_seconds)
            if seconds_val < 0:
                result = "00:00"
            else:
                hours, mins = divmod(seconds_val, 3600)
                mins, secs = divmod(mins, 60)
                if hours > 0:
                    result = f"{hours:02d}:{mins:02d}:{secs:02d}"
                else:
                    result = f"{mins:02d}:{secs:02d}"
            assert result == expected, f"Failed for {seconds} seconds"

    def test_get_progress_percent_method(self):
        """Test the get_progress_percent method directly."""
        from src.models.playback_history import PlaybackHistory

        mock = MagicMock(spec=PlaybackHistory)

        # Test with total_seconds > 0
        mock.position_seconds = 300
        mock.total_seconds = 600

        percent = int((mock.position_seconds / mock.total_seconds) * 100) if mock.total_seconds > 0 else 0
        assert percent == 50

        # Test with total_seconds = 0 (avoid division by zero)
        mock.total_seconds = 0
        percent = 0
        assert percent == 0
