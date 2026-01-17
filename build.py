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


def extract_version() -> str:
    """Extract version from git tag or commit id.
    
    Returns:
        Version string from git tag (without 'v' prefix) or short commit id.
        Falls back to 'dev' if git is not available.
    """
    root = get_project_root()
    
    # Try to get the latest tag
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            tag = result.stdout.strip()
            # Remove 'v' prefix if present
            version = tag.lstrip('vV')
            return version
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # If no tag, try to get commit id
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            commit_id = result.stdout.strip()
            return f"dev-{commit_id}"
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Fallback to 'dev' if git is not available
    return "dev"


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
    # Check for .icns file first (macOS)
    icns_path = root / "static" / "app.icns"
    if icns_path.exists():
        return str(icns_path)
    # Fallback to PNG
    png_path = root / "static" / "favicon.png"
    if png_path.exists():
        return str(png_path)
    return ""


def get_plist_path(root: Path) -> str:
    """Get Info.plist path for macOS."""
    plist_path = root / "distInfo.plist"
    if plist_path.exists():
        return str(plist_path)
    return ""


def run_pyinstaller(args):
    """Run PyInstaller with specified options."""
    root = get_project_root()
    dist_path = root / "dist"
    work_path = root / "build"

    # Extract version and set environment variable for build
    version = extract_version()
    os.environ["ANIME1_VERSION"] = version
    print(f"[BUILD] Version: {version}")
    
    # Create version file for frozen executables
    version_file = root / "src" / "_version.txt"
    version_file.write_text(version, encoding='utf-8')
    print(f"[BUILD] Created version file: {version_file}")

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

    # Custom Info.plist for macOS (to set proper menu bar name)
    plist_path = get_plist_path(root)
    if plist_path and sys.platform == "darwin":
        cmd.extend(["--osx-bundle-identifier", "com.anime1.app"])
        print(f"[BUILD] Bundle ID: com.anime1.app")

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
        (str(root / "distInfo.plist"), "."),
    ]
    
    # Add frontend build output (if exists)
    frontend_dist = root / "static" / "dist"
    if frontend_dist.exists():
        datas.append((str(frontend_dist), "static/dist"))
        print(f"[BUILD] Including frontend build: {frontend_dist}")
    else:
        print(f"[WARNING] Frontend build not found at {frontend_dist}")
        print("[WARNING] Make sure to run 'npm run build' in frontend/ directory first")
    
    # Ensure version file is included (if it exists)
    if version_file.exists():
        # For onedir, include in src directory
        # For onefile, it will be in _MEIPASS/src
        datas.append((str(version_file), "src"))

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

        # Fix macOS app Info.plist to show proper menu bar name
        if sys.platform == "darwin" and not args.onefile:
            app_path = dist_path / "Anime1.app"
            if app_path.exists():
                fix_macos_app_info_plist(app_path)
                fix_macos_app_icon(app_path, icon_path)
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


def fix_macos_app_icon(app_path: Path, icon_path: str):
    """Fix macOS app bundle icon by copying icon file to Resources."""
    if not icon_path:
        print(f"[WARN] No icon file found, app will use default icon")
        return

    # Get the icon filename
    icon_file = Path(icon_path).name
    icon_src = Path(icon_path)

    # Target location in app bundle
    resources_path = app_path / "Contents" / "Resources"

    if not resources_path.exists():
        print(f"[WARN] Resources path not found: {resources_path}")
        return

    # Copy icon file to Resources
    icon_dst = resources_path / icon_file
    try:
        shutil.copy2(icon_src, icon_dst)
        print(f"[BUILD] Copied icon to app bundle: {icon_file}")

        # If it's a PNG, we may need to convert to ICNS
        # For now, try renaming to app.icns if that's what Info.plist expects
        if icon_file.endswith('.png') and icon_file != 'app.icns':
            icns_dst = resources_path / "app.icns"
            shutil.copy2(icon_src, icns_dst)
            print(f"[BUILD] Created app.icns from PNG")
    except Exception as e:
        print(f"[WARN] Could not copy icon: {e}")


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
