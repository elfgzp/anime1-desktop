#!/usr/bin/env python3
"""
macOS Auto-Updater for Anime1 Desktop

This script handles automatic updates from DMG files.
It is designed to be run as a separate process after the main app exits.

Usage:
    python macos_updater.py --dmg /path/to/anime1-macos-0.2.1.dmg --app /path/to/Anime1.app

The updater will:
1. Mount the DMG file
2. Create a backup of the existing app
3. Copy the new app from the mounted volume
4. Unmount the DMG
5. Launch the updated application
"""
import argparse
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, timeout=60):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def get_app_info(app_path):
    """Get application info from Info.plist."""
    info_plist = app_path / "Contents" / "Info.plist"
    if not info_plist.exists():
        return None

    try:
        with open(info_plist, 'rb') as f:
            data = plistlib.load(f)
        return {
            'name': data.get('CFBundleName', data.get('CFBundleDisplayName', 'Unknown')),
            'bundle_id': data.get('CFBundleIdentifier', ''),
            'version': data.get('CFBundleShortVersionString', ''),
            'path': str(app_path)
        }
    except Exception as e:
        print(f"[ERROR] Failed to read app info: {e}")
        return None


def mount_dmg(dmg_path):
    """Mount a DMG file and return the mount point."""
    print(f"[INFO] Mounting DMG: {dmg_path}")

    # Mount the DMG
    success, stdout, stderr = run_command(['hdiutil', 'attach', '-nobrowse', str(dmg_path)])

    if not success:
        print(f"[ERROR] Failed to mount DMG: {stderr}")
        return None

    # Parse the mount output to find the mount point
    # Output format: /dev/disk2s1  Apple_HFS                        /Volumes/Anime1
    for line in stdout.split('\n'):
        if '/Volumes/' in line:
            parts = line.strip().split()
            if len(parts) >= 3:
                mount_point = parts[-1]
                print(f"[INFO] Mounted at: {mount_point}")
                return Path(mount_point)

    # Try to find the mount point
    success, stdout, stderr = run_command(['hdiutil', 'info'])
    for line in stdout.split('\n'):
        if '/Volumes/' in line:
            for part in reversed(line.split()):
                if part.startswith('/Volumes/'):
                    return Path(part)

    print("[ERROR] Could not find mount point")
    return None


def unmount_dmg(mount_point):
    """Unmount a DMG file."""
    print(f"[INFO] Unmounting: {mount_point}")

    # Force unmount if needed
    success, stdout, stderr = run_command(['hdiutil', 'detach', '-force', str(mount_point)])

    if not success:
        # Try without force
        success, stdout, stderr = run_command(['hdiutil', 'detach', str(mount_point)])

    if not success:
        print(f"[WARN] Failed to unmount: {stderr}")
        return False

    print("[INFO] Unmounted successfully")
    return True


def find_app_in_volume(volume_path, app_name="Anime1"):
    """Find the app bundle in the mounted volume."""
    # Check if the app is directly in the volume
    app_path = volume_path / f"{app_name}.app"
    if app_path.exists():
        return app_path

    # Check subdirectories
    for item in volume_path.iterdir():
        if item.is_dir() and item.name.endswith('.app'):
            return item

    return None


