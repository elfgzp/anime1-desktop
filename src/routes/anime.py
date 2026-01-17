"""Anime API routes for listing and detail pages."""
import logging
import re
from typing import List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify

from src.config import PAGE_SIZE, STATIC_DIST, PROJECT_ROOT
from src.constants.api import error_response
from src.constants.messages import (
    ERROR_ANIME_NOT_FOUND,
    ERROR_KEYWORD_REQUIRED,
    ERROR_URL_REQUIRED,
    ERROR_INVALID_DOMAIN,
    DOMAIN_ANIME1_PW,
)
from src.constants.headers import VALUE_USER_AGENT_DEFAULT
from src.models.anime import Anime, AnimePage
from src.parser.anime1_parser import Anime1Parser
from src.parser.cover_finder import CoverFinder
from src.utils.text_converter import get_search_variants
from src import __version__

logger = logging.getLogger(__name__)

anime_bp = Blueprint("anime", __name__, url_prefix="/api/anime")

# Global service instances (lazy initialization)
_services: Optional[Tuple[Anime1Parser, CoverFinder]] = None
_anime_cache: List[Anime] = []


def get_services() -> Tuple[Anime1Parser, CoverFinder]:
    """Get or create parser instances."""
    global _services
    if _services is None:
        _services = (Anime1Parser(), CoverFinder())
    return _services


def get_anime_map() -> dict:
    """Get or create anime map from cache."""
    global _anime_cache
    if not _anime_cache:
        parser, _ = get_services()
        _anime_cache = parser.parse_page(1)
    return {a.id: a for a in _anime_cache}


@anime_bp.route("/")
def get_anime_list():
    """Get anime list for a page.

    Query params:
        page: Page number (default: 1)
    """
    page = request.args.get("page", 1, type=int)

    parser, _ = get_services()
    all_anime = parser.parse_page(page)

    # Calculate pagination
    total_items = len(all_anime)
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_anime = all_anime[start_idx:end_idx]

    anime_page = AnimePage.create(
        anime_list=page_anime,
        current_page=page,
        total_pages=total_pages,
    )

    return jsonify(anime_page.to_dict())


@anime_bp.route("/<anime_id>")
def get_anime_detail(anime_id: str):
    """Get detailed info for a specific anime."""
    parser, finder = get_services()

    anime_list = parser.parse_page(1)
    anime = next((a for a in anime_list if a.id == anime_id), None)

    if anime is None:
        return error_response(ERROR_ANIME_NOT_FOUND, 404)

    # Get additional info from detail page
    html = parser.client.get(anime.detail_url)
    detail_info = parser.parse_anime_detail(html)

    # Find cover using unified Bangumi info function
    finder.get_bangumi_info(anime, update_anime=True)

    # Update anime with additional info
    anime.year = detail_info.get("year", "")
    anime.season = detail_info.get("season", "")
    anime.subtitle_group = detail_info.get("subtitle_group", "")

    return anime.to_dict()


