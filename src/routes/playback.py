"""Playback history API routes."""
import logging
from flask import Blueprint, request, make_response

from src.services.playback_history_service import get_playback_history_service
from src.constants.api import (
    success_response,
    error_response
)

logger = logging.getLogger(__name__)

playback_bp = Blueprint("playback", __name__, url_prefix="/api/playback")


def add_no_cache_headers(response):
    """为响应添加防缓存头"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@playback_bp.route("/update", methods=["POST"])
def update_progress():
    """Update playback progress for an episode.

    Request body:
        anime_id: ID of the anime
        anime_title: Title of the anime
        episode_id: ID of the episode
        episode_num: Episode number
        position_seconds: Current playback position in seconds
        total_seconds: Total duration in seconds (optional, default 0)
        cover_url: URL of the anime cover (optional)
    """
    try:
        data = request.get_json()
        anime_id = data.get("anime_id") if data else None
        episode_id = data.get("episode_id") if data else None
        position_seconds = data.get("position_seconds")

        if not anime_id:
            return error_response("anime_id is required", 400)
        if not episode_id:
            return error_response("episode_id is required", 400)
        if position_seconds is None:
            return error_response("position_seconds is required", 400)

        anime_title = data.get("anime_title", "")
        episode_num = data.get("episode_num", 0)
        total_seconds = data.get("total_seconds", 0.0)
        cover_url = data.get("cover_url", "")

        service = get_playback_history_service()
        success, entry = service.update_progress(
            anime_id=anime_id,
            anime_title=anime_title,
            episode_id=episode_id,
            episode_num=episode_num,
            position_seconds=float(position_seconds),
            total_seconds=float(total_seconds),
            cover_url=cover_url
        )

        if success and entry:
            return success_response(data=entry.to_dict())
        else:
            return error_response("Failed to update progress", 500)

    except Exception as e:
        logger.error(f"Error updating playback progress: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/list", methods=["GET"])
def list_history():
    """Get playback history.

    Query params:
        limit: Maximum number of entries (default: 50, max: 100)
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        service = get_playback_history_service()
        history = service.get_history(limit=limit)

        response = make_response(success_response(data=[entry.to_dict() for entry in history]))
        return add_no_cache_headers(response)
    except Exception as e:
        logger.error(f"Error listing playback history: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/episode", methods=["GET"])
def get_episode_progress():
    """Get playback progress for a specific episode.

    Query params:
        anime_id: ID of the anime
        episode_id: ID of the episode
    """
    try:
        anime_id = request.args.get("anime_id")
        episode_id = request.args.get("episode_id")

        if not anime_id:
            return error_response("anime_id is required", 400)
        if not episode_id:
            return error_response("episode_id is required", 400)

        service = get_playback_history_service()
        entry = service.get_episode_progress(anime_id, episode_id)

        if entry:
            response = make_response(success_response(data=entry.to_dict()))
        else:
            response = make_response(success_response(data=None))
        return add_no_cache_headers(response)

    except Exception as e:
        logger.error(f"Error getting episode progress: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/latest", methods=["GET"])
def get_latest():
    """Get the most recently watched episode for an anime.

    Query params:
        anime_id: ID of the anime
    """
    try:
        anime_id = request.args.get("anime_id")

        if not anime_id:
            return error_response("anime_id is required", 400)

        service = get_playback_history_service()
        entry = service.get_latest_for_anime(anime_id)

        if entry:
            response = make_response(success_response(data=entry.to_dict()))
        else:
            response = make_response(success_response(data=None))
        return add_no_cache_headers(response)

    except Exception as e:
        logger.error(f"Error getting latest progress: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/anime/<anime_id>", methods=["GET"])
def get_history_by_anime(anime_id: str):
    """Get all playback history entries for a specific anime.

    Path params:
        anime_id: ID of the anime
    """
    try:
        service = get_playback_history_service()
        history = service.get_history_by_anime(anime_id)

        response = make_response(success_response(data=[entry.to_dict() for entry in history]))
        return add_no_cache_headers(response)
    except Exception as e:
        logger.error(f"Error getting playback history for anime {anime_id}: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/batch", methods=["GET"])
def get_batch_progress():
    """Get playback progress for multiple episodes at once.

    Query params:
        ids: Comma-separated list of episode IDs in format "anime_id:episode_id"
             Example: "anime1:ep1,anime2:ep2"
    """
    try:
        ids_str = request.args.get("ids", "")

        if not ids_str:
            response = make_response(success_response(data={}))
            return add_no_cache_headers(response)

        # Parse IDs
        id_list = [i.strip() for i in ids_str.split(",") if i.strip() and ":" in i]
        if not id_list:
            response = make_response(success_response(data={}))
            return add_no_cache_headers(response)

        # Limit to prevent abuse
        max_ids = 50
        if len(id_list) > max_ids:
            id_list = id_list[:max_ids]

        service = get_playback_history_service()
        result = {}

        for id_pair in id_list:
            parts = id_pair.split(":", 1)
            if len(parts) == 2:
                anime_id, episode_id = parts
                entry = service.get_episode_progress(anime_id, episode_id)
                if entry:
                    result[id_pair] = entry.to_dict()

        response = make_response(success_response(data=result))
        return add_no_cache_headers(response)

    except Exception as e:
        logger.error(f"Error batch getting playback progress: {e}")
        return error_response(str(e), 500)


@playback_bp.route("/delete", methods=["POST"])
def delete_history():
    """Delete playback history.

    Request body:
        anime_id: Optional - delete all history for this anime
        episode_id: Optional - delete history for specific episode
    """
    try:
        data = request.get_json()
        anime_id = data.get("anime_id") if data else None
        episode_id = data.get("episode_id") if data else None

        service = get_playback_history_service()
        success = service.delete_history(anime_id=anime_id, episode_id=episode_id)

        if success:
            return success_response(message="History deleted successfully")
        else:
            return error_response("Failed to delete history", 500)

    except Exception as e:
        logger.error(f"Error deleting playback history: {e}")
        return error_response(str(e), 500)
