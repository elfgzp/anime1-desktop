"""Video proxy routes for streaming anime content."""
import json
import logging
import re
import urllib.parse
from typing import Optional

import m3u8
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, Response, jsonify, request, after_this_request

from src.config import ANIME1_API_URL, ANIME1_BASE_URL
from src.constants.messages import (
    ERROR_URL_REQUIRED,
    ERROR_INVALID_DOMAIN,
    ERROR_PLAYER_NOT_FOUND,
    ERROR_INCOMPLETE_API_PARAMS,
    ERROR_UNKNOWN_BACKEND,
    ERROR_API_ERROR,
    ERROR_NO_VIDEO_SOURCES,
    ERROR_PLAYER_NOT_FOUND_ON_PAGE,
    ERROR_MISSING_PARAMS,
    KEY_URL,
    KEY_COOKIES,
    KEY_ERROR,
    KEY_RAW,
    API_KEY_SUCCESS,
    API_KEY_FILE,
    API_KEY_STREAM,
    API_KEY_VIDEO_SOURCES,
    API_KEY_SRC,
    CORS_ALLOW_ORIGIN,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    CORS_X_FRAME_OPTIONS,
    VIDEO_API_URL,
    VIDEO_API_PARAM_C,
    VIDEO_API_PARAM_E,
    VIDEO_API_PARAM_T,
    VIDEO_API_PARAM_P,
    VIDEO_API_PARAM_S,
    DOMAIN_ANIME1_ME,
    DOMAIN_ANIME1_PW,
    HLS_DEFAULT_CODECS,
)
from src.constants.headers import (
    HEADER_USER_AGENT,
    HEADER_ACCEPT,
    HEADER_ACCEPT_LANGUAGE,
    HEADER_CONTENT_TYPE,
    HEADER_REFERER,
    HEADER_ORIGIN,
    HEADER_RANGE,
    HEADER_CONTENT_LENGTH,
    HEADER_CONTENT_RANGE,
    HEADER_CONTENT_TYPE as HEADER_CONTENT_TYPE_VALUE,
    HEADER_ACCEPT_RANGES,
    HEADER_UPGRADE_INSECURE_REQUESTS,
    HEADER_SET_COOKIE,
    HEADER_ACCESS_CONTROL_ALLOW_ORIGIN,
    HEADER_ACCESS_CONTROL_ALLOW_METHODS,
    HEADER_ACCESS_CONTROL_ALLOW_HEADERS,
    HEADER_X_FRAME_OPTIONS,
    VALUE_ACCEPT_JSON,
    VALUE_CONTENT_TYPE_FORM,
    VALUE_USER_AGENT_DEFAULT,
    VALUE_ACCEPT_LANGUAGE_ZH_TW,
    VALUE_ACCEPT_HTML,
    VALUE_ACCEPT_ALL,
    VALUE_CONTENT_TYPE_VIDEO_MP4,
    VALUE_UPGRADE_INSECURE_REQUESTS,
    VALUE_ACCEPT_APPLICATION_JSON,
    VALUE_RANGE_BYTES,
)

logger = logging.getLogger(__name__)

proxy_bp = Blueprint("proxy", __name__, url_prefix="/proxy")


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
        # Handle comma-separated Set-Cookie headers (multiple cookies in one header)
        for cookie_part in set_cookie.replace("\n", ",").split(","):
            cookie_part = cookie_part.strip()
            # Each cookie is like: "name=value; expires=...; path=...; domain=...; secure; HttpOnly"
            # Extract only name=value part - split by first "=" only
            if "=" in cookie_part:
                # Find the first "=" to get the cookie name
                first_eq_idx = cookie_part.index("=")
                name = cookie_part[:first_eq_idx].strip()
                # Get value - everything after the first "=" until first ";"
                value = cookie_part[first_eq_idx + 1:].strip()
                if ";" in value:
                    value = value.split(";")[0].strip()
                if name and value:
                    cookies[name] = value

    # Also check all headers (case-insensitive)
    for header_name, header_value in headers.items():
        if header_name.lower() == "set-cookie":
            for cookie_part in header_value.replace("\n", ",").split(","):
                cookie_part = cookie_part.strip()
                if "=" in cookie_part:
                    first_eq_idx = cookie_part.index("=")
                    name = cookie_part[:first_eq_idx].strip()
                    value = cookie_part[first_eq_idx + 1:].strip()
                    if ";" in value:
                        value = value.split(";")[0].strip()
                    if name and value and name not in cookies:
                        cookies[name] = value

    return cookies


