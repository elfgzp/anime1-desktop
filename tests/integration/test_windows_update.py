#!/usr/bin/env python
"""Simple Windows update test - installs old version and triggers update from GitHub."""
import os
import sys
import time
import subprocess
import shutil
import zipfile
import requests
import json

API_URL = "http://127.0.0.1:5172"
INSTALL_DIR = r"C:\Users\74142\AppData\Local\Anime1"
OLD_VERSION = "0.0.1"

def stop_anime1():
    """Stop all Anime1 processes."""
    print("[1] Stopping Anime1 processes...")
    subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
    time.sleep(2)
    print("    Done")

def clear_logs():
    """Clear log files."""
    print("[2] Clearing logs...")
    log_dir = os.path.join(os.environ['APPDATA'], 'Anime1', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'anime1.log')
    if os.path.exists(log_file):
        open(log_file, 'w').close()
    print("    Done")

def install_old_version():
    """Install old version."""
    print(f"[3] Installing old version {OLD_VERSION}...")
    old_zip = f"release/anime1-windows-{OLD_VERSION}.zip"

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    os.makedirs(INSTALL_DIR, exist_ok=True)

    with zipfile.ZipFile(old_zip, 'r') as zf:
        zf.extractall(INSTALL_DIR)
    print(f"    Installed to {INSTALL_DIR}")

def start_old_version():
    """Start old version."""
    print(f"[4] Starting old version...")
    exe_path = os.path.join(INSTALL_DIR, 'Anime1.exe')
    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    print("    Waiting for API...")

    for i in range(30):
        try:
            resp = requests.get(f"{API_URL}/api/settings/about", timeout=2)
            data = resp.json()
            print(f"    API responding! Version: {data['data']['version']}")
            return True
        except:
            time.sleep(1)
    print("    ERROR: API not responding")
    return False

def check_update_from_github():
    """Check for updates from GitHub."""
    print("[5] Checking for updates from GitHub...")
    try:
        resp = requests.get(f"{API_URL}/api/settings/check_update", timeout=10)
        data = resp.json()
        print("    Response:")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        return data
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def trigger_github_update():
    """Trigger update from GitHub (auto-download latest)."""
    print("[6] Triggering update from GitHub...")

    # First get the latest release info
    try:
        resp = requests.get("https://api.github.com/repos/nyaayain/anime1-desktop/releases/latest", timeout=10)
        data = resp.json()
        assets = data.get('assets', [])
        for asset in assets:
            if asset['name'].lower().endswith('.zip'):
                download_url = asset['browser_download_url']
                print(f"    Found: {asset['name']}")
                print(f"    URL: {download_url}")

                # Trigger download
                resp = requests.post(
                    f"{API_URL}/api/settings/update/download",
                    json={"url": download_url, "auto_install": True},
                    timeout=60
                )
                result = resp.json()
                print("    Response:")
                print(json.dumps(result, indent=4, ensure_ascii=False))

                if result.get('success'):
                    print("\n    [OK] Update triggered!")
                    return True
                else:
                    print("\n    [ERROR] Update failed")
                    return False
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False

def wait_and_check():
    """Wait for restart and check version."""
    print("[7] Waiting for restart (30 seconds)...")
    time.sleep(30)

    print("[8] Checking new version...")
    try:
        resp = requests.get(f"{API_URL}/api/settings/about", timeout=5)
        data = resp.json()
        version = data['data']['version']
        print(f"    Current version: {version}")
        if version != OLD_VERSION:
            print("\n    [OK] Update successful!")
            return True
        else:
            print("\n    [WARNING] Version unchanged")
            return False
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False

def show_logs():
    """Show recent logs."""
    print("\n[9] Recent logs:")
    log_file = os.path.join(os.environ['APPDATA'], 'Anime1', 'logs', 'anime1.log')
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                line = line.strip()
                if line and ('UPDATE' in line or 'DOWNLOAD' in line or 'ERROR' in line or 'UPDATER' in line):
                    print(f"    {line}")

def main():
    print("=" * 50)
    print("Windows Update Test (from GitHub)")
    print("=" * 50)

    stop_anime1()
    clear_logs()
    install_old_version()

    if not start_old_version():
        return 1

    check_update_from_github()

    if trigger_github_update():
        wait_and_check()
    else:
        print("\n    [WARNING] Update trigger failed")

    show_logs()

    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
