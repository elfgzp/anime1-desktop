import requests
resp = requests.get('https://api.github.com/repos/elfgzp/anime1-desktop/releases/latest', timeout=10)
data = resp.json()
print('tag_name:', data.get('tag_name'))
print('assets:')
for asset in data.get('assets', []):
    print(f'  - {asset["name"]}')
