"""Anime API routes for listing and detail pages."""
import logging
from typing import List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, render_template, request

from src.config import PAGE_SIZE
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


@anime_bp.route("")
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
        return jsonify({"error": "Anime not found"}), 404

    # Get additional info from detail page
    html = parser.client.get(anime.detail_url)
    detail_info = parser.parse_anime_detail(html)

    # Find cover
    anime = finder.find_cover_for_anime(anime)

    # Update anime with additional info
    anime.year = detail_info.get("year", "")
    anime.season = detail_info.get("season", "")
    anime.subtitle_group = detail_info.get("subtitle_group", "")

    return jsonify(anime.to_dict())


@anime_bp.route("/<anime_id>/episodes")
def get_anime_episodes(anime_id: str):
    """Get episode list for a specific anime.

    Query params:
        page: Page number (default: 1)
    """
    parser, finder = get_services()

    anime_list = parser.parse_page(1)
    anime = next((a for a in anime_list if a.id == anime_id), None)

    if anime is None:
        return jsonify({"error": "Anime not found"}), 404

    # Fetch the detail page
    html = parser.client.get(anime.detail_url)

    # Get total pages for pagination
    total_pages = parser.get_total_episode_pages(html)

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
            page_html = parser.client.get(page_url)

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

    # Find cover for anime
    anime = finder.find_cover_for_anime(anime)

    return jsonify({
        "anime": anime.to_dict(),
        "episodes": all_episodes,
        "total_episodes": len(all_episodes),
    })


@anime_bp.route("/covers")
def get_covers_batch():
    """Get covers for multiple anime (batch API).

    Query params:
        ids: Comma-separated anime IDs
    """
    ids = request.args.get("ids", "")
    if not ids:
        return jsonify([])

    id_list = ids.split(",")
    parser, finder = get_services()

    # Use cached anime map
    anime_map = get_anime_map()

    results = []
    for anime_id in id_list:
        anime_id = anime_id.strip()
        anime = anime_map.get(anime_id)
        if anime:
            anime = finder.find_cover_for_anime(anime)
            # Only fetch additional info if year/season/subtitle are empty
            if not anime.year or not anime.season or not anime.subtitle_group:
                html = parser.client.get(anime.detail_url)
                detail_info = parser.parse_anime_detail(html)
                anime.year = anime.year or detail_info.get("year", "")
                anime.season = anime.season or detail_info.get("season", "")
                anime.subtitle_group = anime.subtitle_group or detail_info.get("subtitle_group", "")
            results.append(anime.to_dict())

    return jsonify(results)


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
        return jsonify({"error": "Keyword is required", "anime_list": []})

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
    """Register non-API page routes."""

    @app.route("/")
    def index():
        page = request.args.get("page", 1, type=int)
        return render_template("index.html", page=page, version=__version__)

    @app.route("/anime/<anime_id>")
    def detail(anime_id: str):
        """Render the anime detail page."""
        return render_template("detail.html", anime_id=anime_id, version=__version__)

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
            return jsonify({"error": "URL is required"}), 400

        if "anime1.me" not in target_url:
            return jsonify({"error": "Only anime1.me URLs are allowed"}), 403

        try:
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for iframes
            iframes = soup.find_all("iframe")

            if iframes:
                iframe_src = iframes[0].get("src", "")
                return jsonify({
                    "iframe_url": iframe_src,
                    "player_page": target_url,
                })

            # Alternative: look for video embedding scripts
            scripts = soup.find_all("script")
            for script in scripts:
                src = script.get("src", "")
                if "player" in src.lower() or "video" in src.lower():
                    return jsonify({
                        "script_url": src,
                        "player_page": target_url,
                    })

            return jsonify({
                "error": "No player found",
                "player_page": target_url,
            }), 404

        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
