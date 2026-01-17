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
    import os

    # Determine log path - use APPDATA for installed app (has write permissions)
    if getattr(sys, 'frozen', False):
        # Running as frozen executable
        app_dir = Path(sys.executable).parent
        # Try APPDATA first for installed app (has write permissions in Program Files)
        appdata_dir = os.environ.get('APPDATA')
        if appdata_dir:
            log_file = Path(appdata_dir) / "Anime1" / "anime1.log"
        else:
            log_file = app_dir / "anime1.log"
    else:
        # Running as normal Python script
        app_dir = Path(__file__).parent.parent
        log_file = app_dir / "anime1.log"

    # Create log directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = None
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    except Exception as e:
        print(f"[WARN] Could not create log file at {log_file}: {e}")
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
from src.utils.version import get_window_title
from src.constants.settings import (
    MACOS_APP_NAME,
    MACOS_BUNDLE_ID,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEVTOOLS_ENABLED,
    WEBVIEW_SETTINGS,
)


def setup_macos_app():
    """设置 macOS 应用名称和标识符"""
    if sys.platform != "darwin":
        return

    try:
        from Foundation import NSBundle, NSProcessInfo
        from AppKit import NSApplication, NSMenu, NSMenuItem, NSWindow, NSWindowStyleMask
        from WebKit import WKWebView
        import objc

        # 启用 WKWebView 开发者工具（必须在创建 webview 之前调用）
        try:
            # 使用 objc 来调用私有 API WKWebView.setInspectable(true)
            # 注意：这可能在 App Store 审核时被拒绝
            WKWebView.setInspectable_(True)
            logger.info("WKWebView inspectable enabled")
        except Exception as e:
            logger.warning(f"Could not enable WKWebView inspectable: {e}")

        # 方法1: 修改进程名称（影响菜单栏显示）
        process_info = NSProcessInfo.processInfo()
        process_info.setProcessName_(MACOS_APP_NAME)
        logger.info(f"NSProcessInfo name set to: {MACOS_APP_NAME}")

        # 方法2: 修改 bundle info dictionary
        bundle = NSBundle.mainBundle()
        if bundle:
            info_dict = bundle.infoDictionary()
            if info_dict:
                info_dict['CFBundleName'] = MACOS_APP_NAME
                info_dict['CFBundleDisplayName'] = MACOS_APP_NAME
                info_dict['CFBundleIdentifier'] = MACOS_BUNDLE_ID
                logger.info(f"Bundle info dictionary set to: {MACOS_APP_NAME}")

        # 方法3: 修改 NSApplication 名称
        app = NSApplication.sharedApplication()
        if app:
            app.setApplicationName_(MACOS_APP_NAME)
            app.setApplicationDisplayName_(MACOS_APP_NAME)
            logger.info(f"NSApplication name set to: {MACOS_APP_NAME}")

            # 移除默认的 "Python" 菜单
            main_menu = app.mainMenu()
            if main_menu:
                # 获取所有菜单项
                menu_items = main_menu.itemArray()
                if menu_items and len(menu_items) > 0:
                    # 移除第一个菜单（通常是 Python 菜单）
                    first_item = menu_items[0]
                    main_menu.removeItem_(first_item)
                    logger.info("Removed default Python menu")

                # 确保 Apple 菜单存在
                apple_menu = None
                for item in menu_items[1:]:
                    if item.title() == "" or item.title() == "Apple":
                        apple_menu = item
                        break

                # 如果没有 Apple 菜单，创建一个
                if not apple_menu:
                    apple_item = NSMenuItem.itemWithTitle_action_keyEquivalent_("Apple", None, "")
                    apple_menu = NSMenu.menuWithTitle_("")
                    apple_item.setSubmenu_(apple_menu)
                    main_menu.insertItem_atIndex_(apple_item, 0)
                    logger.info("Created Apple menu")

    except Exception as e:
        logger.warning(f"Could not fully set macOS app name: {e}")
        # 备用方法: 通过 pywebview 设置
        try:
            import webview
            if hasattr(webview, 'gui'):
                webview.gui.CFBundleName = MACOS_APP_NAME
                webview.gui.CFBundleDisplayName = MACOS_APP_NAME
                webview.gui.CFBundleIdentifier = MACOS_BUNDLE_ID
                logger.info(f"macOS app name set via webview.gui: {MACOS_APP_NAME}")
        except Exception as e2:
            logger.warning(f"Could not set macOS app name via webview: {e2}")


class WebviewApi:
    """JavaScript API exposed to the webview for anime1.pw handling."""

    def navigate(self, url: str) -> str:
        """Navigate the webview to a URL."""
        import webview
        for window in webview.windows:
            if window:
                window.load_url(url)
        return '{"success": true}'

    def evaluate_js(self, code: str) -> str:
        """Execute JavaScript code and return the result."""
        import webview
        result = None
        for window in webview.windows:
            if window:
                try:
                    result = window.evaluate_js(code)
                except Exception as e:
                    logger.error(f"evaluate_js error: {e}")
                    result = f'{{"error": "{str(e)}"}}'
                break
        return str(result) if result is not None else 'null'

    def get_html(self) -> str:
        """Get the current page HTML."""
        return self.evaluate_js("document.documentElement.outerHTML")

    def close(self) -> str:
        """Close the window."""
        import webview
        for window in webview.windows:
            if window:
                window.destroy()
        return '{"success": true}'

    def minimize(self) -> str:
        """Minimize the window."""
        import webview
        for window in webview.windows:
            if window:
                window.minimize()
        return '{"success": true}'

    def maximize(self) -> str:
        """Toggle maximize/restore the window."""
        import webview
        for window in webview.windows:
            if window:
                if window.properties.get('maximized'):
                    window.restore()
                else:
                    window.maximize()
        return '{"success": true}'


