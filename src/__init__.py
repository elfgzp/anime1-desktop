"""Anime1 - Desktop application for browsing Anime1.me"""

# 版本号在构建时注入到这个文件
# 详见 scripts/build.py 中的 update_version_file 函数
import sys
try:
    if getattr(sys, 'frozen', False):
        # In frozen mode, always use get_version() to read from version.txt
        # This ensures the version is correctly read after updates
        from .utils.version import get_version
        __version__ = get_version()
    else:
        from ._version import __version__
except ImportError:
    # If _version.py doesn't exist (development environment), use get_version()
    from .utils.version import get_version
    __version__ = get_version()
