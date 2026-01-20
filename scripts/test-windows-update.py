#!/usr/bin/env python
"""Windows Auto-Update Complete Test Script.

Tests the complete Windows update flow:
1. Stop all Anime1 processes (including dev server)
2. Build old version v0.0.1 and install to test directory
3. Clear logs
4. Start app and wait for API
5. Verify current version is 0.0.1
6. Trigger update from GitHub (v0.2.7)
7. Trigger download and auto-install via API
8. Verify updater_type is "windows"
9. Wait for auto-restart via PowerShell updater
10. Verify new version is running
11. Display update log for debugging

Run with: python scripts/test-windows-update.py
"""
import os
import sys
import time
import subprocess
import shutil
import zipfile
import requests
import json

# Configuration
API_URL = "http://127.0.0.1:5172"
OLD_VERSION = "0.0.1"
TEST_INSTALL_DIR = r"C:\Users\74142\AppData\Local\Anime1-OldTest"


def stop_all_processes():
    """Stop all Anime1 and Python processes."""
    print("\n[1] Stopping all Anime1 and Python processes...")
    subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
    time.sleep(1)

    # Kill any python process using port 5172
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-NetTCPConnection -LocalPort 5172 -ErrorAction Silence | '
             'ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction Silence }'],
            capture_output=True, text=True
        )
        if result.stdout:
            print(f"    Found process on port 5172, terminating...")
            for line in result.stdout.split('\n'):
                if line.strip():
                    subprocess.run(['taskkill', '/F', '/PID', line.strip().split()[0]], capture_output=True)
    except:
        pass

    time.sleep(2)
    print("    Done")


def clear_logs():
    """Clear log files."""
    print("\n[2] Clearing logs...")
    log_dir = r"C:\Users\74142\AppData\Roaming\Anime1\logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'anime1.log')
    if os.path.exists(log_file):
        open(log_file, 'w').close()
    print("    Done")


