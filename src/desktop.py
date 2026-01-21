"""Desktop application entry point using pywebview."""
import os
import sys
# Ensure sys is properly resolved for PyInstaller frozen apps
_sys_module = sys
import socket
import threading
import webview
import logging
import time
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.utils.lock import FileLock, is_file_locked
from src.constants.app import (
    APP_NAME,
    PLATFORM_DARWIN,
    PLATFORM_WIN32,
    IS_FROZEN,
    DIR_LIBRARY,
    DIR_APPLICATION_SUPPORT,
    ENV_APPDATA,
    LOCK_FILE_NAME,
    LOCK_UPDATE_INTERVAL,
    LOCK_TIMEOUT_SECONDS,
    LOCK_MESSAGE_RUNNING,
    LOCK_MESSAGE_BODY,
    ARG_FLASk_ONLY,
    ARG_SUBPROCESS,
    ARG_PORT,
    ARG_WIDTH,
    ARG_HEIGHT,
    ARG_DEBUG,
    ARG_REMOTE,
    ARG_CHECK_UPDATE,
    ARG_AUTO_UPDATE,
    ARG_CHANNEL,
)


def get_data_dir() -> Path:
    """Get the data directory for lock file and logs."""
    if sys.platform == PLATFORM_DARWIN:
        # macOS: always use ~/Library/Application Support/Anime1
        data_dir = Path.home() / DIR_LIBRARY / DIR_APPLICATION_SUPPORT / APP_NAME
    elif IS_FROZEN:
        # Windows frozen: use APPDATA
        appdata_dir = os.environ.get(ENV_APPDATA)
        if appdata_dir:
            data_dir = Path(appdata_dir) / APP_NAME
        else:
            data_dir = Path(sys.executable).parent
    else:
        # Development mode: use project root
        data_dir = Path(__file__).parent.parent

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_lock_file_path() -> Path:
    """Get the path to the instance lock file."""
    return get_data_dir() / LOCK_FILE_NAME


def _get_lock_data() -> dict:
    """Read lock file data. Returns dict with 'pid', 'timestamp', 'exe' or empty dict if invalid."""
    try:
        lock_path = get_lock_file_path()
        if not lock_path.exists():
            return {}

        with open(lock_path, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}

            parts = content.split('\n')
            # New format: pid\ntimestamp\nexe_path
            if len(parts) >= 3:
                try:
                    return {
                        'pid': int(parts[0]),
                        'timestamp': float(parts[1]),
                        'exe': parts[2] if len(parts) > 2 else ''
                    }
                except (ValueError, TypeError):
                    pass
            # Legacy format: pid\ntimestamp (backward compatibility)
            elif len(parts) >= 2:
                try:
                    return {
                        'pid': int(parts[0]),
                        'timestamp': float(parts[1]),
                        'exe': ''
                    }
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    return {}


def _is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        if sys.platform == PLATFORM_WIN32:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError, PermissionError):
        return False


