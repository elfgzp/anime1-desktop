import subprocess
import time
import requests

API_URL = "http://127.0.0.1:5172"

# Kill all processes first
print("Killing processes...")
subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
time.sleep(2)

# Start the app
print("Starting app...")
subprocess.Popen([r"C:\Users\74142\AppData\Local\Anime1-OldTest\Anime1.exe"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
time.sleep(5)

# Check version
print("\nChecking version...")
resp = requests.get(f'{API_URL}/api/settings/about', timeout=5)
print(f"Version: {resp.json()['data']['version']}")

# Trigger update download
print("\nTriggering update download...")
resp = requests.post(
    f'{API_URL}/api/settings/update/download',
    json={"url": "https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.7/anime1-windows-0.2.7.zip", "auto_install": True},
    timeout=180
)
result = resp.json()
print(f"updater_type: {result.get('data', {}).get('updater_type')}")
updater_path = result.get('data', {}).get('updater_path')
print(f"updater_path: {updater_path}")

# Now run the updater (this should start the updater)
print("\nRunning updater (this should start the updater)...")
try:
    resp = requests.post(
        f'{API_URL}/api/settings/update/run-updater',
        json={"updater_path": updater_path},
        timeout=10
    )
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Request error (expected): {e}")

# Then call exit to close the app
print("\nCalling /exit to close the app...")
try:
    resp = requests.post(f'{API_URL}/api/settings/exit', timeout=10)
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Request error (expected): {e}")

# Wait and check if app exited
print("\nWaiting 10 seconds...")
time.sleep(10)

print("\nChecking if app is still running...")
try:
    resp = requests.get(f'{API_URL}/api/settings/about', timeout=2)
    print(f"App still running! Version: {resp.json()['data']['version']}")
except:
    print("App has exited (as expected)")
