#!/usr/bin/env bash
# 获取构建版本号
# 优先使用环境变量，否则从git提取

set -e

# 如果环境变量已设置，直接使用
if [ -n "$ANIME1_VERSION" ]; then
    echo "$ANIME1_VERSION"
    exit 0
fi

# 尝试从git tag获取版本号
if TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    # 移除 'v' 前缀
    VERSION="${TAG#v}"
    VERSION="${VERSION#V}"
    echo "$VERSION"
    exit 0
fi

# 如果没有tag，使用commit id
if COMMIT_ID=$(git rev-parse --short HEAD 2>/dev/null); then
    echo "dev-${COMMIT_ID}"
    exit 0
fi

# 默认值
echo "dev"
exit 0
