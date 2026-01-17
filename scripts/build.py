#!/usr/bin/env python3
"""
Build script for Anime1 desktop application.

Usage:
    python build.py                    # Build for current platform
    python build.py --clean            # Clean dist folder first
    python build.py --onefile          # Create single executable (larger file)
    python build.py --debug            # Build with debug mode
    python build.py --remote           # Build CLI version (browser-based)
    python build.py --installer        # Create installer/package after build
    python build.py --all              # Build all platforms (CI/CD only)

Requirements:
    pip install pyinstaller pywebview

Output:
    release/                           # Final distribution files
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory (works from any location)."""
    # Start from current file's directory
    current = Path(__file__).resolve()
    # Look for project markers to find root
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / "src").exists():
            return parent
    # Fallback to current directory's parent
    return current.parent


def get_size(path: Path) -> str:
    """Get human readable size."""
    if not path.exists():
        return "N/A"
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ============ Version Functions ============

def extract_version() -> str:
    """Extract version from git tag or commit id."""
    root = get_project_root()

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
            version = tag.lstrip('vV')
            return version
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

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

    return "dev"


# ============ Icon Generation ============

def generate_windows_icon():
    """Generate Windows ICO from PNG."""
    root = get_project_root()
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


def generate_macos_icon():
    """Generate macOS ICNS from PNG."""
    root = get_project_root()
    png_path = root / "static" / "favicon.png"
    icns_path = root / "static" / "app.icns"

    if not png_path.exists():
        print(f"[WARN] Source PNG not found: {png_path}")
        return False

    try:
        from PIL import Image
        img = Image.open(png_path)
        # macOS icons are typically 1024x1024 for Retina
        sizes = [256, 512, 1024, 2048]
        img_list = []

        for size in sizes:
            if size <= img.size[0]:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                img_list.append(resized)

        seen = set()
        unique_list = []
        for im in img_list:
            if im.size not in seen:
                seen.add(im.size)
                unique_list.append(im)

        icns_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(icns_path, format='ICNS', sizes=[im.size for im in unique_list])
        print(f"[OK] Generated macOS ICNS: {icns_path}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to generate ICNS: {e}")
        return False


# ============ macOS Specific ============

