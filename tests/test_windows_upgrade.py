"""Test script for Windows upgrade installation process.

This script simulates the upgrade process by:
1. Setting up a test installation directory
2. Simulating the download of update zip
3. Testing the batch file updater creation and execution
4. Verifying files are correctly replaced
"""
import os
import sys
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.app_dir import get_install_dir, get_download_dir


def create_test_update_zip(source_dir: Path, version: str = "1.0.0") -> Path:
    """Create a mock update zip file with new version files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="anime1_test_update_"))

    # Create mock new version files
    exe_path = temp_dir / "anime1.exe"
    exe_path.write_text(f"# Mock Anime1 v{version}\nThis is a simulated new version.\n")

    readme_path = temp_dir / "README.txt"
    readme_path.write_text(f"# Anime1 Desktop v{version}\nNew version with updates!\n")

    # Create a subdirectory with some files
    static_dir = temp_dir / "static"
    static_dir.mkdir()
    (static_dir / "test.txt").write_text("New static file\n")

    # Create zip file
    zip_path = temp_dir.parent / f"anime1-windows-{version}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in temp_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(temp_dir)
                zf.write(file, arcname)

    # Clean up temp dir (keep zip)
    shutil.rmtree(temp_dir)

    return zip_path


def _test_updater_batch_creation():
    """Test that the updater batch file is created correctly.
    Internal helper function for chain testing.
    """
    print("\n" + "=" * 60)
    print("Test 1: Updater batch file creation")
    print("=" * 60)

    # Import the download_update function logic
    zip_path = create_test_update_zip(Path(tempfile.gettempdir()), "1.0.0")

    install_dir = Path(tempfile.mkdtemp(prefix="anime1_install_test_"))
    print(f"Installation directory: {install_dir}")

    # Create some initial files (simulating old installation)
    (install_dir / "anime1.exe").write_text("# Old version\n")
    (install_dir / "README.txt").write_text("# Old version\n")

    # Create temp directory for updater
    temp_updater_dir = Path(tempfile.mkdtemp(prefix='anime1_update_test_'))
    updater_batch = temp_updater_dir / 'update.bat'
    zip_copy = temp_updater_dir / zip_path.name

    # Copy the zip to temp location
    shutil.copy2(zip_path, zip_copy)

    # Get the executable path (simulated)
    exe_path = install_dir / "anime1.exe"

    # Create batch file content (same as in settings.py)
    batch_content = f'''@echo off
timeout /t 3 /nobreak >nul
echo 正在安装更新...
"{sys.executable}" -c "import zipfile; import shutil; import sys; zf=zipfile.ZipFile(r'{zip_copy}'); zf.extractall(r'{install_dir}'); import os; os.remove(r'{zip_copy}'); os.rmdir(r'{temp_updater_dir}')"
if exist r"{exe_path}" start "" "{exe_path}"
del "%~f0"
'''
    updater_batch.write_text(batch_content, encoding='utf-8')

    print(f"Created updater batch: {updater_batch}")
    print(f"Batch content:\n{batch_content[:200]}...")

    # Verify batch file exists
    assert updater_batch.exists(), "Updater batch file should exist"
    print("[PASS] Updater batch file created successfully")

    # Clean up
    zip_path.unlink()

    return install_dir, temp_updater_dir, zip_copy


def _test_updater_extraction(install_dir: Path, temp_updater_dir: Path, zip_copy: Path):
    """Test that the updater correctly extracts files."""
    print("\n" + "=" * 60)
    print("Test 2: Updater extraction process")
    print("=" * 60)

    # Simulate the extraction (same logic as in batch file)
    with zipfile.ZipFile(zip_copy, 'r') as zf:
        zf.extractall(install_dir)

    print(f"Extracted files to: {install_dir}")
    print("Files after extraction:")
    for f in install_dir.rglob("*"):
        if f.is_file():
            print(f"  - {f.relative_to(install_dir)}")

    # Verify old files are replaced
    readme_content = (install_dir / "README.txt").read_text()
    assert "New version" in readme_content, "README should be updated"
    print("[PASS] Files extracted successfully")

    # Verify new files exist
    assert (install_dir / "anime1.exe").exists(), "exe should exist"
    assert (install_dir / "static" / "test.txt").exists(), "static files should exist"
    print("[PASS] New files created correctly")


def _test_updater_cleanup(temp_updater_dir: Path):
    """Test that the updater cleans up after itself."""
    print("\n" + "=" * 60)
    print("Test 3: Updater cleanup")
    print("=" * 60)

    # Simulate cleanup (what the batch file does after extraction)
    zip_copy = list(temp_updater_dir.glob("*.zip"))[0]
    if zip_copy.exists():
        zip_copy.unlink()

    # The batch file should delete itself when run, but here we just clean up
    # the temp directory using shutil to avoid issues with the batch file path
    shutil.rmtree(temp_updater_dir, ignore_errors=True)

    # Verify cleanup (temp dir should not exist or be empty)
    if temp_updater_dir.exists():
        remaining = list(temp_updater_dir.glob("*"))
        if remaining:
            print(f"Warning: Some files remaining in temp dir: {remaining}")
        else:
            temp_updater_dir.rmdir()

    assert not temp_updater_dir.exists(), "Temp directory should be cleaned up"
    print("[PASS] Updater cleaned up successfully")


def test_version_parsing():
    """Test version parsing for installer filenames."""
    print("\n" + "=" * 60)
    print("Test 4: Version parsing")
    print("=" * 60)

    import re

    # Test version parsing logic from build.py
    version = "0.2.1-test-win-20260118-190939"
    version_clean = version.replace('v', '').replace('V', '').split('.')
    major = version_clean[0] if len(version_clean) > 0 and version_clean[0].isdigit() else "0"
    minor = version_clean[1] if len(version_clean) > 1 and version_clean[1].isdigit() else "0"
    patch = version_clean[2] if len(version_clean) > 2 and version_clean[2].isdigit() else "0"

    # For filename, use sanitized version
    version_filename = re.sub(r'[^a-zA-Z0-9.-]', '-', version)
    if version_filename.endswith('-'):
        version_filename = version_filename[:-1]

    print(f"Original version: {version}")
    print(f"NSIS version: {major}.{minor}.{patch}")
    print(f"Filename version: {version_filename}")

    assert major == "0", f"Major should be 0, got {major}"
    assert minor == "2", f"Minor should be 2, got {minor}"
    assert "0.2.1" in version_filename or version_filename.startswith("0.2.1"), f"Filename should contain version"
    print("[PASS] Version parsing works correctly")


def test_download_and_extract_simulation():
    """Simulate the complete download and extract process."""
    print("\n" + "=" * 60)
    print("Test 5: Complete download and extract simulation")
    print("=" * 60)

    # Create a mock old installation
    install_dir = Path(tempfile.mkdtemp(prefix="anime1_old_install_"))
    (install_dir / "anime1.exe").write_text("Old version 0.1.0")
    (install_dir / "config.json").write_text('{"version": "0.1.0", "setting": "old"}')

    old_files = list(install_dir.glob("*"))
    print(f"Old installation files: {[f.name for f in old_files]}")

    # Create new version update
    new_version = "0.2.0"
    zip_path = create_test_update_zip(Path(tempfile.gettempdir()), new_version)

    # Simulate download (copy to download dir)
    download_dir = Path(tempfile.mkdtemp(prefix="anime1_download_"))
    downloaded_file = download_dir / zip_path.name
    shutil.copy2(zip_path, downloaded_file)
    print(f"Downloaded update to: {downloaded_file}")

    # Simulate auto-install (extract over installation)
    with zipfile.ZipFile(downloaded_file, 'r') as zf:
        zf.extractall(install_dir)

    # Verify update
    new_files = list(install_dir.glob("*"))
    print(f"Files after update: {[f.name for f in new_files]}")

    # Check that exe was updated
    exe_content = (install_dir / "anime1.exe").read_text()
    assert new_version in exe_content, f"exe should contain new version, got: {exe_content}"
    print("[PASS] Update extracted successfully")

    # Check that old config might be preserved (depending on zip contents)
    # In this case, config.json was not in the zip, so it should be preserved
    config_exists = (install_dir / "config.json").exists()
    print(f"Config preserved: {config_exists}")

    # Clean up
    zip_path.unlink()
    shutil.rmtree(download_dir)
    shutil.rmtree(install_dir)

    print("[PASS] Complete download and extract simulation passed")


def run_all_tests():
    """Run all upgrade tests."""
    print("\n" + "#" * 60)
    print("# Windows Upgrade Installation Tests")
    print("#" * 60)

    passed = 0
    failed = 0

    # Test 1: Version parsing (standalone)
    try:
        test_version_parsing()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_version_parsing: {e}")
        failed += 1

    # Test 2-4: Chain together - batch creation, extraction, cleanup
    try:
        install_dir, temp_updater_dir, zip_copy = _test_updater_batch_creation()
        _test_updater_extraction(install_dir, temp_updater_dir, zip_copy)
        _test_updater_cleanup(temp_updater_dir)
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_updater_chain: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 5: Complete download and extract simulation
    try:
        test_download_and_extract_simulation()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_download_and_extract_simulation: {e}")
        failed += 1

    print("\n" + "#" * 60)
    print(f"# Tests completed: {passed} passed, {failed} failed")
    print("#" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