@anime_bp.route("/<anime_id>/episodes")
def get_anime_episodes(anime_id: str):
    """Get episode list for a specific anime.

    Query params:
        page: Page number (default: 1)

    Special handling for anime1.pw domains (SSL issues):
        Returns a flag telling frontend to fetch via JavaScript
    """
    parser, finder = get_services()

    logger.info(f"[anime_id={anime_id}] 正在获取番剧详情")

    anime_list = parser.parse_page(1)
    logger.info(f"[anime_id={anime_id}] 解析到 {len(anime_list)} 个番剧")

    anime = next((a for a in anime_list if a.id == anime_id), None)
    logger.info(f"[anime_id={anime_id}] 查找结果: {'找到' if anime else '未找到'}")

    if anime is None:
        # 尝试在更多页中查找
        logger.warning(f"[anime_id={anime_id}] 未找到该番剧，detail_url 以 anime1.pw 结尾的条目数: {sum(1 for a in anime_list if 'anime1.pw' in a.detail_url)}")
        return error_response(ERROR_ANIME_NOT_FOUND, 404)

    # Special handling for anime1.pw (SSL issues - requires frontend fetch)
    if DOMAIN_ANIME1_PW in anime.detail_url:
        return jsonify({
            "anime": anime.to_dict(),
            "episodes": [],
            "total_episodes": 0,
            "requires_frontend_fetch": True,
            "fetch_url": anime.detail_url,
            "message": "由于技术限制，此番剧的剧集需要通过浏览器内核获取。点击\"追番\"后可在播放页面查看所有剧集。"
        })

    try:
        # Fetch the detail page (with SSL handling for problematic domains)
        html = parser.client.get(anime.detail_url)
    except Exception as e:
        logger.error(f"Failed to fetch episode page for {anime_id}: {e}")
        return error_response(f"无法获取番剧页面: {str(e)}", 500)

    # Get total pages for pagination
    total_pages = parser.get_total_episode_pages(html)

    # Limit pages to prevent too many requests
    max_pages = 5
    if total_pages > max_pages:
        total_pages = max_pages

    # Get all episodes from all pages
    all_episodes = []
    seen_ids = set()
    for page in range(1, total_pages + 1):
        if page == 1:
            page_html = html
        else:
            # Construct paginated URL for category pages
            if "/category/" in anime.detail_url:
                parts = anime.detail_url.split("/category/")
                page_url = parts[0] + "/category/" + parts[1] + "/page/" + str(page)
            elif "?cat=" in anime.detail_url:
                page_url = anime.detail_url + "&page=" + str(page)
            else:
                page_url = anime.detail_url + "?page=" + str(page)
            try:
                page_html = parser.client.get(page_url)
            except Exception as e:
                logger.warning(f"Failed to fetch episode page {page} for {anime_id}: {e}")
                break

        episodes = parser._extract_episodes(page_html)
        # Deduplicate episodes
        for ep in episodes:
            if ep["id"] not in seen_ids:
                seen_ids.add(ep["id"])
                all_episodes.append(ep)

    # Sort by episode number (descending - newest first)
    try:
        all_episodes.sort(key=lambda x: float(x["episode"]), reverse=True)
    except (ValueError, KeyError):
        pass

    # Find cover using unified Bangumi info function
    finder.get_bangumi_info(anime, update_anime=True)

    return jsonify({
        "anime": anime.to_dict(),
        "episodes": all_episodes,
        "total_episodes": len(all_episodes),
    })


@anime_bp.route("/<anime_id>/bangumi")
def get_bangumi_info(anime_id: str):
    """Get Bangumi info for a specific anime.

    Uses SQLite cache to avoid repeated network requests.
    If not cached, returns basic info immediately and triggers background fetch.

    Returns:
        JSON with Bangumi info (rating, rank, type, date, summary, genres, staff).
    """
    # Get anime data
    anime_map = get_anime_map()
    anime = anime_map.get(anime_id)

    if anime is None:
        return error_response(ERROR_ANIME_NOT_FOUND, 404)

    # Get cache service
    from src.services.cover_cache_service import get_cover_cache_service
    cache_service = get_cover_cache_service()

    # Check cache first
    cached_info = cache_service.get_bangumi_info(anime_id)
    if cached_info:
        # Remove internal cached_at field if present
        cached_info.pop("_cached_at", None)
        # Trigger background update for fresh data
        _trigger_background_bangumi_update(anime_id, anime, cache_service)
        return jsonify(cached_info)

    # Not cached, return basic info immediately (non-blocking)
    basic_info = {
        "title": anime.title,
        "subject_url": f"https://bgm.tv/search?keyword={anime.title}",
    }

    # Trigger background fetch
    _trigger_background_bangumi_update(anime_id, anime, cache_service)

    return jsonify(basic_info)


