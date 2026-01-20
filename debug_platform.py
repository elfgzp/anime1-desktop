import sys
import requests
import subprocess
import time

# Start the app
subprocess.Popen([r"C:\Users\74142\AppData\Local\Anime1-OldTest\Anime1.exe"])
time.sleep(5)

# Check the version
resp = requests.get('http://127.0.0.1:5172/api/settings/about', timeout=10)
print(f"Version: {resp.json()['data']['version']}")
print(f"sys.platform: {sys.platform}")

# Test the exit endpoint
try:
    resp = requests.post('http://127.0.0.1:5172/api/settings/exit', timeout=5)
    print(f"Exit response: {resp.status_code}")
    print(f"Exit response body: {resp.text}")
except Exception as e:
    print(f"Exit error: {e}")

# Check logs
log_file = r'C:\Users\74142\AppData\Roaming\Anime1\anime1.log'
with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
    for line in lines[-15:]:
        if '[EXIT]' in line or '[taskkill]' in line:
            print(line.strip())
