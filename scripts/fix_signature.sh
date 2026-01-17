#!/bin/bash
#
# Anime1 签名修复脚本
#
# 修复从 GitHub Actions 下载的 DMG 安装后无法运行的问题
#
# 使用方法:
#   chmod +x scripts/fix_signature.sh
#   ./scripts/fix_signature.sh
#
# 或手动执行:
#   bash scripts/fix_signature.sh
#

set -e

APP_PATH="/Applications/Anime1.app"

echo "================================"
echo "Anime1 签名修复脚本"
echo "================================"
echo ""

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "[ERROR] 应用不存在: $APP_PATH"
    echo ""
    echo "请先安装 Anime1:"
    echo "  1. 下载 DMG 文件"
    echo "  2. 双击挂载"
    echo "  3. 将 Anime1.app 拖拽到应用程序文件夹"
    echo ""
    exit 1
fi

echo "[1/4] 移除 quarantine 属性..."
echo "需要输入密码..."
sudo xattr -r -d com.apple.quarantine "$APP_PATH"
echo "  [OK] 完成"

echo ""
echo "[2/4] 移除 Python.framework 内部的签名..."
echo "需要输入密码..."
# 移除 Python.framework 内部的 _CodeSignature 目录
sudo rm -rf "$APP_PATH/Contents/Frameworks/Python.framework/Versions/3.11/_CodeSignature" 2>/dev/null || true
# 移除 Python 二进制文件的签名
sudo codesign --remove-signature "$APP_PATH/Contents/Frameworks/Python.framework/Versions/3.11/Python" 2>/dev/null || true
# 移除 Python 相关的其他签名
sudo rm -rf "$APP_PATH/Contents/Frameworks/Python.framework/Versions/3.11/libpython*" 2>/dev/null || true
echo "  [OK] 完成"

echo ""
echo "[3/4] 移除主应用的 CodeSignature 目录..."
echo "需要输入密码..."
# 移除主应用的 CodeSignature
sudo rm -rf "$APP_PATH/Contents/CodeSignature" 2>/dev/null || true
sudo rm -rf "$APP_PATH/Contents/_CodeSignature" 2>/dev/null || true
echo "  [OK] 完成"

echo ""
echo "[4/4] 重新签名应用..."
echo "需要输入密码..."
sudo codesign --force --sign - --options runtime --timestamp "$APP_PATH"
echo "  [OK] 完成"

echo ""
echo "================================"
echo "修复完成!"
echo ""
echo "现在可以运行 Anime1 了:"
echo "  open /Applications/Anime1.app"
echo ""
echo "================================"