def _trigger_background_bangumi_update(anime_id, anime, cache_service):
    """后台异步更新 Bangumi 信息 (包含封面和信息获取).

    使用统一的 get_bangumi_info 函数一次性获取封面和详细信息，
    避免重复的网络请求。
    """
    import threading

    def _update():
        try:
            _, finder = get_services()
            # 使用统一的函数获取封面和详细信息
            bangumi_info = finder.get_bangumi_info(anime)
            if bangumi_info:
                cache_service.set_bangumi_info(anime_id, bangumi_info)
        except Exception:
            pass  # 后台更新失败不影响

    thread = threading.Thread(target=_update, daemon=True)
    thread.start()


@anime_bp.route("/pw/episodes", methods=["POST"])
def fetch_pw_episodes():
    """Fetch episodes for anime1.pw by parsing HTML content from frontend.

    Request body:
        html: The HTML content from anime1.pw page
        anime_id: The anime ID for reference

    Returns:
        JSON with anime info and episodes list extracted from HTML
    """
    from flask import request

    html_content = request.json.get("html", "").strip()
    anime_id = request.json.get("anime_id", "")

    logger.info(f"[pw/episodes] 收到请求, anime_id={anime_id}, html长度={len(html_content)}")

    if not html_content:
        logger.warning("[pw/episodes] HTML 内容为空")
        return error_response("HTML content is required", 400)

    if not anime_id:
        logger.warning("[pw/episodes] Anime ID 为空")
        return error_response("Anime ID is required", 400)

    try:
        parser, finder = get_services()

        # Get anime info from cache
        anime_map = get_anime_map()
        anime = anime_map.get(anime_id)

        logger.info(f"[pw/episodes] 从缓存查找 anime_id={anime_id}, 结果: {'找到' if anime else '未找到'}")

        if anime is None:
            logger.warning(f"[pw/episodes] 未找到 anime_id={anime_id} 在缓存中")
            return error_response(ERROR_ANIME_NOT_FOUND, 404)

        # Parse episodes from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find cover for anime using unified Bangumi info function
        finder.get_bangumi_info(anime, update_anime=True)

        # Extract episodes using the parser's method
        episodes = parser._extract_episodes(html_content)
        logger.info(f"[pw/episodes] 解析到 {len(episodes)} 个剧集")

        # Sort by episode number (descending - newest first)
        try:
            episodes.sort(key=lambda x: float(x["episode"]), reverse=True)
        except (ValueError, KeyError):
            pass

        result = {
            "anime": anime.to_dict(),
            "episodes": episodes,
            "total_episodes": len(episodes),
            "requires_frontend_fetch": False,
        }
        logger.info(f"[pw/episodes] 返回结果: anime标题={result['anime'].get('title', 'N/A')[:30]}, 剧集数={result['total_episodes']}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"[pw/episodes] 解析失败: {e}", exc_info=True)
        return error_response(f"解析页面失败: {str(e)}", 500)


@anime_bp.route("/covers")
def get_covers_batch():
    """Get cover for a single anime.

    Query params:
        id: Anime ID (only supports single ID, not batch)

    Returns cached data immediately, updates cache in background.
    """
    anime_id = request.args.get("id", "").strip()
    if not anime_id:
        return []

    # Validate ID format (alphanumeric, dash, underscore)
    id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    if not id_pattern.match(anime_id):
        return []

    # Get cover cache service
    from src.services.cover_cache_service import get_cover_cache_service
    cache_service = get_cover_cache_service()

    # Use cached anime map
    from src.routes.anime import get_anime_map
    anime_map = get_anime_map()

    # Check cache first
    cached_covers = cache_service.get_covers([anime_id])
    if anime_id in cached_covers:
        # Remove internal cached_at field before returning
        cached_data = cached_covers[anime_id].copy()
        cached_data.pop("_cached_at", None)

        # 缓存命中，触发后台更新封面（确保数据最新）
        _trigger_background_cover_update(anime_id, anime_map, cache_service)

        return [cached_data]

    # Not cached, return basic info immediately (non-blocking)
    if anime_id in anime_map:
        anime = anime_map[anime_id]
        anime_dict = anime.to_dict()
        # 清除需要网络请求的字段，先返回
        anime_dict.pop("cover_url", None)
        anime_dict.pop("year", None)
        anime_dict.pop("season", None)
        anime_dict.pop("subtitle_group", None)
        anime_dict.pop("match_source", None)
        anime_dict.pop("match_score", None)

        # 后台异步更新封面
        _trigger_background_cover_update(anime_id, anime_map, cache_service)

        return [anime_dict]

    return []


def _trigger_background_cover_update(anime_id, anime_map, cache_service):
    """后台异步更新封面缓存 (使用统一的 Bangumi 信息获取).

    使用统一的 get_bangumi_info 函数获取封面，
    同时保留从 anime1 页面获取 year/season/subtitle_group 的逻辑。
    """
    import threading

    def _update():
        try:
            anime = anime_map.get(anime_id)
            if not anime:
                return

            from src.parser.cover_finder import CoverFinder
            from src.parser.anime1_parser import Anime1Parser

            parser = Anime1Parser()
            finder = CoverFinder()

            # 使用统一的函数获取 Bangumi 信息（包含封面）
            bangumi_info = finder.get_bangumi_info(anime, update_anime=True)

            # 如果 bangumi_info 包含 cover_url，确保 anime 对象已更新
            if bangumi_info and bangumi_info.get("cover_url"):
                anime.cover_url = bangumi_info["cover_url"]
                anime.match_source = "Bangumi"
                anime.match_score = bangumi_info.get("match_score", 0)

            # Only fetch additional info from anime1 if needed
            if not anime.year or not anime.season or not anime.subtitle_group:
                html = parser.client.get(anime.detail_url)
                detail_info = parser.parse_anime_detail(html)
                anime.year = anime.year or detail_info.get("year", "")
                anime.season = anime.season or detail_info.get("season", "")
                anime.subtitle_group = anime.subtitle_group or detail_info.get("subtitle_group", "")

            anime_dict = anime.to_dict()
            cache_service.set_covers({anime_id: anime_dict})
        except Exception:
            pass  # 后台更新失败不影响

    thread = threading.Thread(target=_update, daemon=True)
    thread.start()


@anime_bp.route("/search")
def search_anime():
    """Search anime by keyword.

    Query params:
        q: Search keyword
        page: Page number (default: 1)

    Search supports simplified/traditional Chinese conversion.
    """
    keyword = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    if not keyword:
        return error_response(ERROR_KEYWORD_REQUIRED, 400)

    # Get all anime from cache
    anime_map = get_anime_map()
    all_anime = list(anime_map.values())

    # Get search variants (simplified, traditional)
    search_variants = get_search_variants(keyword)

    # Filter by all keyword variants (case-insensitive, partial match)
    matched_ids = set()
    for anime in all_anime:
        title_lower = anime.title.lower()
        for variant in search_variants:
            if variant.lower() in title_lower:
                matched_ids.add(anime.id)
                break

    filtered_anime = [a for a in all_anime if a.id in matched_ids]

    # Calculate pagination
    total_items = len(filtered_anime)
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_anime = filtered_anime[start_idx:end_idx]

    anime_page = AnimePage.create(
        anime_list=page_anime,
        current_page=page,
        total_pages=total_pages,
    )

    return jsonify(anime_page.to_dict())


# Page routes (non-API)
def register_page_routes(app):
    """Register non-API page routes.

    All routes now serve the Vue SPA index.html.
    Vue Router handles client-side routing.

    Note: API routes (blueprints) should be registered BEFORE this function
    to ensure API endpoints are not caught by the catch-all route.
    """

    def get_manifest_paths():
        """Read Vite manifest.json and return CSS/JS paths."""
        import json
        from pathlib import Path

        # Check both possible locations:
        # 1. static/dist/.vite/ (when running from built executable)
        # 2. frontend/dist/.vite/ (when running from source with npm run build)
        manifest_paths = [
            STATIC_DIST / ".vite" / "manifest.json",
            PROJECT_ROOT / "frontend" / "dist" / ".vite" / "manifest.json",
        ]

        manifest_path = None
        for path in manifest_paths:
            if path.exists():
                manifest_path = path
                break

        if not manifest_path:
            return None, None

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Find index.html entry
            index_entry = manifest.get('index.html', {})
            css_files = index_entry.get('css', [])
            js_file = index_entry.get('file', '')

            css_path = f"/{css_files[0]}" if css_files else None
            js_path = f"/{js_file}" if js_file else None

            return css_path, js_path
        except Exception as e:
            print(f"[WARN] Failed to read manifest: {e}")
            return None, None

    def render_spa():
        """Helper function to render the Vue SPA template.

        Returns the index.html template with version and dev mode.
        """
        dev = app.config.get("DEV", False)
        css_path, js_path = get_manifest_paths()
        return render_template("index.html", version=__version__, dev=dev, css_path=css_path, js_path=js_path)

    @app.route("/")
    def index():
        """Render the Vue SPA."""
        return render_spa()

    @app.route("/anime/<anime_id>")
    def detail(anime_id: str):
        """Render the Vue SPA (Vue Router handles detail page)."""
        return render_spa()
    
    @app.route("/favorites")
    def favorites():
        """Render the Vue SPA (Vue Router handles favorites page)."""
        return render_spa()
    
    @app.route("/settings")
    def settings():
        """Render the Vue SPA (Vue Router handles settings page)."""
        return render_spa()

    # Catch-all route for SPA: all other routes should return index.html
    # This allows Vue Router to handle client-side routing
    # Must be registered LAST to not interfere with API routes
    # Flask's static file handler will serve static files before this route is checked
    @app.route("/<path:path>")
    def catch_all(path: str):
        """Catch-all route for Vue SPA.
        
        Returns index.html for any route that doesn't match API endpoints.
        Vue Router will handle the actual routing on the client side.
        
        Note: Flask automatically handles static files (from static_folder),
        so static file requests won't reach this route.
        """
        from flask import request
        
        # Double-check: don't catch API routes (shouldn't reach here if registered correctly)
        # This is a safety check in case of misconfiguration
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            from flask import abort
            abort(404)
        
        return render_spa()

    # 404 handler for API routes
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors.

        For API routes, return JSON error.
        For page routes, return index.html (handled by catch-all above).
        """
        from flask import request

        # If it's an API request, return JSON error
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            return error_response("Not found", 404)

        # For other routes, return index.html (SPA fallback)
        # This should rarely be hit due to catch-all route above
        return render_spa(), 404

    @app.route("/api/extract-player")
    def extract_player():
        """Extract video player URL from anime1.me episode page.

        Query params:
            url: The anime1.me episode URL

        Returns:
            JSON with video iframe URL
        """
        target_url = request.args.get("url", "").strip()

        if not target_url:
            return error_response(ERROR_URL_REQUIRED, 400)

        if "anime1.me" not in target_url:
            return error_response(ERROR_INVALID_DOMAIN, 403)

        try:
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": VALUE_USER_AGENT_DEFAULT,
            }
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for iframes
            iframes = soup.find_all("iframe")

            if iframes:
                iframe_src = iframes[0].get("src", "")
                return {
                    "iframe_url": iframe_src,
                    "player_page": target_url,
                }

            # Alternative: look for video embedding scripts
            scripts = soup.find_all("script")
            for script in scripts:
                src = script.get("src", "")
                if "player" in src.lower() or "video" in src.lower():
                    return {
                        "script_url": src,
                        "player_page": target_url,
                    }

            return error_response("No player found", 404)

        except requests.RequestException as e:
            return error_response(str(e), 500)
