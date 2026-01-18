"""Version utility functions."""
import os
import subprocess
import sys
from pathlib import Path


def _run_subprocess(args, **kwargs):
    """Run subprocess with CREATE_NO_WINDOW flag on Windows to avoid terminal flash.

    Args:
        args: Command arguments
        **kwargs: Additional arguments for subprocess.run

    Returns:
        subprocess.CompletedProcess result
    """
    # On Windows, use CREATE_NO_WINDOW to avoid terminal flash
    if sys.platform == "win32":
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(args, **kwargs)


from .constants import (
    ENV_VERSION,
    VERSION_DEV,
    VERSION_DEV_PREFIX,
    GIT_COMMAND,
    GIT_DESCRIBE_CMD,
    GIT_DESCRIBE_TAGS_FLAG,
    GIT_DESCRIBE_ABBREV_FLAG,
    GIT_REV_PARSE_CMD,
    GIT_REV_PARSE_SHORT_FLAG,
    GIT_HEAD_REF,
    GIT_COMMAND_TIMEOUT,
    GIT_SUCCESS_CODE,
    VERSION_PREFIXES,
    WINDOW_TITLE_BASE,
    WINDOW_TITLE_VERSION_PREFIX,
    WINDOW_TITLE_TEST_SUFFIX,
    COMMIT_ID_DISPLAY_LENGTH,
)


def get_version_file_path() -> Path:
    """Get the path to the version file.

    For frozen executables, the version file is stored:
    - On Windows/Linux: next to the executable OR in src/ subdirectory
    - On macOS: in the Resources directory within the app bundle

    For development mode, it's stored in the project root.

    Returns:
        Path to the version file
    """
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent

        # Check if running from macOS app bundle
        if sys.platform == "darwin" and exe_dir.name == "MacOS":
            # In macOS app bundle, resources are in ../Resources
            resources_dir = exe_dir.parent.parent / "Resources"
            # Check version.txt in Resources (PyInstaller standard)
            version_path = resources_dir / "version.txt"
            if version_path.exists():
                return version_path
            # Check in Resources/src/ (from --add-data src:src)
            src_version = resources_dir / "src" / "version.txt"
            if src_version.exists():
                return src_version
        else:
            # Windows/Linux: check multiple locations
            # 1. Directly next to executable (for some builds)
            version_path = exe_dir / "version.txt"
            if version_path.exists():
                return version_path
            # 2. In src/ subdirectory (from PyInstaller --add-data)
            src_version = exe_dir / "src" / "version.txt"
            if src_version.exists():
                return src_version

        # Fallback to executable directory
        return exe_dir / "version.txt"
    else:
        # Running as normal Python script - version file in project root
        return Path(__file__).parent.parent.parent / "version.txt"


def get_git_version() -> str:
    """Get version from git tag or commit id.
    
    Returns:
        Version string from git tag (without 'v' prefix) or short commit id.
        Falls back to 'dev' if git is not available.
    """
    try:
        # Get project root
        if getattr(sys, 'frozen', False):
            # Running as frozen executable
            project_root = Path(sys.executable).parent
        else:
            # Running as normal Python script
            project_root = Path(__file__).parent.parent.parent
        
        # Try to get the latest tag
        try:
            result = _run_subprocess(
                [GIT_COMMAND, GIT_DESCRIBE_CMD, GIT_DESCRIBE_TAGS_FLAG, GIT_DESCRIBE_ABBREV_FLAG],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=GIT_COMMAND_TIMEOUT,
                check=False,
            )
            if result.returncode == GIT_SUCCESS_CODE and result.stdout.strip():
                tag = result.stdout.strip()
                # Remove 'v' prefix if present
                version = tag.lstrip(VERSION_PREFIXES)
                return version
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # If no tag, try to get commit id
        try:
            result = _run_subprocess(
                [GIT_COMMAND, GIT_REV_PARSE_CMD, GIT_REV_PARSE_SHORT_FLAG, GIT_HEAD_REF],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=GIT_COMMAND_TIMEOUT,
                check=False,
            )
            if result.returncode == GIT_SUCCESS_CODE and result.stdout.strip():
                commit_id = result.stdout.strip()
                return f"{VERSION_DEV_PREFIX}{commit_id}"
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
    except Exception:
        pass
    
    # Fallback to 'dev' if git is not available
    return VERSION_DEV


def get_version() -> str:
    """Get application version.
    
    Priority:
    1. Version file (created during build, for frozen executables)
    2. Environment variable ANIME1_VERSION (for build time)
    3. Git tag or commit id
    4. Fallback to 'dev'
    
    Returns:
        Version string
    """
    # Check version file first (for frozen executables)
    version_file = get_version_file_path()
    if version_file.exists():
        try:
            version = version_file.read_text(encoding='utf-8').strip()
            if version:
                return version
        except Exception:
            pass
    
    # Check environment variable (set during build)
    env_version = os.environ.get(ENV_VERSION)
    if env_version:
        return env_version
    
    # Try git
    return get_git_version()


def get_window_title() -> str:
    """Get window title with version information.
    
    Returns:
        Window title string:
        - "Anime1 桌面版 v{version}" if version is a release version
        - "Anime1 桌面版 测试版 ({commit_id})" if version is dev
    """
    version = get_version()
    
    # Check if version is a release version (not dev)
    if version and not version.startswith(VERSION_DEV):
        # It's a release version, show version number
        return f"{WINDOW_TITLE_BASE} {WINDOW_TITLE_VERSION_PREFIX}{version}"
    else:
        # It's a dev version, get commit id
        commit_id = None
        try:
            project_root = Path(__file__).parent.parent.parent
            result = _run_subprocess(
                [GIT_COMMAND, GIT_REV_PARSE_CMD, GIT_REV_PARSE_SHORT_FLAG, GIT_HEAD_REF],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=GIT_COMMAND_TIMEOUT,
                check=False,
            )
            if result.returncode == GIT_SUCCESS_CODE and result.stdout.strip():
                commit_id = result.stdout.strip()[:COMMIT_ID_DISPLAY_LENGTH]
        except Exception:
            pass
        
        if commit_id:
            return f"{WINDOW_TITLE_BASE} {WINDOW_TITLE_TEST_SUFFIX} ({commit_id})"
        else:
            return f"{WINDOW_TITLE_BASE} {WINDOW_TITLE_TEST_SUFFIX}"
