"""Desktop application entry point using pywebview."""
import os
import sys
import socket
import threading
import webview
import logging
import time
from pathlib import Path
from datetime import datetime

# Configure logging
def setup_logging():
    """Setup logging to file and console."""
    # Determine log path
    if getattr(sys, 'frozen', False):
        # Running as frozen executable
        app_dir = Path(sys.executable).parent
    else:
        # Running as normal Python script
        app_dir = Path(__file__).parent.parent

    log_file = app_dir / "anime1.log"

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    except Exception as e:
        print(f"[WARN] Could not create log file: {e}")
        file_handler = None

    # Console handler (for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    return log_file

# Initialize logging early
LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)

# Add project root to path
if getattr(sys, 'frozen', False):
    # Running as frozen executable - resources are in _MEIPASS
    MEIPASS = sys._MEIPASS
    PROJECT_ROOT = Path(MEIPASS).parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    logger.info(f"Running as frozen executable. MEIPASS: {MEIPASS}")
else:
    PROJECT_ROOT = Path(os.path.abspath(__file__)).parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    logger.info(f"Running as normal Python script. Project root: {PROJECT_ROOT}")

from src.app import create_app, download_static_resources, find_free_port, is_port_available, print_banner
from src import __version__


def start_flask_server(port: int, debug: bool = False):
    """Start Flask server in a background thread."""
    logger.info(f"Starting Flask server on port {port}...")
    app = create_app()
    # Configure Flask logging
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Disable reloader in thread to avoid issues
    try:
        app.run(host="127.0.0.1", port=port, debug=debug, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        raise


def main():
    """Main entry point for desktop application."""
    import argparse

    logger.info("=" * 50)
    logger.info("Anime1 Desktop App")
    logger.info("=" * 50)

    parser = argparse.ArgumentParser(description="Anime1 Desktop App")
    parser.add_argument("--width", type=int, default=1200, help="Window width")
    parser.add_argument("--height", type=int, default=800, help="Window height")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--remote", action="store_true", help="Open in browser instead of webview")

    args = parser.parse_args()

    logger.info(f"Arguments: width={args.width}, height={args.height}, debug={args.debug}, remote={args.remote}")

    # Find available port
    port = 7860  # Default port for webview
    if not is_port_available(port):
        logger.warning(f"Port {port} is not available, finding free port...")
        port = find_free_port(port)
        logger.info(f"Using port: {port}")
    else:
        logger.info(f"Using default port: {port}")

    # Download static resources first
    logger.info("Preparing static resources...")
    try:
        download_static_resources()
        logger.info("Static resources prepared successfully")
    except Exception as e:
        logger.error(f"Failed to download static resources: {e}")
        # Continue anyway - resources might already exist

    print_banner("127.0.0.1", port)
    logger.info("Starting desktop application...")
    print("")  # Add newline before starting

    # Start Flask in background thread
    server_thread = threading.Thread(
        target=start_flask_server,
        args=(port, args.debug),
        daemon=True
    )
    server_thread.start()

    # Give Flask a moment to start
    time.sleep(0.5)
    logger.info("Flask server thread started")

    url = f"http://127.0.0.1:{port}"
    logger.info(f"Web server URL: {url}")

    if args.remote:
        # Open in system browser
        import webbrowser
        webbrowser.open(url)
        logger.info(f"Opened in browser: {url}")
        # Keep server running
        server_thread.join()
    else:
        logger.info("Creating webview window...")
        try:
            # Create webview window
            window = webview.create_window(
                title=f"Anime1 v{__version__}",
                url=url,
                width=args.width,
                height=args.height,
                resizable=True,
                background_color="#FFFFFF",
            )
            logger.info("Webview window created successfully")

            # Start webview (blocking)
            logger.info("Starting webview...")
            webview.start(func=None, debug=args.debug)
            logger.info("Webview closed")
        except Exception as e:
            logger.error(f"Webview error: {e}")
            # Try to show error in webview
            try:
                error_html = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Anime1 v{__version__} - 启动失败</title>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                               padding: 40px; text-align: center; background: #f5f5f5; }}
                        .error {{ background: white; padding: 30px; border-radius: 12px;
                                max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #e74c3c; margin-bottom: 20px; }}
                        .message {{ color: #333; margin-bottom: 20px; }}
                        .log-path {{ background: #f8f8f8; padding: 10px; border-radius: 6px;
                                   font-family: monospace; font-size: 12px; word-break: break-all; }}
                        .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px;
                               background: #3498db; color: white; text-decoration: none;
                               border-radius: 6px; }}
                    </style>
                </head>
                <body>
                    <div class="error">
                        <h1>启动失败</h1>
                        <p class="message">{str(e)}</p>
                        <p>日志文件路径:</p>
                        <div class="log-path">{LOG_FILE}</div>
                        <p style="color: #888; font-size: 12px; margin-top: 20px;">
                            请查看日志文件获取详细信息
                        </p>
                    </div>
                </body>
                </html>
                """
                window = webview.create_window(
                    title=f"Anime1 v{__version__} - 启动失败",
                    html=error_html,
                    width=500,
                    height=400,
                    resizable=False,
                )
                webview.start(func=None, debug=False)
            except Exception:
                print(f"\n[ERROR] 启动失败: {e}")
                print(f"[ERROR] 日志文件: {LOG_FILE}\n")
            sys.exit(1)

    logger.info("Application exited")


if __name__ == "__main__":
    main()
