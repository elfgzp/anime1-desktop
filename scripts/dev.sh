#!/usr/bin/env bash
# 开发模式启动脚本 - 同时启动 Flask 后端和 Vite 前端开发服务器
# 使用 bash 版本（更轻量，但功能较少）

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLASK_PORT=${FLASK_PORT:-5172}
VITE_PORT=${VITE_PORT:-5173}

cd "$PROJECT_ROOT"

# 检查依赖
echo "检查依赖..."
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装，请先安装 Node.js"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ 前端依赖未安装，请运行: cd frontend && npm install"
    exit 1
fi

echo "[OK] Dependency check passed"
echo ""

printf "=%.0s" {1..60} && echo ""
echo "Anime1 Desktop - 开发模式"
printf "=%.0s" {1..60} && echo ""
echo "Flask 后端: http://localhost:$FLASK_PORT"
echo "Vite 前端: http://localhost:$VITE_PORT"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $FLASK_PID $VITE_PID 2>/dev/null || true
    wait $FLASK_PID $VITE_PID 2>/dev/null || true
    echo "✅ 所有服务已停止"
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM

# 启动 Flask 后端
echo "🚀 启动 Flask 后端 (端口 $FLASK_PORT)..."
python3 -m src.app --port "$FLASK_PORT" --no-browser --debug &
FLASK_PID=$!

# 等待 Flask 启动
sleep 2

# 启动 Vite 前端
echo "🚀 启动 Vite 前端开发服务器 (端口 $VITE_PORT)..."
cd frontend
npm run dev &
VITE_PID=$!
cd ..

# 等待 Vite 启动
sleep 2

echo ""
echo "✅ 开发环境已启动！"
echo "   前端: http://localhost:$VITE_PORT"
echo "   后端 API: http://localhost:$FLASK_PORT/api"
echo ""
echo "正在运行... (按 Ctrl+C 停止)"
echo ""

# 等待进程
wait $FLASK_PID $VITE_PID
