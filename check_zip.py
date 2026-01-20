import zipfile

# Check version in old zip
zip_file = r"C:\Users\74142\Github\anime1-desktop\release\anime1-windows-0.0.1.zip"
print(f"Checking {zip_file}...")

with zipfile.ZipFile(zip_file, 'r') as zf:
    for name in zf.namelist():
        if 'version' in name.lower() or '_version' in name:
            print(f"Found: {name}")
            try:
                content = zf.read(name).decode('utf-8')
                print(content)
            except:
                pass
