"""Tests for settings API routes."""
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestLogFolderPath:
    """Test that log folder is in correct platform-specific location."""

    def test_get_app_data_dir_windows(self):
        """Test Windows app data directory."""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
                from src.utils.app_dir import get_app_data_dir
                result = get_app_data_dir()
                assert str(result) == "C:\\Users\\Test\\AppData\\Roaming\\Anime1"

    def test_get_app_data_dir_linux(self):
        """Test Linux app data directory."""
        with patch('platform.system', return_value='Linux'):
            with patch.dict(os.environ, {'HOME': '/home/test', 'XDG_DATA_HOME': ''}):
                from src.utils.app_dir import get_app_data_dir
                result = get_app_data_dir()
                assert "/home/test/.local/share/Anime1" in str(result) or ".local/share/Anime1" in str(result)

    def test_log_dir_is_in_app_data(self):
        """Test that log directory is inside app data directory."""
        from src.utils.app_dir import get_app_data_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.utils.app_dir.get_app_data_dir', return_value=Path(tmpdir) / "Anime1"):
                from src.utils.app_dir import ensure_app_data_dir
                app_dir = ensure_app_data_dir()

                log_dir = app_dir / "logs"
                log_file = log_dir / "app.log"

                # Create the directory
                log_dir.mkdir(parents=True, exist_ok=True)

                # Write a test log
                log_file.write_text("2024-01-15 10:30:45,123 [INFO] test: Test message", encoding="utf-8")

                # Verify it exists
                assert log_dir.exists()
                assert log_file.exists()

                # Read it back
                content = log_file.read_text(encoding="utf-8")
                assert "Test message" in content


class TestLogOpen:
    """Test opening log folder functionality."""

    def test_open_logs_folder_creates_directory(self):
        """Test that open logs folder creates directory if not exists."""
        from src.routes.settings import open_logs_folder

        with tempfile.TemporaryDirectory() as tmpdir:
            expected_log_dir = Path(tmpdir) / "Anime1" / "logs"

            with patch('src.routes.settings.get_app_data_dir', return_value=expected_log_dir):
                with patch('platform.system', return_value='Linux'):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        # Call the function
                        result = open_logs_folder()

                        # Verify directory was created
                        assert expected_log_dir.exists()

                        # Verify subprocess was called
                        mock_run.assert_called_once()

    def test_open_logs_folder_windows(self):
        """Test Windows log folder opening."""
        from src.routes.settings import open_logs_folder

        with tempfile.TemporaryDirectory() as tmpdir:
            expected_log_dir = Path(tmpdir) / "Anime1" / "logs"

            with patch('src.routes.settings.get_app_data_dir', return_value=expected_log_dir):
                with patch('platform.system', return_value='Windows'):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        result = open_logs_folder()

                        # Verify explorer.exe was called
                        call_args = mock_run.call_args
                        assert "explorer.exe" in call_args[0][0]

    def test_open_logs_folder_macos(self):
        """Test macOS log folder opening."""
        from src.routes.settings import open_logs_folder

        with tempfile.TemporaryDirectory() as tmpdir:
            expected_log_dir = Path(tmpdir) / "Anime1" / "logs"

            with patch('src.routes.settings.get_app_data_dir', return_value=expected_log_dir):
                with patch('platform.system', return_value='Darwin'):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        result = open_logs_folder()

                        # Verify 'open' command was called
                        call_args = mock_run.call_args
                        assert "open" in call_args[0][0]


class TestLogFileReading:
    """Test reading log files."""

    def test_read_log_file_with_utf8_encoding(self):
        """Test reading log file with UTF-8 encoding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "app.log"

            # Write log with UTF-8 content (including Chinese)
            content = "2024-01-15 10:30:45,123 [INFO] src.test: 测试消息\n"
            content += "2024-01-15 10:30:46,123 [ERROR] src.test: Error 错误"
            log_file.write_text(content, encoding="utf-8")

            # Read it back
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2
            assert "测试消息" in lines[0]
            assert "错误" in lines[1]

    def test_parse_log_line_format(self):
        """Test parsing standard log format."""
        line = "2024-01-15 10:30:45,123 [INFO] src.test: Test message"

        if " [" in line and "] " in line:
            timestamp_part, rest = line.split(" [", 1)
            level_part, message = rest.split("] ", 1)

            assert timestamp_part == "2024-01-15 10:30:45,123"
            assert level_part == "INFO"
            assert message == "src.test: Test message"


class TestLogClear:
    """Test clearing log files."""

    def test_clear_log_file(self):
        """Test clearing log file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "app.log"

            # Write initial content
            log_file.write_text("Some old log content", encoding="utf-8")
            assert log_file.stat().st_size > 0

            # Clear the file
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")

            # Verify it's empty
            assert log_file.stat().st_size == 0
            assert log_file.read_text(encoding="utf-8") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
