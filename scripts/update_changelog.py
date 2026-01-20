#!/usr/bin/env python3
"""Update CHANGELOG.md with release date for a version."""
import sys
from pathlib import Path

def update_changelog(version: str):
    """Add or update version entry in CHANGELOG.md."""
    current_date = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")
    changelog = Path("CHANGELOG.md")

    if not changelog.exists():
        print("[ERROR] CHANGELOG.md not found", file=sys.stderr)
        sys.exit(1)

    content = changelog.read_text(encoding="utf-8")
    version_header = f"## [{version}]"

    if version_header in content:
        print(f"[RELEASE] Updating existing version entry for {version}")
        # Update existing entry date
        import re
        pattern = rf"(## \[{re.escape(version)}\] - ).*"
        content = re.sub(pattern, rf"\g<1>{current_date}", content)
    else:
        print(f"[RELEASE] Creating new version entry for {version}")
        # Add new entry after Unreleased section
        new_entry = f"""

## [{version}] - {current_date}

### Added

### Changed

### Fixed

### Security
"""
        content = content.replace("## [Unreleased]", f"## [Unreleased]{new_entry}")

    changelog.write_text(content, encoding="utf-8")
    print("[RELEASE] CHANGELOG updated successfully")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_changelog.py <version>", file=sys.stderr)
        sys.exit(1)
    update_changelog(sys.argv[1])
