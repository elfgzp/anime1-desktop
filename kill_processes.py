import subprocess
import time

# Force kill again
subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
time.sleep(3)
print('Killed processes')

# Check if any Anime1 processes are running
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Anime1.exe'], capture_output=True, text=True)
print(result.stdout)
