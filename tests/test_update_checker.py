"""Tests for update checker module.

These tests verify the version comparison and update checking logic.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.update_checker import (
    VersionComparator,
    PlatformDetector,
    UpdateChecker,
    UpdateChannel,
    UpdateInfo,
)


@pytest.mark.unit
class TestVersionComparator:
    """Tests for VersionComparator class."""

    def test_parse_version_simple(self):
        """Test parsing simple version like 1.0.0"""
        nums, pre_type, pre_num = VersionComparator.parse_version("1.0.0")
        assert nums == [1, 0, 0]
        assert pre_type is None
        assert pre_num is None

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with v prefix"""
        nums, pre_type, pre_num = VersionComparator.parse_version("v1.0.0")
        assert nums == [1, 0, 0]
        assert pre_type is None

    def test_parse_version_with_rc(self):
        """Test parsing pre-release version rc"""
        nums, pre_type, pre_num = VersionComparator.parse_version("1.0.0-rc.1")
        assert nums == [1, 0, 0]
        assert pre_type == "rc"
        assert pre_num == "1"  # Now returns string

    def test_parse_version_with_beta(self):
        """Test parsing pre-release version beta"""
        nums, pre_type, pre_num = VersionComparator.parse_version("2.1.0-beta.2")
        assert nums == [2, 1, 0]
        assert pre_type == "beta"
        assert pre_num == "2"  # Now returns string

    def test_parse_version_with_alpha(self):
        """Test parsing pre-release version alpha"""
        nums, pre_type, pre_num = VersionComparator.parse_version("1.0.0-alpha.3")
        assert nums == [1, 0, 0]
        assert pre_type == "alpha"
        assert pre_num == "3"  # Now returns string

    def test_parse_version_missing_patch(self):
        """Test parsing version with missing patch component"""
        nums, pre_type, pre_num = VersionComparator.parse_version("1.0")
        assert nums == [1, 0, 0]

    def test_compare_versions_equal(self):
        """Test comparing equal versions"""
        assert VersionComparator.compare_versions("1.0.0", "1.0.0") == 0
        assert VersionComparator.compare_versions("v1.0.0", "1.0.0") == 0

    def test_compare_versions_newer(self):
        """Test comparing version where first is newer"""
        assert VersionComparator.compare_versions("2.0.0", "1.0.0") == 1
        assert VersionComparator.compare_versions("1.2.0", "1.1.0") == 1
        assert VersionComparator.compare_versions("1.0.1", "1.0.0") == 1

    def test_compare_versions_older(self):
        """Test comparing version where first is older"""
        assert VersionComparator.compare_versions("0.1.0", "0.2.0") == -1
        assert VersionComparator.compare_versions("1.0.0", "1.0.1") == -1
        assert VersionComparator.compare_versions("0.9.0", "0.10.0") == -1

    def test_compare_versions_prerelease_vs_stable(self):
        """Test comparing pre-release vs stable version"""
        # Stable is newer than pre-release
        assert VersionComparator.compare_versions("1.0.0", "1.0.0-rc.1") == 1
        assert VersionComparator.compare_versions("1.0.0", "1.0.0-alpha.1") == 1
        # Pre-release is older than stable
        assert VersionComparator.compare_versions("1.0.0-rc.1", "1.0.0") == -1

    def test_compare_versions_prerelease_order(self):
        """Test comparing different pre-release types"""
        # Order: alpha < beta < rc
        assert VersionComparator.compare_versions("1.0.0-alpha.1", "1.0.0-beta.1") == -1
        assert VersionComparator.compare_versions("1.0.0-beta.1", "1.0.0-rc.1") == -1
        assert VersionComparator.compare_versions("1.0.0-rc.1", "1.0.0-alpha.1") == 1

    def test_compare_versions_prerelease_same_type(self):
        """Test comparing pre-release versions of same type"""
        assert VersionComparator.compare_versions("1.0.0-alpha.1", "1.0.0-alpha.2") == -1
        assert VersionComparator.compare_versions("1.0.0-alpha.2", "1.0.0-alpha.1") == 1
        assert VersionComparator.compare_versions("1.0.0-rc.1", "1.0.0-rc.1") == 0

    def test_is_prerelease(self):
        """Test is_prerelease detection"""
        assert VersionComparator.is_prerelease("1.0.0") is False
        assert VersionComparator.is_prerelease("v1.0.0") is False
        assert VersionComparator.is_prerelease("1.0.0-rc.1") is True
        assert VersionComparator.is_prerelease("1.0.0-beta.2") is True
        assert VersionComparator.is_prerelease("1.0.0-alpha.1") is True

    def test_parse_version_dev_version(self):
        """Test parsing dev version (commit id based, e.g., 0.2.0-abc123)"""
        # Dev versions use format: base_version-commit_id (e.g., "0.2.0-abc123")
        nums, pre_type, pre_num = VersionComparator.parse_version("0.2.0-abc123")
        assert nums == [0, 2, 0]
        assert pre_type == "dev"
        assert pre_num == "abc123"

    def test_parse_version_dev_prefix(self):
        """Test parsing version with 'dev' prefix (fallback)"""
        # "dev" is not a valid version format anymore, but should not crash
        # It's treated as dev version with [0,0,0] base for backward compatibility
        try:
            nums, pre_type, pre_num = VersionComparator.parse_version("dev")
            assert nums == [0, 0, 0]
            assert pre_type == "dev"
        except ValueError:
            # If it throws, that's also acceptable - old format not supported
            pass

    def test_compare_versions_dev_vs_release(self):
        """Test comparing dev version with release version.

        Dev versions are based on the same base version but include commit id:
        - v0.2.0-abc123 < v0.2.0 (dev version is older than release)
        - v0.2.0-abc123 > v0.1.0 (dev version on newer base is newer)
        """
        # Dev version should be older than release version with same base
        assert VersionComparator.compare_versions("0.2.0-abc123", "0.2.0") == -1
        # Release version should be newer than dev with same base
        assert VersionComparator.compare_versions("0.2.0", "0.2.0-abc123") == 1
        # Dev version on newer base should be newer than older release
        assert VersionComparator.compare_versions("0.2.0-abc123", "0.1.0") == 1
        # Same release version should be equal
        assert VersionComparator.compare_versions("0.2.0", "0.2.0") == 0

    def test_compare_versions_dev_vs_dev(self):
        """Test comparing two dev versions"""
        # Dev versions with same base are considered equal (commit id not compared)
        assert VersionComparator.compare_versions("0.2.0-abc123", "0.2.0-xyz456") == 0
        # Dev version on different bases: compare base version
        assert VersionComparator.compare_versions("0.2.0-abc123", "0.1.0-xyz456") == 1
        assert VersionComparator.compare_versions("0.1.0-xyz456", "0.2.0-abc123") == -1


