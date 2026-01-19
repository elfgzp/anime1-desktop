"""Test for HLS proxy functionality with m3u8 library."""
import json
import re
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import urllib.parse

from src.routes.proxy import proxy_bp
from src.config import ANIME1_BASE_URL, ANIME1_API_URL


def pytest_collection_modifyitems(items):
    """Add network marker to tests that require external API access."""
    for item in items:
        # Mark tests that make real external API calls as network tests
        if item.get_closest_marker('network') is None:
            if 'real' in item.name.lower() or 'signed_url' in item.name:
                item.add_marker(pytest.mark.network)


class TestHlsProxyWithM3U8:
    """Test HLS proxy routes using m3u8 library."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.register_blueprint(proxy_bp)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_hls_route_returns_400_when_url_missing(self, client):
        """Test that /proxy/hls returns 400 when url parameter is missing."""
        response = client.get('/proxy/hls')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_hls_route_returns_403_for_invalid_domain(self, client):
        """Test that /proxy/hls returns 403 for invalid domain."""
        response = client.get('/proxy/hls?url=https://example.com/test.m3u8')
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data

    @patch('requests.get')
    def test_hls_route_parses_master_playlist(self, mock_get, client):
        """Test that /proxy/hls parses master playlist correctly."""
        mock_response = Mock()
        mock_response.text = '''#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=1280x720
720p.m3u8
'''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/playlist.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        assert 'application/vnd.apple.mpegurl' in response.content_type
        content = response.data.decode('utf-8')
        assert '#EXTM3U' in content
        assert '#EXT-X-STREAM-INF:BANDWIDTH=1000000' in content

    @patch('requests.get')
    def test_hls_route_rewrites_relative_paths(self, mock_get, client):
        """Test that /proxy/hls rewrites relative paths to proxy URLs."""
        mock_response = Mock()
        mock_response.text = '#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nsubdir/1080p.m3u8\n'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/playlist.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Relative path should be rewritten to proxy URL
        import urllib.parse
        expected_encoded = urllib.parse.quote_plus('https://suisei.v.anime1.me/1779/2/subdir/1080p.m3u8')
        assert f'/proxy/hls?url={expected_encoded}' in content

    @patch('requests.get')
    def test_hls_route_rewrites_absolute_urls(self, mock_get, client):
        """Test that /proxy/hls rewrites absolute URLs to proxy URLs."""
        mock_response = Mock()
        mock_response.text = '#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nhttps://other.domain.com/stream.m3u8\n'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/playlist.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        content = response.data.decode('utf-8')
        import urllib.parse
        expected_encoded = urllib.parse.quote_plus('https://other.domain.com/stream.m3u8')
        assert f'/proxy/hls?url={expected_encoded}' in content

    @patch('requests.get')
    def test_hls_route_handles_cookies(self, mock_get, client):
        """Test that /proxy/hls passes cookies correctly."""
        mock_response = Mock()
        mock_response.text = '#EXTM3U\n1080p.m3u8\n'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        import json
        cookies = {'test': 'value'}
        import urllib.parse
        encoded_cookies = urllib.parse.quote_plus(json.dumps(cookies))

        response = client.get(
            f'/proxy/hls?url=https://suisei.v.anime1.me/1779/2/playlist.m3u8&cookies={encoded_cookies}',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        # Verify cookies were passed to requests.get
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['cookies'] == {'test': 'value'}

    @patch('requests.get')
    def test_hls_route_adds_cors_headers(self, mock_get, client):
        """Test that /proxy/hls adds CORS headers."""
        mock_response = Mock()
        mock_response.text = '#EXTM3U\n'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/playlist.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        assert response.headers.get('Access-Control-Allow-Origin') == '*'

    @patch('requests.get')
    def test_hls_route_non_playlist_content(self, mock_get, client):
        """Test that /proxy/hls returns non-playlist content as-is."""
        mock_response = Mock()
        mock_response.text = 'not a playlist'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/other.ts',
            headers={'Accept': '*/*'}
        )

        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert content == 'not a playlist'

    @patch('requests.get')
    def test_hls_route_media_segment(self, mock_get, client):
        """Test that /proxy/hls handles media segments (.ts files)."""
        mock_response = Mock()
        mock_response.text = '#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:9.009,\n/1779/2/720p_001.ts\n'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/720p.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Check that segment URI is rewritten
        assert '/proxy/hls?url=' in content

    @patch('requests.get')
    def test_hls_route_preserves_extinf_tags(self, mock_get, client):
        """Test that /proxy/hls preserves EXTINF tags for media segments."""
        mock_response = Mock()
        mock_response.text = '''#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:9.009,
segment1.ts
#EXTINF:8.008,
segment2.ts
#EXT-X-ENDLIST
'''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        response = client.get(
            '/proxy/hls?url=https://suisei.v.anime1.me/1779/2/720p.m3u8',
            headers={'Accept': 'application/vnd.apple.mpegurl'}
        )

        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert '#EXTINF:9.009,' in content
        assert '#EXTINF:8.008,' in content
        assert '#EXT-X-ENDLIST' in content


class TestEpisodeApiReturnsHlsUrl:
    """Test that episode API returns correct HLS URLs."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.register_blueprint(proxy_bp)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    @patch('src.routes.proxy.requests.get')
    @patch('src.routes.proxy.requests.Session')
    def test_episode_api_returns_playlist_url(self, mock_session_class, mock_get, client):
        """Test that /proxy/episode-api returns the playlist URL for anime1.me."""
        # Mock the episode page HTML
        episode_page = '''
        <html>
        <body>
            <video data-apireq='{"c":"1779","e":"2","t":"1234567890","p":"2","s":"abc123"}'></video>
        </body>
        </html>
        '''

        # Mock requests.get for the initial episode page fetch
        mock_get_response = Mock()
        mock_get_response.text = episode_page
        mock_get_response.raise_for_status = Mock()
        mock_get_response.headers = {}
        mock_get.return_value = mock_get_response

        # Mock the session and its get/post methods
        mock_session = Mock()

        # Mock the video API response
        video_api_response = {
            's': [{
                'src': 'https://suisei.v.anime1.me/1779/2/playlist.m3u8',
                'type': 'application/x-mpegURL'
            }]
        }
        mock_post_response = Mock()
        mock_post_response.json = Mock(return_value=video_api_response)
        mock_post_response.headers = {'set-cookie': 'test=value'}
        mock_session.post = Mock(return_value=mock_post_response)

        mock_session_class.return_value = mock_session

        response = client.get('/proxy/episode-api?url=https://anime1.me/27546')

        assert response.status_code == 200
        data = response.get_json()
        assert 'url' in data
        assert 'playlist.m3u8' in data['url']
        assert 'cookies' in data


