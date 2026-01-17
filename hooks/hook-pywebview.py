# PyInstaller hook for pywebview
# This hook ensures all pywebview submodules and dependencies are included

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all pywebview submodules
hidden_imports = collect_submodules('pywebview')

# Add specific pywebview modules that are often needed
hidden_imports += [
    'pywebview',
    'pywebview.util',
    'pywebview.http',
    'pywebview.guarded_encodings',
    'pywebview.window',
    'pywebview.dom',
    'pywebview.browse',
    'pywebview.js',
]

# Platform-specific imports
import sys
if sys.platform == 'win32':
    hidden_imports += [
        'pywebview.win32',
        'pywebview.win32.edge',
        'pywebview.win32.edge.webview2',
        'pywebview.win32.net',
        'pywebview.win32.util',
    ]
elif sys.platform == 'darwin':
    hidden_imports += [
        'pywebview.macos',
        'pywebview.macos.util',
    ]
elif sys.platform == 'linux':
    hidden_imports += [
        'pywebview.linux',
        'pywebview.linux.gtk',
        'pywebview.linux.util',
    ]

# Add to hidden imports
a = hidden_imports
