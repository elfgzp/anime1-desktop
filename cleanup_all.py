import subprocess
import time

# Kill all Anime1 processes
print("Killing all Anime1 processes...")
subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
time.sleep(3)

# Verify
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Anime1.exe'], capture_output=True, text=True)
print(result.stdout)

# Check if API is still responding
import requests
print("\nChecking API...")
try:
    resp = requests.get('http://127.0.0.1:5172/api/settings/about', timeout=2)
    print(f"API still responding! Version: {resp.json()['data']['version']}")
except:
    print("API not responding - all processes killed")
