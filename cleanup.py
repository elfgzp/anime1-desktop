import subprocess
import time
import os

# Stop all Anime1 processes
print("Stopping all Anime1 processes...")
subprocess.run(['taskkill', '/F', '/IM', 'Anime1.exe'], capture_output=True)
time.sleep(3)

# Check for remaining processes
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Anime1.exe'], capture_output=True, text=True)
print(result.stdout)

# Clear logs
print("\nClearing logs...")
log_dir = r'C:\Users\74142\AppData\Roaming\Anime1'
log_file = os.path.join(log_dir, 'anime1.log')
if os.path.exists(log_file):
    with open(log_file, 'w') as f:
        pass
    print(f"Cleared: {log_file}")

# Clear temp updater directories
import glob
temp_pattern = r'C:\Users\74142\AppData\Local\Temp\anime1_update_*'
for temp_dir in glob.glob(temp_pattern):
    try:
        os.rmdir(temp_dir)
        print(f"Removed temp dir: {temp_dir}")
    except:
        pass

print("\nCleanup complete!")
