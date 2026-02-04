"""Update check API routes."""
import logging
from flask import Blueprint, jsonify, request

from src.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME, UPDATE_CHANNEL
from src.services.update_checker import UpdateChecker, UpdateChannel, UpdateInfo

logger = logging.getLogger(__name__)

update_bp = Blueprint("update", __name__, url_prefix="/api/update")


@update_bp.route("/check")
def check_update():
    """Check for available updates.

    Query params:
        channel: Update channel ("stable" or "test"), defaults to config value

    Returns:
        JSON with update information
    """
    try:
        # Get channel from query param or use config default
        channel_param = request.args.get("channel", UPDATE_CHANNEL).lower()
        channel = UpdateChannel.TEST if channel_param == "test" else UpdateChannel.STABLE

        logger.debug(f"[UPDATE-API] check_update called:")
        logger.debug(f"  channel_param: {channel_param}")
        logger.debug(f"  channel: {channel}")
        logger.debug(f"  UPDATE_CHANNEL (config): {UPDATE_CHANNEL}")

        # Create update checker
        checker = UpdateChecker(
            repo_owner=GITHUB_REPO_OWNER,
            repo_name=GITHUB_REPO_NAME,
            channel=channel
        )

        logger.debug(f"[UPDATE-API] checker.current_version: {checker.current_version}")

        # Check for updates
        update_info = checker.check_for_update()

        logger.debug(f"[UPDATE-API] check_for_update result:")
        logger.debug(f"  has_update: {update_info.has_update}")
        logger.debug(f"  current_version: {update_info.current_version}")
        logger.debug(f"  latest_version: {update_info.latest_version}")

        # Convert to dict for JSON response - always include latest_version
        result = {
            "has_update": update_info.has_update,
            "current_version": update_info.current_version,
            "latest_version": update_info.latest_version,
        }

        if update_info.has_update:
            result.update({
                "is_prerelease": update_info.is_prerelease,
                "release_notes": update_info.release_notes,
                "download_url": update_info.download_url,
                "asset_name": update_info.asset_name,
                "download_size": update_info.download_size,
                "published_at": update_info.published_at,
            })

        logger.debug(f"[UPDATE-API] Returning: has_update={result['has_update']}, current={result['current_version']}, latest={result.get('latest_version')}")
        response = jsonify(result)
        # Prevent caching for update check responses
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    except Exception as e:
        logger.error(f"Error checking for updates: {e}", exc_info=True)
        # Try to get current_version if checker was created
        current_version = None
        try:
            current_version = checker.current_version
        except (NameError, AttributeError):
            pass
        error_response = jsonify({
            "error": str(e),
            "error_type": "update_check_failed",
            "has_update": False,
            "current_version": current_version,
            "latest_version": None,
        }), 500
        # Also prevent caching for error responses
        error_response[0].headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        error_response[0].headers['Pragma'] = 'no-cache'
        error_response[0].headers['Expires'] = '0'
        return error_response


@update_bp.route("/info")
def update_info():
    """Get current version and update channel information.
    
    Returns:
        JSON with current version and channel info
    """
    from src import __version__

    response = jsonify({
        "current_version": __version__,
        "channel": UPDATE_CHANNEL,
        "repo_owner": GITHUB_REPO_OWNER,
        "repo_name": GITHUB_REPO_NAME,
    })
    # Prevent caching for version info
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