def fix_macos_app_info_plist(app_path: Path):
    """Fix macOS app bundle Info.plist."""
    info_plist_path = app_path / "Contents" / "Info.plist"
    if not info_plist_path.exists():
        print(f"[WARN] Info.plist not found: {info_plist_path}")
        return

    try:
        with open(info_plist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'CFBundleDisplayName' not in content:
            content = content.replace(
                '<key>CFBundleName</key>',
                '<key>CFBundleDisplayName</key>\n\t<string>Anime1</string>\n\t<key>CFBundleName</key>'
            )

        with open(info_plist_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[BUILD] Updated Info.plist for proper menu bar name")
    except Exception as e:
        print(f"[WARN] Failed to update Info.plist: {e}")


def fix_macos_app_icon(app_path: Path, icon_path: str):
    """Copy icon to macOS app bundle."""
    if not icon_path:
        print(f"[WARN] No icon file found")
        return

    icon_file = Path(icon_path).name
    icon_src = Path(icon_path)
    resources_path = app_path / "Contents" / "Resources"

    if not resources_path.exists():
        print(f"[WARN] Resources path not found: {resources_path}")
        return

    try:
        icon_dst = resources_path / icon_file
        shutil.copy2(icon_src, icon_dst)
        print(f"[BUILD] Copied icon to app bundle: {icon_file}")

        if icon_file.endswith('.png') and icon_file != 'app.icns':
            icns_dst = resources_path / "app.icns"
            shutil.copy2(icon_src, icns_dst)
            print(f"[BUILD] Created app.icns from PNG")
    except Exception as e:
        print(f"[WARN] Could not copy icon: {e}")


def create_macos_dmg(app_path: Path, version: str):
    """Create macOS DMG from app bundle."""
    root = get_project_root()
    dmg_name = f"anime1-macos-{version}.dmg"

    # Check if create-dmg is available
    if not shutil.which("create-dmg"):
        print("[WARN] create-dmg not found, skipping DMG creation")
        print("[INFO] Install with: brew install create-dmg")
        return None

    try:
        # Create a temporary directory for DMG contents
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_app_path = Path(tmpdir) / "Anime1.app"
            shutil.copytree(app_path, tmp_app_path)

            # Create fix script for macOS
            fix_script = Path(tmpdir) / "fix_permissions.sh"
            fix_script.write_text('''#!/bin/bash
# Fix macOS app permissions for cross-machine usage
chmod -R u+w "$1/Contents/Resources" 2>/dev/null || true
echo "Permissions fixed. You can now move Anime1.app to /Applications/"
''')
            fix_script.chmod(0o755)

            dmg_path = root / "release" / dmg_name
            dmg_path.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run([
                "create-dmg",
                "--volname", "Anime1",
                "--window-size", "500", "400",
                "--icon-size", "100",
                "--icon", "Anime1.app", "150", "150",
                "--icon", "fix_permissions.sh", "350", "150",
                "--hide-extension", "Anime1.app",
                "--app-drop-link", "400", "150",
                str(dmg_path),
                str(tmpdir)
            ], capture_output=True, text=True)

            if result.returncode == 0 and dmg_path.exists():
                print(f"[OK] Created DMG: {dmg_path}")
                print(f"  Size: {get_size(dmg_path)}")
                return dmg_path
            else:
                print(f"[WARN] create-dmg failed: {result.stderr}")
                return None
    except Exception as e:
        print(f"[WARN] Failed to create DMG: {e}")
        return None


# ============ Windows Specific ============

def create_windows_installer(version: str):
    """Create Windows NSIS installer."""
    root = get_project_root()
    dist_path = root / "dist"
    release_path = root / "release"
    release_path.mkdir(parents=True, exist_ok=True)

    # Find NSIS
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    makensis_path = None
    for path in nsis_paths:
        if Path(path).exists():
            makensis_path = path
            break

    if not makensis_path:
        makensis_path = shutil.which("makensis")

    if not makensis_path:
        print("[WARN] NSIS not found, skipping installer")
        print("[INFO] Install with: choco install nsis")
        return None

    # Generate Windows icon
    generate_windows_icon()
    ico_src = root / "static" / "app.ico"
    ico_dst = dist_path / "app.ico"
    if ico_src.exists() and dist_path.exists():
        shutil.copy2(ico_src, ico_dst)

    # Generate NSIS script
    dist_path_abs = str(dist_path.resolve())
    release_path_abs = str((root / "release").resolve())
    nsis_script = f'''; Anime1 Desktop Windows Installer
; Auto-generated by build.py

!include LogicLib.nsh

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - Anime Browser"
!define VERSIONMAJOR 0
!define VERSIONMINOR 0
!define INSTALLSIZE 120000
!define INSTDIR "$PROGRAMFILES\\${{APPNAME}}"
!define VERSION "{version}"

Name "${{APPNAME}} v${{VERSION}}"
Caption "${{APPNAME}} v${{VERSION}} - Installation Wizard"
OutFile "{release_path_abs}\\anime1-windows-x64-setup.exe"
InstallDir "${{INSTDIR}}"
InstallDirRegKey HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show

VIProductVersion "0.0.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${{APPNAME}}"
VIAddVersionKey /LANG=2052 "CompanyName" "${{COMPANYNAME}}"
VIAddVersionKey /LANG=2052 "FileDescription" "${{DESCRIPTION}}"
VIAddVersionKey /LANG=2052 "FileVersion" "0.0.0.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2024 ${{COMPANYNAME}}"

Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "Main Application" SecMain
    SectionIn RO

    SetOutPath "$INSTDIR"
    File /r "{dist_path_abs}\\*"

    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\Anime1.exe" "" "$INSTDIR\\app.ico" 0
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\Anime1.exe" "" "$INSTDIR\\app.ico" 0

    SetOutPath "$INSTDIR"
    WriteUninstaller "$INSTDIR\\Uninstall.exe"

    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "UninstallString" '"$INSTDIR\\Uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "DisplayIcon" "$INSTDIR\\app.ico"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "Publisher" "${{COMPANYNAME}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "VersionMajor" 0
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "VersionMinor" 0
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "EstimatedSize" ${{INSTALLSIZE}}

    WriteRegStr HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" \
                     "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" \
                     "Version" "0.0"

    SetAutoClose true
SectionEnd

Section "Uninstall"
    Delete "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk"
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    RMDir "$SMPROGRAMS\\${{APPNAME}}"

    Delete "$INSTDIR\\*.*"
    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
    DeleteRegKey HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}"

    SetAutoClose true
SectionEnd
'''

    nsis_script_path = root / "scripts" / "installer_temp.nsi"
    nsis_script_path.write_text(nsis_script, encoding='utf-8')

    try:
        result = subprocess.run(
            [makensis_path, str(nsis_script_path)],
            cwd=str(root),
            capture_output=True,
            text=True
        )

        installer_path = root / "release" / "anime1-windows-x64-setup.exe"
        if installer_path.exists():
            size = installer_path.stat().st_size / (1024 * 1024)
            print(f"[OK] Created installer: {installer_path}")
            print(f"  Size: {size:.1f} MB")
            return installer_path
        else:
            print(f"[WARN] NSIS completed but installer not found")
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr}")
            return None
    except Exception as e:
        print(f"[WARN] Failed to create installer: {e}")
        return None
    finally:
        if nsis_script_path.exists():
            nsis_script_path.unlink()


# ============ Linux Specific ============

def create_linux_tarball(exe_path: Path, version: str):
    """Create Linux tarball from executable."""
    root = get_project_root()
    tar_name = f"anime1-linux-x64.tar.gz"

    try:
        tar_path = root / "release" / tar_name
        tar_path.parent.mkdir(parents=True, exist_ok=True)

        with tarfile.open(tar_path, "w:gz") as tar:
            # Add the executable
            tar.add(exe_path, arcname="Anime1")

            # Add icon if exists
            icon_path = root / "static" / "favicon.png"
            if icon_path.exists():
                tar.add(icon_path, arcname="anime1.png")

            # Add README
            readme_content = f'''# Anime1 Desktop {version}

## Installation

1. Extract the archive:
   tar -xzf anime1-linux-x64.tar.gz

2. Add execute permission:
   chmod +x Anime1

3. Run the application:
   ./Anime1

## Requirements

- WebView2 Runtime (installed automatically on most distributions)
- For Ubuntu/Debian: sudo apt install webview2
'''
            info = tarfile.TarInfo(name="README.txt")
            info.size = len(readme_content.encode())
            tar.addfile(info, BytesIO(readme_content.encode()))

        print(f"[OK] Created tarball: {tar_path}")
        print(f"  Size: {get_size(tar_path)}")
        return tar_path
    except Exception as e:
        print(f"[WARN] Failed to create tarball: {e}")
        return None


# ============ Common Package Functions ============

def create_portable_zip(exe_path: Path, version: str):
    """Create portable zip package (Windows/Linux)."""
    root = get_project_root()
    dist_path = root / "dist"
    zip_name = f"anime1-windows-x64.zip" if sys.platform == "win32" else f"anime1-linux-x64.tar.gz"

    try:
        zip_path = root / "release" / zip_name
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        if sys.platform == "win32":
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add executable
                zf.write(exe_path, arcname="Anime1.exe")

                # Add icon
                icon_path = dist_path / "app.ico"
                if icon_path.exists():
                    zf.write(icon_path, arcname="app.ico")

                # Add README
                readme = f'''# Anime1 Desktop {version}

## Portable Version

Extract and run Anime1.exe directly.

Note: Requires WebView2 Runtime on Windows.
'''
                zf.writestr("README.txt", readme)
        else:
            return create_linux_tarball(exe_path, version)

        print(f"[OK] Created portable zip: {zip_path}")
        print(f"  Size: {get_size(zip_path)}")
        return zip_path
    except Exception as e:
        print(f"[WARN] Failed to create zip: {e}")
        return None


# ============ Frontend Build Functions ============

# Windows 需要 shell=True 来运行 npm
USE_SHELL = sys.platform == "win32"


def run_subprocess(cmd, cwd=None, timeout=300, check=True):
    """Run subprocess with consistent settings (handles Windows shell=True and UTF-8 encoding)."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=USE_SHELL,
        check=check,
        encoding='utf-8',
    )


def build_frontend(args) -> bool:
    """Build the Vue frontend application.

    Returns True if successful, False otherwise.
    """
    root = get_project_root()
    frontend_dir = root / "frontend"
    dist_dir = root / "static" / "dist"

    # Check if npm is available
    try:
        result = run_subprocess(["npm", "--version"], timeout=5, check=False)
        if result.returncode != 0:
            print("[WARN] npm is not available, skipping frontend build")
            return False
    except (FileNotFoundError, subprocess.SubprocessError):
        print("[WARN] npm not found, skipping frontend build")
        return False

    # Check if frontend directory exists
    if not frontend_dir.exists():
        print("[WARN] frontend directory not found, skipping frontend build")
        return False

    # Clean frontend dist if requested
    if args.clean and dist_dir.exists():
        print("[BUILD] Cleaning frontend dist directory...")
        shutil.rmtree(dist_dir)

    print("[BUILD] Building frontend...")
    try:
        # Install dependencies and build
        result = run_subprocess(["npm", "ci"], cwd=frontend_dir, check=False)
        if result.returncode != 0:
            print(f"[ERROR] npm ci failed: {result.stderr}")
            return False

        result = run_subprocess(["npm", "run", "build"], cwd=frontend_dir, check=False)
        if result.returncode != 0:
            print(f"[ERROR] npm run build failed: {result.stderr}")
            return False

        # Check if build output exists
        if not dist_dir.exists():
            print("[ERROR] Frontend build completed but output directory not found")
            return False

        print(f"[BUILD] Frontend built successfully to {dist_dir}")
        return True

    except subprocess.TimeoutExpired:
        print("[ERROR] Frontend build timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Frontend build failed: {e}")
        return False


# ============ Main Build Functions ============

def run_pyinstaller(args):
    """Run PyInstaller with specified options."""
    root = get_project_root()
    dist_path = root / "dist"
    work_path = root / "build"

    # Extract version
    version = extract_version()
    os.environ["ANIME1_VERSION"] = version
    print(f"[BUILD] Version: {version}")

    # Create version file
    version_file = root / "src" / "_version.txt"
    version_file.write_text(version, encoding='utf-8')

    # Clean if requested
    if args.clean and dist_path.exists():
        shutil.rmtree(dist_path)

    dist_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean", "--noconfirm",
        f"--distpath={dist_path}",
        f"--workpath={work_path}",
    ]

    # Windowed mode (no console) for desktop app on Windows
    cmd.extend(["--windowed", "--noconsole"])

    # Single file or directory
    if args.onefile:
        cmd.append("--onefile")
        print("[BUILD] Mode: single executable (onefile)")
    else:
        cmd.append("--onedir")
        print("[BUILD] Mode: directory bundle (onedir)")

    if args.debug:
        cmd.append("--debug=all")
        print("[BUILD] Debug mode: enabled")

    # Entry point
    if args.remote:
        entry_point = str(root / "src" / "app.py")
        cmd.extend(["--name=anime1-cli", entry_point])
        print("[BUILD] Mode: CLI (browser-based)")
    else:
        entry_point = str(root / "src" / "desktop.py")
        cmd.extend(["--name=Anime1", entry_point])

    # Icon
    icon_path = get_icon_path(root)
    if icon_path:
        if sys.platform == "darwin" and not args.onefile:
            cmd.extend(["--icon", icon_path])
        elif sys.platform == "win32":
            cmd.extend(["--icon", icon_path])

    # macOS bundle identifier
    if sys.platform == "darwin":
        cmd.extend(["--osx-bundle-identifier", "com.anime1.app"])
        cmd.extend(["--codesign-identity", "-"])

    # Hidden imports
    hidden_imports = [
        "flask", "flask_cors", "flask.templating", "jinja2", "markupsafe", "werkzeug",
        "requests", "requests.utils", "requests.auth",
        "urllib3", "urllib3.util", "urllib3.connection",
        "beautifulsoup4", "soupsieve", "bs4", "bs4.builder",
        "pywebview", "pywebview.guarded_encodings", "pywebview.util", "pywebview.http",
        "hanziconv", "threading", "socket", "webbrowser", "argparse", "json", "click",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Excludes
    for ex in ["tkinter", "test", "unittest", "pydoc", "doctest", "pdb"]:
        cmd.extend(["--exclude-module", ex])

    # Data files
    datas = [
        (str(root / "static"), "static"),
        (str(root / "src"), "src"),
        (str(root / "distInfo.plist"), "."),
    ]

    frontend_dist = root / "static" / "dist"
    if frontend_dist.exists():
        datas.append((str(frontend_dist), "static/dist"))

    if version_file.exists():
        datas.append((str(version_file), "src"))

    for src, dst in datas:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    print(f"\n{'='*60}")
    print("Building Anime1...")
    print(f"{'='*60}\n")
    print(f"[INFO] Python: {sys.executable}")
    print(f"[INFO] Platform: {sys.platform}")
    print(f"[INFO] Output: {dist_path}")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\n[ERROR] Build failed!")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("[SUCCESS] Build completed!")
    print(f"{'='*60}")

    # Post-build actions based on platform
    if sys.platform == "darwin" and not args.onefile:
        app_path = dist_path / "Anime1.app"
        if app_path.exists():
            fix_macos_app_info_plist(app_path)
            fix_macos_app_icon(app_path, icon_path)
            print(f"macOS App: {app_path}")
            print(f"  Size: {get_size(app_path)}")

    # Find executable
    if sys.platform == "win32":
        exe_name = "anime1.exe"
    elif sys.platform == "darwin":
        exe_name = "anime1"
    else:
        exe_name = "anime1"

    exe_path = dist_path / exe_name
    if not exe_path.exists():
        # Try alternative names
        for name in dist_path.iterdir():
            if name.is_file() and (name.suffix == '.exe' or name.name.lower() in ['anime1', 'anime1.exe']):
                exe_path = name
                break

    if exe_path.exists():
        print(f"\nExecutable: {exe_path}")
        print(f"  Size: {get_size(exe_path)}")

    # Create installer/package if requested
    if args.installer:
        create_platform_package(exe_path, version)

    print("\n[DONE] Ready for distribution!")


def get_icon_path(root: Path) -> str:
    """Get icon path for current platform."""
    if sys.platform == "darwin":
        icns_path = root / "static" / "app.icns"
        if icns_path.exists():
            return str(icns_path)
        png_path = root / "static" / "favicon.png"
        if png_path.exists():
            return str(png_path)
    elif sys.platform == "win32":
        ico_path = root / "static" / "app.ico"
        if ico_path.exists():
            return str(ico_path)
        png_path = root / "static" / "favicon.png"
        if png_path.exists():
            return str(png_path)
    else:
        png_path = root / "static" / "favicon.png"
        if png_path.exists():
            return str(png_path)
    return ""


def create_platform_package(exe_path: Path, version: str):
    """Create platform-specific package/installer."""
    root = get_project_root()
    release_path = root / "release"
    release_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("Creating distribution package...")
    print(f"{'='*60}\n")

    if sys.platform == "win32":
        # Windows: NSIS installer + portable zip
        print("[BUILD] Creating Windows installer...")
        create_windows_installer(version)
        create_portable_zip(exe_path, version)

    elif sys.platform == "darwin":
        # macOS: DMG
        print("[BUILD] Creating macOS DMG...")
        dist_path = root / "dist"
        app_path = dist_path / "Anime1.app"
        if app_path.exists():
            create_macos_dmg(app_path, version)
        else:
            print("[WARN] App bundle not found, skipping DMG")

    elif sys.platform == "linux":
        # Linux: tarball
        print("[BUILD] Creating Linux tarball...")
        create_linux_tarball(exe_path, version)

    # List release files
    print(f"\n[RELEASE] Files in {release_path}:")
    for f in sorted(release_path.iterdir()):
        print(f"  {f.name} ({get_size(f)})")


# ============ Main Entry ============

def verify_dependencies():
    """Check if required packages are installed."""
    print("[VERIFY] Checking dependencies...")
    missing = []

    try:
        import PyInstaller
        print(f"  [OK] PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print(f"  [MISSING] PyInstaller")
        missing.append("pyinstaller")

    try:
        import webview
        print(f"  [OK] pywebview: installed")
    except ImportError:
        print(f"  [MISSING] pywebview")
        missing.append("pywebview")

    if missing:
        print(f"\n[ERROR] Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install pyinstaller pywebview")
        sys.exit(1)
    print("")


def main():
    parser = argparse.ArgumentParser(description="Build Anime1 desktop application")
    parser.add_argument("--clean", action="store_true", help="Clean dist folder before building", default=True)
    parser.add_argument("--onefile", action="store_true", default=True, help="Create single executable (larger file)")
    parser.add_argument("--debug", action="store_true", help="Build with debug mode")
    parser.add_argument("--remote", action="store_true", help="Build CLI version (browser-based)")
    parser.add_argument("--installer", action="store_true", default=True, help="Create installer/package after build")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build")

    args = parser.parse_args()

    print(f"Python: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Project root: {get_project_root()}")

    # Build frontend first
    if not args.skip_frontend:
        frontend_success = build_frontend(args)
        if not frontend_success:
            print("[ERROR] Frontend build failed, aborting")
            sys.exit(1)

    verify_dependencies()
    run_pyinstaller(args)


if __name__ == "__main__":
    main()