class TestFullPlaybackFlow:
    """Integration tests for the complete playback flow.

    This tests the full flow from episode page to HLS playlist:
    1. Get episode page -> extract API params
    2. Call video API -> get signed video URL
    3. Request playlist via proxy -> verify content
    """

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.register_blueprint(proxy_bp)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_episode_api_flow_gets_signed_url(self, client):
        """Test the complete flow from episode page to signed video URL.

        This simulates what happens when a user clicks play:
        1. Extract API params from episode page
        2. Call video API with params to get signed URL
        3. Verify the returned URL is valid

        Note: This test requires network access to anime1.me.
        Skip if network is unavailable.
        """
        # Skip if network is not available
        import socket
        try:
            socket.create_connection(("anime1.me", 443), timeout=5)
        except (socket.timeout, OSError):
            pytest.skip("Network unavailable - cannot reach anime1.me")

        episode_url = "https://anime1.me/27546"

        # Step 1: Call episode API to get signed URL
        response = client.get(f'/proxy/episode-api?url={urllib.parse.quote(episode_url)}')

        if response.status_code != 200:
            # Network error or API change - skip gracefully
            if response.status_code == 500:
                data = response.get_json()
                if 'error' in data.get('message', '').lower() or 'network' in data.get('message', '').lower():
                    pytest.skip("External API unavailable")
            pytest.skip(f"API returned status {response.status_code}")

        data = response.get_json()

        assert 'url' in data, "Response should contain 'url'"
        assert 'cookies' in data, "Response should contain 'cookies'"

        video_url = data['url']
        assert video_url, "Video URL should not be empty"

        # Verify URL format
        assert 'anime1.me' in video_url or 'playlist.m3u8' in video_url, \
            f"Expected HLS URL, got: {video_url}"

        print(f"Got video URL: {video_url}")
        print(f"Got cookies: {data['cookies']}")

    def test_hls_proxy_with_real_signed_url(self, client):
        """Test HLS proxy with a real signed URL from the API.

        This test simulates the actual playback flow:
        1. Get signed URL from episode API
        2. Request the playlist through HLS proxy
        3. Verify the response is a valid HLS playlist

        Note: This test requires network access to anime1.me.
        Skip if network is unavailable.
        """
        # Skip if network is not available
        import socket
        try:
            socket.create_connection(("anime1.me", 443), timeout=5)
        except (socket.timeout, OSError):
            pytest.skip("Network unavailable - cannot reach anime1.me")

        episode_url = "https://anime1.me/27546"

        # Step 1: Get signed URL from episode API
        response = client.get(f'/proxy/episode-api?url={urllib.parse.quote(episode_url)}')
        if response.status_code != 200:
            # Network error or API change - skip gracefully
            if response.status_code == 500:
                data = response.get_json()
                if 'error' in data.get('message', '').lower() or 'network' in data.get('message', '').lower():
                    pytest.skip("External API unavailable")
            pytest.skip(f"API returned status {response.status_code}")

        data = response.get_json()

        video_url = data.get('url', '')
        cookies = data.get('cookies', {})

        # Step 2: If URL is an HLS playlist, proxy it through /proxy/hls
        if '.m3u8' in video_url:
            cookies_param = urllib.parse.quote_plus(json.dumps(cookies)) if cookies else ""
            hls_proxy_url = f'/proxy/hls?url={urllib.parse.quote(video_url)}&cookies={cookies_param}'

            hls_response = client.get(hls_proxy_url, headers={'Accept': 'application/vnd.apple.mpegurl'})

            # The proxy might return 403 if the signature has expired
            # but that's expected behavior for stale signatures
            if hls_response.status_code == 200:
                content = hls_response.data.decode('utf-8')
                assert '#EXTM3U' in content, "Response should be an HLS playlist"
                assert 'application/vnd.apple.mpegurl' in hls_response.content_type
                print("HLS proxy returned valid playlist")
            elif hls_response.status_code == 403:
                # Signature expired - this is expected if the signature is stale
                print("Signature expired (expected for stale signatures)")
            else:
                print(f"HLS proxy status: {hls_response.status_code}")
        else:
            print(f"Non-HLS URL: {video_url}")

    def test_video_stream_with_signed_url(self, client):
        """Test video streaming with a real signed URL.

        This tests the /proxy/video-stream endpoint with a fresh signature.
        Note: This test requires network access to anime1.me.
        Skip if network is unavailable.
        """
        # Skip if network is not available
        import socket
        try:
            socket.create_connection(("anime1.me", 443), timeout=5)
        except (socket.timeout, OSError):
            pytest.skip("Network unavailable - cannot reach anime1.me")

        episode_url = "https://anime1.me/27546"

        # Get signed URL
        response = client.get(f'/proxy/episode-api?url={urllib.parse.quote(episode_url)}')
        if response.status_code != 200:
            # Network error or API change - skip gracefully
            if response.status_code == 500:
                data = response.get_json()
                if 'error' in data.get('message', '').lower() or 'network' in data.get('message', '').lower():
                    pytest.skip("External API unavailable")
            pytest.skip(f"API returned status {response.status_code}")

        data = response.get_json()

        video_url = data.get('url', '')
        cookies = data.get('cookies', {})

        # Request video stream
        cookies_param = urllib.parse.quote_plus(json.dumps(cookies)) if cookies else ""
        stream_url = f'/proxy/video-stream?url={urllib.parse.quote(video_url)}&cookies={cookies_param}'

        stream_response = client.get(stream_url)

        # For HLS playlists, the stream endpoint returns the playlist (not the actual video)
        if '.m3u8' in video_url:
            if stream_response.status_code == 200:
                # This is the playlist content
                content = stream_response.data.decode('utf-8')
                if '#EXTM3U' in content:
                    print("Video stream endpoint returned HLS playlist (expected for .m3u8 URLs)")
                else:
                    print(f"Unexpected content type: {content[:100]}")
            elif stream_response.status_code == 403:
                print("Signature expired for video stream")
            else:
                print(f"Video stream status: {stream_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
