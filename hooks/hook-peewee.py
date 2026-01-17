# PyInstaller hook for peewee
# Ensures peewee and its dependencies are properly bundled

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('peewee')

# Also include playhouse modules which may be needed
hiddenimports += [
    'playhouse',
    'playhouse.migrate',
    'playhouse.sqlite_ext',
    'playhouse.sqlite_hooks',
    'playhouse.utf8',
    'playhouse.reflection',
    'playhouse.shortcuts',
]
