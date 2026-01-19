"""Tests for build.py module."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import from the scripts directory
import sys
scripts_path = Path(__file__).parent.parent / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))


class TestDistInfoPlist:
    """Tests for distInfo.plist creation and updates."""

    def test_create_dist_info_plist_template(self):
        """Test that distInfo.plist is created from template when not exists."""
        from build import create_dist_info_plist_template, get_project_root

        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_project_root to return our temp directory
            with patch('build.get_project_root', return_value=Path(tmpdir)):
                # Create a mock template file
                template_dir = Path(tmpdir) / "scripts" / "resources"
                template_dir.mkdir(parents=True, exist_ok=True)
                template_file = template_dir / "distInfo.plist.template"
                template_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleShortVersionString</key>
    <string>__VERSION__</string>
    <key>CFBundleVersion</key>
    <string>0</string>
</dict>
</plist>
''', encoding='utf-8')

                plist_path = Path(tmpdir) / "distInfo.plist"

                # Should not exist yet
                assert not plist_path.exists()

                # Create template
                create_dist_info_plist_template()

                # Now should exist
                assert plist_path.exists()

                # Content should match template
                content = plist_path.read_text(encoding='utf-8')
                assert '__VERSION__' in content

    def test_create_dist_info_plist_template_already_exists(self):
        """Test that existing distInfo.plist is not overwritten."""
        from build import create_dist_info_plist_template

        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "distInfo.plist"
            original_content = '<?xml version="1.0" encoding="UTF-8"?>'
            plist_path.write_text(original_content, encoding='utf-8')

            with patch('build.get_project_root', return_value=Path(tmpdir)):
                create_dist_info_plist_template()

                # Content should be unchanged
                assert plist_path.read_text(encoding='utf-8') == original_content

    def test_update_dist_info_plist_version(self):
        """Test that version is correctly updated in distInfo.plist."""
        from build import update_dist_info_plist

        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "distInfo.plist"
            plist_path.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleShortVersionString</key>
    <string>0.0.0</string>
    <key>CFBundleVersion</key>
    <string>0</string>
</dict>
</plist>
''', encoding='utf-8')

            with patch('build.get_project_root', return_value=Path(tmpdir)):
                update_dist_info_plist("1.2.3")

                content = plist_path.read_text(encoding='utf-8')
                # CFBundleShortVersionString should be updated to 1.2.3
                assert '<string>1.2.3</string>' in content
                # CFBundleVersion should be 10203 (1*10000 + 2*100 + 3)
                assert '<string>10203</string>' in content

    def test_update_dist_info_plist_with_dev_version(self):
        """Test that dev version suffix is stripped when updating plist."""
        from build import update_dist_info_plist

        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "distInfo.plist"
            plist_path.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleShortVersionString</key>
    <string>0.0.0</string>
    <key>CFBundleVersion</key>
    <string>0</string>
</dict>
</plist>
''', encoding='utf-8')

            with patch('build.get_project_root', return_value=Path(tmpdir)):
                # Dev version should have suffix stripped
                update_dist_info_plist("1.2.3-abc123")

                content = plist_path.read_text(encoding='utf-8')
                # Should be 1.2.3, not 1.2.3-abc123
                assert '<string>1.2.3</string>' in content
                # Version should not contain the commit hash
                assert 'abc123' not in content

    def test_update_dist_info_plist_creates_if_missing(self):
        """Test that distInfo.plist is created if template exists."""
        from build import update_dist_info_plist

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the template directory structure
            template_dir = Path(tmpdir) / "scripts" / "resources"
            template_dir.mkdir(parents=True, exist_ok=True)
            template_file = template_dir / "distInfo.plist.template"
            template_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleShortVersionString</key>
    <string>__VERSION__</string>
    <key>CFBundleVersion</key>
    <string>0</string>
</dict>
</plist>
''', encoding='utf-8')

            plist_path = Path(tmpdir) / "distInfo.plist"
            assert not plist_path.exists()

            with patch('build.get_project_root', return_value=Path(tmpdir)):
                update_dist_info_plist("2.0.0")

                # Should be created
                assert plist_path.exists()
                content = plist_path.read_text(encoding='utf-8')
                assert '<string>2.0.0</string>' in content


class TestVersionParsing:
    """Tests for version parsing utilities."""

    def test_normalize_version(self):
        """Test version normalization."""
        from build import normalize_version

        assert normalize_version("1.2.3") == "1.2.3"
        assert normalize_version("v1.2.3") == "1.2.3"
        assert normalize_version("V1.2.3") == "1.2.3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
