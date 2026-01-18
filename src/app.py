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
    performance_bp,
    register_page_routes
)
from src.parser.anime1_parser import Anime1Parser
from src.parser.cover_finder import CoverFinder
from src import __version__


def download_static_resources():
    """Download and cache static resources on startup."""
    import requests

    STATIC_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Static resources to cache (only download if not exists to speed up startup)
    resources = {
        "videojs.bundle.js": "https://sta.anicdn.com/videojs.bundle.js?ver=8",
    }

    for filename, url in resources.items():
        filepath = STATIC_CACHE_DIR / filename
        try:
            # Skip if already exists (speed up startup)
            if filepath.exists() and filepath.stat().st_size > 0:
                continue

            print(f"Downloading {filename}...")
            response = requests.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            if response.content:
                filepath.write_bytes(response.content)
                print(f"  Downloaded {filename} ({len(response.content)} bytes)")
            else:
                print(f"  Empty response for {filename}")

        except Exception as e:
            print(f"  Failed to download {filename}: {e}")
            # Continue anyway - the resource might be served from elsewhere


def create_app() -> Flask:
    """Create and configure the Flask application."""
    from flask_cors import CORS
    from flask import Flask, request, g

    # Initialize database first
    from src.models.database import init_database
    init_database()

    app = Flask(
        __name__,
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config["JSON_SORT_KEYS"] = False

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
        """Record start time for request timing and setup tracing."""
        # Only time API requests (skip static files)
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            g.start_time = time.time()

            # Setup tracing - get trace_id from header or generate new
            from src.utils.trace import start_trace, get_trace_id
            trace_id = request.headers.get('X-Trace-ID')
            start_trace(trace_id)
            g.trace_id = get_trace_id()

    @app.after_request
    def after_request(response):
        """Log request timing and record trace span."""
        from src.utils.trace import end_trace, TraceSpan

        # Only log API requests
        if request.path.startswith("/api/") or request.path.startswith("/proxy/"):
            # Record trace span for the API call
            if hasattr(g, 'trace_id') and hasattr(g, 'start_time'):
                elapsed = (time.time() - g.start_time) * 1000
                method = request.method
                path = request.path

                # Create span for the API call
                with TraceSpan(f'{method} {path}', 'api_call', {
                    'method': method,
                    'path': path,
                    'status_code': response.status_code
                }) as span:
                    span.end(success=response.status_code < 400)

                # Log slow requests (>100ms) with warning
                if elapsed > 100:
                    logger.warning(f"SLOW REQUEST: {method} {path} - {elapsed:.2f}ms")
                else:
                    logger.info(f"{method} {path} - {elapsed:.2f}ms")

                # Add trace_id to response header
                response.headers['X-Trace-ID'] = g.trace_id

            # End tracing context
            end_trace()

        return response

    # Register blueprints
    app.register_blueprint(anime_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(update_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(playback_bp)
    app.register_blueprint(performance_bp)

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

    # Stop cache service
    from src.services.anime_cache_service import stop_cache_service
    stop_cache_service()


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
    banner = f"""
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
    """
    logger.info(banner)


def setup_file_logging():
    """Set up logging to file and console in app data directory."""
    from src.utils.app_dir import get_app_data_dir

    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Console handler - show INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler - show DEBUG and above (Python 3.8 不支持 errors 参数)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Only log from our application, not third-party libraries
    # This prevents encoding issues from subprocess output
    app_logger = logging.getLogger("src")
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    app_logger.setLevel(logging.DEBUG)

    # Also add handler for root logger but filter to only ERROR and above for third-party
    root_handler = logging.FileHandler(log_file, encoding="utf-8", errors="replace")
    root_handler.setLevel(logging.ERROR)
    root_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(root_handler)

    # Suppress noisy third-party library logs to console
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)

    return log_file


def main():
    # Set up file logging
    log_file = setup_file_logging()
    print(f"日志文件: {log_file}")

    parser = argparse.ArgumentParser(description="Anime1 Desktop App")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--dev", action="store_true", help="Development mode (use Vite dev server)")
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
    # 设置开发模式（用于模板中判断是否使用 Vite dev server）
    app.config['DEV'] = args.dev

    # Start cache service in background
    # Use quick_start in dev mode for faster startup (data loads in background)
    from src.services.anime_cache_service import start_cache_service
    start_cache_service(quick_start=args.dev)

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
