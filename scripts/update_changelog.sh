#!/usr/bin/env bash
# Update CHANGELOG.md with release date for a version
# Usage: ./update_changelog.sh <version>

set -e

VERSION="$1"
current_date=$(date -u +%Y-%m-%d)

if [ -z "$VERSION" ]; then
    echo "[ERROR] Version not provided" >&2
    exit 1
fi

echo "[RELEASE] Processing version $VERSION for date $current_date" >&2

# Check if version entry exists, if not create it
if grep -q "## \[$VERSION\]" CHANGELOG.md; then
    echo "[RELEASE] Updating existing version entry for $VERSION" >&2
    sed -i "" "s/## \[$VERSION\] - .*/## [$VERSION] - $current_date/" CHANGELOG.md
else
    echo "[RELEASE] Creating new version entry for $VERSION" >&2
    # Create new entry content
    new_entry="## [$VERSION] - $current_date

### Added

### Changed

### Fixed

### Security
"
    # Add new version entry after Unreleased section using awk (more portable)
    awk -v version="$VERSION" -v date="$current_date" -v entry="$new_entry" '
        /^## \[Unreleased\]/ {
            print
            printf "%s\n", entry
            next
        }
        { print }
    ' CHANGELOG.md > CHANGELOG.tmp && mv CHANGELOG.tmp CHANGELOG.md
fi

echo "[RELEASE] CHANGELOG updated successfully" >&2
