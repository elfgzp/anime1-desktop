"""Routes package for Flask application."""
from src.routes.anime import anime_bp, register_page_routes
from src.routes.proxy import proxy_bp
from src.routes.update import update_bp

__all__ = ["anime_bp", "proxy_bp", "update_bp", "register_page_routes"]