def create_backup(app_path):
    """Create a backup of the existing app."""
    parent = app_path.parent
    backup_dir = parent / f"{app_path.stem}_backup_{int(time.time())}"

    print(f"[INFO] Creating backup: {backup_dir}")

    try:
        shutil.copytree(app_path, backup_dir)
        print(f"[INFO] Backup created: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"[WARN] Failed to create backup: {e}")
        return None


def remove_backup(backup_dir):
    """Remove the backup directory."""
    if backup_dir and backup_dir.exists():
        print(f"[INFO] Removing backup: {backup_dir}")
        try:
            shutil.rmtree(backup_dir)
            return True
        except Exception as e:
            print(f"[WARN] Failed to remove backup: {e}")
            return False
    return True


def copy_app(source_app, dest_app):
    """Copy the new app over the old one."""
    print(f"[INFO] Copying new app from {source_app} to {dest_app}")

    # Remove the old app
    if dest_app.exists():
        print(f"[INFO] Removing old app: {dest_app}")
        try:
            shutil.rmtree(dest_app)
        except Exception as e:
            print(f"[ERROR] Failed to remove old app: {e}")
            return False

    try:
        shutil.copytree(source_app, dest_app)
        print(f"[INFO] New app installed: {dest_app}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to copy app: {e}")
        return False


def launch_app(app_path):
    """Launch the updated application."""
    print(f"[INFO] Launching: {app_path}")

    # Make sure the app is executable
    exec_path = app_path / "Contents" / "MacOS" / "Anime1"
    if exec_path.exists():
        os.chmod(exec_path, 0o755)

    # Use open command to launch the app
    success, stdout, stderr = run_command(['open', str(app_path)], timeout=10)

    if success:
        print("[INFO] App launched successfully")
        return True
    else:
        print(f"[ERROR] Failed to launch app: {stderr}")
        return False


def cleanup(dmg_path, mount_point):
    """Clean up temporary files."""
    # Remove the downloaded DMG
    if dmg_path and dmg_path.exists():
        print(f"[INFO] Removing downloaded DMG: {dmg_path}")
        try:
            dmg_path.unlink()
        except Exception as e:
            print(f"[WARN] Failed to remove DMG: {e}")

    # Unmount DMG if still mounted
    if mount_point and mount_point.exists():
        unmount_dmg(mount_point)


def update(dmg_path, app_path, cleanup_dmg=True):
    """Perform the update process.

    Args:
        dmg_path: Path to the downloaded DMG file
        app_path: Path to the existing app to update
        cleanup_dmg: Whether to remove the DMG after update

    Returns:
        True if update was successful, False otherwise
    """
    print("=" * 60)
    print("Anime1 macOS Auto-Updater")
    print("=" * 60)
    print(f"DMG: {dmg_path}")
    print(f"App: {app_path}")
    print("=" * 60)

    mount_point = None
    backup_dir = None

    try:
        # Step 1: Mount the DMG
        mount_point = mount_dmg(dmg_path)
        if not mount_point:
            return False

        # Step 2: Find the app in the mounted volume
        new_app = find_app_in_volume(mount_point)
        if not new_app:
            print("[ERROR] Could not find app in mounted DMG")
            return False

        print(f"[INFO] Found app in DMG: {new_app}")

        # Step 3: Create backup
        backup_dir = create_backup(app_path)

        # Step 4: Copy new app
        if not copy_app(new_app, app_path):
            # Restore from backup if copy failed
            if backup_dir and backup_dir.exists():
                print("[INFO] Restoring from backup...")
                shutil.rmtree(app_path)
                shutil.copytree(backup_dir, app_path)
            return False

        # Step 5: Clean up
        if cleanup_dmg:
            cleanup(dmg_path, mount_point)
        else:
            unmount_dmg(mount_point)

        # Remove backup if update was successful
        remove_backup(backup_dir)

        # Step 6: Launch the updated app
        launch_app(app_path)

        print("[SUCCESS] Update completed!")
        return True

    except Exception as e:
        print(f"[ERROR] Update failed: {e}")
        import traceback
        traceback.print_exc()

        # Try to restore from backup
        if backup_dir and backup_dir.exists() and app_path.exists():
            print("[INFO] Attempting to restore from backup...")
            shutil.rmtree(app_path)
            shutil.copytree(backup_dir, app_path)

        # Cleanup
        if cleanup_dmg:
            cleanup(dmg_path, mount_point)
        elif mount_point:
            unmount_dmg(mount_point)

        return False


def main():
    parser = argparse.ArgumentParser(description="Anime1 macOS Auto-Updater")
    parser.add_argument("--dmg", required=True, type=str, help="Path to DMG file")
    parser.add_argument("--app", required=True, type=str, help="Path to existing app")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't remove DMG after update")

    args = parser.parse_args()

    dmg_path = Path(args.dmg).resolve()
    app_path = Path(args.app).resolve()

    if not dmg_path.exists():
        print(f"[ERROR] DMG file not found: {dmg_path}")
        sys.exit(1)

    if not app_path.exists():
        print(f"[ERROR] App not found: {app_path}")
        sys.exit(1)

    success = update(dmg_path, app_path, cleanup_dmg=not args.no_cleanup)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
