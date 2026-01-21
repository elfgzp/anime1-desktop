import os
import sys
import subprocess
import time
import requests
import json
import shutil
import zipfile
import pytest

# Skip on non-Windows platforms
if sys.platform != 'win32':
    pytest.skip("This script is only for Windows platforms.", allow_module_level=True)

pytestmark = pytest.mark.integration

API_URL = "http://127.0.0.1:5172"
OLD_VERSION = "0.0.1"
NEW_VERSION = "0.2.7"
INSTALL_DIR = r"C:\Users\74142\AppData\Local\Anime1-OldTest"
DOWNLOAD_URL = "https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.7/anime1-windows-0.2.7.zip"

# Kill all processes first
print("Killing processes...")
proc = subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True, timeout=5)
time.sleep(2)

# Install old version
print(f"\nInstalling old version {OLD_VERSION}...")
zip_file = f"release/anime1-windows-{OLD_VERSION}.zip"

if os.path.exists(INSTALL_DIR):
    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
os.makedirs(INSTALL_DIR)

with zipfile.ZipFile(zip_file, 'r') as zf:
    zf.extractall(INSTALL_DIR)
print(f"    Installed to {INSTALL_DIR}")

# Start old version
print(f"\nStarting old version...")
exe = os.path.join(INSTALL_DIR, 'Anime1.exe')
subprocess.Popen([exe], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

# Wait for API
print("Waiting for API...")
for i in range(30):
    try:
        resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
        data = resp.json()
        version = data['data']['version']
        print(f"    API version: {version}")
        break
    except:
        time.sleep(1)
else:
    print("    API not responding!")
    exit(1)

# Trigger update with correct URL
print(f"\nTriggering update from {DOWNLOAD_URL}...")
try:
    resp = requests.post(
        f'{API_URL}/api/settings/update/download',
        json={"url": DOWNLOAD_URL, "auto_install": True},
        timeout=180
    )
    result = resp.json()
    print("Response:")
    print(json.dumps(result, indent=4, ensure_ascii=False))

    updater_type = result.get('data', {}).get('updater_type')
    print(f"\nupdater_type: {updater_type}")

    if updater_type == 'windows':
        print("[OK] Windows updater type!")
    elif updater_type == 'linux_zip':
        print("[ERROR] Still using Linux branch - platform detection fix not working!")
    else:
        print(f"[INFO] Unknown type: {updater_type}")
except Exception as e:
    print(f"Error: {e}")

# Read logs
print("\n--- Logs ---")
log_file = r'C:\Users\74142\AppData\Roaming\Anime1\anime1.log'
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        for line in lines[-30:]:
            if 'WINDOWS' in line or 'UPDATE' in line or 'UPDATER' in line or 'DOWNLOAD' in line or 'platform' in line.lower():
                print(line.strip())