def build_old_version():
    """Build old version v0.0.1."""
    print(f"\n[3] Building old version {OLD_VERSION}...")
    old_zip = f"release/anime1-windows-{OLD_VERSION}.zip"
    if os.path.exists(old_zip):
        print(f"    Old version already exists: {old_zip}")
        return
    print(f"    Building old version {OLD_VERSION}...")
    result = subprocess.run([sys.executable, 'scripts/build.py', '--version', OLD_VERSION], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ERROR: Build failed: {result.stderr}")
        sys.exit(1)
    print(f"    Done: {old_zip}")


def install_old_version():
    """Install old version to test directory."""
    print(f"\n[4] Installing old version {OLD_VERSION}...")
    old_zip = f"release/anime1-windows-{OLD_VERSION}.zip"
    if os.path.exists(TEST_INSTALL_DIR):
        shutil.rmtree(TEST_INSTALL_DIR, ignore_errors=True)
    os.makedirs(TEST_INSTALL_DIR)
    with zipfile.ZipFile(old_zip, 'r') as zf:
        zf.extractall(TEST_INSTALL_DIR)
    print(f"    Installed to: {TEST_INSTALL_DIR}")
    exe_path = os.path.join(TEST_INSTALL_DIR, 'Anime1.exe')
    if not os.path.exists(exe_path):
        print(f"    ERROR: Executable not found: {exe_path}")
        sys.exit(1)


def start_app():
    """Start the app."""
    print(f"\n[5] Starting app from {TEST_INSTALL_DIR}...")
    exe_path = os.path.join(TEST_INSTALL_DIR, 'Anime1.exe')
    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    print("    Waiting for API...")
    for i in range(30):
        try:
            resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
            data = resp.json()
            version = data['data']['version']
            print(f"    API responding! Version: {version}")
            return version
        except:
            time.sleep(1)
    print("    ERROR: API not responding after 30 seconds")
    sys.exit(1)


def trigger_update():
    """Trigger update from GitHub."""
    print("\n[6] Triggering update from GitHub...")

    # Use the app's check_update API to get the correct download URL
    try:
        resp = requests.get(f'{API_URL}/api/settings/check_update', timeout=10)
        data = resp.json()
        print(f"    has_update: {data.get('has_update')}")
        print(f"    latest_version: {data.get('latest_version')}")
        download_url = data.get('download_url')
        print(f"    download_url: {download_url}")
    except Exception as e:
        print(f"    ERROR checking updates: {e}")
        download_url = "https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.7/anime1-windows-0.2.7.zip"

    print(f"\n[7] Downloading update...")
    try:
        resp = requests.post(
            f'{API_URL}/api/settings/update/download',
            json={"url": download_url, "auto_install": True},
            timeout=180
        )
        result = resp.json()

        print("    Response:")
        print(json.dumps(result, indent=4, ensure_ascii=False))

        updater_type = result.get('data', {}).get('updater_type')
        print(f"\n    updater_type: {updater_type}")

        if updater_type == 'windows':
            print("    [OK] Windows updater type detected!")
            return result
        elif updater_type == 'linux_zip':
            print("    [ERROR] Using Linux branch instead of Windows!")
            print("    This indicates platform detection is broken!")
            return None
        else:
            print(f"    [WARNING] Unknown updater_type: {updater_type}")
            return result

    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def run_updater(updater_path):
    """Run the updater and exit."""
    print(f"\n[8] Running updater: {updater_path}...")

    try:
        resp = requests.post(
            f'{API_URL}/api/settings/update/run-updater',
            json={"updater_path": updater_path},
            timeout=10
        )
        result = resp.json()
        print("    Response:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        print("    Updater launched, app will exit...")
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def wait_for_restart():
    """Wait for app to restart."""
    print("\n[9] Waiting for auto-restart (45 seconds)...")

    time.sleep(45)

    for i in range(15):
        try:
            resp = requests.get(f'{API_URL}/api/settings/about', timeout=5)
            data = resp.json()
            version = data['data']['version']
            print(f"    API responding! Version: {version}")
            return version
        except:
            time.sleep(2)
    print("    WARNING: API not responding after restart")
    return None


def show_logs():
    """Show update-related logs."""
    print("\n[10] Recent update logs:")
    log_file = r"C:\Users\74142\AppData\Roaming\Anime1\anime1.log"
    if not os.path.exists(log_file):
        print("    Log file not found")
        return
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        relevant = [line.strip() for line in lines[-100:] if any(x in line for x in ['UPDATE', 'DOWNLOAD', 'UPDATER', 'WINDOWS', 'zip', 'UPDATER'])]
        if relevant:
            for line in relevant[-40:]:
                print(f"    {line}")
        else:
            print("    No update logs found")


def main():
    print("=" * 60)
    print("Windows Auto-Update Complete Test")
    print("=" * 60)
    print(f"Test: v{OLD_VERSION} -> v0.2.7")
    print(f"API URL: {API_URL}")
    print(f"Install dir: {TEST_INSTALL_DIR}")

    stop_all_processes()
    clear_logs()
    build_old_version()
    install_old_version()
    current = start_app()

    if current != OLD_VERSION:
        print(f"\n    WARNING: Expected version {OLD_VERSION}, got {current}")

    result = trigger_update()

    if result and result.get('success'):
        updater_path = result.get('data', {}).get('updater_path')
        if updater_path:
            run_updater(updater_path)
            new_version = wait_for_restart()
            if new_version:
                if new_version == "0.2.7":
                    print(f"\n    [OK] Update successful: {OLD_VERSION} -> {new_version}")
                else:
                    print(f"\n    [WARNING] Version mismatch: expected 0.2.7, got {new_version}")
            else:
                print("\n    [INFO] App exited for update, restart expected...")
    else:
        print("\n    [ERROR] Update failed - check updater_type")

    show_logs()
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
