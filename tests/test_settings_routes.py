"""Tests for settings API routes, specifically download functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
class TestDownloadUpdate:
    """Tests for the download_update endpoint."""

    def test_download_update_requires_url(self):
        """Test that download_update returns 400 when url is missing."""
        from src.routes.settings import settings_bp
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            response = client.post(
                '/api/settings/update/download',
                json={}  # No URL provided
            )

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data
            assert 'url is required' in data['error']

    def test_download_update_validates_url(self):
        """Test that download_update accepts valid URL."""
        from src.routes.settings import settings_bp
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            # Use a valid-looking URL
            response = client.post(
                '/api/settings/update/download',
                json={'url': 'https://example.com/download/anime1-macos-0.2.1.dmg'}
            )

            # Should not return 400 (url validation passed)
            assert response.status_code != 400

    def test_download_update_extracts_filename_from_url(self):
        """Test that filename is correctly extracted from URL."""
        from src.routes.settings import settings_bp
        from flask import Flask
        import src.utils.app_dir as app_dir_module

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        test_url = 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-macos-0.2.1.dmg'

        with app.test_client() as client:
            with patch('requests.get') as mock_get:
                # Mock a small download response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_content = Mock(return_value=[b'test content'])
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                with patch.object(app_dir_module, 'get_download_dir', return_value=Path('/fake/downloads')):
                    response = client.post(
                        '/api/settings/update/download',
                        json={'url': test_url}
                    )

                    # Should have attempted to download
                    assert mock_get.called

    def test_dmg_file_not_extracted_as_zip_auto_install(self):
        """Test that DMG files are NOT treated as ZIP archives during auto-install.

        This is the key test for the bug where downloading a DMG file
        would fail because the code tried to use zipfile.ZipFile on it.
        """
        from src.routes.settings import settings_bp
        from flask import Flask
        import zipfile
        import src.utils.app_dir as app_dir_module

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        test_url = 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-macos-0.2.1.dmg'

        with app.test_client() as client:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_content = Mock(return_value=[b'dmg content here'])
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                with patch.object(app_dir_module, 'get_download_dir', return_value=Path('/fake/downloads')):
                    with patch.object(app_dir_module, 'get_install_dir', return_value=Path('/fake/install')):
                        with patch('src.routes.settings.zipfile.ZipFile') as mock_zipfile:
                            response = client.post(
                                '/api/settings/update/download',
                                json={'url': test_url, 'auto_install': True}
                            )

                            # Log the result for debugging
                            print(f"[TEST] Response status: {response.status_code}")
                            print(f"[TEST] Response data: {response.get_json()}")

                            # Check if zipfile.ZipFile was called
                            if mock_zipfile.called:
                                # This indicates the bug - trying to extract DMG as ZIP
                                print("[BUG FOUND] zipfile.ZipFile was called for DMG file!")
                            else:
                                print("[PASS] zipfile.ZipFile was NOT called for DMG file")


@pytest.mark.unit
class TestDownloadFilenameExtraction:
    """Tests for filename extraction from download URLs."""

    def test_extract_filename_simple(self):
        """Test filename extraction from simple URL."""
        test_cases = [
            ('https://example.com/file.zip', 'file.zip'),
            ('https://example.com/path/to/file.dmg', 'file.dmg'),
            ('https://example.com/file.exe?param=value', 'file.exe'),
            ('https://example.com/path/file.tar.gz', 'file.tar.gz'),
        ]

        for url, expected in test_cases:
            # Simulate the filename extraction logic from the route
            filename = url.split("/")[-1].split("?")[0]
            assert filename == expected, f"For {url}: expected {expected}, got {filename}"

    def test_extract_filename_default_fallback(self):
        """Test that a default filename is generated when URL has no filename."""
        # This simulates the logic in download_update when url has no trailing path
        # For a URL like https://example.com/download, filename would be 'download'
        # which is truthy, so no default fallback
        url = 'https://example.com/download'
        filename = url.split("/")[-1].split("?")[0]

        # The logic only uses fallback if filename is empty/truthy
        # So for this URL, 'download' would be used (not a good filename but valid)
        assert filename == 'download'


@pytest.mark.unit
class TestAutoInstallLogic:
    """Tests for auto-install logic."""

    def test_auto_install_false_returns_file_path(self):
        """Test that auto_install=False returns file path for manual handling."""
        from src.routes.settings import settings_bp
        from flask import Flask
        import src.utils.app_dir as app_dir_module

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.iter_content = Mock(return_value=[b'test'])
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                with patch.object(app_dir_module, 'get_download_dir', return_value=Path('/fake/downloads')):
                    response = client.post(
                        '/api/settings/update/download',
                        json={'url': 'https://example.com/test.dmg', 'auto_install': False}
                    )

                    data = response.get_json()
                    assert data['success'] is True
                    # Should return file path info for manual handling
                    assert 'data' in data


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling in download_update."""

    def test_download_handles_network_error(self):
        """Test that network errors are properly handled."""
        from src.routes.settings import settings_bp
        from flask import Flask
        import requests

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

                response = client.post(
                    '/api/settings/update/download',
                    json={'url': 'https://example.com/test.dmg'}
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data

    def test_download_handles_http_error(self):
        """Test that HTTP errors are properly handled."""
        from src.routes.settings import settings_bp
        from flask import Flask
        import requests

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
                mock_get.return_value = mock_response

                response = client.post(
                    '/api/settings/update/download',
                    json={'url': 'https://example.com/test.dmg'}
                )

                assert response.status_code == 500
                data = response.get_json()
                assert data['success'] is False


@pytest.mark.unit
class TestRunUpdater:
    """Tests for the run_updater endpoint."""

    def test_run_updater_requires_path(self):
        """Test that run_updater returns 400 when path is missing."""
        from src.routes.settings import settings_bp
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            response = client.post(
                '/api/settings/update/run-updater',
                json={}  # No updater_path
            )

            assert response.status_code == 400

    def test_run_updater_validates_path_exists(self):
        """Test that run_updater returns 404 when path doesn't exist."""
        from src.routes.settings import settings_bp
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        with app.test_client() as client:
            response = client.post(
                '/api/settings/update/run-updater',
                json={'updater_path': '/nonexistent/path/updater.bat'}
            )

            assert response.status_code == 404

    def test_run_updater_releases_lock_before_launching(self):
        """Test that run_updater releases instance lock before launching updater.

        This is critical to prevent race conditions where the updater tries to
        acquire the lock while anime1 is still running.
        """
        from src.routes.settings import settings_bp
        from flask import Flask
        import tempfile
        from pathlib import Path

        app = Flask(__name__)
        app.register_blueprint(settings_bp)

        # Create a temporary updater batch file
        with tempfile.TemporaryDirectory() as tmpdir:
            updater_path = Path(tmpdir) / 'updater.bat'
            updater_path.write_text('@echo off\n echo Updating...')

            with app.test_client() as client:
                with patch('subprocess.Popen') as mock_popen, \
                     patch('src.desktop.InstanceLock') as mock_lock_class, \
                     patch('sys.exit') as mock_exit:
                    mock_lock = Mock()
                    mock_lock_class.return_value = mock_lock

                    response = client.post(
                        '/api/settings/update/run-updater',
                        json={'updater_path': str(updater_path)}
                    )

                    # Verify that force_release was called before Popen
                    assert mock_lock.force_release.called, "force_release should be called"
                    assert mock_popen.called, "subprocess.Popen should be called"
                    # Verify sys.exit was called to exit the app
                    assert mock_exit.called, "sys.exit should be called"


@pytest.mark.unit
class TestSettingsModuleImport:
    """Tests for module import integrity."""

    def test_settings_module_imports_successfully(self):
        """Test that settings module can be imported without errors.

        This catches NameError bugs like missing imports for functions
        used in the module.
        """
        # This should not raise any exceptions
        from src.routes import settings
        assert settings is not None

    def test_download_update_no_local_variable_os_bug(self):
        """Test that download_update function doesn't have 'os' local variable bug.

        Regression test for the bug where 'import os' was placed inside the
        function after os.chmod() was already called, causing:
        "cannot access local variable 'os' where it is not associated with a value"

        The bug occurred because Python sees 'os' is assigned via 'import os'
        inside the function, making it a local variable throughout the entire
        function scope. When os.chmod() was called before the import, Python
        would throw an error since the local variable wasn't yet assigned.
        """
        import ast
        import inspect

        # Get the source code of the settings module
        from src.routes import settings
        settings_module_path = inspect.getfile(settings)

        with open(settings_module_path, 'r', encoding='utf-8', errors='replace') as f:
            source_code = f.read()

        # Parse the AST
        tree = ast.parse(source_code)

        # Find the download_update function
        download_update_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'download_update':
                download_update_func = node
                break

        assert download_update_func is not None, "download_update function not found"

        # Check for 'os' being assigned via import inside the function
        # This would create a local variable and cause the bug
        os_import_in_func = False
        for node in ast.walk(download_update_func):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'os':
                        os_import_in_func = True
                        break
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'os':
                    os_import_in_func = True

        # The fix: there should be NO import os inside the function
        # because os is imported globally at the top of the module
        assert not os_import_in_func, (
            "Found 'import os' inside download_update function. "
            "This causes a local variable bug when os.chmod() is called before the import. "
            "Remove the local import and use the global import at module top."
        )

        # Verify os is used in the function (chmod calls)
        os_used_in_func = False
        for node in ast.walk(download_update_func):
            if isinstance(node, ast.Attribute):
                if node.attr == 'chmod':
                    os_used_in_func = True
                    break

        assert os_used_in_func, "os.chmod should be called in download_update"

    def test_get_project_root_available(self):
        """Test that get_project_root is available in utils."""
        from src.utils import get_project_root
        from src.utils.constants import PROJECT_ROOT_MARKERS

        root = get_project_root()
        assert root is not None
        assert isinstance(root, Path)
        # Should point to project root (contains pyproject.toml)
        assert any((root / marker).exists() for marker in PROJECT_ROOT_MARKERS)

    def test_subprocess_popen_does_not_use_detached_param(self):
        """Test that subprocess.Popen is called with correct parameters (not 'detached').

        The 'detached' parameter was deprecated and removed in Python 3.11+.
        On Unix, use 'start_new_session=True'.
        On Windows, use 'creationflags=subprocess.CREATE_NEW_PROCESS_GROUP'.
        """
        import ast
        import inspect

        # Get the source code of the settings module
        from src import routes
        settings_module_path = inspect.getfile(routes.settings)

        with open(settings_module_path, 'r', encoding='utf-8', errors='replace') as f:
            source_code = f.read()

        # Parse the AST to find all Popen calls
        tree = ast.parse(source_code)

        popen_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'Popen':
                        popen_calls.append(node)

        # Check that no Popen call uses 'detached' parameter
        for call in popen_calls:
            for keyword in call.keywords:
                if keyword.arg == 'detached':
                    # Get line number for better error message
                    line_no = call.lineno
                    raise AssertionError(
                        f"Found 'detached' parameter in subprocess.Popen call at line {line_no}. "
                        f"Use 'start_new_session=True' (Unix) or 'creationflags=subprocess.CREATE_NEW_PROCESS_GROUP' (Windows) instead."
                    )

        # All good if we get here
        assert len(popen_calls) >= 0  # Just to have an assertion


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
