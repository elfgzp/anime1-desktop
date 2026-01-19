"""Utils package."""
from pathlib import Path

from .constants import PROJECT_ROOT_MARKERS
from .http import HttpClient, create_session, fetch_page
from .version import get_version, get_git_version, get_window_title


def get_project_root() -> Path:
    """Get project root directory (works from any location).

    Returns:
        Path to the project root directory.
    """
    # Start from this file's directory (src/utils/)
    current = Path(__file__).resolve()
    # Go up to project root (src/utils -> src -> project_root)
    return current.parent.parent.parent


__all__ = [
    "HttpClient", "create_session", "fetch_page",
    "get_version", "get_git_version", "get_window_title",
    "get_project_root",
]
