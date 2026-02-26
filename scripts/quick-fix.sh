#!/bin/bash

# Anime1 Desktop 快速修复脚本
# 用于修复常见的开发环境问题

echo "=== Anime1 Desktop Quick Fix ==="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 修复 1: 重置数据库（解决数据问题）
fix_database() {
    echo -e "${YELLOW}Fixing database...${NC}"
    DB_PATH="$HOME/Library/Application Support/anime1-desktop-electron/anime1.db"
    
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$DB_PATH.backup.$(date +%s)"
        echo "Database backed up"
        
        # 重置设置
        sqlite3 "$DB_PATH" "DELETE FROM settings;"
        echo "Settings cleared"
    fi
    
    echo -e "${GREEN}Database fixed${NC}"
}

# 修复 2: 重置暗黑模式
fix_theme() {
    echo -e "${YELLOW}Setting dark theme...${NC}"
    DB_PATH="$HOME/Library/Application Support/anime1-desktop-electron/anime1.db"
    
    sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', '\"dark\"');"
    echo -e "${GREEN}Dark theme set${NC}"
}

# 修复 3: 清理缓存并重启
fix_cache() {
    echo -e "${YELLOW}Clearing cache...${NC}"
    rm -rf dist/ dist-electron/
    echo "Cache cleared"
    
    echo -e "${YELLOW}Rebuilding...${NC}"
    npm run dev &
    echo -e "${GREEN}App restarted${NC}"
}

# 修复 4: 检查资源文件
fix_resources() {
    echo -e "${YELLOW}Checking resources...${NC}"
    
    if [ ! -f "resources/icon.icns" ]; then
        echo -e "${RED}Missing icon.icns${NC}"
        echo "Please add icon files to resources/"
    else
        echo -e "${GREEN}Resources OK${NC}"
    fi
}

# 修复 5: 运行完整检查
full_check() {
    echo -e "${YELLOW}Running full check...${NC}"
    
    # 检查端口
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}Vite server running on 5173${NC}"
    else
        echo -e "${RED}Vite server not running${NC}"
    fi
    
    # 检查 CDP
    if curl -s http://localhost:9222/json/list >/dev/null; then
        echo -e "${GREEN}CDP available${NC}"
    else
        echo -e "${RED}CDP not available${NC}"
    fi
    
    # 检查数据库
    DB_PATH="$HOME/Library/Application Support/anime1-desktop-electron/anime1.db"
    if [ -f "$DB_PATH" ]; then
        echo -e "${GREEN}Database exists${NC}"
        echo "Settings:"
        sqlite3 "$DB_PATH" "SELECT * FROM settings;"
        echo "Favorites count:"
        sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM favorite_anime;"
    else
        echo -e "${RED}Database not found${NC}"
    fi
}

# 主菜单
case "$1" in
    db)
        fix_database
        ;;
    theme)
        fix_theme
        ;;
    cache)
        fix_cache
        ;;
    resources)
        fix_resources
        ;;
    check)
        full_check
        ;;
    all)
        fix_resources
        fix_database
        full_check
        ;;
    *)
        echo "Usage: $0 {db|theme|cache|resources|check|all}"
        echo ""
        echo "Commands:"
        echo "  db        - Reset database"
        echo "  theme     - Set dark theme"
        echo "  cache     - Clear cache and restart"
        echo "  resources - Check resource files"
        echo "  check     - Full system check"
        echo "  all       - Run all fixes"
        ;;
esac