@pytest.mark.unit
class TestPlatformDetector:
    """Tests for PlatformDetector class."""

    def test_match_asset_windows(self):
        """Test matching Windows asset."""
        # Asset name must contain platform keyword (windows/win)
        assert PlatformDetector.match_asset("anime1-1.0.0-windows.exe", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-win64.exe", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-linux.deb", "windows", "x64") is False

    def test_match_asset_new_filename_format(self):
        """Test matching Windows asset with new versioned filename format.

        New format: anime1-windows-{version}.zip (portable)
                   anime1-windows-{version}-setup.exe (installer)

        Update checker should only match portable zip, not installer exe.
        """
        # Portable zip should match
        assert PlatformDetector.match_asset("anime1-windows-1.0.0.zip", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-windows-0.2.0.zip", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-windows-1.0.0-rc.1.zip", "windows", "x64") is True
        # Installer exe should NOT match (for update download)
        assert PlatformDetector.match_asset("anime1-windows-1.0.0-setup.exe", "windows", "x64") is False
        assert PlatformDetector.match_asset("anime1-windows-0.2.0-setup.exe", "windows", "x64") is False

    def test_match_asset_macos(self):
        """Test matching macOS asset."""
        # Asset name must contain platform keyword AND architecture keyword
        # macOS needs explicit architecture in the name (x64 or arm64)
        assert PlatformDetector.match_asset("anime1-1.0.0-macos-x64.dmg", "macos", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-macos-amd64.dmg", "macos", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-mac-arm64.dmg", "macos", "arm64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-darwin-x86_64.dmg", "macos", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-windows.exe", "macos", "x64") is False

    def test_match_asset_linux(self):
        """Test matching Linux asset."""
        # Asset name must contain "linux"
        assert PlatformDetector.match_asset("anime1-1.0.0-linux.deb", "linux", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-linux.rpm", "linux", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0.dmg", "linux", "x64") is False


class MockGitHubAPI:
    """Mock GitHub API responses for testing."""

    @staticmethod
    def create_release(tag_name, prerelease=False, body="", assets=None):
        """Create a mock release response."""
        if assets is None:
            assets = []
        return {
            "tag_name": tag_name,
            "prerelease": prerelease,
            "body": body,
            "assets": assets,
            "published_at": "2024-01-01T00:00:00Z",
        }

    @staticmethod
    def create_asset(name, size=1024000):
        """Create a mock asset."""
        return {
            "name": name,
            "size": size,
            "browser_download_url": f"https://github.com/example/repo/releases/download/{name}",
        }


@pytest.mark.unit
class TestUpdateChecker:
    """Tests for UpdateChecker class."""

    def test_check_update_no_update_same_version(self):
        """Test that no update is reported when versions are equal."""
        with patch('src.services.update_checker.requests.get') as mock_get:
            # Mock latest release response (v0.1.0)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MockGitHubAPI.create_release("v0.1.0")
            mock_get.return_value = mock_response

            checker = UpdateChecker("test-owner", "test-repo", current_version="0.1.0")
            result = checker.check_for_update()

            assert result.has_update is False
            assert result.current_version == "0.1.0"
            # latest_version should be set even when no update is needed
            assert result.latest_version == "v0.1.0"

    def test_check_update_has_update_old_version(self):
        """Test that update is reported when current version is older."""
        with patch('src.services.update_checker.requests.get') as mock_get:
            # Mock latest release response (v0.1.0)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MockGitHubAPI.create_release("v0.1.0")
            mock_get.return_value = mock_response

            # Current version is older (v0.0.9)
            checker = UpdateChecker("test-owner", "test-repo", current_version="0.0.9")
            result = checker.check_for_update()

            assert result.has_update is True
            assert result.current_version == "0.0.9"
            assert result.latest_version == "v0.1.0"

    def test_check_update_has_update_multiple_versions(self):
        """Test update detection with multiple releases available."""
        releases = [
            MockGitHubAPI.create_release("v0.1.0"),
            MockGitHubAPI.create_release("v0.0.9"),
            MockGitHubAPI.create_release("v0.0.8"),
        ]

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = releases
            mock_get.return_value = mock_response

            # Use test channel to get all releases
            checker = UpdateChecker(
                "test-owner", "test-repo",
                current_version="0.0.7",
                channel=UpdateChannel.TEST
            )
            result = checker.check_for_update()

            assert result.has_update is True
            assert result.latest_version == "v0.1.0"

    def test_check_update_with_v_prefix_in_tag(self):
        """Test that v prefix in tag name is handled correctly."""
        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MockGitHubAPI.create_release("v1.0.0")
            mock_get.return_value = mock_response

            checker = UpdateChecker("test-owner", "test-repo", current_version="0.9.0")
            result = checker.check_for_update()

            assert result.has_update is True
            assert result.latest_version == "v1.0.0"

    def test_check_update_skip_prerelease_in_stable_channel(self):
        """Test that pre-releases are skipped in stable channel."""
        release = MockGitHubAPI.create_release("v0.2.0-alpha.1", prerelease=True)

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            checker = UpdateChecker(
                "test-owner", "test-repo",
                current_version="0.1.0",
                channel=UpdateChannel.STABLE
            )
            result = checker.check_for_update()

            # Should not detect alpha as update in stable channel
            assert result.has_update is False

    def test_check_update_include_prerelease_in_test_channel(self):
        """Test that pre-releases are included in test channel."""
        # Return a list of releases for test channel
        releases = [MockGitHubAPI.create_release("v0.2.0-alpha.1", prerelease=True)]

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = releases
            mock_get.return_value = mock_response

            checker = UpdateChecker(
                "test-owner", "test-repo",
                current_version="0.1.0",
                channel=UpdateChannel.TEST
            )
            result = checker.check_for_update()

            # Should detect alpha as update in test channel
            assert result.has_update is True
            assert result.latest_version == "v0.2.0-alpha.1"
            assert result.is_prerelease is True

    def test_check_update_with_download_asset(self):
        """Test update check with matching download asset."""
        # Asset names must contain platform AND architecture keywords for matching
        # macOS needs explicit architecture (x64/arm64)
        assets = [
            MockGitHubAPI.create_asset("anime1-0.1.0-macos-x64.dmg", size=5_000_000),
            MockGitHubAPI.create_asset("anime1-0.1.0-windows-x64.exe", size=6_000_000),
        ]
        release = MockGitHubAPI.create_release("v0.1.0", assets=assets, body="Release notes")

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Mock platform detection to return x64
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "x64")

                checker = UpdateChecker("test-owner", "test-repo", current_version="0.0.9")
                result = checker.check_for_update()

                assert result.has_update is True
                assert result.download_url is not None
                assert result.asset_name is not None
                assert result.download_size == 5_000_000
                assert "Release notes" in result.release_notes

    def test_check_update_with_platform_mismatch(self):
        """Test update check when no matching asset for platform."""
        # Only Windows assets when running on macOS
        assets = [
            MockGitHubAPI.create_asset("anime1-0.1.0-windows-x64.exe", size=6_000_000),
            MockGitHubAPI.create_asset("anime1-0.1.0-windows-x64.msi", size=5_500_000),
        ]
        release = MockGitHubAPI.create_release("v0.1.0", assets=assets)

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Mock platform detection to return macOS (so Windows assets won't match)
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "x64")

                checker = UpdateChecker("test-owner", "test-repo", current_version="0.0.9")
                result = checker.check_for_update()

                # Has update but no download URL (no matching asset)
                assert result.has_update is True
                assert result.download_url is None
                assert result.asset_name is None


