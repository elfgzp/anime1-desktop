"""Flask web application for Anime1."""
import argparse
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask

logger = logging.getLogger(__name__)

# Add parent directory to path for imports
PROJECT_ROOT = Path(os.path.abspath(__file__)).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_HOST, DEFAULT_PORT, STATIC_CACHE_DIR
from src.routes import (
    anime_bp,
    proxy_bp,
    update_bp,
    favorite_bp,
    settings_bp,
    playback_bp,
    register_page_routes
)
from src.parser.anime1_parser import Anime1Parser
from src.parser.cover_finder import CoverFinder
from src import __version__


def download_static_resources():
    """Download and cache static resources on startup."""
    import requests

    STATIC_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Static resources to cache
    resources = {
        "videojs.bundle.js": "https://sta.anicdn.com/videojs.bundle.js?ver=8",
    }

    for filename, url in resources.items():
        filepath = STATIC_CACHE_DIR / filename
        try:
            print(f"Checking {filename}...")
            response = requests.get(url, timeout=60, allow_redirects=True)
            response.raise_for_status()

            content_changed = True
            if filepath.exists():
                existing_content = filepath.read_bytes()
                if existing_content == response.content:
                    print(f"  {filename} unchanged, skipping")
                    content_changed = False

            if content_changed:
                filepath.write_bytes(response.content)
                print(f"  Downloaded {filename} ({len(response.content)} bytes)")

        except Exception as e:
            print(f"  Failed to download {filename}: {e}")


def create_app() -> Flask:
    """Create and configure the Flask application."""
    from jinja2 import FileSystemLoader
    from flask_cors import CORS
    from flask import Flask, request, g

    # Initialize database first
    from src.models.database import init_database
    init_database()

    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config["JSON_SORT_KEYS"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Serve vite-built assets from /assets/* path
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        from flask import send_from_directory
        return send_from_directory(str(PROJECT_ROOT / "static" / "dist" / "assets"), filename)

    # Enable CORS for all routes
    CORS(app)

    # Request timing middleware - logs all API requests
    @app.before_request
    def before_request():
        """Record start time for request timing."""
        # Only time API requests (skip static files)
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Log request timing."""
        # Only log API requests
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            if hasattr(g, 'start_time'):
                elapsed = (time.time() - g.start_time) * 1000  # Convert to ms
                # Log slow requests (>100ms) with warning
                if elapsed > 100:
                    logger.warning(f"SLOW REQUEST: {request.method} {request.path} - {elapsed:.2f}ms")
                else:
                    logger.info(f"{request.method} {request.path} - {elapsed:.2f}ms")
        return response

    # Fix DispatchingJinjaLoader threading issue
    app.jinja_loader = FileSystemLoader(str(PROJECT_ROOT / "templates"))

    # Register blueprints
    app.register_blueprint(anime_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(update_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(playback_bp)

    # Register page routes
    register_page_routes(app)

    return app


# Global service instances
_services = None


def shutdown_services():
    """Shutdown all service instances."""
    global _services
    if _services is not None:
        parser, finder = _services
        parser.close()
        finder.close()
        _services = None

    # Close database connection
    from src.models.database import close_database
    close_database()


def find_free_port(start_port: int = DEFAULT_PORT) -> int:
    """Find a free port starting from start_port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", start_port))
            return start_port
        except OSError:
            s.bind(("", 0))
            return s.getsockname()[1]


def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return True
    except OSError:
        return False


def open_browser(port: int):
    """Open browser after a short delay."""
    time.sleep(1)
    url = f"http://localhost:{port}"
    webbrowser.open(url)


def print_banner(host: str, port: int):
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Anime1 v{__version__:<15}              ║
║                                                          ║
║   Server running at: http://{host}:{port}              ║
║                                                          ║
║   Usage:                                                  ║
║   - View anime list: http://{host}:{port}/               ║
║   - API: http://{host}:{port}/api/anime?page=1           ║
║                                                          ║
║   Ctrl+C to stop                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def main():
    parser = argparse.ArgumentParser(description="Anime1 Desktop App")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser")

    args = parser.parse_args()

    port = args.port
    if port == DEFAULT_PORT and not is_port_available(port):
        port = find_free_port()

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    print_banner(args.host, port)

    print("\nPreparing static resources...")
    download_static_resources()
    print("")

    app = create_app()

    try:
        app.run(
            host=args.host,
            port=port,
            debug=args.debug,
            threaded=True,
            # Enable reloader only in debug mode and when not in frozen binary
            use_reloader=args.debug and not getattr(sys, 'frozen', False),
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        shutdown_services()


if __name__ == "__main__":
    main()
