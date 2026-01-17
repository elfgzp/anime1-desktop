#!/usr/bin/env bash
# 构建脚本
# 根据平台自动选择构建方式

set -e

PLATFORM="$1"

echo "Building for platform: $PLATFORM"

# 构建前端
echo "Building frontend..."
if command -v npm &> /dev/null; then
    cd frontend
    npm ci
    npm run build
    cd ..
    echo "Frontend build completed"
    
    # 注入构建后的资源路径到模板
    echo "Injecting Vite assets into template..."
    python3 scripts/inject-vite-assets.py || echo "Warning: Failed to inject assets (template may need manual update)"
else
    echo "Warning: npm not found, skipping frontend build"
    echo "Make sure to run 'npm install && npm run build' in frontend/ directory first"
fi

# 提取版本号并设置环境变量
VERSION=$(bash scripts/get_build_version.sh)
export ANIME1_VERSION="$VERSION"
echo "Build version: $VERSION"

# GitHub Actions runner.os 的值可能是 "Windows", "macOS", "Linux"
# 但为了兼容性，也检查其他可能的格式
case "$PLATFORM" in
    "Windows"|"windows-latest"|"windows")
        echo "Building Windows (onefile)..."
        python build.py --clean --onefile
        ;;
    "macOS"|"macos-latest"|"macos-12"|"macos")
        echo "Building macOS (onedir)..."
        python build.py --clean
        ;;
    "Linux"|"ubuntu-latest"|"linux")
        echo "Building Linux (onefile)..."
        python build.py --clean --onefile
        ;;
    *)
        echo "Unknown platform: $PLATFORM"
        echo "Available platforms: Windows, macOS, Linux"
        exit 1
        ;;
esac

echo "Build completed successfully"
