"""Routes package for Flask application."""
from src.routes.anime import anime_bp, register_page_routes
from src.routes.proxy import proxy_bp
from src.routes.update import update_bp
from src.routes.favorite import favorite_bp
from src.routes.settings import settings_bp
from src.routes.playback import playback_bp
from src.routes.performance import performance_bp

__all__ = [
    "anime_bp",
    "proxy_bp",
    "update_bp",
    "favorite_bp",
    "settings_bp",
    "playback_bp",
    "performance_bp",
    "register_page_routes"
]
