import os
import subprocess
import time
import requests
import json
import shutil
import zipfile

API_URL = "http://127.0.0.1:5172"
OLD_VERSION = "0.0.1"
NEW_VERSION = "0.2.7"
INSTALL_DIR = r"C:\Users\74142\AppData\Local\Anime1-OldTest"

def stop_all():
    """Stop all processes."""
    print("Stopping all processes...")
    subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
    time.sleep(2)

def install_old():
    """Install old version."""
    print(f"Installing old version {OLD_VERSION}...")
    zip_file = f"release/anime1-windows-{OLD_VERSION}.zip"

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    os.makedirs(INSTALL_DIR)

    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(INSTALL_DIR)
    print(f"    Installed to {INSTALL_DIR}")

def start_old():
    """Start old version."""
    print(f"Starting old version...")
    exe = os.path.join(INSTALL_DIR, 'Anime1.exe')
    subprocess.Popen([exe], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    # Wait for API
    for i in range(30):
        try:
            resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
            data = resp.json()
            print(f"    API version: {data['data']['version']}")
            return True
        except:
            time.sleep(1)
    return False

def check_update():
    """Check for updates."""
    print("Checking for updates...")
    resp = requests.get(f'{API_URL}/api/settings/check_update', timeout=10)
    data = resp.json()
    print(f"    Has update: {data.get('has_update')}")
    print(f"    Latest: {data.get('latest_version')}")
    print(f"    Download URL: {data.get('download_url')}")
    return data

def trigger_update(download_url):
    """Trigger update."""
    print("Triggering update...")

    try:
        resp = requests.post(
            f'{API_URL}/api/settings/update/download',
            json={"url": download_url, "auto_install": True},
            timeout=180
        )
        result = resp.json()
        print("Response:")
        print(json.dumps(result, indent=4, ensure_ascii=False))

        updater_type = result.get('data', {}).get('updater_type')
        print(f"\nupdater_type: {updater_type}")

        if updater_type == 'windows':
            print("[OK] Windows updater type detected!")
        elif updater_type == 'linux_zip':
            print("[ERROR] Wrong updater_type! Using Linux branch instead of Windows")
        else:
            print(f"[WARNING] Unknown updater_type: {updater_type}")

        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=" * 50)
    print("Windows Update Flow Test")
    print("=" * 50)

    stop_all()
    install_old()

    if not start_old():
        print("Failed to start old version")
        return 1

    data = check_update()

    if data.get('has_update'):
        download_url = data.get('download_url')
        result = trigger_update(download_url)

        if result and result.get('success'):
            print("\nUpdate triggered! Waiting 30 seconds...")
            time.sleep(30)

            # Check version after restart
            print("\nChecking version after restart...")
            try:
                resp = requests.get(f'{API_URL}/api/settings/about', timeout=5)
                data = resp.json()
                version = data['data']['version']
                print(f"New version: {version}")
                if version == NEW_VERSION:
                    print("[OK] Update successful!")
                else:
                    print(f"[WARNING] Version mismatch: expected {NEW_VERSION}, got {version}")
            except:
                print("API not responding after restart")

    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()