def create_menus():
    """创建自定义菜单（支持 macOS）"""
    import webview

    # 创建完整菜单（pywebview 5.0 兼容版本，无分隔符）
    menu = webview.Menu([
        webview.Menu(
            'Edit',
            [
                webview.Menu('Undo', lambda: _execute_js('document.execCommand("undo")')),
                webview.Menu('Redo', lambda: _execute_js('document.execCommand("redo")')),
                webview.Menu('Cut', lambda: _execute_js('document.execCommand("cut")')),
                webview.Menu('Copy', lambda: _execute_js('document.execCommand("copy")')),
                webview.Menu('Paste', lambda: _execute_js('document.execCommand("paste")')),
                webview.Menu('Select All', lambda: _execute_js('document.execCommand("selectAll")')),
            ]
        ),
        webview.Menu(
            'View',
            [
                webview.Menu('Reload', lambda: _execute_js('location.reload()')),
                webview.Menu('Zoom In', lambda: _execute_js('document.body.style.zoom = parseFloat(document.body.style.zoom || 1) * 1.1')),
                webview.Menu('Zoom Out', lambda: _execute_js('document.body.style.zoom = parseFloat(document.body.style.zoom || 1) / 1.1')),
                webview.Menu('Reset Zoom', lambda: _execute_js('document.body.style.zoom = 1')),
            ]
        ),
        webview.Menu(
            'Window',
            [
                webview.Menu('Minimize', lambda: _minimize_window()),
                webview.Menu('Zoom', lambda: _toggle_maximize()),
            ]
        ),
    ])
    return menu


def _execute_js(js_code):
    """在当前窗口执行 JavaScript"""
    import webview
    try:
        # 尝试获取当前窗口并执行 JS
        for window in webview.windows:
            window.evaluate_js(js_code)
    except Exception:
        pass


def _minimize_window():
    """最小化窗口"""
    import webview
    try:
        for window in webview.windows:
            window.minimize()
    except Exception:
        pass


def _toggle_maximize():
    """切换最大化"""
    import webview
    try:
        for window in webview.windows:
            if window.properties.get('maximized'):
                window.restore()
            else:
                window.maximize()
    except Exception:
        pass


def start_flask_server(port: int, debug: bool = False):
    """Start Flask server in a background thread."""
    import os
    # Completely disable werkzeug reloader subprocess
    os.environ['WERKZEUG_RUN_MAIN'] = 'false'

    logger.info(f"Starting Flask server on port {port}...")
    app = create_app()

    # Configure Flask logging
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.ERROR)  # Suppress werkzeug info logs

    # Use quiet mode - disable debug, reloader, and any subprocess spawning
    try:
        # Use a simple threaded server without debug mode
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False,  # Must be False to avoid reloader
            threaded=True,
            use_reloader=False,
            extra_files=[],  # No extra files to watch
            reloader_type='stat',
        )
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        raise


def main():
    """Main entry point for desktop application."""
    import argparse

    logger.info("=" * 50)
    logger.info("Anime1 Desktop App")
    logger.info("=" * 50)

    # 设置 macOS 应用名称
    setup_macos_app()

    parser = argparse.ArgumentParser(description="Anime1 Desktop App")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Window width")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Window height")
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

    # Wait for Flask server to be ready
    url = f"http://127.0.0.1:{port}"
    logger.info(f"Web server URL: {url}")

    # Test server connection
    import socket
    server_ready = False
    for i in range(20):  # Wait up to 2 seconds
        time.sleep(0.1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                server_ready = True
                logger.info("Flask server is ready")
                break
        except:
            pass
        finally:
            sock.close()

    if not server_ready:
        logger.warning("Flask server may not be ready, continuing anyway...")

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
            window_title = get_window_title()

            # Note: pywebview 5.0 does not support icon parameter
            # Icon is set at OS level via the executable's icon (PyInstaller icon)

            # Create JS API instance for anime1.pw handling
            js_api = WebviewApi()

            window = webview.create_window(
                title=window_title,
                url=url,
                width=args.width,
                height=args.height,
                resizable=True,
                background_color="#1a1a2e",  # 使用暗色主题背景色
                confirm_close=False,  # 禁用关闭确认对话框
                js_api=js_api,  # Expose API to JavaScript for anime1.pw handling
                # Note: icon parameter removed (not supported in pywebview 5.0)
                # Apply webview settings for better video playback
                **WEBVIEW_SETTINGS,
            )
            logger.info("Webview window created successfully")

            # 手动暴露 API 方法（pywebview 5.x 需要手动调用 expose）
            logger.info("Exposing JS API methods...")
            window.expose(
                js_api.navigate,
                js_api.evaluate_js,
                js_api.get_html,
                js_api.close,
                js_api.minimize,
                js_api.maximize
            )
            logger.info("JS API methods exposed")

            # Start webview (blocking)
            logger.info("Starting webview...")
            webview.start(debug=args.debug)
            logger.info("Webview closed")
        except Exception as e:
            logger.error(f"Webview error: {e}")
            # Try to show error in webview
            try:
                window_title = get_window_title()
                error_html = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{window_title} - 启动失败</title>
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
                    title=f"{window_title} - 启动失败",
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
