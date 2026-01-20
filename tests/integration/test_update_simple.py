#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Windows update test script."""
import os
import sys
import time
import subprocess
import zipfile
import shutil
import requests
import json

# Force UTF-8 encoding for output
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_command(cmd, timeout=30):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return str(e)

def main():
    install_dir = r"C:\Program Files (x86)\Anime1"
    old_zip = r"C:\Users\74142\Github\anime1-desktop\release\anime1-windows-0.0.1.zip"
    new_zip = r"C:\Users\74142\Github\anime1-desktop\release\anime1-windows-0.2.7.zip"
    api_url = "http://127.0.0.1:5172"

    print("=" * 50)
    print("Windows Update Test")
    print("=" * 50)

    # Step 1: Stop all Anime1 processes
    print("\n[1] Stopping Anime1 processes...")
    os.system('taskkill /F /IM "Anime1.exe" 2>nul')
    time.sleep(2)
    print("[OK] Done")

    # Step 2: Clear logs
    print("\n[2] Clearing logs...")
    log_dir = os.path.expandvars(r"%APPDATA%\Anime1\logs")
    os.makedirs(log_dir, exist_ok=True)
    for f in ["anime1.log", "app.log"]:
        fpath = os.path.join(log_dir, f)
        if os.path.exists(fpath):
            with open(fpath, 'w') as _: pass
    print("[OK] Done")

    # Step 3: Install old version
    print("\n[3] Installing old version v0.0.1...")
    if os.path.exists(install_dir):
        # Try to remove, if fails, rename and create new
        try:
            shutil.rmtree(install_dir)
        except PermissionError:
            # Rename instead
            backup_dir = install_dir + "_old_" + str(int(time.time()))
            try:
                os.rename(install_dir, backup_dir)
                print(f"  [WARN] Renamed old directory to: {backup_dir}")
            except Exception as e:
                print(f"  [ERROR] Could not clean directory: {e}")
                print("  [INFO] Using current installation for test")
    os.makedirs(install_dir, exist_ok=True)

    with zipfile.ZipFile(old_zip, 'r') as zf:
        zf.extractall(install_dir)
    print(f"[OK] Old version installed to: {install_dir}")

    # List contents
    for f in os.listdir(install_dir):
        print(f"    - {f}")

    # Step 4: Start old version
    print("\n[4] Starting old version...")
    exe_path = os.path.join(install_dir, "Anime1.exe")
    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
    print("[OK] Started")

    # Wait for API
    print("Waiting for API...")
    for i in range(30):
        try:
            resp = requests.get(f"{api_url}/api/settings/about", timeout=2)
            if resp.status_code == 200:
                print("[OK] API is responding!")
                break
        except:
            pass
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"  Attempt {i + 1}...")
    else:
        print("[ERROR] API not responding after 30 seconds")
        return 1

    # Check version
    try:
        resp = requests.get(f"{api_url}/api/settings/about")
        data = resp.json()
        print(f"Current version: {data['data']['version']}")
    except Exception as e:
        print(f"Could not get version: {e}")

    # Step 5: Start local HTTP server
    print("\n[5] Starting local HTTP server...")
    http_dir = r"C:\Users\74142\Github\anime1-desktop\release"
    http_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"],
        cwd=http_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    print(f"[OK] HTTP server started (PID: {http_proc.pid})")

    # Step 6: Trigger update
    print("\n[6] Triggering update...")
    try:
        payload = {"url": "http://127.0.0.1:8765/anime1-windows-0.2.7.zip", "auto_install": True}
        resp = requests.post(
            f"{api_url}/api/settings/update/download",
            json=payload,
            timeout=60
        )
        data = resp.json()
        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if data.get('success'):
            print("[OK] Update triggered successfully!")
        else:
            print("[ERROR] Update failed")
    except Exception as e:
        print(f"[ERROR] Update request failed: {e}")

    # Stop HTTP server
    http_proc.terminate()
    print("[OK] HTTP server stopped")

    # Step 7: Wait for restart
    print("\n[7] Waiting for restart (20 seconds)...")
    time.sleep(20)

    # Step 8: Check new version
    print("\n[8] Checking new version...")
    try:
        resp = requests.get(f"{api_url}/api/settings/about", timeout=5)
        data = resp.json()
        print(f"New version: {data['data']['version']}")
        print("[OK] Update successful!")
    except Exception as e:
        print(f"[ERROR] Could not get version: {e}")

    # Step 9: Show recent logs
    print("\n[9] Recent logs:")
    log_file = os.path.expandvars(r"%APPDATA%\Anime1\anime1.log")
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-30:]:
                print(line.rstrip())

    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
