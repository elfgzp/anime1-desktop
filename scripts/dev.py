#!/usr/bin/env python3
"""
开发模式启动脚本 - 同时启动 Flask 后端和 Vite 前端开发服务器
"""
import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Windows 需要 shell=True 来运行 npm
USE_SHELL = sys.platform == "win32"


def check_dependencies():
    """检查必要的依赖是否已安装"""
    errors = []

    # 检查 Python 依赖
    try:
        import flask
    except ImportError:
        errors.append("Flask 未安装，请运行: pip install -e .")

    # 检查 Node.js 和 npm
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=USE_SHELL
        )
        if result.returncode != 0:
            errors.append("npm 未安装或不可用")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        errors.append("npm 未安装，请先安装 Node.js")

    # 检查前端依赖
    frontend_node_modules = PROJECT_ROOT / "frontend" / "node_modules"
    if not frontend_node_modules.exists():
        errors.append("前端依赖未安装，请运行: cd frontend && npm install")

    if errors:
        print("❌ 依赖检查失败:")
        for error in errors:
            print(f"  - {error}")
        print("\n请先运行: make install")
        sys.exit(1)

    print("✓ 依赖检查通过")


def kill_process_by_port(port):
    """根据端口查找并停止进程"""
    import signal

    try:
        # 使用 lsof 查找占用端口的进程
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    pid = int(pid)
                    if pid == os.getpid():
                        continue
                    os.kill(pid, signal.SIGTERM)
                    print(f"  已停止端口 {port} 上的进程 (PID: {pid})")
                    return True
                except (ValueError, ProcessLookupError, PermissionError):
                    pass
    except FileNotFoundError:
        # lsof 不存在，尝试使用其他方法
        pass

    return False


def kill_residual_processes():
    """清理残留的项目进程"""
    import signal

    killed_any = False

    # 通过 ps -ef 查找残留的 Python 进程 (src.app 或 src.desktop)
    try:
        result = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # 查找包含 src.app 或 src.desktop 的进程
                if ('src.app' in line or 'src.desktop' in line) and 'grep' not in line:
                    try:
                        # 提取 PID (第二个字段)
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = int(parts[1])
                            # 跳过当前进程
                            if pid == os.getpid():
                                continue
                            os.kill(pid, signal.SIGTERM)
                            print(f"  已停止残留的 Python 进程 (PID: {pid})")
                            killed_any = True
                    except (ValueError, ProcessLookupError, IndexError):
                        pass
    except FileNotFoundError:
        pass

    # 通过 lsof 清理占用端口的进程
    for port in [5172, 5173, 7860]:
        if kill_process_by_port(port):
            killed_any = True

    if killed_any:
        print("  等待进程完全停止...")
        time.sleep(1)