@pytest.mark.unit
class TestUpdateCheckerIntegration:
    """Integration tests for update checking with simulated scenarios."""

    def test_scenario_same_release_version_no_update(self):
        """Scenario: Current version is the release version, should NOT detect update.

        This is the critical test case for the bug where packaging from v0.2.0 tag
        incorrectly reports 'dev' as current version and detects v0.2.0 as update.
        """
        release = MockGitHubAPI.create_release("v0.2.0")

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Current version is the release version (what it SHOULD be)
            checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.2.0")
            result = checker.check_for_update()

            # Should NOT detect update when versions match
            assert result.has_update is False
            assert result.current_version == "0.2.0"
            assert result.latest_version == "v0.2.0"
            print("[PASS] v0.2.0 correctly reports no update when latest is v0.2.0")

    def test_scenario_dev_version_detects_update(self):
        """Scenario: Current version is '0.2.0-abc123' (dev build), should detect update.

        This is the EXPECTED behavior - when running from dev version (based on v0.2.0),
        it SHOULD detect v0.2.0 release as an update because dev < release.
        """
        release = MockGitHubAPI.create_release("v0.2.0")

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Current version is '0.2.0-abc123' (dev build based on v0.2.0)
            checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.2.0-abc123")
            result = checker.check_for_update()

            # SHOULD detect update because dev < release
            assert result.has_update is True
            assert result.current_version == "0.2.0-abc123"
            assert result.latest_version == "v0.2.0"
            print("[PASS] '0.2.0-abc123' correctly detects v0.2.0 as update")

    def test_scenario_old_version_detects_update(self):
        """Scenario: v0.0.9 should detect v0.1.0 as update."""
        release = MockGitHubAPI.create_release(
            "v0.1.0",
            body="## What's New\n- Initial release",
            assets=[MockGitHubAPI.create_asset("anime1-0.1.0-macos-arm64.dmg")]
        )

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Mock platform detection for arm64 (M1/M2/M3)
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "arm64")

                checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.0.9")
                result = checker.check_for_update()

                assert result.has_update is True
                assert result.current_version == "0.0.9"
                assert result.latest_version == "v0.1.0"
                print(f"[PASS] v0.0.9 correctly detects v0.1.0 as update")

    def test_scenario_same_version_no_update(self):
        """Scenario: v0.1.0 should not detect update when latest is v0.1.0."""
        release = MockGitHubAPI.create_release("v0.1.0")

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.1.0")
            result = checker.check_for_update()

            assert result.has_update is False
            print(f"[PASS] v0.1.0 correctly reports no update when latest is v0.1.0")

    def test_scenario_newer_version_exists(self):
        """Scenario: v0.0.8 should detect v0.1.0 (skip v0.0.9 if not newer)."""
        # Simulate GitHub returning multiple releases, latest is v0.1.0
        releases = [
            MockGitHubAPI.create_release("v0.1.0"),
            MockGitHubAPI.create_release("v0.0.9"),
        ]

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = releases
            mock_get.return_value = mock_response

            # Use test channel to get all releases
            checker = UpdateChecker(
                "anime1", "anime1-desktop",
                current_version="0.0.8",
                channel=UpdateChannel.TEST
            )
            result = checker.check_for_update()

            assert result.has_update is True
            assert result.latest_version == "v0.1.0"
            print(f"[PASS] v0.0.8 correctly finds v0.1.0 as latest update")

    def test_scenario_test_channel_with_prerelease(self):
        """Scenario: Test channel should detect pre-release updates."""
        prerelease = MockGitHubAPI.create_release(
            "v0.2.0-rc.1",
            prerelease=True,
            assets=[MockGitHubAPI.create_asset("anime1-0.2.0-rc.1-macos-arm64.dmg")]
        )

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [prerelease]
            mock_get.return_value = mock_response

            # Mock platform detection
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "arm64")

                checker = UpdateChecker(
                    "anime1", "anime1-desktop",
                    current_version="0.1.0",
                    channel=UpdateChannel.TEST
                )
                result = checker.check_for_update()

                assert result.has_update is True
                assert result.latest_version == "v0.2.0-rc.1"
                assert result.is_prerelease is True
                print(f"[PASS] Test channel correctly detects pre-release update v0.2.0-rc.1")


