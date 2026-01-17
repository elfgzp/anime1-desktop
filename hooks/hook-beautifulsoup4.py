# PyInstaller hook for beautifulsoup4
# This hook ensures all beautifulsoup4 submodules are included

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules('bs4')
hidden_imports += [
    'bs4.builder',
    'bs4.dammit',
    'bs4.element',
    'bs4.formatter',
]

a = collect_submodules('beautifulsoup4')
hidden_imports += a
hidden_imports += [
    'beautifulsoup4',
    'soupsieve',
    'soupsieve.bs4',
]

# Add all found imports
for imp in hidden_imports:
    if imp not in a.hiddenimports:
        a.hiddenimports.append(imp)
