import os

log_file = r'C:\Users\74142\AppData\Roaming\Anime1\anime1.log'
with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
    for line in lines[-100:]:
        if 'EXIT' in line or 'UPDATER' in line or 'parent' in line.lower():
            print(line.strip())