def is_port_available(port):
    """检查端口是否可用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False


def find_available_port(start_port, max_attempts=10):
    """查找可用的端口"""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    return None


def is_our_process_on_port(port):
    """检查端口是否被我们的进程占用"""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # 检查是否包含我们的进程关键字
                if ('src.app' in line or 'python' in line) and 'grep' not in line:
                    return True
    except FileNotFoundError:
        pass
    return False


def start_flask(port=5172):
    """启动 Flask 后端服务器，返回 (process, actual_port)"""
    # 如果端口被占用，先尝试清理我们的进程
    if not is_port_available(port):
        if is_our_process_on_port(port):
            print(f"⚠️  端口 {port} 被我们的进程占用，正在清理...")
            kill_process_by_port(port)
            time.sleep(1)
            if is_port_available(port):
                print(f"  ✅ 端口 {port} 已释放")
        else:
            print(f"⚠️  端口 {port} 被其他进程占用，尝试备用端口...")
            new_port = find_available_port(port + 1)
            if new_port:
                port = new_port
                print(f"  使用端口 {port}")
            else:
                print(f"  ❌ 无法找到可用的端口")
                return None, port

    cmd = [
        sys.executable,
        "-m", "src.app",
        "--port", str(port),
        "--no-browser",
        "--dev"
    ]

    print(f"🚀 启动 Flask 后端 (端口 {port})...")
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process, port


def start_vite(port=5173, flask_port=5172):
    """启动 Vite 前端开发服务器，返回 (process, actual_port)"""
    env = os.environ.copy()
    env['FLASK_PORT'] = str(flask_port)  # 传递 Flask 端口给 Vite

    # 如果端口被占用，先尝试清理我们的进程
    if not is_port_available(port):
        if is_our_process_on_port(port):
            print(f"⚠️  端口 {port} 被我们的进程占用，正在清理...")
            kill_process_by_port(port)
            time.sleep(1)
            if is_port_available(port):
                print(f"  ✅ 端口 {port} 已释放")
        else:
            print(f"⚠️  端口 {port} 被其他进程占用，尝试备用端口...")
            new_port = find_available_port(port + 1)
            if new_port:
                port = new_port
                print(f"  使用端口 {port}")
            else:
                print(f"  ⚠️  无法找到可用端口，Vite 可能启动失败")

    cmd = ["npm", "run", "dev"]

    print(f"🚀 启动 Vite 前端开发服务器 (端口 {port})...")
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT / "frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        shell=USE_SHELL
    )
    return process, port


def open_browser(url):
    """在默认浏览器中打开 URL"""
    import webbrowser
    print(f"🌐 正在浏览器中打开: {url}")
    webbrowser.open(url)


def _execute_js(js_code):
    """在当前窗口执行 JavaScript"""
    import webview
    try:
        for window in webview.windows:
            window.evaluate_js(js_code)
    except Exception:
        pass


def create_menus():
    """创建自定义菜单（支持 macOS）"""
    from webview.menu import Menu, MenuAction, MenuSeparator
    menu = Menu([
        Menu(
            'Edit',
            [
                MenuAction('Undo', lambda: _execute_js('document.execCommand("undo")')),
                MenuAction('Redo', lambda: _execute_js('document.execCommand("redo")')),
                MenuSeparator(),  # 分隔线
                MenuAction('Cut', lambda: _execute_js('document.execCommand("cut")')),
                MenuAction('Copy', lambda: _execute_js('document.execCommand("copy")')),
                MenuAction('Paste', lambda: _execute_js('document.execCommand("paste")')),
                MenuAction('Select All', lambda: _execute_js('document.execCommand("selectAll")')),
            ]
        ),
        Menu(
            'View',
            [
                MenuAction('Reload', lambda: _execute_js('location.reload()')),
                MenuAction('Zoom In', lambda: _execute_js('document.body.style.zoom = parseFloat(document.body.style.zoom || 1) * 1.1')),
                MenuAction('Zoom Out', lambda: _execute_js('document.body.style.zoom = parseFloat(document.body.style.zoom || 1) / 1.1')),
                MenuAction('Reset Zoom', lambda: _execute_js('document.body.style.zoom = 1')),
            ]
        ),
        Menu(
            'Window',
            [
                MenuAction('Minimize', lambda: None),
                MenuAction('Zoom', lambda: None),
            ]
        ),
    ])
    return menu


def setup_macos():
    """macOS 启动时设置（延迟导入以加快启动速度）"""
    if sys.platform != "darwin":
        return

    try:
        from Foundation import NSProcessInfo

        # 设置进程名称
        NSProcessInfo.processInfo().setProcessName_("Anime1")
        print("✓ macOS 进程名称已设置为 Anime1")
    except Exception as e:
        print(f"⚠️  macOS 设置警告: {e}")


def start_webview(url, width=1200, height=800, debug=False):
    """启动 webview 窗口"""
    import webview
    import time

    # macOS 启动时设置
    setup_macos()

    # 添加时间戳参数强制刷新缓存
    url_with_ts = f"{url}?_v={int(time.time())}"

    print(f"🪟 正在启动 webview 窗口...")
    if debug:
        print("   💡 提示: 右键点击页面选择 'Inspect' 打开开发者工具")

    window_title = "Anime1"
    window = webview.create_window(
        title=window_title,
        url=url_with_ts,
        width=width,
        height=height,
        resizable=True,
        background_color="#FFFFFF",
        confirm_close=False
    )

    # 禁用关闭确认对话框的本地化设置
    localization = {
        'global.quitConfirmation': '',
    }

    # macOS 上创建菜单
    app_menu = [create_menus()] if sys.platform == 'darwin' else None

    webview.start(func=None, debug=debug, menu=app_menu, localization=localization)

    # 注意：macOS 上请使用快捷键 Option+Cmd+I 打开开发者工具


def print_output(process, prefix):
    """打印进程输出"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{prefix}] {line.rstrip()}")
    except (ValueError, OSError):
        # Stream might be closed
        pass
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="启动开发环境（Flask + Vite）",
        epilog="""
示例:
  %(prog)s                      # 默认 webview 模式
  %(prog)s --browser            # 在浏览器中打开
  %(prog)s --browser --skip-check --no-cleanup  # 快速启动
  %(prog)s --flask-port=5180    # 自定义 Flask 端口

提示: 使用 make 命令时，可以用环境变量简化参数:
  DEV_BROWSER=1 make dev        # 在浏览器中打开
  DEV_DEBUG=1 make dev          # 启用开发者工具
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--flask-port",
        type=int,
        default=5172,
        help="Flask 后端端口（默认: 5172）"
    )
    parser.add_argument(
        "--vite-port",
        type=int,
        default=5173,
        help="Vite 前端端口（默认: 5173）"
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="跳过依赖检查"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="不清理残留进程"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="跳过检查并强制启动（等同于 --skip-check --no-cleanup）"
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="在浏览器中打开（默认打开 webview）"
    )
    parser.add_argument(
        "--webview",
        action="store_true",
        default=True,
        help="在 webview 窗口中打开（默认行为）"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="webview 窗口宽度（默认: 1200）"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="webview 窗口高度（默认: 800）"
    )
    parser.add_argument(
        "--debug-webview",
        action="store_true",
        default=True,
        help="打开 webview 开发者工具（默认开启，使用 --no-debug-webview 关闭）"
    )
    parser.add_argument(
        "--no-debug-webview",
        action="store_false",
        dest="debug_webview",
        help="关闭 webview 开发者工具"
    )

    args = parser.parse_args()

    # 处理 --force 参数
    if args.force:
        args.skip_check = True
        args.no_cleanup = True

    if not args.skip_check:
        check_dependencies()

    # 清理残留进程
    if not args.no_cleanup:
        print("检查残留进程...")
        kill_residual_processes()

    print("\n" + "="*60)
    print("Anime1 Desktop - 开发模式")
    print("="*60)
    print(f"Flask 后端: http://localhost:{args.flask_port}")
    print(f"Vite 前端: http://localhost:{args.vite_port}")
    print(f"打开方式: {'浏览器' if args.browser else 'webview'}")
    print("\n按 Ctrl+C 停止所有服务\n")

    processes = []

    try:
        # 启动 Flask
        flask_result = start_flask(args.flask_port)
        if flask_result is None:
            print("❌ Flask 启动失败")
            sys.exit(1)
        flask_process, flask_port = flask_result
        processes.append(("Flask", flask_process))

        # 等待 Flask 完全启动
        time.sleep(3)

        # 启动 Vite，传入 Flask 端口
        vite_result = start_vite(args.vite_port, flask_port)
        if vite_result is None:
            print("❌ Vite 启动失败")
            sys.exit(1)
        vite_process, vite_port = vite_result
        processes.append(("Vite", vite_process))

        # 等待 Vite 启动
        time.sleep(2)

        print("\n✅ 开发环境已启动！")
        print(f"   前端: http://localhost:{vite_port}")
        print(f"   后端 API: http://localhost:{flask_port}/api")
        print("\n正在运行... (按 Ctrl+C 停止)\n")

        # 启动日志监控线程
        stop_event = threading.Event()

        def monitor_output(name, proc):
            try:
                for line in iter(proc.stdout.readline, ''):
                    if stop_event.is_set():
                        break
                    if line:
                        print(f"[{name}] {line.rstrip()}")
            except (ValueError, OSError):
                pass
            except Exception:
                pass

        monitor_threads = []
        for name, proc in processes:
            t = threading.Thread(target=monitor_output, args=(name, proc), daemon=True)
            t.start()
            monitor_threads.append(t)

        # 根据参数决定打开方式
        vite_url = f"http://localhost:{vite_port}"
        print(f"[DEBUG] args.browser = {args.browser}")
        if args.browser:
            open_browser(vite_url)
        else:
            start_webview(vite_url, args.width, args.height, args.debug_webview)

        # 停止日志监控
        stop_event.set()

        # 停止服务（webview 关闭后）
        raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")

        # 停止所有进程
        for name, proc in processes:
            if proc.poll() is None:
                print(f"   停止 {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   强制停止 {name}...")
                    proc.kill()

        print("✅ 所有服务已停止")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ 错误: {e}")

        # 清理进程
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()

        sys.exit(1)


if __name__ == "__main__":
    main()