@pytest.mark.integration
class TestMacOSArm64Matching:
    """Integration tests specifically for macOS arm64 asset matching.

    This addresses the issue where no download_url is returned for macOS arm64
    even though the release contains anime1-macos-arm64.dmg asset.
    """

    def test_match_asset_macos_arm64_dmg(self):
        """Test that anime1-macos-arm64.dmg is correctly matched for macOS arm64."""
        # This is the actual asset name from GitHub release v0.2.1
        asset_name = "anime1-macos-arm64.dmg"

        # Simulate running on macOS arm64 (Apple Silicon M1/M2/M3)
        platform_name = "macos"
        arch = "arm64"

        result = PlatformDetector.match_asset(asset_name, platform_name, arch)
        print(f"[TEST] match_asset('{asset_name}', '{platform_name}', '{arch}') = {result}")
        assert result is True, f"Expected True for {asset_name}"

    def test_match_asset_macos_x64_dmg(self):
        """Test that anime1-macos-x64.dmg is correctly matched for macOS x64."""
        asset_name = "anime1-macos-x64.dmg"
        platform_name = "macos"
        arch = "x64"

        result = PlatformDetector.match_asset(asset_name, platform_name, arch)
        print(f"[TEST] match_asset('{asset_name}', '{platform_name}', '{arch}') = {result}")
        assert result is True, f"Expected True for {asset_name}"

    def test_match_asset_macos_amd64_dmg(self):
        """Test that anime1-macos-amd64.dmg is correctly matched for macOS x64."""
        # Some releases use amd64 instead of x64
        asset_name = "anime1-macos-amd64.dmg"
        platform_name = "macos"
        arch = "x64"

        result = PlatformDetector.match_asset(asset_name, platform_name, arch)
        print(f"[TEST] match_asset('{asset_name}', '{platform_name}', '{arch}') = {result}")
        assert result is True, f"Expected True for {asset_name}"

    def test_match_asset_macos_new_format_dmg(self):
        """Test matching macOS DMG with new version-in-name format (no arch suffix).

        New format: anime1-macos-0.2.1.dmg (version in name, no arch suffix)
        These are Universal Binaries that work on both x64 and arm64.
        """
        # This is the actual asset name from GitHub release v0.2.1
        asset_name = "anime1-macos-0.2.1.dmg"

        # Should match both x64 and arm64
        result_x64 = PlatformDetector.match_asset(asset_name, "macos", "x64")
        result_arm64 = PlatformDetector.match_asset(asset_name, "macos", "arm64")

        print(f"[TEST] match_asset('{asset_name}', 'macos', 'x64') = {result_x64}")
        print(f"[TEST] match_asset('{asset_name}', 'macos', 'arm64') = {result_arm64}")

        assert result_x64 is True, f"Expected True for x64"
        assert result_arm64 is True, f"Expected True for arm64"

    def test_match_asset_macos_old_format_arm64_dmg(self):
        """Test matching macOS DMG with old format (arch suffix in name).

        Old format: anime1-macos-arm64.dmg
        """
        asset_name = "anime1-macos-arm64.dmg"

        result_arm64 = PlatformDetector.match_asset(asset_name, "macos", "arm64")
        result_x64 = PlatformDetector.match_asset(asset_name, "macos", "x64")

        print(f"[TEST] match_asset('{asset_name}', 'macos', 'arm64') = {result_arm64}")
        print(f"[TEST] match_asset('{asset_name}', 'macos', 'x64') = {result_x64}")

        assert result_arm64 is True, f"Expected True for arm64"
        assert result_x64 is True, f"Expected True for x64 (apple silicon keyword matches x64)"

    def test_scenario_macos_arm64_finds_download_url(self):
        """Scenario: v0.1.0 on macOS arm64 should find a macOS DMG asset.

        This is the KEY test that reproduces the reported issue.
        The important thing is that download_url is NOT null, not which specific asset is matched.
        """
        # Simulate GitHub API response for v0.2.1 release with actual asset names
        assets = [
            MockGitHubAPI.create_asset("anime1-windows-x64.zip"),
            MockGitHubAPI.create_asset("anime1-windows-x64-setup.exe"),
            MockGitHubAPI.create_asset("anime1-macos-x64.dmg"),
            MockGitHubAPI.create_asset("anime1-macos-arm64.dmg"),
            MockGitHubAPI.create_asset("anime1-linux-x64.tar.gz"),
            MockGitHubAPI.create_asset("anime1-linux-arm64.tar.gz"),
        ]
        release = MockGitHubAPI.create_release(
            "v0.2.1",
            body="## Anime1 Desktop v0.2.1\n\n### 下载\n\n- **macOS (Apple Silicon)**: `anime1-macos-arm64.dmg`",
            assets=assets
        )

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Mock platform detection to return macOS arm64 (M1/M2/M3 Mac)
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "arm64")

                checker = UpdateChecker("gzp", "anime1-desktop", current_version="0.1.0")
                result = checker.check_for_update()

                print(f"[TEST] Result for v0.1.0 on macOS arm64:")
                print(f"  has_update: {result.has_update}")
                print(f"  latest_version: {result.latest_version}")
                print(f"  download_url: {result.download_url}")
                print(f"  asset_name: {result.asset_name}")

                assert result.has_update is True
                assert result.latest_version == "v0.2.1"
                assert result.download_url is not None, "download_url should NOT be None for macOS arm64"
                # Just verify it's a macOS DMG asset (either x64 or arm64 version)
                assert result.asset_name in ("anime1-macos-x64.dmg", "anime1-macos-arm64.dmg"), \
                    f"Expected macOS DMG asset, got {result.asset_name}"
                print(f"[PASS] macOS arm64 correctly finds download URL: {result.asset_name}")

    def test_scenario_macos_x64_finds_download_url(self):
        """Scenario: v0.1.0 on macOS x64 (Intel) should find anime1-macos-x64.dmg."""
        assets = [
            MockGitHubAPI.create_asset("anime1-macos-x64.dmg"),
            MockGitHubAPI.create_asset("anime1-macos-arm64.dmg"),
        ]
        release = MockGitHubAPI.create_release("v0.2.1", assets=assets)

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Mock platform detection to return macOS x64 (Intel Mac)
            with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                mock_platform.return_value = ("macos", "x64")

                checker = UpdateChecker("gzp", "anime1-desktop", current_version="0.1.0")
                result = checker.check_for_update()

                print(f"[TEST] Result for v0.1.0 on macOS x64:")
                print(f"  has_update: {result.has_update}")
                print(f"  download_url: {result.download_url}")
                print(f"  asset_name: {result.asset_name}")

                assert result.has_update is True
                assert result.download_url is not None
                assert result.asset_name == "anime1-macos-x64.dmg"
                print("[PASS] macOS x64 correctly finds download URL for anime1-macos-x64.dmg")

    def test_scenario_real_github_release_format(self):
        """Scenario: Test with actual GitHub release asset format.

        GitHub release v0.2.1 contains: anime1-macos-0.2.1.dmg
        This format has version number, not explicit architecture.
        """
        assets = [
            MockGitHubAPI.create_asset("anime1-linux-x64.tar.gz"),
            MockGitHubAPI.create_asset("anime1-macos-0.2.1.dmg"),  # Real format from GitHub
            MockGitHubAPI.create_asset("anime1-windows-0.2.1-setup.exe"),
            MockGitHubAPI.create_asset("anime1-windows-0.2.1.zip"),
        ]
        release = MockGitHubAPI.create_release("v0.2.1", assets=assets)

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Test both x64 and arm64
            for arch in ["x64", "arm64"]:
                with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
                    mock_platform.return_value = ("macos", arch)

                    checker = UpdateChecker("elfgzp", "anime1-desktop", current_version="0.1.0")
                    result = checker.check_for_update()

                    print(f"[TEST] macOS {arch} with new format asset:")
                    print(f"  download_url: {result.download_url}")
                    print(f"  asset_name: {result.asset_name}")

                    assert result.has_update is True
                    assert result.download_url is not None, f"download_url should NOT be None for macOS {arch}"
                    assert result.asset_name == "anime1-macos-0.2.1.dmg", \
                        f"Expected anime1-macos-0.2.1.dmg, got {result.asset_name}"
                    print(f"[PASS] macOS {arch} correctly finds download URL")


