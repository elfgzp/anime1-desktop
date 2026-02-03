#!/bin/bash
# Docker entrypoint script

set -e

# 修复数据目录权限（处理 Docker 卷挂载时的 root 权限问题）
if [ -d "/app/data" ]; then
    # 如果目录不属于 anime1 用户，修复权限
    if [ "$(stat -c '%u' /app/data 2>/dev/null || echo '0')" != "1000" ]; then
        echo "Fixing /app/data permissions..."
        sudo chown -R anime1:anime1 /app/data 2>/dev/null || true
    fi
fi

# 确保 downloads 目录存在且有正确权限
mkdir -p /app/data/downloads
if [ "$(stat -c '%u' /app/data/downloads 2>/dev/null || echo '0')" != "1000" ]; then
    sudo chown -R anime1:anime1 /app/data/downloads 2>/dev/null || true
fi

# Docker 环境：设置默认下载路径为持久化目录
if [ -z "$ANIME1_DOWNLOAD_PATH" ]; then
    export ANIME1_DOWNLOAD_PATH="/app/data/downloads"
    echo "Using default download path: $ANIME1_DOWNLOAD_PATH"
fi

# 执行传入的命令
exec "$@"
