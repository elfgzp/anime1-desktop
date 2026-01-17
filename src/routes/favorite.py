"""Favorite anime API routes."""
import logging
import re
from flask import Blueprint, request

from src.services.favorite_service import get_favorite_service
from src.routes.anime import get_anime_map
from src.constants.api import (
    success_response,
    error_response
)
from src.constants.messages import (
    ERROR_ANIME_NOT_FOUND,
    ERROR_ANIME_ID_REQUIRED,
    ERROR_ALREADY_IN_FAVORITES,
    ERROR_NOT_IN_FAVORITES,
    SUCCESS_FAVORITE_ADDED,
    SUCCESS_FAVORITE_REMOVED,
)

logger = logging.getLogger(__name__)

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/favorite")


@favorite_bp.route("/add", methods=["POST"])
def add_favorite():
    """Add an anime to favorites.

    Request body:
        anime_id: ID of the anime to add
    """
    try:
        data = request.get_json()
        anime_id = data.get("anime_id") if data else None

        if not anime_id:
            return error_response(ERROR_ANIME_ID_REQUIRED, 400)

        # Get anime from cache
        anime_map = get_anime_map()
        anime = anime_map.get(anime_id)

        if not anime:
            return error_response(ERROR_ANIME_NOT_FOUND, 404)

        # Add to favorites
        service = get_favorite_service()
        success = service.add_favorite(anime)

        if success:
            return success_response(message=SUCCESS_FAVORITE_ADDED)
        else:
            return error_response(ERROR_ALREADY_IN_FAVORITES, 409)

    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        return error_response(str(e), 500)


@favorite_bp.route("/remove", methods=["POST"])
def remove_favorite():
    """Remove an anime from favorites.

    Request body:
        anime_id: ID of the anime to remove
    """
    try:
        data = request.get_json()
        anime_id = data.get("anime_id") if data else None

        if not anime_id:
            return error_response(ERROR_ANIME_ID_REQUIRED, 400)

        service = get_favorite_service()
        success = service.remove_favorite(anime_id)

        if success:
            return success_response(message=SUCCESS_FAVORITE_REMOVED)
        else:
            return error_response(ERROR_NOT_IN_FAVORITES, 404)

    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        return error_response(str(e), 500)


@favorite_bp.route("/list", methods=["GET"])
def list_favorites():
    """Get all favorites."""
    try:
        service = get_favorite_service()
        favorites = service.get_favorites()

        return success_response(data=[fav.to_dict() for fav in favorites])
    except Exception as e:
        logger.error(f"Error listing favorites: {e}")
        return error_response(str(e), 500)


@favorite_bp.route("/check", methods=["GET"])
def check_updates():
    """Check for updates in favorites."""
    try:
        service = get_favorite_service()
        updates = service.check_for_updates()

        return success_response(
            data=[fav.to_dict() for fav in updates],
            message="has_updates" if len(updates) > 0 else None
        )
    except Exception as e:
        logger.error(f"Error checking updates: {e}")
        return error_response(str(e), 500)


@favorite_bp.route("/is_favorite", methods=["GET"])
def is_favorite():
    """Check if an anime is in favorites.

    Query params:
        anime_id: ID of the anime to check
    """
    try:
        anime_id = request.args.get("anime_id")

        if not anime_id:
            return error_response(ERROR_ANIME_ID_REQUIRED, 400)

        service = get_favorite_service()
        is_fav = service.is_favorite(anime_id)

        return success_response(data={"is_favorite": is_fav})
    except Exception as e:
        logger.error(f"Error checking favorite status: {e}")
        return error_response(str(e), 500)


@favorite_bp.route("/batch_status", methods=["GET"])
def batch_status():
    """Check favorite status for multiple anime at once.

    Query params:
        ids: Comma-separated anime IDs to check
    """
    try:
        ids_str = request.args.get("ids", "")

        if not ids_str:
            return success_response(data={})

        # Parse and validate IDs
        id_list = [i.strip() for i in ids_str.split(",") if i.strip()]
        if not id_list:
            return success_response(data={})

        # Limit the number of IDs to prevent abuse
        max_ids = 100
        if len(id_list) > max_ids:
            id_list = id_list[:max_ids]

        # Validate ID format (alphanumeric, dash, underscore)
        id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        id_list = [i for i in id_list if id_pattern.match(i)]
        if not id_list:
            return success_response(data={})

        service = get_favorite_service()
        favorites = service.get_favorites()
        favorite_ids = {fav.id for fav in favorites}

        # Build result map
        status_map = {}
        for anime_id in id_list:
            status_map[anime_id] = anime_id in favorite_ids

        return success_response(data=status_map)
    except Exception as e:
        logger.error(f"Error batch checking favorite status: {e}")
        return error_response(str(e), 500)

