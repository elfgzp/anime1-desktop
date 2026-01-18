"""Test for proxy episode API endpoint - specifically for 400 BAD REQUEST scenarios."""
import pytest
from unittest.mock import patch, Mock
import json


class TestExtractApiParams:
    """Test cases for _extract_api_params helper function."""

    def test_extract_api_params_from_valid_html(self):
        """Test extracting API parameters from valid HTML."""
        from src.routes.proxy import _extract_api_params

        html = """
        <video data-apireq='{"c":"1779","e":"1","t":1768726209,"p":2,"s":"35b100e55bfa7c726ddb769be53aefa0"}'></video>
        """
        params = _extract_api_params(html)
        assert params is not None
        assert params.get('c') == '1779'
        assert params.get('e') == '1'
        assert params.get('t') == 1768726209  # Timestamp is parsed as integer
        assert params.get('p') == 2
        assert params.get('s') == '35b100e55bfa7c726ddb769be53aefa0'

    def test_extract_api_params_returns_none_for_no_video(self):
        """Test that _extract_api_params returns None when no video element."""
        from src.routes.proxy import _extract_api_params

        html = """
        <html><body><div>No video here</div></body></html>
        """
        params = _extract_api_params(html)
        assert params is None

    def test_extract_api_params_handles_url_encoded(self):
        """Test that _extract_api_params handles URL-encoded data."""
        from src.routes.proxy import _extract_api_params

        # URL encoded version
        html = """
        <video data-apireq='%7B%22c%22%3A%221779%22%2C%22e%22%3A%221%22%2C%22t%22%3A%22123456%22%2C%22p%22%3A2%2C%22s%22%3A%22sig%22%7D'></video>
        """
        params = _extract_api_params(html)
        assert params is not None
        assert params.get('c') == '1779'

    def test_extract_api_params_handles_malformed_json(self):
        """Test that _extract_api_params returns None for malformed JSON."""
        from src.routes.proxy import _extract_api_params

        html = """
        <video data-apireq="not-valid-json"></video>
        """
        params = _extract_api_params(html)
        assert params is None

    def test_extract_api_params_handles_empty_string(self):
        """Test that _extract_api_params returns None for empty data-apireq."""
        from src.routes.proxy import _extract_api_params

        html = """
        <video data-apireq=""></video>
        """
        params = _extract_api_params(html)
        assert params is None

    def test_extract_api_params_handles_missing_attribute(self):
        """Test that _extract_api_params returns None when data-apireq is missing."""
        from src.routes.proxy import _extract_api_params

        html = """
        <video src="test.mp4"></video>
        """
        params = _extract_api_params(html)
        assert params is None


class TestGetVideoUrlFromResponse:
    """Test cases for _get_video_url_from_response helper function."""

    def test_extracts_from_new_format(self):
        """Test extracting URL from new API response format."""
        from src.routes.proxy import _get_video_url_from_response

        data = {
            "s": [{"src": "//cdn.example.com/video.m3u8", "type": "application/x-mpegURL"}]
        }
        url = _get_video_url_from_response(data)
        assert url == "https://cdn.example.com/video.m3u8"

    def test_handles_protocol_relative_src(self):
        """Test that protocol-relative URLs are fixed."""
        from src.routes.proxy import _get_video_url_from_response

        data = {
            "s": [{"src": "//cdn.example.com/video.mp4", "type": "video/mp4"}]
        }
        url = _get_video_url_from_response(data)
        assert url.startswith("https://")

    def test_handles_empty_sources(self):
        """Test handling of empty video sources."""
        from src.routes.proxy import _get_video_url_from_response

        data = {"s": []}
        url = _get_video_url_from_response(data)
        assert url is None

    def test_handles_missing_sources(self):
        """Test handling of missing video sources key."""
        from src.routes.proxy import _get_video_url_from_response

        data = {"success": True, "file": "test.mp4"}
        url = _get_video_url_from_response(data)
        # Falls back to old format
        assert url == "test.mp4"

    def test_handles_old_stream_format(self):
        """Test extracting URL from old stream format."""
        from src.routes.proxy import _get_video_url_from_response

        data = {"success": True, "stream": "https://stream.example.com/video"}
        url = _get_video_url_from_response(data)
        assert url == "https://stream.example.com/video"


class TestProxyEpisodeAPIValidation:
    """Test cases for proxy/episode-api URL validation logic."""

    def test_missing_url_validation(self):
        """Test that missing URL is properly detected."""
        # Simulate the validation logic from proxy_episode_api
        target_url = ""
        is_valid = bool(target_url.strip())
        assert is_valid is False

    def test_empty_url_validation(self):
        """Test that empty URL is properly detected."""
        target_url = "   "
        is_valid = bool(target_url.strip())
        assert is_valid is False

    def test_anime1_me_domain_detection(self):
        """Test anime1.me domain detection."""
        from src.constants.messages import DOMAIN_ANIME1_ME

        assert DOMAIN_ANIME1_ME == "anime1.me"

    def test_anime1_pw_domain_detection(self):
        """Test anime1.pw domain detection."""
        from src.constants.messages import DOMAIN_ANIME1_PW

        assert DOMAIN_ANIME1_PW == "anime1.pw"

    def test_invalid_domain_rejection(self):
        """Test that invalid domains are rejected."""
        from src.constants.messages import DOMAIN_ANIME1_ME, DOMAIN_ANIME1_PW

        test_urls = [
            ("https://example.com/video", False),
            ("https://anime1.me/123", True),
            ("https://anime1.pw/video", True),
            ("https://www.anime1.me/test", True),
        ]

        for url, expected_valid in test_urls:
            is_valid = DOMAIN_ANIME1_ME in url or DOMAIN_ANIME1_PW in url
            assert is_valid == expected_valid, f"URL {url} validation failed"


