"""Video proxy routes for streaming anime content."""
import json
import logging
import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, Response, jsonify, request, after_this_request

from src.config import ANIME1_API_URL, ANIME1_BASE_URL

logger = logging.getLogger(__name__)

proxy_bp = Blueprint("proxy", __name__, url_prefix="/proxy")

# Static resources to cache
STATIC_RESOURCES = {
    "videojs.css": "https://sta.anicdn.com/videojs.css",
    "videojs.bundle.js": "https://sta.anicdn.com/videojs.bundle.js?ver=8",
}

# Video API endpoint
VIDEO_API_URL = "https://v.anime1.me/api"


def _extract_api_params(html: str) -> Optional[dict]:
    """Extract video API parameters from episode page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    video_elem = soup.find("video", {"data-apireq": True})
    if not video_elem:
        return None

    data_apireq = urllib.parse.unquote(video_elem.get("data-apireq", "{}"))
    try:
        return json.loads(data_apireq)
    except json.JSONDecodeError:
        return None


def _parse_cookies(headers: dict) -> dict:
    """Parse cookies from Set-Cookie header."""
    cookies = {}
    set_cookie = headers.get("set-cookie", "")
    if set_cookie:
        for cookie_part in set_cookie.replace("\n", ",").split(","):
            cookie_part = cookie_part.strip()
            if "=" in cookie_part:
                name, value = cookie_part.split("=", 1)
                name = name.strip()
                value = value.strip().split(";")[0]
                cookies[name] = value

    # Also check all headers
    for header_name, header_value in headers.items():
        if header_name.lower() == "set-cookie":
            for cookie_part in header_value.replace("\n", ",").split(","):
                cookie_part = cookie_part.strip()
                if "=" in cookie_part:
                    name, value = cookie_part.split("=", 1)
                    name = name.strip()
                    value = value.strip().split(";")[0]
                    if name not in cookies:
                        cookies[name] = value

    return cookies


def _call_video_api(params: dict, session: requests.Session) -> tuple:
    """Call anime1.me video API and return video URL and cookies."""
    post_data = {
        "c": params["c"],
        "e": params["e"],
        "t": params["t"],
        "p": params["p"],
        "s": params["s"],
    }
    encoded_data = urllib.parse.urlencode({"d": json.dumps(post_data)})

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": ANIME1_BASE_URL,
        "Origin": ANIME1_BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    api_response = session.post(
        VIDEO_API_URL,
        data=encoded_data,
        headers=headers,
        timeout=10,
        allow_redirects=False,
    )

    cookies = _parse_cookies(api_response.headers)
    return api_response.json(), cookies


def _get_video_url_from_response(data: dict) -> Optional[str]:
    """Extract video URL from API response."""
    # New format: {"s": [{"src": "//host/path/file.mp4", "type": "video/mp4"}]}
    video_sources = data.get("s", [])
    if video_sources and len(video_sources) > 0:
        src = video_sources[0].get("src", "")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            return src

    # Old format fallback
    if data.get("success") and data.get("file"):
        return data["file"]
    if data.get("success") and data.get("stream"):
        return data["stream"]

    return None


@proxy_bp.route("/episode-api")
def proxy_episode_api():
    """Get video info from anime1.me episode page.

    Query params:
        url: The anime1.me episode URL

    Returns:
        JSON with video URL and cookies needed for streaming
    """
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        api_params = _extract_api_params(response.text)
        if not api_params:
            return jsonify({"error": "Video player not found"}), 404

        params = {
            "c": api_params.get("c", ""),
            "e": api_params.get("e", ""),
            "t": api_params.get("t", ""),
            "p": api_params.get("p", 0),
            "s": api_params.get("s", ""),
        }

        if not all([params["c"], params["e"], params["t"], params["s"]]):
            return jsonify({"error": "Incomplete video API params"}), 400

        # Call API
        session = requests.Session()
        data, cookies = _call_video_api(params, session)

        video_url = _get_video_url_from_response(data)
        if video_url:
            return jsonify({"url": video_url, "cookies": cookies})

        return jsonify({"error": data.get("error", "Unknown error")}), 400

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/video-url")
def proxy_video_url():
    """Get video URL with fresh signature (for JavaScript to use)."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
        }
        session = requests.Session()
        page_response = session.get(target_url, headers=headers, timeout=10)
        page_response.raise_for_status()

        api_params = _extract_api_params(page_response.text)
        if not api_params:
            return jsonify({"error": "Video player not found"}), 404

        params = {
            "c": api_params.get("c", ""),
            "e": api_params.get("e", ""),
            "t": api_params.get("t", ""),
            "p": api_params.get("p", 0),
            "s": api_params.get("s", ""),
        }

        if not all([params["c"], params["e"], params["t"], params["s"]]):
            return jsonify({"error": "Incomplete video API params"}), 400

        data, _ = _call_video_api(params, session)
        video_url = _get_video_url_from_response(data)

        if video_url:
            return jsonify({"url": video_url})

        return jsonify({"error": data.get("error", "Unknown error")}), 400

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/video-stream", methods=["GET", "POST"])
def proxy_video_stream():
    """Proxy the video stream with CORS support.

    GET/POST params:
        url: Video URL to proxy
        cookies: Optional JSON string of cookies to use

    Returns:
        Video stream with proper CORS headers
    """
    # Check for url parameter
    video_url = request.args.get("url") or request.form.get("url")

    if video_url:
        # Parse cookies
        cookies = {}
        cookies_param = request.args.get("cookies") or request.form.get("cookies")
        if cookies_param:
            try:
                cookies = json.loads(cookies_param)
            except json.JSONDecodeError:
                pass

        # Get range header for seeking
        range_header = request.headers.get("Range")
        range_header_forward = {}
        if range_header:
            range_header_forward["Range"] = range_header

        try:
            video_response = requests.get(
                video_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": ANIME1_BASE_URL,
                    **range_header_forward,
                },
                cookies=cookies if cookies else None,
                timeout=30,
                stream=True,
            )

            response_headers = {
                "Content-Type": video_response.headers.get("Content-Type", "video/mp4"),
                "Accept-Ranges": "bytes",
            }

            if video_response.headers.get("Content-Range"):
                response_headers["Content-Range"] = video_response.headers.get("Content-Range")
            if video_response.headers.get("Content-Length"):
                response_headers["Content-Length"] = video_response.headers.get("Content-Length")

            @after_this_request
            def add_cors_headers(response):
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Range"
                return response

            return Response(
                video_response.iter_content(chunk_size=8192),
                status=video_response.status_code,
                headers=response_headers,
            )

        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    # POST with c,e,t,p,s parameters
    params = {
        "c": request.form.get("c", ""),
        "e": request.form.get("e", ""),
        "t": request.form.get("t", ""),
        "p": request.form.get("p", "0"),
        "s": request.form.get("s", ""),
    }

    if not all([params["c"], params["e"], params["t"], params["s"]]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        session = requests.Session()
        data, cookies = _call_video_api(params, session)

        video_url = _get_video_url_from_response(data)
        if not video_url:
            if data.get("success") is False:
                return jsonify({"error": data.get("error", "API returned error")}), 400
            return jsonify({"error": "No video sources found in API response", "raw": data}), 400

        # Request video with cookies
        video_response = session.get(
            video_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": ANIME1_BASE_URL,
            },
            cookies=cookies,
            timeout=30,
            stream=True,
        )

        @after_this_request
        def add_cookies(response):
            for name, value in cookies.items():
                response.headers[f"Set-Cookie_{name}"] = f"{name}={value}; Path=/"
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        return Response(
            video_response.iter_content(chunk_size=8192),
            status=video_response.status_code,
            headers={
                "Content-Type": video_response.headers.get("Content-Type", "video/mp4"),
                "Accept-Ranges": "bytes",
            },
        )

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/player")
def proxy_player():
    """Proxy anime1.me player page with modified video player."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        video_elem = soup.find("video", {"data-apireq": True})

        api_params = {}
        if video_elem:
            data_apireq = urllib.parse.unquote(video_elem.get("data-apireq", "{}"))
            try:
                api_params = json.loads(data_apireq)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing API params: {e}")

        video_url = ""
        if api_params:
            params = {
                "c": api_params.get("c", ""),
                "e": api_params.get("e", ""),
                "t": api_params.get("t", ""),
                "p": api_params.get("p", 0),
                "s": api_params.get("s", ""),
            }
            video_url = f"/proxy/video?{urllib.parse.urlencode(params)}"

        poster = video_elem.get("poster", "") if video_elem else ""

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>播放器</title>
    <link href="//sta.anicdn.com/videojs.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
        .player-wrapper {{ width: 100%; height: 100%; display: flex; flex-direction: column; }}
        .video-container {{ flex: 1; position: relative; }}
        video {{ width: 100%; height: 100%; object-fit: contain; }}
        .video-js {{ width: 100% !important; height: 100% !important; }}
    </style>
</head>
<body>
    <div class="player-wrapper">
        <div class="video-container">
            <video id="video" class="video-js vjs-big-play-centered" controls preload="none" poster="{poster}">
                <source src="{video_url}" type="application/x-mpegURL">
            </video>
        </div>
    </div>
    <script src="//code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="//sta.anicdn.com/videojs.bundle.js?ver=8" defer onload="initPlayer()"></script>
    <script>
        function initPlayer() {{
            videojs('video', {{
                controls: true, autoplay: false, preload: 'none', fluid: true
            }});
        }}
    </script>
</body>
</html>"""

        @after_this_request
        def add_headers(response):
            response.headers["X-Frame-Options"] = "ALLOWALL"
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/video")
def proxy_video():
    """Proxy video stream from anime1.me API (legacy endpoint)."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
            "Upgrade-Insecure-Requests": "1",
        }
        session = requests.Session()
        page_response = session.get(target_url, headers=headers, timeout=10)
        page_response.raise_for_status()

        api_params = _extract_api_params(page_response.text)
        if not api_params:
            return jsonify({"error": "Video player not found on page"}), 404

        params = {
            "c": api_params.get("c", ""),
            "e": api_params.get("e", ""),
            "t": api_params.get("t", ""),
            "p": api_params.get("p", 0),
            "s": api_params.get("s", ""),
        }

        if not all([params["c"], params["e"], params["t"], params["s"]]):
            return jsonify({"error": "Incomplete video API params"}), 400

        data, _ = _call_video_api(params, session)
        video_url = _get_video_url_from_response(data)

        if video_url:
            return {"url": video_url} if request.is_json else jsonify({"url": video_url})

        return jsonify({"error": data.get("error", "Unknown error")}), 400

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/full")
def proxy_full():
    """Proxy the full anime1.me page for iframe embedding."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text
        # Remove CSP meta tags and add base tag
        import re
        html = re.sub(r'<meta[^>]*content-security-policy[^>]*>', "", html, flags=re.IGNORECASE)
        html = re.sub(r"<head>", f'<head><base href="{target_url}">', html)

        @after_this_request
        def add_headers(response):
            response.headers["X-Frame-Options"] = "ALLOWALL"
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@proxy_bp.route("/embed")
def proxy_embed():
    """Proxy only the video player from anime1.me episode page."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({"error": "URL is required"}), 400

    if "anime1.me" not in target_url:
        return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": ANIME1_BASE_URL,
            "Origin": ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        video = soup.find("video")
        if not video:
            return jsonify({"error": "Video player not found"}), 404

        video_attrs = {
            "src": video.get("src", ""),
            "poster": video.get("poster", ""),
            "data-apireq": video.get("data-apireq", ""),
        }

        api_params = {}
        if video_attrs["data-apireq"]:
            try:
                data_apireq = urllib.parse.unquote(video_attrs["data-apireq"])
                api_params = json.loads(data_apireq)
            except json.JSONDecodeError:
                pass

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>播放器</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 100%; height: 100%; overflow: hidden; background: #000; }}
        .player-container {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
        video {{ width: 100%; height: 100%; object-fit: contain; background: #000; }}
    </style>
</head>
<body>
    <div class="player-container">
        <video id="video" controls preload="none" poster="{video_attrs['poster']}"></video>
    </div>
    <script>
        (function() {{
            var video = document.getElementById('video');
            var hasLoaded = false;

            function initWithParams(params) {{
                if (!params || hasLoaded) return;
                hasLoaded = true;

                var formData = new URLSearchParams();
                formData.append('c', params.c || '');
                formData.append('e', params.e || '');
                formData.append('t', params.t || '');
                formData.append('p', params.p || 0);
                formData.append('s', params.s || '');

                fetch('/proxy/video-stream', {{
                    method: 'POST',
                    headers: {{ 'Accept': 'application/json' }},
                    body: formData
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.error) throw new Error(data.error);
                    video.src = '/proxy/video-stream?url=' + encodeURIComponent(data.url) + '&cookies=' + encodeURIComponent(JSON.stringify(data.cookies));
                    video.play().catch(() => {{}});
                }})
                .catch(e => console.error(e));
            }}

            var embeddedParams = {json.dumps(api_params) if api_params else '{{}}'};
            if (embeddedParams && embeddedParams.c && embeddedParams.s) {{
                initWithParams(embeddedParams);
            }}

            document.body.addEventListener('click', () => {{
                if (!hasLoaded && embeddedParams && embeddedParams.c) {{
                    initWithParams(embeddedParams);
                }}
            }});
        }})();
    </script>
</body>
</html>"""

        @after_this_request
        def add_headers(response):
            response.headers["X-Frame-Options"] = "ALLOWALL"
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
