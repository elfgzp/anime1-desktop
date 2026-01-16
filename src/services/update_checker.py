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
    
    @staticmethod
    def parse_version(version_str: str) -> Tuple[List[int], Optional[str], Optional[int]]:
        """Parse version string into components.
        
        Args:
            version_str: Version string like "1.0.0" or "1.0.0-rc.1"
            
        Returns:
            Tuple of (version_numbers, pre_release_type, pre_release_number)
            Example: ("1.0.0") -> ([1, 0, 0], None, None)
                     ("1.0.0-rc.1") -> ([1, 0, 0], "rc", 1)
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('vV')
        
        # Split version and pre-release
        parts = version_str.split('-', 1)
        base_version = parts[0]
        pre_release = parts[1] if len(parts) > 1 else None
        
        # Parse base version (MAJOR.MINOR.PATCH)
        version_numbers = [int(x) for x in base_version.split('.')]
        # Ensure we have at least 3 components
        while len(version_numbers) < 3:
            version_numbers.append(0)
        
        # Parse pre-release if present
        pre_release_type = None
        pre_release_number = None
        
        if pre_release:
            # Match patterns like "rc.1", "beta.2", "alpha.3"
            match = re.match(r'^(rc|beta|alpha)\.?(\d+)?', pre_release.lower())
            if match:
                pre_release_type = match.group(1)
                pre_release_number = int(match.group(2)) if match.group(2) else 0
        
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
        for i in range(3):
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
        pre_order = {"alpha": 1, "beta": 2, "rc": 3}
        v1_order = pre_order.get(v1_pre, 0)
        v2_order = pre_order.get(v2_pre, 0)
        
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
        if system == "darwin":
            platform_name = "macos"
        elif system == "windows":
            platform_name = "windows"
        elif system == "linux":
            platform_name = "linux"
        else:
            platform_name = system
        
        # Normalize architecture
        if machine in ("x86_64", "amd64"):
            arch = "x64"
        elif machine in ("arm64", "aarch64"):
            arch = "arm64"
        elif machine in ("i386", "i686", "x86"):
            arch = "x86"
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
            "windows": ["windows", "win"],
            "macos": ["macos", "mac", "darwin"],
            "linux": ["linux"]
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
            "x64": ["x64", "amd64", "x86_64"],
            "arm64": ["arm64", "aarch64", "m1", "m2", "m3", "apple"],
            "x86": ["x86", "i386", "i686"]
        }
        
        arch_match = False
        for keyword in arch_keywords.get(arch, []):
            if keyword in asset_lower:
                arch_match = True
                break
        
        # If no architecture keyword found, assume x64 for Windows/Linux
        if not arch_match and platform_name in ("windows", "linux"):
            # Check if it's explicitly not arm64
            if "arm" not in asset_lower and "aarch" not in asset_lower:
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
        self.api_base = "https://api.github.com"
        
    def _get_releases_url(self, latest_only: bool = False) -> str:
        """Get GitHub Releases API URL.
        
        Args:
            latest_only: If True, get only the latest release
            
        Returns:
            API URL string
        """
        if latest_only:
            return f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        return f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
    
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
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Anime1-Desktop-Updater/1.0"
            }
            
            if self.channel == UpdateChannel.STABLE and not include_prerelease:
                # For stable channel, get only latest stable release
                url = self._get_releases_url(latest_only=True)
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                # Handle rate limit
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if rate_limit_remaining == "0":
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")
                
                response.raise_for_status()
                release = response.json()
                # Filter out pre-releases for stable channel
                if release.get("prerelease", False):
                    return []
                return [release]
            else:
                # For test channel or when including pre-releases, get all releases
                url = self._get_releases_url(latest_only=False)
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                # Handle rate limit
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if rate_limit_remaining == "0":
                        raise Exception("GitHub API 速率限制已用完，请稍后再试")
                
                response.raise_for_status()
                releases = response.json()
                
                # Filter based on channel
                if self.channel == UpdateChannel.STABLE:
                    releases = [r for r in releases if not r.get("prerelease", False)]
                # For test channel, include all releases
                
                return releases
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("仓库或发布版本不存在")
            elif e.response.status_code == 403:
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
            asset_name = asset.get("name", "")
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
                tag_name = release.get("tag_name", "")
                # Remove 'v' prefix for comparison
                version_str = tag_name.lstrip('vV')
                
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
            assets = latest_release.get("assets", [])
            matching_asset = self._find_matching_asset(assets)
            
            if not matching_asset:
                return UpdateInfo(
                    has_update=True,
                    current_version=self.current_version,
                    latest_version=latest_release.get("tag_name", ""),
                    is_prerelease=latest_release.get("prerelease", False),
                    release_notes=latest_release.get("body", ""),
                )
            
            return UpdateInfo(
                has_update=True,
                current_version=self.current_version,
                latest_version=latest_release.get("tag_name", ""),
                is_prerelease=latest_release.get("prerelease", False),
                release_notes=latest_release.get("body", ""),
                download_url=matching_asset.get("browser_download_url"),
                asset_name=matching_asset.get("name"),
                download_size=matching_asset.get("size"),
                published_at=latest_release.get("published_at"),
            )
            
        except Exception as e:
            # Return error state
            return UpdateInfo(
                has_update=False,
                current_version=self.current_version
            )