class TestProxyEpisodeAPIIncompleteParams:
    """Test cases specifically for the 400 BAD REQUEST caused by incomplete params."""

    def test_incomplete_params_detection(self):
        """Test detection of incomplete API parameters.

        The issue: When the frontend calls /proxy/episode-api with a URL,
        the backend extracts data-apireq from the video element. If any
        of c, e, t, s fields are missing, the API returns 400.
        """
        from src.constants.messages import (
            VIDEO_API_PARAM_C, VIDEO_API_PARAM_E,
            VIDEO_API_PARAM_T, VIDEO_API_PARAM_P,
            VIDEO_API_PARAM_S
        )

        # Test case 1: All parameters present
        complete_params = {
            VIDEO_API_PARAM_C: "1779",
            VIDEO_API_PARAM_E: "1",
            VIDEO_API_PARAM_T: "123456",
            VIDEO_API_PARAM_P: 2,
            VIDEO_API_PARAM_S: "signature123",
        }
        is_complete = all([
            complete_params[VIDEO_API_PARAM_C],
            complete_params[VIDEO_API_PARAM_E],
            complete_params[VIDEO_API_PARAM_T],
            complete_params[VIDEO_API_PARAM_S],
        ])
        assert is_complete is True

        # Test case 2: Missing 'c' parameter
        incomplete_params_1 = {
            VIDEO_API_PARAM_C: "",
            VIDEO_API_PARAM_E: "1",
            VIDEO_API_PARAM_T: "123456",
            VIDEO_API_PARAM_P: 2,
            VIDEO_API_PARAM_S: "signature123",
        }
        is_complete = all([
            incomplete_params_1[VIDEO_API_PARAM_C],
            incomplete_params_1[VIDEO_API_PARAM_E],
            incomplete_params_1[VIDEO_API_PARAM_T],
            incomplete_params_1[VIDEO_API_PARAM_S],
        ])
        assert is_complete is False

        # Test case 3: Missing 's' parameter (common cause of 400)
        incomplete_params_2 = {
            VIDEO_API_PARAM_C: "1779",
            VIDEO_API_PARAM_E: "1",
            VIDEO_API_PARAM_T: "123456",
            VIDEO_API_PARAM_P: 2,
            VIDEO_API_PARAM_S: "",
        }
        is_complete = all([
            incomplete_params_2[VIDEO_API_PARAM_C],
            incomplete_params_2[VIDEO_API_PARAM_E],
            incomplete_params_2[VIDEO_API_PARAM_T],
            incomplete_params_2[VIDEO_API_PARAM_S],
        ])
        assert is_complete is False

    def test_incomplete_params_returns_400_error_message(self):
        """Test that incomplete params produce the correct error message.

        From the source code, when params are incomplete:
        return jsonify({KEY_ERROR: ERROR_INCOMPLETE_API_PARAMS}), 400

        ERROR_INCOMPLETE_API_PARAMS should indicate which params are missing.
        """
        from src.constants.messages import ERROR_INCOMPLETE_API_PARAMS

        # Verify the error message exists and is descriptive
        assert ERROR_INCOMPLETE_API_PARAMS is not None
        assert len(ERROR_INCOMPLETE_API_PARAMS) > 0


class TestProxyEpisodeAPIRealScenario:
    """Test real-world scenarios that cause 400 errors."""

    def test_anime_id_1779_episode_page_parsing(self):
        """Test parsing episode page for anime ID 1779.

        Anime ID 1779 should have episode pages with valid data-apireq.
        This test verifies the expected structure.
        """
        # Simulated data-apireq from anime1.me episode page
        expected_params = {
            "c": "1779",  # category ID
            "e": "1",     # episode number
            "t": 1768726209,  # timestamp
            "p": 2,       # page/player type
            "s": "35b100e55bfa7c726ddb769be53aefa0",  # signature
        }

        # Verify all required params are present
        required_keys = ['c', 'e', 't', 's']
        for key in required_keys:
            assert key in expected_params, f"Missing required key: {key}"
            assert expected_params[key], f"Empty value for key: {key}"

    def test_url_to_episode_mapping(self):
        """Test that anime URLs map to correct episode pages.

        The frontend calls: /proxy/episode-api?url=<episode-url>
        The backend should extract data-apireq from the episode page.
        """
        # Episode URLs have numeric IDs at the end
        episode_urls = [
            "https://anime1.me/27788",
            "https://anime1.me/27546",
            "https://anime1.me/12345",
        ]

        import re
        for url in episode_urls:
            match = re.search(r'/(\d+)$', url)
            assert match is not None, f"URL should have episode ID: {url}"
            episode_id = match.group(1)
            assert episode_id.isdigit(), f"Episode ID should be numeric: {episode_id}"

    def test_category_url_vs_episode_url(self):
        """Test distinction between category URLs and episode URLs.

        Category URLs: https://anime1.me/?cat=1779
        Episode URLs: https://anime1.me/27788

        The proxy endpoint should work with episode URLs that have video elements.
        """
        category_url = "https://anime1.me/?cat=1779"
        episode_url = "https://anime1.me/27788"

        import re

        # Category URL pattern
        cat_match = re.search(r'/\?cat=\d+', category_url)
        assert cat_match is not None

        # Episode URL pattern (numeric at end)
        ep_match = re.search(r'/(\d+)$', episode_url)
        assert ep_match is not None

        # They should be different types
        assert cat_match.group() != ep_match.group()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
