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

    For frozen executables, the version file location depends on the build mode:
    - Onedir mode: in Resources directory (macOS) or next to executable (Windows/Linux)
    - Onefile mode: in the _MEIPASS temporary extraction directory

    For development mode, it's stored in the project root.

    Returns:
        Path to the version file
    """
    import logging
    logger = logging.getLogger(__name__)

    if getattr(sys, 'frozen', False):
        # Running as frozen executable
        exe_dir = Path(sys.executable).parent

        # Check if running from macOS app bundle (onedir mode)
        if sys.platform == "darwin" and exe_dir.name == "MacOS":
            resources_dir = exe_dir.parent.parent / "Resources"
            version_path = resources_dir / "version.txt"
            if version_path.exists():
                logger.debug(f"[VERSION] Found version.txt in Resources: {version_path}")
                return version_path
            # Also check in Resources/src/ (from --add-data src:src)
            src_version = resources_dir / "src" / "version.txt"
            if src_version.exists():
                logger.debug(f"[VERSION] Found version.txt in Resources/src: {src_version}")
                return src_version

        # Check if running in onefile mode (files extracted to _MEIPASS)
        if hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            logger.debug(f"[VERSION] Onefile mode detected, MEIPASS: {meipass}")

            # In onefile mode, data files are extracted to _MEIPASS
            # The src directory should be at _MEIPASS/src/
            src_in_meipass = meipass / "src" / "version.txt"
            if src_in_meipass.exists():
                logger.debug(f"[VERSION] Found version.txt in _MEIPASS/src: {src_in_meipass}")
                return src_in_meipass

            # Also check at root of _MEIPASS
            version_in_meipass = meipass / "version.txt"
            if version_in_meipass.exists():
                logger.debug(f"[VERSION] Found version.txt in _MEIPASS: {version_in_meipass}")
                return version_in_meipass

        # Onedir mode (Windows/Linux or non-bundle macOS): check next to executable
        version_path = exe_dir / "version.txt"
        if version_path.exists():
            logger.debug(f"[VERSION] Found version.txt next to executable: {version_path}")
            return version_path

        # Also check in src/ subdirectory (from PyInstaller --add-data)
        src_version = exe_dir / "src" / "version.txt"
        if src_version.exists():
            logger.debug(f"[VERSION] Found version.txt in src/ subdirectory: {src_version}")
            return src_version

        # Fallback to executable directory
        logger.debug(f"[VERSION] Version file not found, using fallback: {exe_dir / 'version.txt'}")
        return exe_dir / "version.txt"
    else:
        # Running as normal Python script - version file in project root
        version_path = Path(__file__).parent.parent.parent / "version.txt"
        logger.debug(f"[VERSION] Development mode, version file: {version_path}")
        return version_path


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
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[VERSION] get_version() called, frozen={getattr(sys, 'frozen', False)}")

    # Check version file first (for frozen executables)
    version_file = get_version_file_path()
    logger.debug(f"[VERSION] Version file path: {version_file}")
    logger.debug(f"[VERSION] Version file exists: {version_file.exists()}")

    if version_file.exists():
        try:
            version = version_file.read_text(encoding='utf-8').strip()
            logger.debug(f"[VERSION] Read from file: '{version}'")
            if version:
                return version
        except Exception as e:
            logger.debug(f"[VERSION] Failed to read version file: {e}")

    # Check environment variable (set during build)
    env_version = os.environ.get(ENV_VERSION)
    logger.debug(f"[VERSION] Environment variable: {env_version}")
    if env_version:
        return env_version

    # Try git
    git_version = get_git_version()
    logger.debug(f"[VERSION] Git version: {git_version}")
    return git_version


def get_window_title() -> str:
    """Get window title with version information.

    Returns:
        Window title string:
        - "Anime1 桌面版 v{version}" if version is a release version
        - "Anime1 桌面版 测试版 ({commit_id})" if version is dev
    """
    version = get_version()

    # Check if version is a release version (matches v1.2.3 or 1.2.3 or 1.2.3-abc123 format)
    # Release versions have at least major.minor.patch pattern (x.y.z)
    if version and _is_release_version(version):
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


def _is_release_version(version: str) -> bool:
    """Check if version is a release version (not dev).

    Release version formats:
    - v1.2.3 or 1.2.3 (semantic version)
    - 1.2.3-abc123 (version with commit id)

    Dev version formats:
    - dev
    - dev-abc123

    Args:
        version: Version string to check

    Returns:
        True if it's a release version, False if it's a dev version
    """
    # Remove v/V prefix if present
    version = version.lstrip(VERSION_PREFIXES)

    # Split by '-' to separate version and commit id
    parts = version.split('-', 1)
    base_version = parts[0]

    # Check if base version matches semantic versioning pattern (x.y.z or x.y)
    # Pattern: digits.digits or digits.digits.digits
    import re
    pattern = r'^\d+\.\d+(\.\d+)?$'
    return bool(re.match(pattern, base_version))
