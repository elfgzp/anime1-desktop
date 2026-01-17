#!/usr/bin/env bash
# 验证前端构建是否完成

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIST="${PROJECT_ROOT}/static/dist"

echo "Checking frontend build..."

if [ ! -d "$FRONTEND_DIST" ]; then
    echo "Error: Frontend build not found at $FRONTEND_DIST"
    echo "Please run 'cd frontend && npm install && npm run build' first"
    exit 1
fi

# 检查关键文件
if [ ! -f "$FRONTEND_DIST/index.html" ] && [ ! -f "$FRONTEND_DIST/assets/index.html" ]; then
    echo "Error: Frontend build incomplete - index.html not found"
    exit 1
fi

if [ ! -d "$FRONTEND_DIST/assets" ]; then
    echo "Warning: Frontend assets directory not found"
    echo "The build might be incomplete"
fi

echo "✓ Frontend build verified"
exit 0
