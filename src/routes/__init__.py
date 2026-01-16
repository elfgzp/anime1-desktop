"""Routes package for Flask application."""
from src.routes.anime import anime_bp, register_page_routes
from src.routes.proxy import proxy_bp

__all__ = ["anime_bp", "proxy_bp", "register_page_routes"]
