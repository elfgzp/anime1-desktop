#!/usr/bin/env python3
"""
Build script for Anime1 desktop application.

Usage:
    python build.py                    # Build for current platform
    python build.py --clean            # Clean dist folder first
    python build.py --onefile          # Create single executable (larger file)
    python build.py --debug            # Build with debug mode
    python build.py --remote           # Build CLI version (browser-based)

Requirements:
    pip install pyinstaller pywebview

Output:
    dist/Anime1.app/ (macOS)
    dist/anime1/ (Linux)
    dist/anime1.exe (Windows single file)
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.resolve()


def clean_dist():
    """Clean the dist folder."""
    dist_path = get_project_root() / "dist"
    if dist_path.exists():
        print(f"[CLEAN] Removing {dist_path}")
        shutil.rmtree(dist_path)
    print("[CLEAN] Dist folder cleaned.")
    print("")


def get_icon_path(root: Path) -> str:
    """Get icon path for current platform."""
    icon_path = root / "static" / "favicon.png"
    if icon_path.exists():
        return str(icon_path)
    return ""


def run_pyinstaller(args):
    """Run PyInstaller with specified options."""
    root = get_project_root()
    dist_path = root / "dist"
    work_path = root / "build"

    # Ensure dist exists
    dist_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        f"--distpath={dist_path}",
        f"--workpath={work_path}",
    ]

    # Windowed mode (no console) - default for desktop app
    cmd.extend(["--windowed", "--noconsole"])

    # Single file or directory
    if args.onefile:
        cmd.append("--onefile")
        print("[BUILD] Mode: single executable (onefile)")
    else:
        cmd.append("--onedir")
        print("[BUILD] Mode: directory bundle (onedir)")

    # Debug mode
    if args.debug:
        cmd.append("--debug=all")
        print("[BUILD] Debug mode: enabled")

    # App name and icon
    app_name = "Anime1"

    # Remote/browser mode (CLI)
    if args.remote:
        cmd.remove("--windowed")
        cmd.remove("--noconsole")
        cmd.append("--console")
        entry_point = str(root / "src" / "app.py")
        cmd.extend(["--name=anime1-cli", entry_point])
        print("[BUILD] Mode: CLI (browser-based)")
    else:
        entry_point = str(root / "src" / "desktop.py")
        cmd.extend(["--name=Anime1", entry_point])
        print(f"[BUILD] App name: {app_name}")

    # Icon for macOS
    icon_path = get_icon_path(root)
    if icon_path and sys.platform == "darwin" and not args.onefile:
        cmd.extend(["--icon", icon_path])
        print(f"[BUILD] Icon: {icon_path}")

    # Hidden imports for pywebview and dependencies
    hidden_imports = [
        "flask", "flask.templating", "jinja2", "markupsafe", "werkzeug",
        "requests", "requests.utils", "requests.auth",
        "urllib3", "urllib3.util", "urllib3.connection",
        "beautifulsoup4", "soupsieve", "bs4", "bs4.builder",
        "pywebview", "pywebview.guarded_encodings", "pywebview.util", "pywebview.http",
        "hanziconv",
        "threading", "socket", "webbrowser", "argparse", "json", "click",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Exclude unnecessary modules to reduce size
    excludes = ["tkinter", "test", "unittest", "pydoc", "doctest", "pdb"]
    for ex in excludes:
        cmd.extend(["--exclude-module", ex])

    # Add data files (templates, static, etc.)
    datas = [
        (str(root / "templates"), "templates"),
        (str(root / "static"), "static"),
        (str(root / "src"), "src"),
    ]

    for src, dst in datas:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    print(f"\n{'='*60}")
    print("Building Anime1...")
    print(f"{'='*60}\n")
    print(f"[INFO] Python: {sys.executable}")
    print(f"[INFO] Platform: {sys.platform}")
    print(f"[INFO] Output: {dist_path}")
    print(f"\n[COMMAND] {' '.join(cmd[:3])} ... {' '.join(cmd[-3:])}")
    print("")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n{'='*60}")
        print("[SUCCESS] Build completed!")
        print(f"{'='*60}")
        print(f"\nOutput location: {dist_path}")

        if sys.platform == "darwin" and not args.onefile:
            app_path = dist_path / "Anime1.app"
            if app_path.exists():
                print(f"macOS App: {app_path}")
                print(f"  Size: {get_size(app_path)}")

        if sys.platform == "win32" and args.onefile:
            exe_path = dist_path / "anime1.exe"
            if exe_path.exists():
                print(f"Windows EXE: {exe_path}")
                print(f"  Size: {get_size(exe_path)}")

        if sys.platform == "darwin" and args.onefile:
            exe_path = dist_path / "anime1"
            if exe_path.exists():
                print(f"macOS Binary: {exe_path}")
                print(f"  Size: {get_size(exe_path)}")

        if sys.platform == "linux" and args.onefile:
            exe_path = dist_path / "anime1"
            if exe_path.exists():
                print(f"Linux Binary: {exe_path}")
                print(f"  Size: {get_size(exe_path)}")

        print("\n[DONE] Ready for distribution!")
    else:
        print("\n[ERROR] Build failed!")
        sys.exit(1)


def get_size(path: Path) -> str:
    """Get human readable size."""
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def verify_dependencies():
    """Check if required packages are installed."""
    print("[VERIFY] Checking dependencies...")
    missing = []

    try:
        import PyInstaller
        print(f"  [OK] PyInstaller: {PyInstaller.__version__}")
    except ImportError as e:
        print(f"  [MISSING] PyInstaller: {e}")
        missing.append("pyinstaller")

    try:
        import webview
        print(f"  [OK] pywebview: installed")
    except ImportError as e:
        print(f"  [MISSING] pywebview: {e}")
        missing.append("pywebview")

    if missing:
        print(f"\n[ERROR] Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install pyinstaller pywebview")
        sys.exit(1)
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="Build Anime1 desktop application"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean dist folder before building"
    )
    parser.add_argument(
        "--onefile", action="store_true", help="Create single executable (larger file)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Build with debug mode"
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Build CLI version that opens in browser (no window)",
    )

    args = parser.parse_args()

    print(f"Python: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Project root: {get_project_root()}")

    verify_dependencies()

    if args.clean:
        clean_dist()

    run_pyinstaller(args)


if __name__ == "__main__":
    main()
