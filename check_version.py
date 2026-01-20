import subprocess
import time

# Kill the python process using port 5172
print("Killing python process 21568...")
subprocess.run(['taskkill', '/F', '/PID', '21568'], capture_output=True)
time.sleep(2)

# Verify
result = subprocess.run(['tasklist', '/FI', 'PID eq 21568'], capture_output=True, text=True)
print(result.stdout)

# Check if API is still responding
import requests
print("\nChecking if API is responding...")
try:
    resp = requests.get('http://127.0.0.1:5172/api/settings/about', timeout=2)
    data = resp.json()
    print(f"API still responding! Version: {data['data']['version']}")
except Exception as e:
    print(f"API not responding: {e}")
    print("Good - development server is dead")
