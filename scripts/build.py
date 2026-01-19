#!/usr/bin/env python3
"""
Build script for Anime1 desktop application.

Usage:
    python build.py                    # Build for current platform (onefile)
    python build.py --clean            # Clean dist folder first
    python build.py --debug            # Build with debug mode
    python build.py --remote           # Build CLI version (browser-based)
    python build.py --all              # Build all platforms (CI/CD only)
    python build.py --version v0.1.0   # Specify version for testing updates

Examples:
    # Build for current platform (onefile mode - default)
    python build.py

    # Build with specific version to test update detection
    python build.py --version v0.1.0

    # Build with dev version (includes commit hash)
    python build.py --version 0.2.0-abc123

    # Clean and build
    python build.py --clean

Requirements:
    pip install pyinstaller pywebview

Output:
    release/                           # Final distribution files
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path


# ============ Constants ============

# Resource file paths (relative to project root)
DISTINFO_PLIST_TEMPLATE = "scripts/resources/distInfo.plist.template"


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

def normalize_version(version: str) -> str:
    """Normalize version string by removing 'v' prefix if present.

    Args:
        version: Version string like "v0.2.1", "V0.2.1", or "0.2.1"

    Returns:
        Normalized version without 'v' prefix
    """
    return version.lstrip('vV')


def parse_version_string(version_str: str) -> tuple:
    """Parse version string into (base_version, is_dev) tuple.

    Args:
        version_str: Version like "0.2.1", "0.2.1-abc123", or "v0.1.0"

    Returns:
        (base_version, is_dev) - base_version is "0.2.1", is_dev indicates dev build
    """
    # Remove 'v' prefix
    version = normalize_version(version_str)

    # Check if it has a commit hash suffix (dev version)
    if '-' in version and len(version.split('-')) == 2:
        parts = version.split('-', 1)
        base_version = parts[0]
        commit_hash = parts[1]

        # Check if commit hash looks valid (alphanumeric, 4-40 chars)
        if commit_hash and len(commit_hash) >= 4 and len(commit_hash) <= 40 and commit_hash.replace('_', '').replace('-', '').isalnum():
            return version, True  # It's a dev version

    # Check if it's a prerelease version (alpha, beta, rc)
    if any(x in version for x in ['-alpha', '-beta', '-rc', '-dev']):
        return version, True

    # Regular release version
    return version, False


def create_dist_info_plist_template():
    """Create a template distInfo.plist file if it doesn't exist.

    Uses the template from scripts/resources/distInfo.plist.template
    """
    root = get_project_root()
    plist_path = root / "distInfo.plist"

    if plist_path.exists():
        return

    # Copy from bundled template
    template_path = root / DISTINFO_PLIST_TEMPLATE
    if template_path.exists():
        shutil.copy(template_path, plist_path)
        print(f"[BUILD] Created distInfo.plist from template")
    else:
        raise FileNotFoundError(f"distInfo.plist template not found: {template_path}")


def update_dist_info_plist(version: str):
    """Update the distInfo.plist with the correct version number.

    Args:
        version: Version string like "0.2.1" or "0.2.1-abc123"
    """
    root = get_project_root()
    plist_path = root / "distInfo.plist"

    # Create template if doesn't exist
    if not plist_path.exists():
        create_dist_info_plist_template()

    try:
        with open(plist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract major.minor.patch from version (e.g., "0.2.1-abc123" -> "0.2.1")
        base_version = version.split('-')[0]
        version_parts = base_version.split('.')
        major = version_parts[0] if len(version_parts) > 0 else "0"
        minor = version_parts[1] if len(version_parts) > 1 else "0"
        patch = version_parts[2] if len(version_parts) > 2 else "0"

        # Update CFBundleShortVersionString (e.g., "0.2.1")
        content = re.sub(
            r'<key>CFBundleShortVersionString</key>\s*<string>.*?</string>',
            f'<key>CFBundleShortVersionString</key>\n\t<string>{base_version}</string>',
            content
        )

        # Update CFBundleVersion (build number, use major*10000 + minor*100 + patch)
        try:
            build_number = int(major) * 10000 + int(minor) * 100 + int(patch)
            content = re.sub(
                r'<key>CFBundleVersion</key>\s*<string>.*?</string>',
                f'<key>CFBundleVersion</key>\n\t<string>{build_number}</string>',
                content
            )
        except ValueError:
            pass

        with open(plist_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[BUILD] Updated distInfo.plist version to {base_version}")
    except Exception as e:
        print(f"[WARN] Failed to update distInfo.plist: {e}")


def extract_version() -> str:
    """Extract version from git tag or commit id.

    Priority:
    1. If on a release tag, (e.g., use the tag version "0.2.0")
    2. Otherwise, use base_version-{commit_id} format (e.g., "0.2.0-abc123")

    This ensures dev versions are correctly compared against release versions:
    - v0.1.0 < v0.1.0-xyz456 < v0.2.0 < v0.2.0-abc123
    - Local dev versions are detected as having available updates
    """
    root = get_project_root()

    # First, get the base version from the latest tag
    base_version = "0.0.0"
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
            base_version = tag.lstrip('vV')
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    # Check if we're exactly on a release tag
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            # We're on a release tag, use this version
            tag = result.stdout.strip()
            version = tag.lstrip('vV')
            print(f"[BUILD] Using release tag version: {version}")
            return version
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    # If not on a release tag, use base_version-{commit_id}
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
            version = f"{base_version}-{commit_id}"
            print(f"[BUILD] Using dev version: {version}")
            return version
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    print("[BUILD] Using fallback version: 0.0.0-dev")
    return "0.0.0-dev"


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
    """Generate macOS ICNS from PNG using iconutil (native macOS tool)."""
    root = get_project_root()
    png_path = root / "static" / "favicon.png"
    icns_path = root / "static" / "app.icns"

    if not png_path.exists():
        print(f"[WARN] Source PNG not found: {png_path}")
        return False

    # Use system iconutil for proper ICNS format
    try:
        from PIL import Image
        img = Image.open(png_path)

        # Create temporary iconset directory
        iconset_path = root / "static" / "app.iconset"
        if iconset_path.exists():
            shutil.rmtree(iconset_path)
        iconset_path.mkdir(parents=True, exist_ok=True)

        # Generate standard macOS icon sizes
        sizes = {
            'icon_16x16.png': (16, 16),
            'icon_32x32.png': (32, 32),
            'icon_64x64.png': (64, 64),
            'icon_128x128.png': (128, 128),
            'icon_256x256.png': (256, 256),
            'icon_512x512.png': (512, 512),
        }

        for name, size in sizes.items():
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized.save(iconset_path / name)

        # Add @2x versions for Retina
        retina_sizes = {
            'icon_16x16@2x.png': (32, 32),
            'icon_32x32@2x.png': (64, 64),
            'icon_128x128@2x.png': (256, 256),
            'icon_256x256@2x.png': (512, 512),
            'icon_512x512@2x.png': (1024, 1024),
        }

        for name, size in retina_sizes.items():
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized.save(iconset_path / name)

        # Convert iconset to ICNS using native tool
        result = subprocess.run(
            ['iconutil', '--convert', 'icns', '--output', str(icns_path), str(iconset_path)],
            capture_output=True, text=True
        )

        # Clean up iconset
        shutil.rmtree(iconset_path)

        if result.returncode == 0 and icns_path.exists():
            print(f"[OK] Generated macOS ICNS: {icns_path}")
            return True
        else:
            print(f"[WARN] iconutil failed: {result.stderr}")
            raise Exception("iconutil failed")
    except Exception as e:
        print(f"[WARN] Failed to generate ICNS with iconutil: {e}")
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

        # Add icon file reference if not present
        if 'CFBundleIconFile' not in content:
            content = content.replace(
                '<key>CFBundleDisplayName</key>',
                '<key>CFBundleIconFile</key>\n\t<string>app.icns</string>\n\t<key>CFBundleDisplayName</key>'
            )

        with open(info_plist_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[BUILD] Updated Info.plist for proper menu bar name and icon")
    except Exception as e:
        print(f"[WARN] Failed to update Info.plist: {e}")


def fix_macos_app_icon(app_path: Path, icon_path: str):
    """Copy icon to macOS app bundle."""
    resources_path = app_path / "Contents" / "Resources"

    if not resources_path.exists():
        print(f"[WARN] Resources path not found: {resources_path}")
        return

    # First, generate ICNS if it doesn't exist
    root = get_project_root()
    icns_path = root / "static" / "app.icns"
    if not icns_path.exists():
        generate_macos_icon()

    # Copy the ICNS file
    icns_src = root / "static" / "app.icns"
    if icns_src.exists():
        try:
            icon_dst = resources_path / "app.icns"
            shutil.copy2(icns_src, icon_dst)
            print(f"[BUILD] Copied app.icns to app bundle")
        except Exception as e:
            print(f"[WARN] Could not copy app.icns: {e}")
    else:
        print(f"[WARN] ICNS file not found: {icns_src}")


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

            dmg_path = root / "release" / dmg_name
            dmg_path.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run([
                "create-dmg",
                "--volname", "Anime1",
                "--window-size", "500", "400",
                "--icon-size", "100",
                "--icon", "Anime1.app", "150", "150",
                "--app-drop-link", "350", "150",
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


def create_macos_zip(app_path: Path, version: str):
    """Create macOS ZIP archive from app bundle for auto-update.

    This creates a ZIP file that can be extracted directly over the existing app.
    """
    root = get_project_root()
    zip_name = f"anime1-macos-{version}.zip"
    zip_path = root / "release" / zip_name

    try:
        release_path = root / "release"
        release_path.mkdir(parents=True, exist_ok=True)

        # Remove existing zip if present
        if zip_path.exists():
            zip_path.unlink()

        # Create ZIP with the app bundle
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add the entire app bundle
            for file_path in app_path.rglob('*'):
                if file_path.is_file():
                    # Calculate arcname relative to app bundle parent
                    arcname = f"Anime1.app/Contents/MacOS/{app_path.name}" + str(file_path)[len(str(app_path)):]
                    # Normalize the path
                    arcname = arcname.replace('\\', '/')
                    zf.write(file_path, arcname)

        if zip_path.exists():
            print(f"[OK] Created macOS ZIP: {zip_path}")
            print(f"  Size: {get_size(zip_path)}")
            return zip_path
        else:
            print(f"[WARN] ZIP file was not created")
            return None
    except Exception as e:
        print(f"[WARN] Failed to create macOS ZIP: {e}")
        return None


def create_macos_portable(app_path: Path, version: str):
    """Create macOS portable version (directory structure for auto-update).

    This creates a structure that can be used for auto-update similar to Linux.
    """
    root = get_project_root()
    portable_path = root / "release" / f"anime1-macos-{version}"
    portable_zip = root / "release" / f"anime1-macos-{version}.zip"

    try:
        release_path = root / "release"
        release_path.mkdir(parents=True, exist_ok=True)

        # Remove existing files
        if portable_path.exists():
            shutil.rmtree(portable_path)
        if portable_zip.exists():
            portable_zip.unlink()

        # Copy app bundle to portable location
        shutil.copytree(app_path, portable_path)

        # Create ZIP
        shutil.make_archive(
            str(portable_zip.parent / portable_zip.stem),
            'zip',
            portable_path.parent,
            portable_path.name
        )

        if portable_zip.exists():
            print(f"[OK] Created macOS portable ZIP: {portable_zip}")
            print(f"  Size: {get_size(portable_zip)}")
            return portable_zip
        else:
            print(f"[WARN] Portable ZIP was not created")
            return None
    except Exception as e:
        print(f"[WARN] Failed to create macOS portable ZIP: {e}")
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

    # Parse version string (e.g., "1.2.3" -> major=1, minor=2, patch=3)
    # Sanitize version for NSIS (only numeric parts are valid)
    version_clean = version.replace('v', '').replace('V', '').split('.')
    major = version_clean[0] if len(version_clean) > 0 and version_clean[0].isdigit() else "0"
    minor = version_clean[1] if len(version_clean) > 1 and version_clean[1].isdigit() else "0"
    patch = version_clean[2] if len(version_clean) > 2 and version_clean[2].isdigit() else "0"

    # For filename, use sanitized version (replace non-alphanumeric with dash)
    version_filename = re.sub(r'[^a-zA-Z0-9.-]', '-', version)
    if version_filename.endswith('-'):
        version_filename = version_filename[:-1]

    nsis_script = f'''; Anime1 Desktop Windows Installer
; Auto-generated by build.py

!include LogicLib.nsh

!define APPNAME "Anime1"
!define COMPANYNAME "Anime1"
!define DESCRIPTION "Anime1 Desktop - Anime Browser"
!define VERSIONMAJOR {major}
!define VERSIONMINOR {minor}
!define INSTALLSIZE 120000
!define INSTDIR "$PROGRAMFILES\\${{APPNAME}}"
!define VERSION "{version}"

Name "${{APPNAME}} v${{VERSION}}"
Caption "${{APPNAME}} v${{VERSION}} - Installation Wizard"
OutFile "{release_path_abs}\\anime1-windows-{version_filename}-setup.exe"
InstallDir "${{INSTDIR}}"
InstallDirRegKey HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show

VIProductVersion "{major}.{minor}.{patch}.0"
VIAddVersionKey /LANG=2052 "ProductName" "${{APPNAME}}"
VIAddVersionKey /LANG=2052 "CompanyName" "${{COMPANYNAME}}"
VIAddVersionKey /LANG=2052 "FileDescription" "${{DESCRIPTION}}"
VIAddVersionKey /LANG=2052 "FileVersion" "{major}.{minor}.{patch}.0"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (C) 2025 ${{COMPANYNAME}}"

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
                     "VersionMajor" {major}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "VersionMinor" {minor}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" \
                     "EstimatedSize" ${{INSTALLSIZE}}

    WriteRegStr HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" \
                     "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" \
                     "Version" "{major}.{minor}"

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

        installer_path = root / "release" / f"anime1-windows-{version_filename}-setup.exe"
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
    zip_name = f"anime1-windows-{version}.zip" if sys.platform == "win32" else f"anime1-linux-{version}.tar.gz"

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
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    # Windows cmd 需要 chcp 65001 才能输出 UTF-8
    if sys.platform == "win32" and USE_SHELL:
        # 通过 shell 执行时，先切换编码
        cmd = f"chcp 65001 && {' '.join(cmd)}"

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=USE_SHELL,
        check=check,
        encoding='utf-8',
        errors='replace',
        env=env,
    )


def build_frontend(args) -> bool:
    """Build the Vue frontend application.

    Returns True if successful, False otherwise.
    """
    root = get_project_root()
    frontend_dir = root / "frontend"
    dist_dir = root / "static" / "dist"
    frontend_dist = frontend_dir / "dist"

    print(f"[DEBUG] Project root: {root}")
    print(f"[DEBUG] Frontend dir: {frontend_dir}")
    print(f"[DEBUG] Expected dist dir: {dist_dir}")

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

    # Clean frontend dist if requested (always clean to ensure fresh build)
    if args.clean:
        if frontend_dist.exists():
            print(f"[BUILD] Cleaning frontend/dist directory...")
            shutil.rmtree(frontend_dist)
        if dist_dir.exists():
            print(f"[BUILD] Cleaning static/dist directory...")
            shutil.rmtree(dist_dir)

    print("[BUILD] Building frontend...")
    try:
        # Install dependencies and build
        result = run_subprocess(["npm", "ci"], cwd=frontend_dir, check=False)
        # Windows 控制台默认使用 GBK 编码，无法显示 emoji 等 Unicode 字符
        # 只在非 Windows 系统打印详细输出
        if sys.platform != "win32":
            print(f"[DEBUG] npm ci stdout: {result.stdout[:500] if result.stdout else 'empty'}")
            print(f"[DEBUG] npm ci stderr: {result.stderr[:500] if result.stderr else 'empty'}")
        if result.returncode != 0:
            print(f"[ERROR] npm ci failed (code={result.returncode})")
            return False

        result = run_subprocess(["npm", "run", "build"], cwd=frontend_dir, check=False)
        if sys.platform != "win32":
            print(f"[DEBUG] npm run build stdout: {result.stdout[:500] if result.stdout else 'empty'}")
            print(f"[DEBUG] npm run build stderr: {result.stderr[:500] if result.stderr else 'empty'}")
        if result.returncode != 0:
            print(f"[ERROR] npm run build failed (code={result.returncode})")
            return False

        # Check if build output exists
        print(f"[DEBUG] Checking frontend/dist: {frontend_dist.exists()}")
        print(f"[DEBUG] Checking static/dist: {dist_dir.exists()}")

        if frontend_dist.exists():
            # Vite built to frontend/dist, move it to static/dist
            if dist_dir.exists():
                shutil.rmtree(dist_dir)
            dist_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(frontend_dist, dist_dir)
            print(f"[BUILD] Frontend built successfully to {dist_dir}")
            return True
        else:
            print(f"[ERROR] Frontend build completed but output directory not found")
            return False

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

    # Extract version - use provided version or extract from git
    if hasattr(args, 'version') and args.version:
        # User specified a version - use it directly
        version = normalize_version(args.version)
        print(f"[BUILD] Using specified version: {version}")
        is_dev = '-' in version  # Treat as dev if has commit hash suffix
    else:
        # Auto-detect version from git
        version = extract_version()
        is_dev = version.endswith('-')

    os.environ["ANIME1_VERSION"] = version
    print(f"[BUILD] Version: {version}")
    print(f"[BUILD] Is dev build: {is_dev}")

    # Update distInfo.plist for macOS bundle
    update_dist_info_plist(version)

    # Create version file (for fallback)
    version_file = root / "src" / "version.txt"
    version_file.write_text(version, encoding='utf-8')

    # Create _version.py with embedded version (like Go's -X flag)
    # This file will be bundled into the binary, making version immutable
    version_py_content = f'''"""Auto-generated version file - DO NOT EDIT
