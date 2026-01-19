#!/usr/bin/env bash
# 提取 CHANGELOG 内容（用于 Release 页面，简化格式）

set -e

VERSION="$1"
REPO="$2"

if [ -z "$VERSION" ] || [ "$VERSION" == "test" ]; then
    CHANGELOG="测试构建 - 查看 [CHANGELOG.md](https://github.com/$REPO/blob/main/CHANGELOG.md) 了解详细变更。"
else
    # 使用 --compact 标志，生成不带版本标题的简化格式
    CHANGELOG=$(python scripts/extract_changelog.py "$VERSION" --compact)
    if [ -z "$CHANGELOG" ]; then
        CHANGELOG="查看 [CHANGELOG.md](https://github.com/$REPO/blob/main/CHANGELOG.md) 了解详细变更。"
    fi
fi

{
    echo "changelog<<EOF"
    echo "$CHANGELOG"
    echo "EOF"
}
