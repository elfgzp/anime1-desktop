#!/usr/bin/env bash
# 验证所有 workflow 相关脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  验证 Workflow 相关脚本            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}\n"

ERRORS=0

# 检查脚本文件是否存在
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${GREEN}[OK]${NC} $file 存在"
        return 0
    else
        echo -e "${RED}✗${NC} $file 不存在"
        ((ERRORS++))
        return 1
    fi
}

# 检查脚本语法
check_syntax() {
    local file=$1
    local type=$2
    
    if [ "$type" == "bash" ]; then
        if bash -n "$file" 2>/dev/null; then
            echo -e "${GREEN}[OK]${NC} $file syntax correct"
            return 0
        else
            echo -e "${RED}✗${NC} $file 语法错误"
            bash -n "$file"
            ((ERRORS++))
            return 1
        fi
    elif [ "$type" == "python" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}[OK]${NC} $file syntax correct"
            return 0
        else
            echo -e "${RED}✗${NC} $file 语法错误"
            python3 -m py_compile "$file"
            ((ERRORS++))
            return 1
        fi
    fi
}

# 检查执行权限
check_permission() {
    local file=$1
    if [ -x "$file" ]; then
        echo -e "${GREEN}[OK]${NC} $file 有执行权限"
        return 0
    else
        echo -e "${YELLOW}○${NC} $file 无执行权限（将自动添加）"
        chmod +x "$file"
        return 0
    fi
}

echo -e "${BLUE}1. 检查脚本文件...${NC}\n"

# Bash 脚本
check_file "scripts/build.sh"
check_file "scripts/extract_version.sh"
check_file "scripts/extract_changelog.sh"
check_file "scripts/test-workflow.sh"
check_file "scripts/verify-frontend.sh"

# Python 脚本
check_file "scripts/prepare_artifacts.py"
check_file "scripts/create_dmg.py"
check_file "scripts/extract_changelog.py"
check_file "scripts/prepare_release_assets.py"

echo -e "\n${BLUE}2. 检查脚本语法...${NC}\n"

check_syntax "scripts/build.sh" "bash"
check_syntax "scripts/extract_version.sh" "bash"
check_syntax "scripts/extract_changelog.sh" "bash"
check_syntax "scripts/test-workflow.sh" "bash"
check_syntax "scripts/verify-frontend.sh" "bash"

check_syntax "scripts/prepare_artifacts.py" "python"
check_syntax "scripts/create_dmg.py" "python"
check_syntax "scripts/extract_changelog.py" "python"
check_syntax "scripts/prepare_release_assets.py" "python"

echo -e "\n${BLUE}3. 检查执行权限...${NC}\n"

check_permission "scripts/build.sh"
check_permission "scripts/extract_version.sh"
check_permission "scripts/extract_changelog.sh"
check_permission "scripts/test-workflow.sh"
check_permission "scripts/verify-frontend.sh"

echo -e "\n${BLUE}4. 测试脚本功能...${NC}\n"

# 测试 extract_version.sh
echo -e "${BLUE}测试 extract_version.sh:${NC}"
if result=$(bash scripts/extract_version.sh workflow_dispatch "1.0.0-test" "refs/heads/main" 2>&1); then
    echo -e "${GREEN}[OK]${NC} extract_version.sh works correctly"
    echo "$result" | grep -q "tag_name='v1.0.0-test'" && echo -e "${GREEN}  [OK]${NC} Output correct"
else
    echo -e "${RED}✗${NC} extract_version.sh 测试失败"
    ((ERRORS++))
fi

# 测试 extract_changelog.py
echo -e "\n${BLUE}测试 extract_changelog.py:${NC}"
if result=$(python3 scripts/extract_changelog.py "1.0.0" 2>&1); then
    if [ -n "$result" ]; then
        echo -e "${GREEN}[OK]${NC} extract_changelog.py works correctly"
        echo "$result" | grep -q "Added" && echo -e "${GREEN}  [OK]${NC} Output contains content"
    else
        echo -e "${YELLOW}○${NC} extract_changelog.py 返回空（可能是版本不存在）"
    fi
else
    echo -e "${RED}✗${NC} extract_changelog.py 测试失败"
    ((ERRORS++))
fi

# 测试 build.sh（不实际构建）
echo -e "\n${BLUE}测试 build.sh (dry-run):${NC}"
if bash scripts/build.sh "Windows" 2>&1 | head -3 | grep -q "Building Windows"; then
    echo -e "${GREEN}[OK]${NC} build.sh can recognize Windows platform"
else
    echo -e "${RED}✗${NC} build.sh Windows 平台测试失败"
    ((ERRORS++))
fi

echo -e "\n${BLUE}5. 检查 workflow 文件...${NC}\n"

if [ -f ".github/workflows/release.yml" ]; then
    echo -e "${GREEN}[OK]${NC} .github/workflows/release.yml exists"
    # 检查是否引用了所有脚本
    if grep -q "scripts/build.sh" .github/workflows/release.yml; then
        echo -e "${GREEN}  [OK]${NC} references build.sh"
    else
        echo -e "${RED}  ✗${NC} 未引用 build.sh"
        ((ERRORS++))
    fi
    # 检查前端构建步骤
    if grep -q "Build frontend" .github/workflows/release.yml; then
        echo -e "${GREEN}  [OK]${NC} contains frontend build step"
    else
        echo -e "${YELLOW}  ○${NC} 未找到前端构建步骤（可能需要更新）"
    fi
else
    echo -e "${RED}✗${NC} .github/workflows/release.yml 不存在"
    ((ERRORS++))
fi

echo -e "\n${BLUE}=== 验证结果 ===${NC}\n"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}[OK] All scripts verified!${NC}"
    exit 0
else
    echo -e "${RED}✗ 发现 $ERRORS 个问题${NC}"
    exit 1
fi
