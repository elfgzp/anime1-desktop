#!/usr/bin/env python
log_file = r'C:\Users\74142\AppData\Roaming\Anime1\anime1.log'
with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'DOWNLOAD' in line or 'UPDATE' in line:
            try:
                print(f'{i}: {line.rstrip()}')
            except:
                pass
