"""Update checker service for checking GitHub Releases.

This module provides functionality to check for updates from GitHub Releases.
It uses the GitHub REST API which does NOT require authentication for public repositories.

Rate Limits:
- Unauthenticated requests: 60 requests per hour
- Authenticated requests: 5000 requests per hour (if token is provided)

For this application, unauthenticated requests are sufficient as update checks
are infrequent. The rate limit of 60/hour is more than enough for normal usage.
"""
import re
import platform
import sys
import os
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

import requests

from ..config import DEFAULT_TIMEOUT
from .. import __version__
from .constants import (
    VERSION_PREFIXES,
    VERSION_SEPARATOR,
    VERSION_COMPONENT_COUNT,
    DEFAULT_VERSION_COMPONENT,
    PRE_RELEASE_ALPHA,
    PRE_RELEASE_BETA,
    PRE_RELEASE_RC,
    PRE_RELEASE_DEV,
    PRE_RELEASE_ORDER,
    PRE_RELEASE_PATTERN,
    GITHUB_API_BASE,
    GITHUB_API_ACCEPT_HEADER,
    GITHUB_USER_AGENT,
    GITHUB_RELEASES_ENDPOINT,
    GITHUB_LATEST_RELEASE_ENDPOINT,
    API_FIELD_TAG_NAME,
    API_FIELD_ASSETS,
    API_FIELD_PRERELEASE,
    API_FIELD_BROWSER_DOWNLOAD_URL,
    API_FIELD_NAME,
    API_FIELD_SIZE,
    API_FIELD_PUBLISHED_AT,
    API_FIELD_BODY,
    HTTP_STATUS_FORBIDDEN,
    HTTP_STATUS_NOT_FOUND,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_EXHAUSTED,
    PLATFORM_WINDOWS_KEYWORDS,
    PLATFORM_MACOS_KEYWORDS,
    PLATFORM_LINUX_KEYWORDS,
    ARCH_X64_KEYWORDS,
    ARCH_ARM64_KEYWORDS,
    ARCH_X86_KEYWORDS,
    PLATFORM_WINDOWS,
    PLATFORM_MACOS,
    PLATFORM_LINUX,
    ARCH_X64,
    ARCH_ARM64,
    ARCH_X86,
    SYSTEM_DARWIN,
    SYSTEM_WINDOWS,
    SYSTEM_LINUX,
    MACHINE_X86_64,
    MACHINE_AMD64,
    MACHINE_ARM64,
    MACHINE_AARCH64,
    MACHINE_I386,
    MACHINE_I686,
    MACHINE_X86,
    ARCH_EXCLUDE_ARM,
    ARCH_EXCLUDE_AARCH,
)


# GitHub token for authenticated requests (higher rate limit)
# Set via environment variable GITHUB_TOKEN
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


class UpdateChannel(Enum):
    """Update channel type."""
    STABLE = "stable"  # 只检查稳定版本
    TEST = "test"  # 检查测试版本（包括 rc、beta、alpha）


@dataclass
class UpdateInfo:
    """Update information."""
    has_update: bool
    current_version: str
    latest_version: Optional[str] = None
    is_prerelease: bool = False
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    asset_name: Optional[str] = None
    download_size: Optional[int] = None
    published_at: Optional[str] = None


