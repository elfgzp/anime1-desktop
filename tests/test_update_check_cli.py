"""CLI tool for checking updates without starting the main app.

This script allows testing the update checking functionality independently,
useful for CI/CD pipelines and manual testing after builds.

Usage:
    python tests/test_update_check_cli.py --version 0.1.0
    python tests/test_update_check_cli.py --version 0.1.0 --channel stable
    python tests/test_update_check_cli.py --version 0.1.0 --channel test
"""
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import at module level (avoid imports inside functions)
from src.services.update_checker import UpdateChecker, UpdateChannel, UpdateInfo
from src.config import GITHUB_REPO_OWNER, GITHUB_REPO_NAME
from src import __version__ as app_version


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


def main():
    """Main entry point for CLI update checker."""
    parser = argparse.ArgumentParser(
        description="Check for app updates without starting the main app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check with version from build
    python tests/test_update_check_cli.py --version 0.1.0

    # Check with test channel (includes prereleases)
    python tests/test_update_check_cli.py --version 0.1.0 --channel test

    # Check current app version
    python tests/test_update_check_cli.py --current

    # Verbose output with debug logging
    python tests/test_update_check_cli.py --version 0.1.0 --verbose
        """
    )

    # Version source options
    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument(
        "--version", "-v",
        help="Version to check for updates (e.g., 0.1.0)"
    )
    version_group.add_argument(
        "--current", "-c",
        action="store_true",
        help="Use current app version from built-in __version__"
    )

    # Channel options
    parser.add_argument(
        "--channel", "-ch",
        default="stable",
        choices=["stable", "test"],
        help="Update channel (default: stable)"
    )

    # Repository options (for testing)
    parser.add_argument(
        "--owner",
        default=GITHUB_REPO_OWNER,
        help=f"GitHub repository owner (default: {GITHUB_REPO_OWNER})"
    )
    parser.add_argument(
        "--repo",
        default=GITHUB_REPO_NAME,
        help=f"GitHub repository name (default: {GITHUB_REPO_NAME})"
    )

    # Output options
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        logger = logging.getLogger(__name__)
        logger.debug(f"[CLI] Verbose mode enabled")
        logger.debug(f"[CLI] Python: {sys.version}")
        logger.debug(f"[CLI] Project root: {PROJECT_ROOT}")

    # Determine version to check
    if args.current:
        current_version = app_version
        print(f"[CLI] Using current app version: {current_version}")
    else:
        current_version = args.version
        print(f"[CLI] Using specified version: {current_version}")

    print(f"[CLI] Channel: {args.channel}")
    print(f"[CLI] Repository: {args.owner}/{args.repo}")
    print()

    # Check for updates
    try:
        update_info = check_update(
            current_version=current_version,
            channel=args.channel,
            repo_owner=args.owner,
            repo_name=args.repo
        )

        if args.json:
            import json
            result = {
                "current_version": update_info.current_version,
                "latest_version": update_info.latest_version,
                "has_update": update_info.has_update,
                "is_prerelease": update_info.is_prerelease,
                "download_url": update_info.download_url,
                "asset_name": update_info.asset_name,
                "download_size": update_info.download_size,
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_update_result(update_info, current_version)

        # Exit code: 0 = no update, 1 = update available, 2 = error
        sys.exit(0 if not update_info.has_update else 1)

    except Exception as e:
        print(f"[ERROR] Update check failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
