"""API route constants."""
from typing import Final
from flask import jsonify


# API route prefixes
API_PREFIX_FAVORITE: Final[str] = "/api/favorite"
API_PREFIX_SETTINGS: Final[str] = "/api/settings"

# Favorite API endpoints
FAVORITE_ADD: Final[str] = "add"
FAVORITE_REMOVE: Final[str] = "remove"
FAVORITE_LIST: Final[str] = "list"
FAVORITE_CHECK: Final[str] = "check"
FAVORITE_IS_FAVORITE: Final[str] = "is_favorite"

# Settings API endpoints
SETTINGS_THEME: Final[str] = "theme"
SETTINGS_CHECK_UPDATE: Final[str] = "check_update"
SETTINGS_ABOUT: Final[str] = "about"

# Theme values
THEME_DARK: Final[str] = "dark"
THEME_LIGHT: Final[str] = "light"
THEME_SYSTEM: Final[str] = "system"

# Response keys
KEY_SUCCESS: Final[str] = "success"
KEY_ERROR: Final[str] = "error"
KEY_DATA: Final[str] = "data"
KEY_MESSAGE: Final[str] = "message"


def success_response(data=None, message: str = None):
    """Create a success response with consistent format.

    Args:
        data: Response data (will be wrapped in KEY_DATA)
        message: Optional success message
    """
    response = {KEY_SUCCESS: True}
    if data is not None:
        response[KEY_DATA] = data
    if message:
        response[KEY_MESSAGE] = message
    return jsonify(response)


def error_response(error: str, status_code: int = 400):
    """Create an error response with consistent format.

    Args:
        error: Error message
        status_code: HTTP status code
    """
    return jsonify({
        KEY_SUCCESS: False,
        KEY_ERROR: error
    }), status_code