def _call_video_api(params: dict, session: requests.Session) -> tuple:
    """Call anime1.me video API and return video URL and cookies."""
    post_data = {
        VIDEO_API_PARAM_C: params[VIDEO_API_PARAM_C],
        VIDEO_API_PARAM_E: params[VIDEO_API_PARAM_E],
        VIDEO_API_PARAM_T: params[VIDEO_API_PARAM_T],
        VIDEO_API_PARAM_P: params[VIDEO_API_PARAM_P],
        VIDEO_API_PARAM_S: params[VIDEO_API_PARAM_S],
    }
    encoded_data = urllib.parse.urlencode({"d": json.dumps(post_data)})

    headers = {
        HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
        HEADER_ACCEPT: VALUE_ACCEPT_JSON,
        HEADER_REFERER: ANIME1_BASE_URL,
        HEADER_ORIGIN: ANIME1_BASE_URL,
        HEADER_CONTENT_TYPE: VALUE_CONTENT_TYPE_FORM,
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
    video_sources = data.get(API_KEY_VIDEO_SOURCES, [])
    if video_sources and len(video_sources) > 0:
        src = video_sources[0].get(API_KEY_SRC, "")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            return src

    # Old format fallback
    if data.get(API_KEY_SUCCESS) and data.get(API_KEY_FILE):
        return data[API_KEY_FILE]
    if data.get(API_KEY_SUCCESS) and data.get(API_KEY_STREAM):
        return data[API_KEY_STREAM]

    return None


@proxy_bp.route("/episode-api")
def proxy_episode_api():
    """Get video info from anime1.me or anime1.pw episode page.

    Query params:
        url: The anime1.me or anime1.pw episode URL

    Returns:
        JSON with video URL and cookies needed for streaming
        For anime1.me: extracts API params and calls video API
        For anime1.pw: extracts direct video URL from embedded src
    """
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: "text/html,*/*",
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        # For anime1.pw: extract direct video URL from src attribute
        if DOMAIN_ANIME1_PW in target_url:
            soup = BeautifulSoup(response.text, "html.parser")
            video_elem = soup.find("video", {"src": True})
            if video_elem and video_elem.get("src"):
                video_url = video_elem.get("src")
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                return jsonify({KEY_URL: video_url, KEY_COOKIES: {}})
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

        # For anime1.me: extract API params and call video API
        api_params = _extract_api_params(response.text)
        if not api_params:
            logger.warning(f"[proxy/episode-api] 未找到 video[data-apireq] 元素: {target_url[:100]}")
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

        params = {
            VIDEO_API_PARAM_C: api_params.get(VIDEO_API_PARAM_C, ""),
            VIDEO_API_PARAM_E: api_params.get(VIDEO_API_PARAM_E, ""),
            VIDEO_API_PARAM_T: api_params.get(VIDEO_API_PARAM_T, ""),
            VIDEO_API_PARAM_P: api_params.get(VIDEO_API_PARAM_P, 0),
            VIDEO_API_PARAM_S: api_params.get(VIDEO_API_PARAM_S, ""),
        }

        if not all([params[VIDEO_API_PARAM_C], params[VIDEO_API_PARAM_E], params[VIDEO_API_PARAM_T], params[VIDEO_API_PARAM_S]]):
            logger.warning(f"[proxy/episode-api] API 参数不完整: {params}")
            return jsonify({KEY_ERROR: ERROR_INCOMPLETE_API_PARAMS}), 400

        # Call API
        session = requests.Session()
        data, cookies = _call_video_api(params, session)

        video_url = _get_video_url_from_response(data)
        if video_url:
            return jsonify({KEY_URL: video_url, KEY_COOKIES: cookies})

        logger.warning(f"[proxy/episode-api] 未能从响应中提取视频URL: {data}")
        return jsonify({KEY_ERROR: data.get(KEY_ERROR, ERROR_UNKNOWN_BACKEND)}), 400

    except requests.RequestException as e:
        logger.error(f"[proxy/episode-api] 请求失败: {e}")
        return jsonify({KEY_ERROR: str(e)}), 500
    except Exception as e:
        logger.error(f"[proxy/episode-api] 未知错误: {e}", exc_info=True)
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/video-url")
def proxy_video_url():
    """Get video URL with fresh signature (for JavaScript to use)."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: VALUE_ACCEPT_HTML,
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
        }
        session = requests.Session()
        page_response = session.get(target_url, headers=headers, timeout=10)
        page_response.raise_for_status()

        # For anime1.pw: extract direct video URL from src attribute
        if DOMAIN_ANIME1_PW in target_url:
            soup = BeautifulSoup(page_response.text, "html.parser")
            video_elem = soup.find("video", {"src": True})
            if video_elem and video_elem.get("src"):
                video_url = video_elem.get("src")
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                return jsonify({KEY_URL: video_url})

        # For anime1.me: extract API params
        api_params = _extract_api_params(page_response.text)
        if not api_params:
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

        params = {
            VIDEO_API_PARAM_C: api_params.get(VIDEO_API_PARAM_C, ""),
            VIDEO_API_PARAM_E: api_params.get(VIDEO_API_PARAM_E, ""),
            VIDEO_API_PARAM_T: api_params.get(VIDEO_API_PARAM_T, ""),
            VIDEO_API_PARAM_P: api_params.get(VIDEO_API_PARAM_P, 0),
            VIDEO_API_PARAM_S: api_params.get(VIDEO_API_PARAM_S, ""),
        }

        if not all([params[VIDEO_API_PARAM_C], params[VIDEO_API_PARAM_E], params[VIDEO_API_PARAM_T], params[VIDEO_API_PARAM_S]]):
            return jsonify({KEY_ERROR: ERROR_INCOMPLETE_API_PARAMS}), 400

        data, _ = _call_video_api(params, session)
        video_url = _get_video_url_from_response(data)

        if video_url:
            return jsonify({KEY_URL: video_url})

        return jsonify({KEY_ERROR: data.get(KEY_ERROR, ERROR_UNKNOWN_BACKEND)}), 400

    except requests.RequestException as e:
        logger.error(f"[proxy/video-url] 请求失败: {e}")
        return jsonify({KEY_ERROR: str(e)}), 500
    except Exception as e:
        logger.error(f"[proxy/video-url] 未知错误: {e}", exc_info=True)
        return jsonify({KEY_ERROR: str(e)}), 500


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
                    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
                    HEADER_ACCEPT: VALUE_ACCEPT_ALL,
                    HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
                    HEADER_REFERER: ANIME1_BASE_URL,
                    "Accept-Encoding": "identity",
                    **range_header_forward,
                },
                cookies=cookies if cookies else None,
                timeout=60,
                stream=True,
                allow_redirects=True,
            )

            # 检查响应状态
            if video_response.status_code == 403:
                logger.error(f"[proxy/video-stream] 视频返回 403，可能签名已过期: {video_url[:100]}")
            elif video_response.status_code == 404:
                logger.error(f"[proxy/video-stream] 视频返回 404: {video_url[:100]}")

            video_response.raise_for_status()

            response_headers = {
                HEADER_CONTENT_TYPE: video_response.headers.get(HEADER_CONTENT_TYPE.lower(), "video/mp4"),
                HEADER_ACCEPT_RANGES: VALUE_RANGE_BYTES,
            }

            if video_response.headers.get("Content-Range"):
                response_headers["Content-Range"] = video_response.headers.get("Content-Range")
            if video_response.headers.get("Content-Length"):
                response_headers["Content-Length"] = video_response.headers.get("Content-Length")

            @after_this_request
            def add_cors_headers(response):
                # Allow all origins for webview compatibility
                response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
                response.headers[HEADER_ACCESS_CONTROL_ALLOW_METHODS] = "GET, POST, OPTIONS"
                response.headers[HEADER_ACCESS_CONTROL_ALLOW_HEADERS] = "Range, Content-Type, Accept, Origin, Referer, User-Agent"
                # Cache control for better streaming
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            # Handle OPTIONS preflight
            if request.method == "OPTIONS":
                return "", 200, {
                    HEADER_ACCESS_CONTROL_ALLOW_ORIGIN: "*",
                    HEADER_ACCESS_CONTROL_ALLOW_METHODS: "GET, POST, OPTIONS",
                    HEADER_ACCESS_CONTROL_ALLOW_HEADERS: "Range, Content-Type, Accept, Origin, Referer, User-Agent",
                }

            return Response(
                video_response.iter_content(chunk_size=8192),
                status=video_response.status_code,
                headers=response_headers,
            )

        except requests.exceptions.ChunkedEncodingError as e:
            # 连接在流式传输过程中被中断，这通常是上游服务器的问题
            logger.error(f"[proxy/video-stream] 流式传输连接被中断: {e}")
            return jsonify({KEY_ERROR: "视频流连接中断，请重试"}), 503
        except requests.RequestException as e:
            logger.error(f"[proxy/video-stream] 获取视频失败: {e}")
            return jsonify({KEY_ERROR: str(e)}), 500
        except Exception as e:
            logger.error(f"[proxy/video-stream] 未知错误: {e}", exc_info=True)
            return jsonify({KEY_ERROR: str(e)}), 500

    # POST with c,e,t,p,s parameters
    params = {
        VIDEO_API_PARAM_C: request.form.get(VIDEO_API_PARAM_C, ""),
        VIDEO_API_PARAM_E: request.form.get(VIDEO_API_PARAM_E, ""),
        VIDEO_API_PARAM_T: request.form.get(VIDEO_API_PARAM_T, ""),
        VIDEO_API_PARAM_P: request.form.get(VIDEO_API_PARAM_P, "0"),
        VIDEO_API_PARAM_S: request.form.get(VIDEO_API_PARAM_S, ""),
    }

    if not all([params[VIDEO_API_PARAM_C], params[VIDEO_API_PARAM_E], params[VIDEO_API_PARAM_T], params[VIDEO_API_PARAM_S]]):
        return jsonify({KEY_ERROR: ERROR_MISSING_PARAMS}), 400

    try:
        session = requests.Session()
        data, cookies = _call_video_api(params, session)

        video_url = _get_video_url_from_response(data)
        if not video_url:
            if data.get(API_KEY_SUCCESS) is False:
                return jsonify({KEY_ERROR: data.get(KEY_ERROR, ERROR_API_ERROR)}), 400
            return jsonify({KEY_ERROR: ERROR_NO_VIDEO_SOURCES, KEY_RAW: data}), 400

        # Request video with cookies
        video_response = session.get(
            video_url,
            headers={
                HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
                HEADER_ACCEPT: VALUE_ACCEPT_ALL,
                HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
                HEADER_REFERER: ANIME1_BASE_URL,
            },
            cookies=cookies,
            timeout=30,
            stream=True,
        )

        @after_this_request
        def add_cookies(response):
            for name, value in cookies.items():
                response.headers[f"{HEADER_SET_COOKIE}_{name}"] = f"{name}={value}; Path=/"
            # Allow all origins for webview compatibility
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_METHODS] = "GET, POST, OPTIONS"
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_HEADERS] = "Range, Content-Type, Accept, Origin, Referer, User-Agent"
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        # Handle OPTIONS preflight
        if request.method == "OPTIONS":
            return "", 200, {
                HEADER_ACCESS_CONTROL_ALLOW_ORIGIN: "*",
                HEADER_ACCESS_CONTROL_ALLOW_METHODS: "GET, POST, OPTIONS",
                HEADER_ACCESS_CONTROL_ALLOW_HEADERS: "Range, Content-Type, Accept, Origin, Referer, User-Agent",
            }

        return Response(
            video_response.iter_content(chunk_size=8192),
            status=video_response.status_code,
            headers={
                HEADER_CONTENT_TYPE: video_response.headers.get(HEADER_CONTENT_TYPE.lower(), "video/mp4"),
                HEADER_ACCEPT_RANGES: VALUE_RANGE_BYTES,
            },
        )

    except requests.exceptions.ChunkedEncodingError as e:
        # 连接在流式传输过程中被中断，这通常是上游服务器的问题
        logger.error(f"[proxy/video-stream] POST流式传输连接被中断: {e}")
        return jsonify({KEY_ERROR: "视频流连接中断，请重试"}), 503
    except requests.RequestException as e:
        logger.error(f"[proxy/video-stream] POST请求失败: {e}")
        return jsonify({KEY_ERROR: str(e)}), 500
    except Exception as e:
        logger.error(f"[proxy/video-stream] POST未知错误: {e}", exc_info=True)
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/player")
def proxy_player():
    """Proxy anime1.me or anime1.pw player page with modified video player."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: VALUE_ACCEPT_HTML,
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        video_elem = soup.find("video")

        # For anime1.pw: extract direct video URL from src attribute
        if DOMAIN_ANIME1_PW in target_url:
            video_elem = soup.find("video", {"src": True})
            if video_elem and video_elem.get("src"):
                video_url = video_elem.get("src")
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                poster = video_elem.get("poster", "") or ""
                # Use direct video URL with proxy stream
                proxy_video_url = f"/proxy/video-stream?url={urllib.parse.quote_plus(video_url)}"
            else:
                return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404
        else:
            # For anime1.me: use data-apireq attribute
            video_elem = soup.find("video", {"data-apireq": True})
            if not video_elem:
                return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

            api_params = {}
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

        # Determine if this is anime1.pw (direct MP4) or anime1.me (HLS)
        is_anime1_pw = DOMAIN_ANIME1_PW in target_url
        # Use proxy video URL for anime1.pw, regular video URL for anime1.me
        final_video_url = proxy_video_url if is_anime1_pw else video_url
        video_type = "video/mp4" if is_anime1_pw else "application/x-mpegURL"

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>播放器</title>
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
                <source src="{final_video_url}" type="{video_type}">
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
            response.headers[HEADER_X_FRAME_OPTIONS] = CORS_X_FRAME_OPTIONS
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = CORS_ALLOW_ORIGIN
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/video")
def proxy_video():
    """Proxy video stream from anime1.me or anime1.pw (legacy endpoint)."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: VALUE_ACCEPT_HTML,
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
            HEADER_UPGRADE_INSECURE_REQUESTS: VALUE_UPGRADE_INSECURE_REQUESTS,
        }
        session = requests.Session()
        page_response = session.get(target_url, headers=headers, timeout=10)
        page_response.raise_for_status()

        # For anime1.pw: extract direct video URL from src attribute
        if DOMAIN_ANIME1_PW in target_url:
            soup = BeautifulSoup(page_response.text, "html.parser")
            video_elem = soup.find("video", {"src": True})
            if video_elem and video_elem.get("src"):
                video_url = video_elem.get("src")
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                return {KEY_URL: video_url} if request.is_json else jsonify({KEY_URL: video_url})
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

        # For anime1.me: extract API params
        api_params = _extract_api_params(page_response.text)
        if not api_params:
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND_ON_PAGE}), 404

        params = {
            VIDEO_API_PARAM_C: api_params.get(VIDEO_API_PARAM_C, ""),
            VIDEO_API_PARAM_E: api_params.get(VIDEO_API_PARAM_E, ""),
            VIDEO_API_PARAM_T: api_params.get(VIDEO_API_PARAM_T, ""),
            VIDEO_API_PARAM_P: api_params.get(VIDEO_API_PARAM_P, 0),
            VIDEO_API_PARAM_S: api_params.get(VIDEO_API_PARAM_S, ""),
        }

        if not all([params[VIDEO_API_PARAM_C], params[VIDEO_API_PARAM_E], params[VIDEO_API_PARAM_T], params[VIDEO_API_PARAM_S]]):
            return jsonify({KEY_ERROR: ERROR_INCOMPLETE_API_PARAMS}), 400

        data, _ = _call_video_api(params, session)
        video_url = _get_video_url_from_response(data)

        if video_url:
            return {KEY_URL: video_url} if request.is_json else jsonify({KEY_URL: video_url})

        return jsonify({KEY_ERROR: data.get(KEY_ERROR, ERROR_UNKNOWN_BACKEND)}), 400

    except requests.RequestException as e:
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/full")
def proxy_full():
    """Proxy the full anime1.me or anime1.pw page for iframe embedding."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: VALUE_ACCEPT_HTML,
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
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
            response.headers[HEADER_X_FRAME_OPTIONS] = CORS_X_FRAME_OPTIONS
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = CORS_ALLOW_ORIGIN
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/embed")
def proxy_embed():
    """Proxy only the video player from anime1.me or anime1.pw episode page."""
    target_url = request.args.get("url", "").strip()

    if not target_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain - allow anime1.me and anime1.pw
    if DOMAIN_ANIME1_ME not in target_url and DOMAIN_ANIME1_PW not in target_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: VALUE_ACCEPT_HTML,
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
            HEADER_ORIGIN: ANIME1_BASE_URL,
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        video = soup.find("video")
        if not video:
            return jsonify({KEY_ERROR: ERROR_PLAYER_NOT_FOUND}), 404

        # For anime1.pw: extract direct video URL from src attribute
        if DOMAIN_ANIME1_PW in target_url:
            video_src = video.get("src", "")
            if video_src.startswith("//"):
                video_src = "https:" + video_src
            poster = video.get("poster", "") or ""
            video_type = "video/mp4"
            # Direct video URL - use proxy stream
            video_url = f"/proxy/video-stream?url={urllib.parse.quote_plus(video_src)}"
            js_code = f"""
            (function() {{
                var video = document.getElementById('video');
                video.src = "{video_url}";
                video.play().catch(() => {{}});
            }})();
            """
        else:
            # For anime1.me: use data-apireq attribute
            video_attrs = {
                "src": video.get("src", ""),
                "poster": video.get("poster", ""),
                "data-apireq": video.get("data-apireq", ""),
            }

            poster = video_attrs["poster"]
            video_type = "application/x-mpegURL"

            api_params = {}
            if video_attrs["data-apireq"]:
                try:
                    data_apireq = urllib.parse.unquote(video_attrs["data-apireq"])
                    api_params = json.loads(data_apireq)
                except json.JSONDecodeError:
                    pass

            js_code = f"""
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
            """

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
        <video id="video" controls preload="none" poster="{poster}" type="{video_type}"></video>
    </div>
    <script>
        {js_code}
    </script>
</body>
</html>"""

        @after_this_request
        def add_headers(response):
            response.headers[HEADER_X_FRAME_OPTIONS] = CORS_X_FRAME_OPTIONS
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = CORS_ALLOW_ORIGIN
            return response

        return Response(html, mimetype="text/html")

    except requests.RequestException as e:
        return jsonify({KEY_ERROR: str(e)}), 500


@proxy_bp.route("/hls")
def proxy_hls_playlist():
    """Proxy HLS playlist files and rewrite relative paths.

    Uses m3u8 library to parse and serialize HLS playlists,
    rewriting relative paths to proxy URLs.

    Query params:
        url: The playlist URL to proxy
        cookies: Optional JSON string of cookies to use
    """
    playlist_url = request.args.get("url", "").strip()

    if not playlist_url:
        return jsonify({KEY_ERROR: ERROR_URL_REQUIRED}), 400

    # Check domain
    if DOMAIN_ANIME1_ME not in playlist_url and DOMAIN_ANIME1_PW not in playlist_url:
        return jsonify({KEY_ERROR: ERROR_INVALID_DOMAIN}), 403

    try:
        headers = {
            HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
            HEADER_ACCEPT: "*/*",
            HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
            HEADER_REFERER: ANIME1_BASE_URL,
        }

        # Parse cookies from query param
        cookies = {}
        cookies_param = request.args.get("cookies", "").strip()
        if cookies_param:
            try:
                cookies = json.loads(urllib.parse.unquote(cookies_param))
            except (json.JSONDecodeError, ValueError):
                pass

        response = requests.get(playlist_url, headers=headers, cookies=cookies, timeout=10)
        response.raise_for_status()

        # Handle both string and binary responses
        # For text content (playlists), prefer response.text
        # For binary content (segments), use response.content
        if hasattr(response, 'content') and isinstance(response.content, bytes):
            content = response.content
            is_binary = True
        else:
            content = response.text
            is_binary = False

        # Only parse as HLS playlist if it looks like one
        content_check = content if isinstance(content, (str, bytes)) else ""
        if isinstance(content_check, str):
            is_playlist = "#EXTM3U" in content_check or ".m3u8" in content_check
        else:
            is_playlist = b"#EXTM3U" in content_check or b".m3u8" in content_check

        if not is_playlist:
            # Not an HLS playlist, return as-is (binary content)
            @after_this_request
            def add_cors_headers(response):
                response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                return response
            return Response(content, mimetype="video/mp2t")

        # Parse HLS playlist using m3u8 library
        # m3u8.loads can accept both string and bytes
        if isinstance(content, bytes):
            content_str = content.decode('utf-8', errors='replace')
            playlist = m3u8.loads(content_str)
        else:
            playlist = m3u8.loads(content)

        # Helper to rewrite a URI to proxy URL
        def rewrite_uri(uri: str) -> str:
            if uri.startswith("http://") or uri.startswith("https://"):
                # Absolute URL - proxy it
                encoded_url = urllib.parse.quote_plus(uri)
            elif uri.startswith("/"):
                # Absolute path on same domain
                parsed = urllib.parse.urlparse(playlist_url)
                encoded_url = urllib.parse.quote_plus(f"{parsed.scheme}://{parsed.netloc}{uri}")
            else:
                # Relative path - convert to absolute using base URL
                parsed = urllib.parse.urlparse(playlist_url)
                base_dir = parsed.path.rsplit('/', 1)[0]
                absolute_uri = f"{base_dir}/{uri}"
                encoded_url = urllib.parse.quote_plus(f"{parsed.scheme}://{parsed.netloc}{absolute_uri}")

            cookies_str = urllib.parse.quote_plus(json.dumps(cookies)) if cookies else ""
            return f"/proxy/hls?url={encoded_url}&cookies={cookies_str}"

        # Rewrite segment URIs
        if playlist.segments:
            for segment in playlist.segments:
                if segment.uri:
                    segment.uri = rewrite_uri(segment.uri)

        # Rewrite playlist URIs (variant streams)
        if playlist.playlists:
            for variant in playlist.playlists:
                if variant.uri:
                    variant.uri = rewrite_uri(variant.uri)
                # Add CODECS attribute if missing (required by video.js)
                stream_info = variant.stream_info
                if stream_info and not getattr(stream_info, 'codecs', None):
                    # Add default H.264 + AAC codec string
                    # Most anime1.me videos use H.264/AAC
                    stream_info.codecs = HLS_DEFAULT_CODECS

        # Serialize back to string
        content = playlist.dumps()

        @after_this_request
        def add_cors_headers(response):
            response.headers[HEADER_ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        return Response(content, mimetype="application/vnd.apple.mpegurl")

    except m3u8.ParseError as e:
        logger.error(f"[proxy/hls] M3U8 解析错误: {e}")
        # Fallback: return original content if parsing fails
        return Response(response.content, mimetype="application/vnd.apple.mpegurl")
    except requests.RequestException as e:
        logger.error(f"[proxy/hls] 获取playlist失败: {e}")
        return jsonify({KEY_ERROR: str(e)}), 500
    except Exception as e:
        logger.error(f"[proxy/hls] 未知错误: {e}", exc_info=True)
        return jsonify({KEY_ERROR: str(e)}), 500
