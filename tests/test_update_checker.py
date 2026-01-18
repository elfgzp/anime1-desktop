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
        assert pre_num == 1

    def test_parse_version_with_beta(self):
        """Test parsing pre-release version beta"""
        nums, pre_type, pre_num = VersionComparator.parse_version("2.1.0-beta.2")
        assert nums == [2, 1, 0]
        assert pre_type == "beta"
        assert pre_num == 2

    def test_parse_version_with_alpha(self):
        """Test parsing pre-release version alpha"""
        nums, pre_type, pre_num = VersionComparator.parse_version("1.0.0-alpha.3")
        assert nums == [1, 0, 0]
        assert pre_type == "alpha"
        assert pre_num == 3

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
        """Test parsing dev version (commit id based)"""
        # Dev versions are parsed as [0, 0, 0] with "dev" pre-release type
        # This ensures dev versions are always considered older than release versions
        nums, pre_type, pre_num = VersionComparator.parse_version("devabc123")
        assert nums == [0, 0, 0]
        assert pre_type == "dev"
        assert pre_num == 0

    def test_parse_version_dev_prefix(self):
        """Test parsing version with 'dev' prefix"""
        nums, pre_type, pre_num = VersionComparator.parse_version("dev")
        assert nums == [0, 0, 0]
        assert pre_type == "dev"

    def test_compare_versions_dev_vs_release(self):
        """Test comparing dev version with release version.

        This is the critical test case: when packaged from a release tag,
        the version should be the release version (e.g., 0.2.0), NOT 'dev'.

        If version is 'dev', it will always be considered older than any release.
        """
        # Dev version should be older than any release version
        assert VersionComparator.compare_versions("dev", "0.2.0") == -1
        assert VersionComparator.compare_versions("devabc123", "0.2.0") == -1
        # Release version should be newer than dev
        assert VersionComparator.compare_versions("0.2.0", "dev") == 1
        # Same release version should be equal
        assert VersionComparator.compare_versions("0.2.0", "0.2.0") == 0

    def test_compare_versions_dev_vs_dev(self):
        """Test comparing two dev versions"""
        # All dev versions should be considered equal
        assert VersionComparator.compare_versions("dev", "dev") == 0
        assert VersionComparator.compare_versions("devabc123", "devabc456") == 0
        assert VersionComparator.compare_versions("dev", "devabc123") == 0


@pytest.mark.unit
class TestPlatformDetector:
    """Tests for PlatformDetector class."""

    def test_match_asset_windows(self):
        """Test matching Windows asset."""
        # Asset name must contain platform keyword (windows/win)
        assert PlatformDetector.match_asset("anime1-1.0.0-windows.exe", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-win64.exe", "windows", "x64") is True
        assert PlatformDetector.match_asset("anime1-1.0.0-linux.deb", "windows", "x64") is False

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
        """Scenario: Current version is 'dev', should detect update.

        This is the EXPECTED behavior - when running from 'dev' version,
        it SHOULD detect the latest release as an update.
        """
        release = MockGitHubAPI.create_release("v0.2.0")

        with patch('src.services.update_checker.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = release
            mock_get.return_value = mock_response

            # Current version is 'dev' (e.g., running from source without tag)
            checker = UpdateChecker("anime1", "anime1-desktop", current_version="dev")
            result = checker.check_for_update()

            # SHOULD detect update when running from dev version
            assert result.has_update is True
            assert result.current_version == "dev"
            assert result.latest_version == "v0.2.0"
            print("[PASS] 'dev' correctly detects v0.2.0 as update")

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
