import os
import sys
import time
import subprocess
import shutil
import zipfile
import requests
import json

API_URL = "http://127.0.0.1:5172"
INSTALL_DIR = r"C:\Users\74142\AppData\Local\Anime1-Test"
NEW_VERSION = "0.2.7"

def stop_anime1():
    """Stop all Anime1 processes."""
    print("[1] Stopping Anime1 processes...")
    subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
    time.sleep(2)
    print("    Done")

def clear_logs():
    """Clear log files."""
    print("[2] Clearing logs...")
    log_dir = r"C:\Users\74142\AppData\Roaming\Anime1\logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'anime1.log')
    if os.path.exists(log_file):
        open(log_file, 'w').close()
    print("    Done")

def install_version(version):
    """Install version to test directory."""
    print(f"[3] Installing version {version}...")
    zip_file = f"release/anime1-windows-{version}.zip"

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    os.makedirs(INSTALL_DIR, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(INSTALL_DIR)
    print(f"    Installed to {INSTALL_DIR}")

def start_app():
    """Start the app."""
    print(f"[4] Starting app...")
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

def check_update():
    """Check for updates."""
    print("[5] Checking for updates...")
    try:
        resp = requests.get(f"{API_URL}/api/settings/check_update", timeout=10)
        data = resp.json()
        print(f"    Has update: {data.get('has_update')}")
        print(f"    Latest version: {data.get('latest_version')}")
        print(f"    Download URL: {data.get('download_url')}")
        return data
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def trigger_update(download_url):
    """Trigger update."""
    print(f"[6] Triggering update...")

    try:
        resp = requests.post(
            f"{API_URL}/api/settings/update/download",
            json={"url": download_url, "auto_install": True},
            timeout=120
        )
        result = resp.json()
        print("    Response:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        return result
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def show_logs():
    """Show recent logs."""
    print("\n[7] Recent logs:")
    log_file = r"C:\Users\74142\AppData\Roaming\Anime1\logs\anime1.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                line = line.strip()
                if line and ('UPDATE' in line or 'DOWNLOAD' in line or 'ERROR' in line or 'UPDATER' in line or 'WINDOWS' in line or 'zip' in line.lower()):
                    print(f"    {line}")

def main():
    print("=" * 50)
    print("Test Current Version Update Flow")
    print("=" * 50)

    stop_anime1()
    clear_logs()
    install_version(NEW_VERSION)

    if not start_app():
        return 1

    data = check_update()
    if data:
        download_url = data.get('download_url')
        if download_url:
            result = trigger_update(download_url)
            if result and result.get('success'):
                print("\n    Update triggered! Check if restart happens...")

    show_logs()

    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
