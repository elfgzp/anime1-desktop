#!/usr/bin/env bash
# 提取 CHANGELOG 内容

set -e

VERSION="$1"
REPO="$2"

if [ -z "$VERSION" ] || [ "$VERSION" == "test" ]; then
    CHANGELOG="测试构建 - 查看 [CHANGELOG.md](https://github.com/$REPO/blob/main/CHANGELOG.md) 了解详细变更。"
else
    CHANGELOG=$(python scripts/extract_changelog.py "$VERSION")
    if [ -z "$CHANGELOG" ]; then
        CHANGELOG="查看 [CHANGELOG.md](https://github.com/$REPO/blob/main/CHANGELOG.md) 了解详细变更。"
    fi
fi

{
    echo "changelog<<EOF"
    echo "$CHANGELOG"
    echo "EOF"
}
