#!/usr/bin/env python
import os

log_dir = os.path.expandvars(r"%APPDATA%\Anime1")
log_file = os.path.join(log_dir, "anime1.log")

print(f"Log dir: {log_dir}")
print(f"Log file: {log_file}")
print(f"Log exists: {os.path.exists(log_file)}")

if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"\n=== Last 50 lines ({len(lines)} total) ===")
        for line in lines[-50:]:
            print(line.rstrip())
else:
    # Try alternative locations
    alt_paths = [
        r"C:\Users\74142\AppData\Roaming\Anime1\anime1.log",
        r"C:\Users\74142\AppData\Roaming\Anime1\logs\anime1.log",
    ]
    for p in alt_paths:
        print(f"Checking: {p} -> {os.path.exists(p)}")
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n=== Last 50 lines from {p} ===")
                for line in lines[-50:]:
                    print(line.rstrip())
