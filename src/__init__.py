"""Anime1 - Desktop application for browsing Anime1.me"""

# 版本号在构建时注入到这个文件
# 详见 scripts/build.py 中的 update_version_file 函数
try:
    from ._version import __version__
except ImportError:
    # 如果 _version.py 不存在（开发环境），使用 get_version()
    from .utils.version import get_version
    __version__ = get_version()
