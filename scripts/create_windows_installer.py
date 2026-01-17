#!/usr/bin/env python3
"""
Create Windows installer using NSIS.

Usage:
    python scripts/create_windows_installer.py [--cleanup]
"""
import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
RELEASE_DIR = PROJECT_ROOT / "release"
NSIS_SCRIPT = PROJECT_ROOT / "scripts" / "create_installer.nsi"


def run_nsis():
    """Run NSIS to create the installer."""
    # Check if NSIS is installed in common locations
    nsis_paths = [
        "makinson",  # Just in case
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]

    # First try command line
    import shutil
    makensis_path = shutil.which("makensis")
    if makensis_path:
        print(f"[OK] NSIS found: {makensis_path}")
    else:
        # Check common installation paths
        for path in nsis_paths[1:]:  # Skip the first placeholder
            if Path(path).exists():
                makensis_path = path
                print(f"[OK] NSIS found: {makensis_path}")
                break

        if not makensis_path:
            # Try using choco to find the installation
            print("[ERROR] NSIS not found in PATH or common locations.")
            print("[ERROR] NSIS was installed but makensis may not be in PATH.")
            print("[INFO] Try restarting the shell or running: refreshenv")
            return False

    # Run NSIS
    cmd = [makensis_path, str(NSIS_SCRIPT)]
    print(f"[BUILD] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def find_build_dir(dist_dir: Path):
    """Find the Windows build directory."""
    # 尝试多个可能的目录名
    candidates = [
        dist_dir / "anime1",  # onedir 模式（小写）
        dist_dir / "Anime1",  # onedir 模式（大写）
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # 检查目录下是否有可执行文件
            exe_files = list(candidate.glob("*.exe"))
            if exe_files:
                return candidate

    return None


def prepare_files():
    """Prepare files for installer."""
    print("[PREPARE] Preparing files for installer...")

    # Find build directory
    app_dir = find_build_dir(DIST_DIR)
    if not app_dir:
        print(f"[ERROR] Build not found in: {DIST_DIR}")
        print("[ERROR] Run 'make build' first.")
        print(f"[INFO] Contents of {DIST_DIR}:")
        if DIST_DIR.exists():
            for item in DIST_DIR.iterdir():
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        return False

    print(f"[OK] Found build directory: {app_dir}")

    # Ensure release directory exists
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[OK] Files prepared in: {DIST_DIR}")
    return True


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Create Windows installer")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temporary files")
    args = parser.parse_args()

    print("=" * 60)
    print("Creating Windows Installer")
    print("=" * 60)

    # Prepare files
    if not prepare_files():
        sys.exit(1)

    # Run NSIS
    if not run_nsis():
        print("[ERROR] Failed to create installer")
        sys.exit(1)

    # Check output
    installer_path = RELEASE_DIR / "anime1-windows-x64-setup.exe"
    if installer_path.exists():
        size = installer_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] Installer created: {installer_path}")
        print(f"     Size: {size:.1f} MB")
    else:
        print("[WARNING] Installer not found at expected location")

    # Cleanup
    if args.cleanup:
        print("\n[CLEANUP] Cleaning up...")
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
            print(f"[OK] Removed: {DIST_DIR}")


if __name__ == "__main__":
    main()
