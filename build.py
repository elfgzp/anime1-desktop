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


def generate_icons():
    """Generate platform-specific icons."""
    root = get_project_root()

    # Windows ICO
    if sys.platform == "win32":
        png_path = root / "static" / "favicon.png"
        ico_path = root / "static" / "app.ico"

        if not png_path.exists():
            print(f"[WARN] Source PNG not found: {png_path}")
            return False

        try:
            from PIL import Image
            img = Image.open(png_path)
            sizes = [16, 32, 48, 64, 128, 256]
            img_list = []

            for size in sizes:
                if size <= img.size[0]:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    img_list.append(resized)

            # Remove duplicates
            seen = set()
            unique_list = []
            for im in img_list:
                if im.size not in seen:
                    seen.add(im.size)
                    unique_list.append(im)

            ico_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(ico_path, format='ICO', sizes=[im.size for im in unique_list])
            print(f"[OK] Generated Windows ICO: {ico_path}")
            return True
        except Exception as e:
            print(f"[WARN] Failed to generate ICO: {e}")
            return False

    return True


def check_npm_available() -> bool:
    """Check if npm is available."""
    return shutil.which("npm") is not None


def build_frontend():
    """Build frontend and copy to static/dist."""
    root = get_project_root()
    frontend_path = root / "frontend"
    static_dist = root / "static" / "dist"

    # Check npm
    if not check_npm_available():
        print("[WARN] npm not found, skipping frontend build")
        print("[INFO] Make sure to run 'npm install && npm run build' in frontend/ directory first")
        return False

    # Use shell=True on Windows to find npm
    use_shell = sys.platform == "win32"
    # Common subprocess options for cross-platform compatibility
    subprocess_kwargs = {
        "cwd": frontend_path,
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "shell": use_shell
    }

    # Install frontend dependencies
    print("[BUILD] Installing frontend dependencies...")
    result = subprocess.run("npm install", **subprocess_kwargs)
    if result.returncode != 0:
        print(f"[ERROR] npm install failed: {result.stderr}")
        return False
    print("[OK] Frontend dependencies installed")

    # Build frontend
    print("[BUILD] Building frontend...")
    result = subprocess.run("npm run build", **subprocess_kwargs)
    if result.returncode != 0:
        print(f"[ERROR] npm run build failed: {result.stderr}")
        return False
    print("[OK] Frontend built")

    # Ensure static/dist exists
    static_dist.mkdir(parents=True, exist_ok=True)

    # Copy frontend/dist to static/dist
    print(f"[BUILD] Copying frontend build to {static_dist}...")
    frontend_dist = frontend_path / "dist"
    if not frontend_dist.exists():
        print(f"[ERROR] Frontend dist not found: {frontend_dist}")
        return False

    # Clean old static/dist content
    if static_dist.exists():
        shutil.rmtree(static_dist)

    # Copy
    shutil.copytree(frontend_dist, static_dist)
    print("[OK] Frontend build copied to static/dist")

    # Inject Vite assets into template
    print("[BUILD] Injecting Vite assets...")
    inject_script = root / "scripts" / "inject-vite-assets.py"
    if inject_script.exists():
        result = subprocess.run(
            [sys.executable, str(inject_script)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"[WARN] Failed to inject Vite assets: {result.stderr}")
        else:
            print("[OK] Vite assets injected")
    else:
        print(f"[WARN] Inject script not found: {inject_script}")

    return True


def get_icon_path(root: Path) -> str:
    """Get icon path for current platform."""
    # Check for platform-specific icons first
    if sys.platform == "darwin":
        # macOS: Check for .icns file first
        icns_path = root / "static" / "app.icns"
        if icns_path.exists():
            return str(icns_path)
        # Fallback to PNG (will be converted to ICNS later)
        png_path = root / "static" / "favicon.png"
        if png_path.exists():
            return str(png_path)
    elif sys.platform == "win32":
        # Windows: Check for .ico file
        ico_path = root / "static" / "app.ico"
        if ico_path.exists():
            return str(ico_path)
        # Fallback to PNG
        png_path = root / "static" / "favicon.png"
        if png_path.exists():
            return str(png_path)
    else:
        # Linux: Use PNG
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

    # Debug mode (only enable when explicitly requested)
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
        # 统一使用 Anime1 作为目录名（跨平台一致）
        cmd.extend(["--name=Anime1", entry_point])
        print(f"[BUILD] App name: Anime1")

    # Icon for macOS and Windows
    icon_path = get_icon_path(root)
    if icon_path:
        if sys.platform == "darwin" and not args.onefile:
            cmd.extend(["--icon", icon_path])
            print(f"[BUILD] macOS Icon: {icon_path}")
        elif sys.platform == "win32":
            cmd.extend(["--icon", icon_path])
            print(f"[BUILD] Windows Icon: {icon_path}")

    # Custom Info.plist for macOS (to set proper menu bar name)
    plist_path = get_plist_path(root)
    if plist_path and sys.platform == "darwin":
        cmd.extend(["--osx-bundle-identifier", "com.anime1.app"])
        print(f"[BUILD] Bundle ID: com.anime1.app")

    # Disable code signing on macOS to avoid cross-machine issues
    if sys.platform == "darwin":
        cmd.extend(["--codesign-identity", "-"])
        print("[BUILD] Code signing disabled")

    # Hidden imports for pywebview and dependencies
    # Use --collect-all for modules with complex dependencies (flask_cors, pywebview)
    hidden_imports = [
        "jinja2", "markupsafe", "werkzeug",
        "requests", "requests.utils", "requests.auth",
        "urllib3", "urllib3.util", "urllib3.connection",
        "beautifulsoup4", "soupsieve", "bs4", "bs4.builder",
        "hanziconv",
        "threading", "socket", "webbrowser", "argparse", "json", "click",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Use --collect-all for flask_cors and flask (they have complex dependencies)
    for imp in ["flask_cors", "flask"]:
        cmd.extend(["--collect-all", imp])

    # Add hooks directory for custom PyInstaller hooks
    hooks_path = root / "hooks"
    if hooks_path.exists():
        cmd.extend([f"--additional-hooks-dir={hooks_path}"])

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

    # Set environment to handle encoding issues on Windows
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    if sys.platform == "win32":
        env['PYTHONUTF8'] = '0'  # Disable UTF-8 mode on Windows to avoid conflicts

    print("[DEBUG] Running PyInstaller...")
    result = subprocess.run(cmd, env=env)
    print(f"[DEBUG] PyInstaller finished with code: {result.returncode}")

    # Check if build succeeded by verifying output file exists
    # PyInstaller may return non-zero exit code due to ERROR messages even on successful build
    exe_exists = False
    if sys.platform == "win32" and args.onefile:
        exe_path = dist_path / "anime1.exe"
        exe_exists = exe_path.exists()
    elif sys.platform == "darwin" and args.onefile:
        exe_path = dist_path / "anime1"
        exe_exists = exe_path.exists()
    elif sys.platform == "linux" and args.onefile:
        exe_path = dist_path / "anime1"
        exe_exists = exe_path.exists()
    elif sys.platform == "darwin" and not args.onefile:
        exe_path = dist_path / "Anime1.app"
        exe_exists = exe_path.exists()

    if exe_exists or result.returncode == 0:
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
    elif not exe_exists:
        print("\n[ERROR] Build failed! Output file not found.")
        sys.exit(1)
    else:
        print("\n[WARNING] Build completed with warnings but output file was created.")


def get_size(path: Path) -> str:
    """Get human readable size."""
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def fix_macos_app_info_plist(app_path: Path):
    """Fix macOS app bundle Info.plist to show proper menu bar name."""
    info_plist_path = app_path / "Contents" / "Info.plist"
    if not info_plist_path.exists():
        print(f"[WARN] Info.plist not found: {info_plist_path}")
        return

    try:
        # Read the Info.plist
        with open(info_plist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update CFBundleName and CFBundleDisplayName to show properly in menu bar
        # If not already set, set CFBundleDisplayName to "Anime1"
        if 'CFBundleDisplayName' not in content:
            # Find the position after CFBundleName and add CFBundleDisplayName
            content = content.replace(
                '<key>CFBundleName</key>',
                '<key>CFBundleDisplayName</key>\n\t<string>Anime1</string>\n\t<key>CFBundleName</key>'
            )

        # Write back
        with open(info_plist_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[BUILD] Updated Info.plist for proper menu bar name")
    except Exception as e:
        print(f"[WARN] Failed to update Info.plist: {e}")


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


def generate_nsis_script(app_dir: Path, project_root: Path) -> str:
    """Generate NSIS script for Windows installer."""
    app_dir_rel = str(app_dir.relative_to(project_root)).replace('\\', '/')

    nsis_template = '''; Anime1 Desktop Windows Installer (NSIS)
; Auto-generated by build.py

SetCompressor /SOLID lzma

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - Anime Browser"
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define INSTALLSIZE 120000
!define INSTDIR "$PROGRAMFILES\\${APPNAME}"

Name "${APPNAME}"
Caption "${APPNAME} v${VERSIONMAJOR}.${VERSIONMINOR} - Installation Wizard"
OutFile "${SRCDIR}\\\\release\\\\anime1-windows-x64-setup.exe"
InstallDir "${INSTDIR}"
InstallDirRegKey HKLM "Software\\${COMPANYNAME}\\${APPNAME}" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show

VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=2052 "CompanyName" "${COMPANYNAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "${DESCRIPTION}"
VIAddVersionKey /LANG=2052 "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.0.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024 ${COMPANYNAME}. All rights reserved."

!include LogicLib.nsh

Function .onInit
    InitPluginsDir
FunctionEnd

Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "Main Application" SecMain
    SectionIn RO

    SetOutPath "$INSTDIR"
    File /r "${SRCDIR}\\${APPDIR}\\*"

    IfFileExists "$INSTDIR\\app.ico" 0 SkipIcon

    CreateDirectory "$SMPROGRAMS\\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\Anime1.exe" "" "$INSTDIR\\app.ico" 0
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\Anime1.exe" "" "$INSTDIR\\app.ico" 0
    Goto AfterShortcuts

SkipIcon:
    CreateDirectory "$SMPROGRAMS\\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\Anime1.exe"
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\Anime1.exe"

AfterShortcuts:
    WriteUninstaller "$INSTDIR\\Uninstall.exe"

    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "UninstallString" '"$INSTDIR\\Uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "DisplayIcon" "$INSTDIR\\app.ico"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "Publisher" "${COMPANYNAME}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" \\
                     "EstimatedSize" ${INSTALLSIZE}

    WriteRegStr HKLM "Software\\${COMPANYNAME}\\${APPNAME}" \\
                     "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\${COMPANYNAME}\\${APPNAME}" \\
                     "Version" "${VERSIONMAJOR}.${VERSIONMINOR}"

    SetAutoClose true

SectionEnd

Section "Uninstall"

    Delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\\${APPNAME}"
    Delete "$DESKTOP\\${APPNAME}.lnk"

    Delete "$INSTDIR\\*.*"
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
    DeleteRegKey HKLM "Software\\${COMPANYNAME}\\${APPNAME}"

    SetAutoClose true

SectionEnd
'''
    src_dir = str(project_root).replace('\\', '/')
    nsis_script = nsis_template.replace('${SRCDIR}', src_dir)
    nsis_script = nsis_script.replace('${APPDIR}', app_dir_rel)
    return nsis_script


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


def create_installer():
    """Create Windows installer (NSIS) and prepare release files."""
    if sys.platform != "win32":
        print("[SKIP] NSIS installer is only for Windows")
        return

    root = get_project_root()
    dist_path = root / "dist"
    release_path = root / "release"

    # Find the EXE file
    exe_path = dist_path / "anime1.exe"
    if not exe_path.exists():
        exe_path = dist_path / "Anime1.exe"
    if not exe_path.exists():
        print("[ERROR] EXE file not found in dist folder")
        return

    print("\n[INSTALLER] Preparing release files...")

    # Create release directory
    release_path.mkdir(parents=True, exist_ok=True)

    # Copy EXE to release
    exe_dst = release_path / exe_path.name
    shutil.copy2(exe_path, exe_dst)
    print(f"[OK] Copied: {exe_path.name} -> release/")

    # Check for NSIS
    import shutil as shutil_module
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    makensis_path = None
    for path in nsis_paths:
        if Path(path).exists():
            makensis_path = path
            print(f"[OK] NSIS found: {makensis_path}")
            break

    if not makensis_path:
        makensis_path = shutil_module.which("makensis")
        if makensis_path:
            print(f"[OK] NSIS found: {makensis_path}")

    if not makensis_path:
        print("[WARN] NSIS not found, skipping installer")
        print("[INFO] Install with: choco install nsis")
        return

    # Create app.ico in dist folder for NSIS
    ico_src = root / "static" / "app.ico"
    ico_dst = dist_path / "app.ico"
    if ico_src.exists() and not ico_dst.exists():
        shutil.copy2(ico_src, ico_dst)
        print(f"[OK] Copied app.ico to dist folder")

    # Generate NSIS script
    nsis_script = generate_nsis_script(dist_path, root)
    nsis_script_path = root / "scripts" / "installer_temp.nsi"
    nsis_script_path.write_text(nsis_script, encoding='utf-8')
    print(f"[OK] Generated NSIS script")

    # Run NSIS
    cmd = [makensis_path, str(nsis_script_path)]
    print(f"[BUILD] Running NSIS...")
    result = subprocess.run(cmd, cwd=str(root))

    # Clean up temp script
    if nsis_script_path.exists():
        nsis_script_path.unlink()

    if result.returncode == 0:
        installer_path = release_path / "anime1-windows-x64-setup.exe"
        if installer_path.exists():
            size = installer_path.stat().st_size / (1024 * 1024)
            print(f"[OK] Installer created: anime1-windows-x64-setup.exe ({size:.1f} MB)")
    else:
        print("[ERROR] NSIS failed to create installer")

    # Cleanup build directory
    build_path = root / "build"
    if build_path.exists():
        shutil.rmtree(build_path)
        print("[OK] Cleaned up build directory")


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
    parser.add_argument(
        "--build-frontend", action="store_true",
        help="Build frontend before building the app"
    )
    parser.add_argument(
        "--installer", action="store_true",
        help="Create installer package (NSIS on Windows, DMG on macOS)"
    )

    args = parser.parse_args()

    print(f"Python: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Project root: {get_project_root()}")

    verify_dependencies()

    if args.clean:
        clean_dist()

    # Generate icons (Windows only)
    if sys.platform == "win32":
        print("[BUILD] Generating Windows icons...")
        generate_icons()

    # Build frontend if requested
    if args.build_frontend:
        print("\n[FRONTEND] Building frontend...")
        if not build_frontend():
            print("[ERROR] Frontend build failed!")
            sys.exit(1)
        print("")

    run_pyinstaller(args)

    # Create installer if requested
    if args.installer:
        if sys.platform == "win32":
            create_installer()
        elif sys.platform == "darwin":
            print("[SKIP] macOS installer creation not implemented yet")
        else:
            print("[SKIP] Linux installer creation not implemented yet")


if __name__ == "__main__":
    main()