class VersionComparator:
    """Semantic version comparator supporting pre-release versions.

    Version format support:
    - Release: "1.0.0", "0.2.0"
    - Pre-release: "1.0.0-rc.1", "1.0.0-beta.2", "1.0.0-alpha.3"
    - Dev version: "1.0.0-abc123" (development build based on 1.0.0)

    Comparison order (oldest to newest):
    - 1.0.0-abc123 (dev version on 1.0.0)
    - 1.0.0 (release)
    - 1.0.0-rc.1 (pre-release)
    - 1.0.1-xyz456 (dev version on 1.0.1)
    - 1.0.1 (release)
    """

    # Development version prefix
    VERSION_DEV_PREFIX = "dev"

    @staticmethod
    def parse_version(version_str: str) -> Tuple[List[int], Optional[str], Optional[str]]:
        """Parse version string into components.

        Args:
            version_str: Version string like "1.0.0", "1.0.0-rc.1", or "1.0.0-abc123"

        Returns:
            Tuple of (version_numbers, pre_release_type, pre_release_extra)
            - version_numbers: List of version components [major, minor, patch]
            - pre_release_type: Pre-release type (e.g., "rc", "beta", "alpha", "dev")
            - pre_release_extra: Additional info (e.g., number for rc/beta/alpha, commit id for dev)

            Example:
            - ("1.0.0") -> ([1, 0, 0], None, None)
            - ("1.0.0-rc.1") -> ([1, 0, 0], "rc", "1")
            - ("1.0.0-abc123") -> ([1, 0, 0], "dev", "abc123")
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip(VERSION_PREFIXES)

        # Split version and pre-release (only split on first "-")
        parts = version_str.split(VERSION_SEPARATOR, 1)
        base_version = parts[0]
        pre_release = parts[1] if len(parts) > 1 else None

        # Parse base version (MAJOR.MINOR.PATCH)
        version_numbers = [int(x) for x in base_version.split('.')]
        # Ensure we have at least 3 components
        while len(version_numbers) < VERSION_COMPONENT_COUNT:
            version_numbers.append(DEFAULT_VERSION_COMPONENT)

        # Parse pre-release if present
        pre_release_type = None
        pre_release_extra = None

        if pre_release:
            # First check for known pre-release patterns: rc, beta, alpha
            # Match patterns like "rc.1", "beta.2", "alpha.3", "rc", "beta", "alpha"
            match = re.match(PRE_RELEASE_PATTERN, pre_release.lower())
            if match:
                pre_release_type = match.group(1)
                pre_release_extra = match.group(2) or str(DEFAULT_VERSION_COMPONENT)
            # Check for dev version: commit id format (e.g., "abc123", "xyz456")
            # Dev versions are identified by having a commit id after the base version
            # Format: "x.x.x-abc123" where abc123 is a git short commit id (4-40 alphanumeric chars)
            # Git short commit ids are typically 7 chars but can be 4-40
            # Must contain at least one digit to distinguish from words like "alpha", "beta"
            elif re.match(r'^[0-9a-z]{4,40}$', pre_release, re.IGNORECASE) and re.search(r'\d', pre_release):
                pre_release_type = PRE_RELEASE_DEV
                pre_release_extra = pre_release

        return version_numbers, pre_release_type, pre_release_extra

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two version strings.

        Version comparison rules:
        1. Compare base version numbers first (major.minor.patch)
        2. If base versions are equal and both are dev versions:
           - Treat dev version as OLDER than stable release (for update check)
        3. If base versions are different:
           - v0.2.0-dev > v0.1.0 (dev version on newer base)

        This ensures:
        - v0.1.0 < v0.1.0-dev-xyz456 < v0.2.0 < v0.2.0-dev-abc123
        - Local dev versions are correctly detected as having available updates

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        v1_nums, v1_pre, v1_extra = VersionComparator.parse_version(version1)
        v2_nums, v2_pre, v2_extra = VersionComparator.parse_version(version2)

        # Compare base version numbers first
        for i in range(VERSION_COMPONENT_COUNT):
            if v1_nums[i] < v2_nums[i]:
                return -1
            elif v1_nums[i] > v2_nums[i]:
                return 1

        # Base versions are equal
        # Special case: if both have same base and both are dev versions
        # Treat dev version as older than stable release (for update checking)
        if v1_pre == PRE_RELEASE_DEV and v2_pre != PRE_RELEASE_DEV:
            if v2_pre is None:
                # v1 is dev, v2 is stable: dev < stable
                return -1
            # v1 is dev, v2 is pre-release (rc/beta/alpha): dev < pre-release
            return -1
        elif v1_pre != PRE_RELEASE_DEV and v2_pre == PRE_RELEASE_DEV:
            # v1 is stable/pre-release, v2 is dev: stable > dev
            return 1

        # Normal pre-release comparison
        pre_release_order = {
            PRE_RELEASE_ALPHA: 0,
            PRE_RELEASE_BETA: 1,
            PRE_RELEASE_RC: 2,
            None: 3,  # Stable release is highest
        }

        v1_order = pre_release_order.get(v1_pre, -1)
        v2_order = pre_release_order.get(v2_pre, -1)

        if v1_order < v2_order:
            return -1
        elif v1_order > v2_order:
            return 1

        # Same pre-release type, compare numbers (for rc/alpha/beta)
        if v1_pre in (PRE_RELEASE_ALPHA, PRE_RELEASE_BETA, PRE_RELEASE_RC):
            try:
                v1_num = int(v1_extra) if v1_extra else 0
                v2_num = int(v2_extra) if v2_extra else 0
                if v1_num < v2_num:
                    return -1
                elif v1_num > v2_num:
                    return 1
            except (ValueError, TypeError):
                pass

        # Dev versions with same base are equal
        return 0

    @staticmethod
    def is_prerelease(version_str: str) -> bool:
        """Check if version is a pre-release version.
        
        Args:
            version_str: Version string
            
        Returns:
            True if version is pre-release (rc, beta, alpha)
        """
        _, pre_release_type, _ = VersionComparator.parse_version(version_str)
        return pre_release_type is not None


class PlatformDetector:
    """Detect current platform and architecture."""
    
    @staticmethod
    def get_platform_info() -> Tuple[str, str]:
        """Get current platform and architecture.

        Returns:
            Tuple of (platform_name, architecture)
            Example: ("windows", "x64"), ("macos", "arm64"), ("linux", "x64")
        """
        logger = logging.getLogger(__name__)

        system = platform.system().lower()
        machine = platform.machine().lower()

        logger.debug(f"[UPDATE] Platform detection: system={system}, machine={machine}")

        # Normalize platform name
        if system == SYSTEM_DARWIN:
            platform_name = PLATFORM_MACOS
        elif system == SYSTEM_WINDOWS:
            platform_name = PLATFORM_WINDOWS
        elif system == SYSTEM_LINUX:
            platform_name = PLATFORM_LINUX
        else:
            platform_name = system

        # Normalize architecture
        if machine in (MACHINE_X86_64, MACHINE_AMD64):
            arch = ARCH_X64
        elif machine in (MACHINE_ARM64, MACHINE_AARCH64):
            arch = ARCH_ARM64
        elif machine in (MACHINE_I386, MACHINE_I686, MACHINE_X86):
            arch = ARCH_X86
        else:
            arch = machine

        logger.debug(f"[UPDATE] Platform detection result: platform={platform_name}, arch={arch}")
        return platform_name, arch
    
    @staticmethod
    def match_asset(asset_name: str, platform_name: str, arch: str) -> bool:
        """Check if asset name matches current platform.

        Args:
            asset_name: Asset filename
            platform_name: Target platform (windows, macos, linux)
            arch: Target architecture (x64, arm64, x86)

        Returns:
            True if asset matches platform and architecture
        """
        logger = logging.getLogger(__name__)

        asset_lower = asset_name.lower()

        # Skip installer files (Windows setup.exe)
        if "-setup.exe" in asset_lower:
            logger.debug(f"[UPDATE] Skipping installer file: {asset_name}")
            return False

        # Platform matching
        platform_keywords = {
            PLATFORM_WINDOWS: PLATFORM_WINDOWS_KEYWORDS,
            PLATFORM_MACOS: PLATFORM_MACOS_KEYWORDS,
            PLATFORM_LINUX: PLATFORM_LINUX_KEYWORDS,
        }

        platform_match = False
        for keyword in platform_keywords.get(platform_name, []):
            if keyword in asset_lower:
                platform_match = True
                break

        logger.debug(f"[UPDATE] Asset '{asset_name}': platform_match={platform_match} (platform={platform_name})")

        if not platform_match:
            return False

        # Architecture matching
        arch_keywords = {
            ARCH_X64: ARCH_X64_KEYWORDS,
            ARCH_ARM64: ARCH_ARM64_KEYWORDS,
            ARCH_X86: ARCH_X86_KEYWORDS,
        }

        arch_match = False
        for keyword in arch_keywords.get(arch, []):
            if keyword in asset_lower:
                arch_match = True
                break

        logger.debug(f"[UPDATE] Asset '{asset_name}': arch_match={arch_match} (arch={arch})")

        # Special handling for macOS DMG files (Universal Binaries)
        # macOS DMG files typically contain Universal Binaries supporting both x64 and arm64
        # Match if filename contains "mac" and ends with ".dmg"
        if not arch_match and platform_name == PLATFORM_MACOS:
            if "mac" in asset_lower and asset_lower.endswith('.dmg'):
                logger.debug(f"[UPDATE] Asset '{asset_name}': macOS DMG universal binary")
                arch_match = True

        # If no architecture keyword found, assume x64 for Windows/Linux
        if not arch_match and platform_name in (PLATFORM_WINDOWS, PLATFORM_LINUX):
            # Check if it's explicitly not arm64
            if ARCH_EXCLUDE_ARM not in asset_lower and ARCH_EXCLUDE_AARCH not in asset_lower:
                arch_match = True

        logger.debug(f"[UPDATE] Asset '{asset_name}': final result={arch_match}")
        return arch_match


class UpdateChecker:
    """Check for updates from GitHub Releases."""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        current_version: Optional[str] = None,
        channel: UpdateChannel = UpdateChannel.STABLE,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize update checker.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            current_version: Current application version (defaults to __version__)
            channel: Update channel (STABLE or TEST)
            timeout: Request timeout in seconds
        """
        logger = logging.getLogger(__name__)

        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version or __version__
        self.channel = channel
        self.timeout = timeout
        self.api_base = GITHUB_API_BASE

        logger.debug(f"[UPDATE] UpdateChecker initialized:")
        logger.debug(f"  repo_owner: {repo_owner}")
        logger.debug(f"  repo_name: {repo_name}")
        logger.debug(f"  current_version: {self.current_version}")
        logger.debug(f"  channel: {channel}")
        logger.debug(f"  sys.frozen: {getattr(sys, 'frozen', False)}")
        logger.debug(f"  __version__ (imported): {__version__}")
        
    def _get_releases_url(self, latest_only: bool = False) -> str:
        """Get GitHub Releases API URL.
        
        Args:
            latest_only: If True, get only the latest release
            
        Returns:
            API URL string
        """
        if latest_only:
            endpoint = GITHUB_LATEST_RELEASE_ENDPOINT
        else:
            endpoint = GITHUB_RELEASES_ENDPOINT
        return f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}{endpoint}"
    
    def _fetch_releases(self, include_prerelease: bool = False) -> List[Dict]:
        """Fetch releases from GitHub API.

        Note: For public repositories, no authentication token is required.
        Unauthenticated requests have a rate limit of 60 requests per hour.
        Authenticated requests (with GITHUB_TOKEN env var) have 5000 requests/hour.

        The GITHUB_TOKEN can be set via environment variable to increase rate limit.
        This is useful in CI/CD environments or when checking for updates frequently.

        Args:
            include_prerelease: Whether to include pre-release versions

        Returns:
            List of release dictionaries

        Raises:
            Exception: If API request fails or rate limit is exceeded
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"[UPDATE] _fetch_releases called:")
            logger.debug(f"  include_prerelease: {include_prerelease}")
            logger.debug(f"  channel: {self.channel}")
            logger.debug(f"  GITHUB_TOKEN set: {bool(GITHUB_TOKEN)}")

            # Build headers - add authentication if token is available
            headers = {
                "Accept": GITHUB_API_ACCEPT_HEADER,
                "User-Agent": GITHUB_USER_AGENT
            }

            # Add authentication header if token is available
            # Authenticated requests get higher rate limit (5000 vs 60 requests/hour)
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"

            # Rate limit: 60 requests/hour for unauthenticated requests
            #           5000 requests/hour for authenticated requests

            if self.channel == UpdateChannel.STABLE and not include_prerelease:
                # For stable channel, get only latest stable release
                url = self._get_releases_url(latest_only=True)
                logger.debug(f"[UPDATE] Fetching latest stable release from: {url}")
                response = requests.get(url, headers=headers, timeout=self.timeout)

                # Handle rate limit
                if response.status_code == HTTP_STATUS_FORBIDDEN:
                    rate_limit_remaining = response.headers.get(RATE_LIMIT_REMAINING_HEADER, RATE_LIMIT_EXHAUSTED)
                    if rate_limit_remaining == RATE_LIMIT_EXHAUSTED:
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")

                response.raise_for_status()
                release = response.json()
                logger.debug(f"[UPDATE] Latest release tag: {release.get(API_FIELD_TAG_NAME, 'unknown')}")
                logger.debug(f"[UPDATE] Is prerelease: {release.get(API_FIELD_PRERELEASE, False)}")

                # Filter out pre-releases for stable channel
                if release.get(API_FIELD_PRERELEASE, False):
                    logger.debug(f"[UPDATE] Latest release is prerelease, filtering out for stable channel")
                    return []
                return [release]
            else:
                # For test channel or when including pre-releases, get all releases
                url = self._get_releases_url(latest_only=False)
                logger.debug(f"[UPDATE] Fetching all releases from: {url}")
                response = requests.get(url, headers=headers, timeout=self.timeout)

                # Handle rate limit
                if response.status_code == HTTP_STATUS_FORBIDDEN:
                    rate_limit_remaining = response.headers.get(RATE_LIMIT_REMAINING_HEADER, RATE_LIMIT_EXHAUSTED)
                    if rate_limit_remaining == RATE_LIMIT_EXHAUSTED:
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")

                response.raise_for_status()
                releases = response.json()
                logger.debug(f"[UPDATE] Fetched {len(releases)} releases")

                # Filter based on channel
                if self.channel == UpdateChannel.STABLE:
                    releases = [r for r in releases if not r.get(API_FIELD_PRERELEASE, False)]
                    logger.debug(f"[UPDATE] After filtering prereleases: {len(releases)} releases")
                # For test channel, include all releases

                return releases
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTP_STATUS_NOT_FOUND:
                raise Exception("仓库或发布版本不存在")
            elif e.response.status_code == HTTP_STATUS_FORBIDDEN:
                raise Exception("GitHub API 速率限制已用完，请稍后再试")
            else:
                raise Exception(f"GitHub API 请求失败: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取发布信息失败: {str(e)}")
    
    def _find_matching_asset(self, assets: List[Dict]) -> Optional[Dict]:
        """Find asset matching current platform and architecture.

        For macOS, prefers ZIP files over DMG files for auto-update support.

        Args:
            assets: List of asset dictionaries from GitHub API

        Returns:
            Matching asset dictionary or None
        """
        logger = logging.getLogger(__name__)

        platform_name, arch = PlatformDetector.get_platform_info()
        logger.debug(f"[UPDATE] _find_matching_asset: platform={platform_name}, arch={arch}")
        logger.debug(f"[UPDATE] Checking {len(assets)} assets...")

        # For macOS, prefer ZIP over DMG for auto-update support
        if platform_name == PLATFORM_MACOS:
            # First, try to find a ZIP file that matches
            for asset in assets:
                asset_name = asset.get(API_FIELD_NAME, "")
                asset_lower = asset_name.lower()
                # Check if it's a ZIP file matching macOS + architecture
                if (asset_lower.endswith('.zip') and
                    PlatformDetector.match_asset(asset_name, platform_name, arch)):
                    logger.debug(f"[UPDATE] Found macOS ZIP asset (preferred): {asset_name}")
                    return asset

            # If no ZIP found, fall back to DMG
            for asset in assets:
                asset_name = asset.get(API_FIELD_NAME, "")
                asset_lower = asset_name.lower()
                if (asset_lower.endswith('.dmg') and
                    PlatformDetector.match_asset(asset_name, platform_name, arch)):
                    logger.debug(f"[UPDATE] Found macOS DMG asset (fallback): {asset_name}")
                    return asset

            logger.debug(f"[UPDATE] No matching macOS asset found")
            return None

        # For other platforms, use the original logic (first match)
        for asset in assets:
            asset_name = asset.get(API_FIELD_NAME, "")
            logger.debug(f"[UPDATE] Checking asset: {asset_name}")
            if PlatformDetector.match_asset(asset_name, platform_name, arch):
                logger.debug(f"[UPDATE] Found matching asset: {asset_name}")
                return asset

        logger.debug(f"[UPDATE] No matching asset found")
        return None
    
    def check_for_update(self) -> UpdateInfo:
        """Check for available updates.

        Returns:
            UpdateInfo object with update status
        """
        logger = logging.getLogger(__name__)

        logger.debug(f"[UPDATE] check_for_update called:")
        logger.debug(f"  current_version: {self.current_version}")
        logger.debug(f"  channel: {self.channel}")

        try:
            # Fetch releases
            include_prerelease = self.channel == UpdateChannel.TEST
            releases = self._fetch_releases(include_prerelease=include_prerelease)

            logger.debug(f"[UPDATE] Got {len(releases)} releases to check")

            if not releases:
                logger.debug(f"[UPDATE] No releases found, returning no update")
                return UpdateInfo(
                    has_update=False,
                    current_version=self.current_version,
                    latest_version=None
                )

            # Find the absolute latest version (for display purposes)
            absolute_latest_release = None
            absolute_latest_version = None

            # Find the latest version that's newer than current
            update_release = None
            update_version = None

            for release in releases:
                tag_name = release.get(API_FIELD_TAG_NAME, "")
                # Remove 'v' prefix for comparison
                version_str = tag_name.lstrip(VERSION_PREFIXES)

                # Track absolute latest for display
                if absolute_latest_version is None or VersionComparator.compare_versions(version_str, absolute_latest_version) > 0:
                    absolute_latest_version = version_str
                    absolute_latest_release = release

                # Compare with current version
                cmp_result = VersionComparator.compare_versions(version_str, self.current_version)
                logger.debug(f"[UPDATE] Comparing {version_str} vs {self.current_version}: {cmp_result}")

                # Skip if not newer than current
                if cmp_result <= 0:
                    continue

                # Check if this is the latest we've seen (that's newer than current)
                if update_version is None or VersionComparator.compare_versions(version_str, update_version) > 0:
                    update_version = version_str
                    update_release = release

            # Use absolute latest for display
            latest_version_for_display = absolute_latest_release.get(API_FIELD_TAG_NAME, "") if absolute_latest_release else None
            logger.debug(f"[UPDATE] absolute_latest_version: {absolute_latest_version}")
            logger.debug(f"[UPDATE] update_version (newer than current): {update_version}")
            logger.debug(f"[UPDATE] latest_version_for_display: {latest_version_for_display}")

            if update_release is None:
                # No update available, but we know the latest version
                logger.debug(f"[UPDATE] No update available (current version is latest or newer)")
                return UpdateInfo(
                    has_update=False,
                    current_version=self.current_version,
                    latest_version=latest_version_for_display
                )

            # Find matching asset
            assets = update_release.get(API_FIELD_ASSETS, [])
            logger.debug(f"[UPDATE] All assets in release: {[a.get('name', '') for a in assets]}")
            matching_asset = self._find_matching_asset(assets)

            logger.debug(f"[UPDATE] Update found: {update_version}")
            logger.debug(f"[UPDATE] matching_asset: {matching_asset.get('name') if matching_asset else None}")

            if not matching_asset:
                return UpdateInfo(
                    has_update=True,
                    current_version=self.current_version,
                    latest_version=update_release.get(API_FIELD_TAG_NAME, ""),
                    is_prerelease=update_release.get(API_FIELD_PRERELEASE, False),
                    release_notes=update_release.get(API_FIELD_BODY, ""),
                )

            return UpdateInfo(
                has_update=True,
                current_version=self.current_version,
                latest_version=update_release.get(API_FIELD_TAG_NAME, ""),
                is_prerelease=update_release.get(API_FIELD_PRERELEASE, False),
                release_notes=update_release.get(API_FIELD_BODY, ""),
                download_url=matching_asset.get(API_FIELD_BROWSER_DOWNLOAD_URL),
                asset_name=matching_asset.get(API_FIELD_NAME),
                download_size=matching_asset.get(API_FIELD_SIZE),
                published_at=update_release.get(API_FIELD_PUBLISHED_AT),
            )

        except Exception as e:
            logger.error(f"[UPDATE] Error checking for updates: {e}", exc_info=True)
            # Return error state - include latest_version as None for proper error display
            return UpdateInfo(
                has_update=False,
                current_version=self.current_version,
                latest_version=None
            )