class InstanceLock:
    """Single instance lock using file locking with timestamp-based timeout."""

    def __init__(self):
        self._file_lock: Optional[FileLock] = None
        self._acquired = False
        self._update_thread = None
        self._stop_update = threading.Event()

    def _cleanup_stale_lock(self):
        """Remove stale lock file if the process is no longer running or lock has expired."""
        try:
            lock_path = get_lock_file_path()
            if not lock_path.exists():
                logger.debug(f"[PID:{os.getpid()}] _cleanup_stale_lock: No lock file exists")
                return

            # Read raw lock file content for debugging
            with open(lock_path, 'r') as f:
                raw_content = f.read().strip()
            logger.debug(f"[PID:{os.getpid()}] _cleanup_stale_lock: Lock file content: {repr(raw_content)}")

            data = _get_lock_data()
            if not data:
                # Invalid format, remove it
                logger.info(f"[PID:{os.getpid()}] _cleanup_stale_lock: Invalid format, removing: {raw_content}")
                lock_path.unlink(missing_ok=True)
                return

            pid = data.get('pid', 0)
            timestamp = data.get('timestamp', 0)
            exe = data.get('exe', '')
            current_time = time.time()
            age_seconds = current_time - timestamp
            logger.debug(f"[PID:{os.getpid()}] _cleanup_stale_lock: Checking PID={pid}, exe={exe}, age={age_seconds:.1f}s, timeout={LOCK_TIMEOUT_SECONDS}s")

            # Check if lock has expired
            if age_seconds > LOCK_TIMEOUT_SECONDS:
                logger.info(f"[PID:{os.getpid()}] _cleanup_stale_lock: EXPIRED (age={age_seconds:.1f}s > {LOCK_TIMEOUT_SECONDS}s), removing stale lock (was PID={pid})")
                lock_path.unlink(missing_ok=True)
                return

            # Check if process is still running
            process_running = _is_process_running(pid)
            logger.debug(f"[PID:{os.getpid()}] _cleanup_stale_lock: Process {pid} running = {process_running}")
            if not process_running:
                logger.info(f"[PID:{os.getpid()}] _cleanup_stale_lock: Process {pid} not running, removing stale lock")
                lock_path.unlink(missing_ok=True)
                return

            logger.debug(f"[PID:{os.getpid()}] _cleanup_stale_lock: Active lock detected (PID={pid}, exe={exe})")

        except Exception as e:
            logger.warning(f"[PID:{os.getpid()}] _cleanup_stale_lock: Error: {e}")
            pass

    def _update_lock_timestamp(self):
        """Periodically update the lock timestamp to prevent timeout."""
        while not self._stop_update.wait(LOCK_UPDATE_INTERVAL):
            try:
                if self._acquired and self._file_lock:
                    current_time = time.time()
                    # Write timestamp and PID using FileLock's method
                    self._file_lock.write_timestamp(current_time, pid=os.getpid())
                    logger.debug(f"[PID:{os.getpid()}] Lock timestamp updated")
            except Exception:
                break

    def acquire(self) -> bool:
        """Try to acquire the instance lock. Returns True if acquired, False if another instance is running."""
        current_pid = os.getpid()
        try:
            # First, clean up any stale lock
            logger.debug(f"[PID:{current_pid}] Cleaning up stale locks...")
            self._cleanup_stale_lock()

            lock_file_path = str(get_lock_file_path())
            logger.debug(f"[PID:{current_pid}] Creating FileLock: {lock_file_path}")

            self._file_lock = FileLock(lock_file_path)
            acquired = self._file_lock.acquire(blocking=False)

            if not acquired:
                logger.warning(f"[PID:{current_pid}] Failed to acquire file lock - another instance may be running")
                self._file_lock = None
                return False

            logger.debug(f"[PID:{current_pid}] FileLock acquired successfully")

            # Write our PID and timestamp using FileLock's method (keeps file handle open)
            current_time = time.time()
            self._file_lock.write_timestamp(current_time, pid=current_pid)

            self._acquired = True
            logger.info(f"[PID:{current_pid}] Instance lock acquired successfully")

            # Start background thread to periodically update timestamp
            self._stop_update.clear()
            self._update_thread = threading.Thread(
                target=self._update_lock_timestamp,
                daemon=True
            )
            self._update_thread.start()

            return True

        except (IOError, OSError, PermissionError, BlockingIOError) as e:
            logger.warning(f"[PID:{current_pid}] Failed to acquire instance lock: {e}")
            self._cleanup()
            return False

    def release(self):
        """Release the instance lock."""
        try:
            # Stop the update thread
            self._stop_update.set()
            if self._update_thread and self._update_thread.is_alive():
                self._update_thread.join(timeout=2)

            # Release file lock via FileLock
            if self._file_lock:
                self._file_lock.release()
                self._file_lock = None

            self._cleanup()
        except Exception:
            pass
        self._acquired = False

    def force_release(self):
        """Force release the lock without requiring _acquired flag.

        Used when the app is exiting and needs to release the lock for updater.
        This method doesn't check _acquired flag and tries to clean up regardless.
        """
        try:
            # Stop the update thread
            self._stop_update.set()
            if self._update_thread and self._update_thread.is_alive():
                self._update_thread.join(timeout=1)

            # Release file lock
            if self._file_lock:
                self._file_lock.release()
                self._file_lock = None

            self._cleanup()
        except Exception:
            pass
        self._acquired = False

    def _cleanup(self):
        """Clean up lock file resources and delete the lock file."""
        try:
            # Delete the lock file to allow new instance to start
            lock_path = get_lock_file_path()
            if lock_path.exists():
                lock_path.unlink(missing_ok=True)
                logger.debug(f"[PID:{os.getpid()}] Lock file deleted: {lock_path}")
        except Exception as e:
            logger.warning(f"[PID:{os.getpid()}] Error cleaning up lock file: {e}")

    def is_running(self) -> bool:
        """Check if another instance is running (without acquiring lock)."""
        try:
            data = _get_lock_data()
            if not data:
                return False

            pid = data.get('pid', 0)
            timestamp = data.get('timestamp', 0)
            current_time = time.time()

            # Check if lock has expired
            if current_time - timestamp > LOCK_TIMEOUT_SECONDS:
                return False

            # Check if process is still running
            return _is_process_running(pid)
        except Exception:
            return False


