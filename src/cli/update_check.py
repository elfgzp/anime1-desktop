"""Shared update checking CLI module.

This module provides update checking functionality that can be used by:
- Main application entry points (app.py, desktop.py)
- CLI test scripts (tests/test_update_check_cli.py)

All imports are at module level to avoid issues with PyInstaller onefile builds.
"""
import sys
from pathlib import Path

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import at module level (avoid imports inside functions for PyInstaller compatibility)
from src.services.update_checker import UpdateChecker, UpdateChannel, UpdateInfo
from src.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME


def print_update_result(update_info: UpdateInfo, current_version: str):
    """Print update check result in a formatted way."""
    print("\n" + "=" * 60)
    print("Update Check Result")
    print("=" * 60)
    print(f"  Current Version: {update_info.current_version}")
    print(f"  Has Update:      {update_info.has_update}")
    print(f"  Latest Version:  {update_info.latest_version or 'unknown'}")
    print(f"  Is Prerelease:   {update_info.is_prerelease}")

    if update_info.has_update:
        print(f"\n  [UPDATE AVAILABLE] v{update_info.latest_version}")
        if update_info.download_url:
            print(f"  Download URL:    {update_info.download_url}")
        if update_info.asset_name:
            print(f"  Asset:           {update_info.asset_name}")
        if update_info.download_size:
            print(f"  Size:            {update_info.download_size:,} bytes")
        if update_info.release_notes:
            print(f"\n  Release Notes:")
            # Indent and wrap release notes
            for line in update_info.release_notes.split('\n')[:10]:
                print(f"    {line}")
            if len(update_info.release_notes.split('\n')) > 10:
                print("    ...")
    else:
        if update_info.latest_version:
            print(f"\n  [UP TO DATE] Already at latest version v{update_info.latest_version}")
        else:
            print(f"\n  [UNKNOWN] Could not determine latest version")

    print("=" * 60 + "\n")


def check_update(
    current_version: str,
    channel: str = "stable",
    repo_owner: str = GITHUB_REPO_OWNER,
    repo_name: str = GITHUB_REPO_NAME,
) -> UpdateInfo:
    """Check for updates with given parameters.

    Args:
        current_version: Current version to compare against
        channel: Update channel (stable or test)
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name

    Returns:
        UpdateInfo with update check results
    """
    # Map channel string to enum
    update_channel = UpdateChannel.TEST if channel == "test" else UpdateChannel.STABLE

    # Create checker and check for updates
    checker = UpdateChecker(
        repo_owner=repo_owner,
        repo_name=repo_name,
        current_version=current_version,
        channel=update_channel
    )

    return checker.check_for_update()


def run_check_update(current_version: str, channel: str = "stable") -> int:
    """Run update check and print results.

    Args:
        current_version: Current version to compare against
        channel: Update channel (stable or test)

    Returns:
        Exit code: 0 = no update, 1 = update available, 2 = error
    """
    print(f"[CHECK-UPDATE] Mode: checking for updates...")
    print(f"[CHECK-UPDATE] Current version: {current_version}")
    print(f"[CHECK-UPDATE] Channel: {channel}")

    try:
        update_info = check_update(
            current_version=current_version,
            channel=channel,
        )

        print_update_result(update_info, current_version)

        # Also print to console for visibility (simple format)
        print(f"\n{'='*50}")
        print(f"Update Check Result:")
        print(f"  Current Version: {update_info.current_version}")
        print(f"  Has Update: {update_info.has_update}")
        if update_info.has_update:
            print(f"  Latest Version: {update_info.latest_version}")
        else:
            print(f"  Latest Version: {update_info.latest_version or 'unknown'}")
        print(f"{'='*50}\n")

        return 0 if not update_info.has_update else 1

    except Exception as e:
        print(f"[CHECK-UPDATE] Error: {e}")
        import traceback
        traceback.print_exc()
        return 2
