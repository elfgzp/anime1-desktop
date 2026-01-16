#!/usr/bin/env bash
# 构建脚本
# 根据平台自动选择构建方式

set -e

PLATFORM="$1"

echo "Building for platform: $PLATFORM"

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
