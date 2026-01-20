import os
import subprocess
import time
import requests
import json

test_exe = r"C:\Users\74142\AppData\Local\Anime1-Test\Anime1.exe"
API_URL = "http://127.0.0.1:5172"

# Kill all processes first
print("Killing all Anime1 processes...")
subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
time.sleep(2)

# Start the test version
print(f"Starting {test_exe}...")
proc = subprocess.Popen(
    [test_exe],
    cwd=os.path.dirname(test_exe),
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

# Wait for API
print("Waiting for API...")
for i in range(30):
    try:
        resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
        data = resp.json()
        version = data['data']['version']
        print(f"API version: {version}")
        break
    except:
        time.sleep(1)
else:
    print("API not responding!")
    exit(1)

# Check for updates
print("\nChecking for updates...")
resp = requests.get(f'{API_URL}/api/settings/check_update', timeout=10)
data = resp.json()
print(f"Has update: {data.get('has_update')}")
print(f"Latest: {data.get('latest_version')}")

# Trigger update
download_url = data.get('download_url')
print(f"\nTriggering update from {download_url}...")

try:
    resp = requests.post(
        f'{API_URL}/api/settings/update/download',
        json={"url": download_url, "auto_install": True},
        timeout=120
    )
    result = resp.json()
    print("Response:")
    print(json.dumps(result, indent=4, ensure_ascii=False))

    if result.get('success'):
        print(f"\nupdater_type: {result.get('data', {}).get('updater_type')}")
        if result.get('data', {}).get('updater_type') == 'windows':
            print("[OK] Windows updater type detected!")
        else:
            print(f"[ERROR] Wrong updater_type! Expected 'windows', got {result.get('data', {}).get('updater_type')}")
except Exception as e:
    print(f"Error: {e}")

# Read logs
print("\n--- Logs ---")
log_file = r'C:\Users\74142\AppData\Roaming\Anime1\anime1.log'
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        for line in lines[-30:]:
            if 'WINDOWS' in line or 'UPDATE' in line or 'UPDATER' in line or 'DOWNLOAD' in line:
                print(line.strip())
