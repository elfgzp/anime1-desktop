#!/usr/bin/env bash
# 提取版本号和 tag 名称

set -e

EVENT_NAME="$1"
INPUT_VERSION="$2"
GITHUB_REF="$3"

if [ "$EVENT_NAME" == "workflow_dispatch" ]; then
    TAG_NAME="v${INPUT_VERSION}"
    VERSION="${INPUT_VERSION}"
else
    TAG_NAME="${GITHUB_REF#refs/tags/}"
    VERSION="${TAG_NAME#v}"
fi

# 输出到标准输出，供 eval 使用
echo "tag_name='$TAG_NAME'"
echo "version='$VERSION'"
# 日志输出到 stderr
echo "Tag/Version: $TAG_NAME" >&2
