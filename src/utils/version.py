"""Version utility functions."""
import os
import subprocess
import sys
from pathlib import Path


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
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                tag = result.stdout.strip()
                # Remove 'v' prefix if present
                version = tag.lstrip('vV')
                return version
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # If no tag, try to get commit id
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                commit_id = result.stdout.strip()
                return f"dev-{commit_id}"
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
    except Exception:
        pass
    
    # Fallback to 'dev' if git is not available
    return "dev"


def get_version() -> str:
    """Get application version.
    
    Priority:
    1. Environment variable ANIME1_VERSION (for build time)
    2. Git tag or commit id
    3. Fallback to 'dev'
    
    Returns:
        Version string
    """
    # Check environment variable first (set during build)
    env_version = os.environ.get("ANIME1_VERSION")
    if env_version:
        return env_version
    
    # Try git
    return get_git_version()