This file is generated at build time and bundled into the executable.
"""
__version__ = "{version}"
'''
    version_py_file = root / "src" / "_version.py"
    version_py_file.write_text(version_py_content, encoding='utf-8')
    print(f"[BUILD] Created _version.py with version: {version}")

    # Generate icons before build
    if sys.platform == "darwin":
        generate_macos_icon()
    elif sys.platform == "win32":
        generate_windows_icon()

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
        if sys.platform == "darwin":
            cmd.extend(["--icon", icon_path])
        elif sys.platform == "win32":
            cmd.extend(["--icon", icon_path])

    # macOS bundle identifier

    # Hidden imports
    hidden_imports = [
        "flask", "flask_cors", "flask.templating", "jinja2", "markupsafe", "werkzeug",
        "requests", "requests.utils", "requests.auth",
        "urllib3", "urllib3.util", "urllib3.connection",
        "beautifulsoup4", "soupsieve", "bs4", "bs4.builder",
        "pywebview", "pywebview.guarded_encodings", "pywebview.util", "pywebview.http",
        "hanziconv", "m3u8", "threading", "socket", "webbrowser", "argparse", "json", "click",
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
        (str(root / "src" / "scripts"), "src/scripts"),
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
    if sys.platform == "darwin":
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

    # Clean release directory to avoid mixing artifacts from different builds
    if release_path.exists():
        shutil.rmtree(release_path)
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
        # macOS: DMG + Portable ZIP for auto-update
        print("[BUILD] Creating macOS DMG...")
        dist_path = root / "dist"
        app_path = dist_path / "Anime1.app"
        if app_path.exists():
            create_macos_dmg(app_path, version)
            # Also create portable ZIP for auto-update
            print("[BUILD] Creating macOS portable ZIP for auto-update...")
            create_macos_portable(app_path, version)
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
    parser.add_argument("--version", type=str, metavar="VERSION",
                        help="Specify version for build (e.g., v0.1.0, 0.2.0-abc123). "
                             "Useful for testing update detection from older versions.")

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