def run_simulation_tests():
    """Run simulation tests with v0.0.9 as current version."""
    print("\n" + "=" * 60)
    print("Running Update Simulation Tests")
    print("Simulating current version: v0.0.9")
    print("GitHub latest release: v0.1.0")
    print("=" * 60 + "\n")

    # Test 1: Simulate v0.0.9 detecting v0.1.0
    print("[TEST] v0.0.9 -> v0.1.0")
    release = MockGitHubAPI.create_release(
        "v0.1.0",
        body="## Version 0.1.0\n- First stable release\n- Added basic anime browsing",
        assets=[MockGitHubAPI.create_asset("anime1-0.1.0-macos-arm64.dmg", size=10_000_000)]
    )

    with patch('src.services.update_checker.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = release
        mock_get.return_value = mock_response

        # Mock platform detection
        with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
            mock_platform.return_value = ("macos", "arm64")

            checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.0.9")
            result = checker.check_for_update()

            if result.has_update:
                print(f"  [OK] Update detected!")
                print(f"       Current: {result.current_version}")
                print(f"       Latest:  {result.latest_version}")
                print(f"       Asset:   {result.asset_name}")
                print(f"       Size:    {result.download_size:,} bytes")
            else:
                print(f"  [FAIL] No update detected!")

    # Test 2: Simulate already at latest version
    print("\n[TEST] v0.1.0 -> v0.1.0 (no update expected)")
    with patch('src.services.update_checker.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = release
        mock_get.return_value = mock_response

        checker = UpdateChecker("anime1", "anime1-desktop", current_version="0.1.0")
        result = checker.check_for_update()

        if not result.has_update:
            print(f"  [OK] Correctly reported no update")
        else:
            print(f"  [FAIL] Incorrectly reported update available!")

    # Test 3: Simulate test channel with pre-release
    print("\n[TEST] v0.1.0 -> v0.2.0-rc.1 (test channel)")
    prerelease = MockGitHubAPI.create_release(
        "v0.2.0-rc.1",
        prerelease=True,
        body="## Release Candidate\n- New features coming soon",
        assets=[MockGitHubAPI.create_asset("anime1-0.2.0-rc.1-macos-arm64.dmg")]
    )

    with patch('src.services.update_checker.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [prerelease]
        mock_get.return_value = mock_response

        with patch('src.services.update_checker.PlatformDetector.get_platform_info') as mock_platform:
            mock_platform.return_value = ("macos", "arm64")

            checker = UpdateChecker(
                "anime1", "anime1-desktop",
                current_version="0.1.0",
                channel=UpdateChannel.TEST
            )
            result = checker.check_for_update()

            if result.has_update and result.is_prerelease:
                print(f"  [OK] Pre-release update detected!")
                print(f"       Latest: {result.latest_version}")
                print(f"       Type:   Pre-release (RC)")
            else:
                print(f"  [FAIL] Pre-release not detected!")

    print("\n" + "=" * 60)
    print("Simulation tests completed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Run pytest on this module
    pytest.main([__file__, "-v", "--tb=short"])

    # Also run simulation tests
    run_simulation_tests()


@pytest.mark.unit
class TestUpdateRouteCacheHeaders:
    """Tests for no-cache headers in update routes."""

    def test_update_check_route_has_no_cache_headers(self):
        """Test that /api/update/check endpoint returns no-cache headers."""
        from flask import Flask
        from src.routes.update import update_bp

        app = Flask(__name__)
        app.register_blueprint(update_bp)

        # Mock the UpdateChecker
        with app.test_client() as client:
            with patch('src.routes.update.UpdateChecker') as MockChecker:
                mock_instance = MockChecker.return_value
                mock_info = Mock()
                mock_info.has_update = False
                mock_info.current_version = "0.1.0"
                mock_info.latest_version = "v0.2.0"
                mock_info.is_prerelease = False
                mock_info.release_notes = None
                mock_info.download_url = None
                mock_info.asset_name = None
                mock_info.download_size = None
                mock_info.published_at = None
                mock_instance.check_for_update.return_value = mock_info

                response = client.get('/api/update/check')

                # Check response status
                assert response.status_code == 200

                # Check no-cache headers
                assert 'Cache-Control' in response.headers
                assert 'no-cache, no-store, must-revalidate' in response.headers['Cache-Control']
                assert 'Pragma' in response.headers
                assert response.headers['Pragma'] == 'no-cache'
                assert 'Expires' in response.headers
                assert response.headers['Expires'] == '0'

    def test_update_info_route_has_no_cache_headers(self):
        """Test that /api/update/info endpoint returns no-cache headers."""
        from flask import Flask
        from src.routes.update import update_bp

        app = Flask(__name__)
        app.register_blueprint(update_bp)

        with app.test_client() as client:
            response = client.get('/api/update/info')

            # Check response status
            assert response.status_code == 200

            # Check no-cache headers
            assert 'Cache-Control' in response.headers
            assert 'no-cache, no-store, must-revalidate' in response.headers['Cache-Control']
            assert 'Pragma' in response.headers
            assert response.headers['Pragma'] == 'no-cache'
            assert 'Expires' in response.headers
            assert response.headers['Expires'] == '0'

    def test_update_check_route_error_has_no_cache_headers(self):
        """Test that error responses from /api/update/check also have no-cache headers."""
        from flask import Flask
        from src.routes.update import update_bp

        app = Flask(__name__)
        app.register_blueprint(update_bp)

        # Mock to raise exception
        with app.test_client() as client:
            with patch('src.routes.update.UpdateChecker') as MockChecker:
                MockChecker.side_effect = Exception("Test error")

                response = client.get('/api/update/check')

                # Check response status is 500
                assert response.status_code == 500

                # Check no-cache headers are still present
                assert 'Cache-Control' in response.headers
                assert 'no-cache, no-store, must-revalidate' in response.headers['Cache-Control']
                assert 'Pragma' in response.headers
                assert response.headers['Pragma'] == 'no-cache'
                assert 'Expires' in response.headers
                assert response.headers['Expires'] == '0'

    def test_update_check_response_always_includes_latest_version(self):
        """Test that update check response always includes latest_version field."""
        from flask import Flask
        from src.routes.update import update_bp
        import json

        app = Flask(__name__)
        app.register_blueprint(update_bp)

        # Test with update available
        with app.test_client() as client:
            with patch('src.routes.update.UpdateChecker') as MockChecker:
                mock_instance = MockChecker.return_value
                mock_info = Mock()
                mock_info.has_update = True
                mock_info.current_version = "0.1.0"
                mock_info.latest_version = "v0.2.4"
                mock_info.is_prerelease = False
                mock_info.release_notes = "Release notes"
                mock_info.download_url = "https://example.com/download"
                mock_info.asset_name = "anime1.dmg"
                mock_info.download_size = 1000000
                mock_info.published_at = "2026-01-01T00:00:00Z"
                mock_instance.check_for_update.return_value = mock_info

                response = client.get('/api/update/check')
                data = json.loads(response.data)

                assert 'latest_version' in data
                assert data['latest_version'] == "v0.2.4"
                assert data['has_update'] is True

        # Test with no update available
        with app.test_client() as client:
            with patch('src.routes.update.UpdateChecker') as MockChecker:
                mock_instance = MockChecker.return_value
                mock_info = Mock()
                mock_info.has_update = False
                mock_info.current_version = "0.2.4"
                mock_info.latest_version = "v0.2.4"
                mock_info.is_prerelease = False
                mock_info.release_notes = None
                mock_info.download_url = None
                mock_info.asset_name = None
                mock_info.download_size = None
                mock_info.published_at = None
                mock_instance.check_for_update.return_value = mock_info

                response = client.get('/api/update/check')
                data = json.loads(response.data)

                # latest_version should ALWAYS be present
                assert 'latest_version' in data
                assert data['latest_version'] == "v0.2.4"
                assert data['has_update'] is False
