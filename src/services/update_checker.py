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
    """Semantic version comparator supporting pre-release versions."""
    
    # Development version prefix (from git describe --tags without tag)
    VERSION_DEV_PREFIX = "dev"

    @staticmethod
    def parse_version(version_str: str) -> Tuple[List[int], Optional[str], Optional[int]]:
        """Parse version string into components.

        Args:
            version_str: Version string like "1.0.0", "1.0.0-rc.1", or "abc123" (dev commit)

        Returns:
            Tuple of (version_numbers, pre_release_type, pre_release_number)
            Example: ("1.0.0") -> ([1, 0, 0], None, None)
                     ("1.0.0-rc.1") -> ([1, 0, 0], "rc", 1)
                     ("abc123") -> ([0, 0, 0], "dev", 0)  # Dev versions are oldest
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip(VERSION_PREFIXES)

        def is_dev_version(s: str) -> bool:
            """Check if this is a development version (commit id or non-standard format)."""
            if s.startswith(VersionComparator.VERSION_DEV_PREFIX):
                return True
            # Check if it's a standard version (num.num.num or num.num.num-prerelease)
            # Standard versions only contain digits, dots, and prerelease identifiers
            import re
            # Match patterns like: 1.0.0, 1.0, 1.0.0-rc.1, 1.0.0-beta.2
            standard_pattern = r'^\d+(\.\d+)*(-(rc|beta|alpha)\.?(\d+)?)?$'
            return not bool(re.match(standard_pattern, s, re.IGNORECASE))

        # Check for dev/development version (e.g., commit id like "abc123" or "devabc123")
        # These are development builds without a proper version tag
        if is_dev_version(version_str):
            # This is a development version, treat it as older than any release
            # Return (0, 0, 0) with "dev" pre-release to ensure it's less than any stable version
            return [0, 0, 0], PRE_RELEASE_DEV, 0

        # Split version and pre-release
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
        pre_release_number = None

        if pre_release:
            # Match patterns like "rc.1", "beta.2", "alpha.3"
            match = re.match(PRE_RELEASE_PATTERN, pre_release.lower())
            if match:
                pre_release_type = match.group(1)
                pre_release_number = int(match.group(2)) if match.group(2) else DEFAULT_VERSION_COMPONENT

        return version_numbers, pre_release_type, pre_release_number
    
    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        v1_nums, v1_pre, v1_pre_num = VersionComparator.parse_version(version1)
        v2_nums, v2_pre, v2_pre_num = VersionComparator.parse_version(version2)
        
        # Compare base version numbers
        for i in range(VERSION_COMPONENT_COUNT):
            if v1_nums[i] < v2_nums[i]:
                return -1
            elif v1_nums[i] > v2_nums[i]:
                return 1
        
        # If base versions are equal, compare pre-release
        # Stable version (no pre-release) > pre-release version
        if v1_pre is None and v2_pre is None:
            return 0
        elif v1_pre is None:
            return 1  # v1 is stable, v2 is pre-release
        elif v2_pre is None:
            return -1  # v1 is pre-release, v2 is stable
        
        # Both are pre-release, compare type and number
        # Order: alpha < beta < rc
        v1_order = PRE_RELEASE_ORDER.get(v1_pre, DEFAULT_VERSION_COMPONENT)
        v2_order = PRE_RELEASE_ORDER.get(v2_pre, DEFAULT_VERSION_COMPONENT)
        
        if v1_order < v2_order:
            return -1
        elif v1_order > v2_order:
            return 1
        
        # Same pre-release type, compare numbers
        if v1_pre_num < v2_pre_num:
            return -1
        elif v1_pre_num > v2_pre_num:
            return 1
        
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
        system = platform.system().lower()
        machine = platform.machine().lower()
        
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
        asset_lower = asset_name.lower()
        
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
        
        # If no architecture keyword found, assume x64 for Windows/Linux
        if not arch_match and platform_name in (PLATFORM_WINDOWS, PLATFORM_LINUX):
            # Check if it's explicitly not arm64
            if ARCH_EXCLUDE_ARM not in asset_lower and ARCH_EXCLUDE_AARCH not in asset_lower:
                arch_match = True
        
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
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version or __version__
        self.channel = channel
        self.timeout = timeout
        self.api_base = GITHUB_API_BASE
        
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
        
        Args:
            include_prerelease: Whether to include pre-release versions
            
        Returns:
            List of release dictionaries
            
        Raises:
            Exception: If API request fails or rate limit is exceeded
        """
        try:
            # Use requests without authentication - works for public repos
            # Rate limit: 60 requests/hour for unauthenticated requests
            headers = {
                "Accept": GITHUB_API_ACCEPT_HEADER,
                "User-Agent": GITHUB_USER_AGENT
            }
            
            if self.channel == UpdateChannel.STABLE and not include_prerelease:
                # For stable channel, get only latest stable release
                url = self._get_releases_url(latest_only=True)
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                # Handle rate limit
                if response.status_code == HTTP_STATUS_FORBIDDEN:
                    rate_limit_remaining = response.headers.get(RATE_LIMIT_REMAINING_HEADER, RATE_LIMIT_EXHAUSTED)
                    if rate_limit_remaining == RATE_LIMIT_EXHAUSTED:
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")
                
                response.raise_for_status()
                release = response.json()
                # Filter out pre-releases for stable channel
                if release.get(API_FIELD_PRERELEASE, False):
                    return []
                return [release]
            else:
                # For test channel or when including pre-releases, get all releases
                url = self._get_releases_url(latest_only=False)
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                # Handle rate limit
                if response.status_code == HTTP_STATUS_FORBIDDEN:
                    rate_limit_remaining = response.headers.get(RATE_LIMIT_REMAINING_HEADER, RATE_LIMIT_EXHAUSTED)
                    if rate_limit_remaining == RATE_LIMIT_EXHAUSTED:
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")
                
                response.raise_for_status()
                releases = response.json()
                
                # Filter based on channel
                if self.channel == UpdateChannel.STABLE:
                    releases = [r for r in releases if not r.get(API_FIELD_PRERELEASE, False)]
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
        
        Args:
            assets: List of asset dictionaries from GitHub API
            
        Returns:
            Matching asset dictionary or None
        """
        platform_name, arch = PlatformDetector.get_platform_info()
        
        for asset in assets:
            asset_name = asset.get(API_FIELD_NAME, "")
            if PlatformDetector.match_asset(asset_name, platform_name, arch):
                return asset
        
        return None
    
    def check_for_update(self) -> UpdateInfo:
        """Check for available updates.
        
        Returns:
            UpdateInfo object with update status
        """
        try:
            # Fetch releases
            include_prerelease = self.channel == UpdateChannel.TEST
            releases = self._fetch_releases(include_prerelease=include_prerelease)
            
            if not releases:
                return UpdateInfo(
                    has_update=False,
                    current_version=self.current_version
                )
            
            # Find the latest version that's newer than current
            latest_release = None
            latest_version = None
            
            for release in releases:
                tag_name = release.get(API_FIELD_TAG_NAME, "")
                # Remove 'v' prefix for comparison
                version_str = tag_name.lstrip(VERSION_PREFIXES)
                
                # Skip if not newer than current
                if VersionComparator.compare_versions(version_str, self.current_version) <= 0:
                    continue
                
                # Check if this is the latest we've seen
                if latest_version is None or VersionComparator.compare_versions(version_str, latest_version) > 0:
                    latest_version = version_str
                    latest_release = release
            
            if latest_release is None:
                return UpdateInfo(
                    has_update=False,
                    current_version=self.current_version
                )
            
            # Find matching asset
            assets = latest_release.get(API_FIELD_ASSETS, [])
            matching_asset = self._find_matching_asset(assets)
            
            if not matching_asset:
                return UpdateInfo(
                    has_update=True,
                    current_version=self.current_version,
                    latest_version=latest_release.get(API_FIELD_TAG_NAME, ""),
                    is_prerelease=latest_release.get(API_FIELD_PRERELEASE, False),
                    release_notes=latest_release.get(API_FIELD_BODY, ""),
                )
            
            return UpdateInfo(
                has_update=True,
                current_version=self.current_version,
                latest_version=latest_release.get(API_FIELD_TAG_NAME, ""),
                is_prerelease=latest_release.get(API_FIELD_PRERELEASE, False),
                release_notes=latest_release.get(API_FIELD_BODY, ""),
                download_url=matching_asset.get(API_FIELD_BROWSER_DOWNLOAD_URL),
                asset_name=matching_asset.get(API_FIELD_NAME),
                download_size=matching_asset.get(API_FIELD_SIZE),
                published_at=latest_release.get(API_FIELD_PUBLISHED_AT),
            )
            
        except Exception as e:
            # Return error state
            return UpdateInfo(
                has_update=False,
                current_version=self.current_version
            )
