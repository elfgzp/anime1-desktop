import os
import sys
import subprocess
import time
import requests
import pytest

# Skip on non-Windows platforms
if sys.platform != 'win32':
    pytest.skip("This script is only for Windows platforms.", allow_module_level=True)

API_URL = "http://127.0.0.1:5172"

print("Checking current status...")

# Check processes
print("\nProcesses:")
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Anime1.exe'], capture_output=True, text=True)
print(result.stdout)

# Check if API is responding
print("\nChecking API...")
for i in range(5):
    try:
        resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
        data = resp.json()
        print(f"Version: {data['data']['version']}")
        break
    except:
        time.sleep(2)

# Check temp updater dirs
print("\nTemp updater directories:")
temp_pattern = r"C:\Users\74142\AppData\Local\Temp\anime1_update_*"
for d in os.listdir(r"C:\Users\74142\AppData\Local\Temp"):
    if d.startswith('anime1_update_'):
        full_path = os.path.join(r"C:\Users\74142\AppData\Local\Temp", d)
        print(f"  {full_path}")
        if os.path.isdir(full_path):
            for f in os.listdir(full_path):
                print(f"    - {f}")

# Check install dir
install_dir = r"C:\Users\74142\AppData\Local\Anime1-Test"
print(f"\nInstall directory contents:")
if os.path.exists(install_dir):
    for f in os.listdir(install_dir):
        print(f"  {f}")