def show_already_running_message():
    """Show a message that another instance is already running."""
    window_title = f"{APP_NAME} - {LOCK_MESSAGE_RUNNING}"
    message = LOCK_MESSAGE_BODY

    try:
        import webview
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{window_title}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       padding: 40px; text-align: center; background: #f5f5f5; }}
                .info {{ background: white; padding: 30px; border-radius: 12px;
                        max-width: 400px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #3498db; margin-bottom: 20px; }}
                .message {{ color: #333; margin-bottom: 20px; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="info">
                <h1>⚠️ 已在运行</h1>
                <p class="message">{message}</p>
            </div>
        </body>
        </html>
        """
        # Create a small notification window
        window = webview.create_window(
            title=window_title,
            html=html,
            width=400,
            height=200,
            resizable=False,
            frameless=False,
        )
        webview.start(func=None, debug=False)
    except Exception:
        print(f"ERROR: {message}", file=sys.stderr)


# CRITICAL: Redirect stdout/stderr BEFORE any print statements
# This prevents console window from appearing on Windows
if sys.platform == PLATFORM_WIN32:
    # Use os.devnull as a persistent file object
    try:
        _null = open(os.devnull, 'w')
        sys.stdout = _null
        sys.stderr = _null
    except Exception:
        pass

# Pre-configure logging (file only, no console)
def setup_logging():
    """Setup logging - file only, no console to avoid window."""
    # Use the same data directory as lock file
    data_dir = get_data_dir()
    log_file = data_dir / "anime1.log"

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler only
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    except Exception:
        file_handler = None

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    if file_handler:
        root_logger.addHandler(file_handler)

    return log_file

LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)

# Add project root to path
if IS_FROZEN:
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
from src.config import DEFAULT_PORT
from src import __version__
from src.utils.version import get_window_title
from src.cli.update_check import run_check_update, run_auto_update
from src.constants.settings import (
    MACOS_APP_NAME,
    MACOS_BUNDLE_ID,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    DEVTOOLS_ENABLED,
)


def setup_macos_app():
    """设置 macOS 应用名称和标识符"""
    if sys.platform != "darwin":
        return

    import time as time_module
    t0 = time_module.time()

    try:
        logger.info(f"[STARTUP] tB0={time_module.time() - start_time:.2f}s - Importing Cocoa frameworks...")
        from Foundation import NSBundle, NSProcessInfo
        from AppKit import NSApplication, NSMenu, NSMenuItem, NSWindow, NSWindowStyleMask
        from WebKit import WKWebView
        import objc
        logger.info(f"[STARTUP] tB1={time_module.time() - start_time:.2f}s - Cocoa frameworks imported")

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

    def log(self, message: str, level: str = "info") -> str:
        """Log a message from JavaScript to the Python logger.

        Usage from JavaScript:
          window.js_api.log("my debug message")
          window.js_api.log("error message", "error")
        """
        import webview
        log_message = f"[JS] {message}"
        if level == "error":
            logger.error(log_message)
        elif level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        return '{"success": true}'

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


import subprocess
import signal
import ctypes


def start_flask_server_subprocess(port: int):
    """Start Flask server as a subprocess without console window."""
    import os

    logger.info(f"Starting Flask server subprocess on port {port}...")

    # Pass parent PID so subprocess can signal parent to exit on update
    parent_pid = os.getpid()
    env = os.environ.copy()
    env['PARENT_PID'] = str(parent_pid)
    env['WERKZEUG_RUN_MAIN'] = 'false'

    if IS_FROZEN:
        # Running as frozen executable - use the executable itself
        exe_path = sys.executable
        cmd = [exe_path, ARG_FLASk_ONLY, ARG_SUBPROCESS, ARG_PORT, str(port)]
    else:
        python_exe = sys.executable
        app_path = os.path.abspath(__file__)
        cmd = [python_exe, app_path, ARG_FLASk_ONLY, ARG_SUBPROCESS, ARG_PORT, str(port)]

    # Windows: Use DETACHED_PROCESS + CREATE_NO_WINDOW to prevent console window
    creation_flags = 0x00000008  # DETACHED_PROCESS
    if sys.platform == PLATFORM_WIN32:
        creation_flags = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW

    # Also set startupinfo to hide window on Windows
    startupinfo = None
    if sys.platform == PLATFORM_WIN32:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    # Only set creationflags and startupinfo on Windows
    kwargs = {}
    if sys.platform == PLATFORM_WIN32:
        kwargs['creationflags'] = creation_flags
        kwargs['startupinfo'] = startupinfo

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        **kwargs
    )

    return proc


def run_flask_inline(port: int, debug: bool = False):
    """Run Flask inline (original method, kept as fallback)."""
    import os
    os.environ['WERKZEUG_RUN_MAIN'] = 'false'

    logger.info(f"Starting Flask server on port {port}...")
    app = create_app()

    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.ERROR)

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False,
        extra_files=[],
        reloader_type='stat',
    )


def hide_console():
    """Hide console window on Windows."""
    if sys.platform == PLATFORM_WIN32:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)


def main():
    """Main entry point for desktop application."""
    import argparse
    import time as time_module

    start_time = time_module.time()
    logger.info(f"[STARTUP] t0={0:.2f}s - App starting...")

    # Hide console window immediately on Windows
    hide_console()

    # Debug: log all arguments
    logger.debug(f"[PID:{os.getpid()}] sys.argv = {sys.argv}")
    logger.debug(f"[PID:{os.getpid()}] IS_FROZEN = {IS_FROZEN}")

    # Check if we're running as a subprocess (Flask server, updater, etc.)
    # Subprocesses should NOT attempt to acquire the instance lock
    # Also skip lock if running in Flask-only mode
    is_subprocess = len(sys.argv) > 1 and (ARG_SUBPROCESS in sys.argv or ARG_FLASk_ONLY in sys.argv)
    logger.debug(f"[PID:{os.getpid()}] is_subprocess = {is_subprocess} (skipping lock acquisition)")

    logger.info(f"[STARTUP] t00={time_module.time() - start_time:.2f}s - Before lock acquisition")

    if not is_subprocess:
        # Check for single instance lock BEFORE any other initialization
        lock = InstanceLock()
        logger.info(f"[PID:{os.getpid()}] Attempting to acquire lock...")
        logger.info(f"[PID:{os.getpid()}] Lock file path: {get_lock_file_path()}")
        logger.info(f"[PID:{os.getpid()}] Lock file exists: {get_lock_file_path().exists()}")

        # 读取锁文件内容用于调试
        if get_lock_file_path().exists():
            try:
                with open(get_lock_file_path(), 'r') as f:
                    lock_content = f.read().strip()
                logger.info(f"[PID:{os.getpid()}] Lock file content: {repr(lock_content)}")
            except Exception as e:
                logger.warning(f"[PID:{os.getpid()}] Failed to read lock file: {e}")

        acquired = lock.acquire()
        logger.info(f"[PID:{os.getpid()}] Lock acquired = {acquired}")

        if not acquired:
            # 获取锁数据用于日志
            lock_data = _get_lock_data()
            logger.warning(f"[PID:{os.getpid()}] Another instance is already running!")
            logger.warning(f"[PID:{os.getpid()}] Running PID from lock: {lock_data.get('pid', 'unknown')}")
            logger.warning(f"[PID:{os.getpid()}] Will show already-running notification and exit")

            # Show notification and exit
            show_already_running_message()
            sys.exit(0)
    else:
        lock = None
        logger.debug(f"[PID:{os.getpid()}] Skipping lock acquisition (subprocess mode)")

    logger.info(f"[STARTUP] t01={time_module.time() - start_time:.2f}s - After lock acquisition")

    parser = argparse.ArgumentParser(description="Anime1 Desktop App")
    parser.add_argument(ARG_WIDTH, type=int, default=DEFAULT_WIDTH, help="Window width")
    parser.add_argument(ARG_HEIGHT, type=int, default=DEFAULT_HEIGHT, help="Window height")
    parser.add_argument(ARG_DEBUG, action="store_true", help="Enable debug mode")
    parser.add_argument(ARG_REMOTE, action="store_true", help="Open in browser instead of webview")
    parser.add_argument(ARG_FLASk_ONLY, action="store_true", help="Run Flask server only (internal use)")
    parser.add_argument(ARG_SUBPROCESS, action="store_true", help="Running as subprocess (internal use)")
    parser.add_argument(ARG_PORT, type=int, default=DEFAULT_PORT, help="Port for Flask server")
    parser.add_argument(ARG_CHECK_UPDATE, action="store_true", help="Check for updates and exit")
    parser.add_argument(ARG_AUTO_UPDATE, action="store_true", help="Check for updates and auto-install if available")
    parser.add_argument(ARG_CHANNEL, default="stable", choices=["stable", "test"],
                        help="Update channel for --check-update/--auto-update (default: stable)")

    args = parser.parse_args()

    # Log version information for debugging
    logger.info(f"[VERSION] ============================================")
    logger.info(f"[VERSION] Anime1 Desktop Application Starting")
    logger.info(f"[VERSION] ============================================")
    logger.info(f"[VERSION] App version: {__version__}")
    logger.info(f"[VERSION] Frozen: {IS_FROZEN}")
    logger.info(f"[VERSION] Executable: {sys.executable}")
    logger.info(f"[VERSION] Data directory: {get_data_dir()}")
    logger.info(f"[VERSION] sys.argv: {sys.argv}")
    logger.info(f"[VERSION] ============================================")

    # Handle --check-update mode
    if args.check_update:
        logger.info(f"[CHECK-UPDATE] Mode: checking for updates...")
        logger.info(f"[CHECK-UPDATE] Current version: {__version__}")

        # Determine channel from args
        channel = "test" if args.channel == "test" else "stable"
        logger.info(f"[CHECK-UPDATE] Channel: {channel}")

        exit_code = run_check_update(__version__, channel)

        # Exit without starting the app
        logger.info("[CHECK-UPDATE] Exiting after update check.")
        print("[CHECK-UPDATE] Exiting after update check.")
        sys.exit(exit_code)

    # Handle --auto-update mode
    if args.auto_update:
        logger.info(f"[AUTO-UPDATE] Mode: check and auto-install updates...")
        logger.info(f"[AUTO-UPDATE] Current version: {__version__}")

        # Determine channel from args
        channel = "test" if args.channel == "test" else "stable"
        logger.info(f"[AUTO-UPDATE] Channel: {channel}")

        exit_code = run_auto_update(__version__, channel)

        # Exit after auto-update attempt
        logger.info("[AUTO-UPDATE] Exiting after auto-update attempt.")
        print("[AUTO-UPDATE] Exiting after auto-update attempt.")
        sys.exit(exit_code)

    # Flask-only mode (used by subprocess)
    if args.flask_only:
        run_flask_inline(args.port)
        return

    logger.info("=" * 50)
    logger.info("Anime1 Desktop App")
    logger.info("=" * 50)

    logger.info(f"[STARTUP] tA={time_module.time() - start_time:.2f}s - After argument parsing")

    # 设置 macOS 应用名称
    setup_macos_app()
    logger.info(f"[STARTUP] tB={time_module.time() - start_time:.2f}s - After setup_macos_app")

    logger.info(f"Arguments: width={args.width}, height={args.height}, debug={args.debug}, remote={args.remote}")

    # Find available port
    # Use default port from config
    port = DEFAULT_PORT
    if not is_port_available(port):
        logger.warning(f"Port {port} is not available, finding free port...")
        port = find_free_port(port)
        logger.info(f"Using port: {port}")
    else:
        logger.info(f"Using default port: {port}")

    logger.info(f"[STARTUP] tC={time_module.time() - start_time:.2f}s - After port check")

    # Download static resources first
    logger.info(f"[STARTUP] tW={time_module.time() - start_time:.2f}s - Preparing static resources...")
    try:
        t_resources = time_module.time()
        download_static_resources()
        logger.info(f"[STARTUP] tW2={time_module.time() - start_time:.2f}s - Static resources prepared successfully")
    except Exception as e:
        logger.error(f"Failed to download static resources: {e}")
        # Continue anyway - resources might already exist

    print_banner("127.0.0.1", port)
    logger.info(f"[STARTUP] tV={time_module.time() - start_time:.2f}s - Starting desktop application...")

    # Start Flask as subprocess (no console window on Windows)
    logger.info("[STARTUP] Starting Flask subprocess...")
    flask_proc = start_flask_server_subprocess(port)
    logger.info(f"[STARTUP] Flask subprocess started, pid={flask_proc.pid}")

    # Wait for Flask server to be ready
    url = f"http://127.0.0.1:{port}"
    logger.info(f"[STARTUP] tX={time_module.time() - start_time:.2f}s - Web server URL: {url}")

    # Test server connection
    import socket
    server_ready = False
    for i in range(20):  # Wait up to 2 seconds
        time_module.sleep(0.1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                server_ready = True
                logger.info(f"[STARTUP] tY={time_module.time() - start_time:.2f}s - Flask server is ready")
                break
        except:
            pass
        finally:
            sock.close()

    if not server_ready:
        logger.warning("Flask server may not be ready, continuing anyway...")

    logger.info(f"[STARTUP] tZ={time_module.time() - start_time:.2f}s - Ready to create webview")

    if args.remote:
        # Open in system browser
        import webbrowser
        webbrowser.open(url)
        logger.info(f"Opened in browser: {url}")
        # Keep server running (wait for keyboard interrupt)
        try:
            flask_proc.wait()
        except KeyboardInterrupt:
            flask_proc.terminate()
        finally:
            lock.release()
    else:
        logger.info("[STARTUP] Creating webview window...")

        try:
            t1 = time_module.time()
            logger.info(f"[STARTUP] t1={t1 - start_time:.2f}s - Creating window...")

            # Create webview window
            window_title = get_window_title()
            logger.info(f"[STARTUP] t2={time_module.time() - start_time:.2f}s - Got window title")

            # Note: pywebview 5.0 does not support icon parameter
            # Icon is set at OS level via the executable's icon (PyInstaller icon)

            # Create JS API instance for anime1.pw handling
            js_api = WebviewApi()
            logger.info(f"[STARTUP] t3={time_module.time() - start_time:.2f}s - Created JS API")

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
                # WEBVIEW_SETTINGS removed to avoid WebView2 compatibility issues
            )
            logger.info(f"[STARTUP] t4={time_module.time() - start_time:.2f}s - Webview window created")

            # 手动暴露 API 方法（pywebview 5.x 需要手动调用 expose）
            logger.info("[STARTUP] Exposing JS API methods...")
            window.expose(
                js_api.navigate,
                js_api.evaluate_js,
                js_api.get_html,
                js_api.close,
                js_api.minimize,
                js_api.maximize
            )
            logger.info(f"[STARTUP] t5={time_module.time() - start_time:.2f}s - JS API methods exposed")

            # Start webview (blocking) - 默认开启 debug 模式
            # 注意：不要在这里设置 WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS，会导致 pywebview 兼容性问题
            logger.info("[STARTUP] Starting webview (this may take a while)...")
            t_start = time_module.time()
            webview.start(debug=True)
            t_end = time_module.time()
            logger.info(f"[STARTUP] t6={t_end - start_time:.2f}s - Webview closed (ran for {t_end - t_start:.2f}s)")

            # Terminate Flask subprocess when webview closes
            flask_proc.terminate()
            logger.info("Flask server terminated")
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
                webview.start(func=None, debug=True)
            except Exception:
                logger.error(f"启动失败: {e}")
                logger.error(f"日志文件: {LOG_FILE}")
            flask_proc.terminate()
            lock.release()
            sys.exit(1)

    logger.info("Application exited")
    # Release the instance lock on normal exit
    lock.release()


if __name__ == "__main__":
    main()
