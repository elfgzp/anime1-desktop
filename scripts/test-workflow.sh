#!/usr/bin/env bash
# GitHub Actions Workflow 测试脚本
# 
# 功能：
# 1. 提交代码到 GitHub
# 2. 触发 workflow 测试
# 3. 持续监测 workflow 运行状态
# 4. 验证所有平台的构建结果

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
WORKFLOW_NAME="Build and Release"
TEST_VERSION="test-$(date +%Y%m%d-%H%M%S)"
MAX_WAIT_TIME=1800  # 最大等待时间（秒）
CHECK_INTERVAL=10   # 检查间隔（秒）

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"
    
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}错误: GitHub CLI (gh) 未安装${NC}"
        echo "安装方法: brew install gh"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}错误: 未登录 GitHub${NC}"
        echo "请运行: gh auth login --scopes workflow"
        exit 1
    fi
    
    # 检查是否有 workflow 权限
    if ! gh auth status 2>&1 | grep -q "workflow"; then
        echo -e "${YELLOW}警告: token 可能没有 workflow 权限${NC}"
        echo "请运行: gh auth login --hostname github.com --scopes workflow"
    fi
    
    echo -e "${GREEN}[OK] Dependencies check passed${NC}\n"
}

# 检查 git 状态
check_git_status() {
    echo -e "${BLUE}检查 Git 状态...${NC}"
    
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}发现未提交的更改${NC}"
        git status --short
        
        read -p "是否提交这些更改? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add -A
            git commit -m "Test: Trigger workflow test - $TEST_VERSION"
            echo -e "${GREEN}[OK] Changes committed${NC}"
        else
            echo -e "${YELLOW}跳过提交，继续测试现有代码${NC}"
        fi
    else
        echo -e "${GREEN}[OK] Working directory clean${NC}"
    fi
    
    # 检查是否需要推送
    local_ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    if [ "$local_ahead" -gt 0 ]; then
        echo -e "${YELLOW}本地有未推送的提交${NC}"
        read -p "是否推送到远程? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push
            echo -e "${GREEN}[OK] Code pushed${NC}"
            # 等待 GitHub 同步
            echo -e "${BLUE}等待 GitHub 同步...${NC}"
            sleep 5
        fi
    fi
    
    echo
}

# 触发 workflow
trigger_workflow() {
    echo -e "${BLUE}触发 workflow: $WORKFLOW_NAME${NC}"
    echo -e "  版本: $TEST_VERSION"
    echo -e "  分支: $(git branch --show-current)"
    echo
    
    local run_output
    run_output=$(gh workflow run "$WORKFLOW_NAME" \
        --ref "$(git branch --show-current)" \
        -f version="$TEST_VERSION" \
        -f create_release=false 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] Workflow triggered${NC}\n"
        return 0
    else
        echo -e "${RED}✗ 触发失败: $run_output${NC}"
        return 1
    fi
}

# 获取最新的运行 ID
get_latest_run_id() {
    gh run list --workflow="$WORKFLOW_NAME" --limit 1 --json databaseId --jq '.[0].databaseId'
}

# 验证所有平台的构建结果
verify_all_platforms() {
    local run_id=$1
    
    echo -e "\n${BLUE}=== 验证所有平台的构建结果 ===${NC}\n"
    
    # 获取所有任务信息
    local jobs_json=$(gh run view "$run_id" --json jobs)
    
    # 期望的平台列表
    local expected_platforms=("windows-latest-x64" "macos-latest-arm64" "macos-12-x64" "ubuntu-latest-x64")
    local all_success=true
    
    for platform in "${expected_platforms[@]}"; do
        local job_name="Build on $platform"
        local job_status=$(echo "$jobs_json" | jq -r ".jobs[] | select(.name == \"$job_name\") | .status")
        local job_conclusion=$(echo "$jobs_json" | jq -r ".jobs[] | select(.name == \"$job_name\") | .conclusion // \"pending\"")
        
        if [ "$job_status" == "completed" ]; then
            if [ "$job_conclusion" == "success" ]; then
                echo -e "  ${GREEN}[OK] $platform: success${NC}"
            else
                echo -e "  ${RED}✗ $platform: 失败 ($job_conclusion)${NC}"
                all_success=false
                
                # 显示失败任务的日志链接
                local job_id=$(echo "$jobs_json" | jq -r ".jobs[] | select(.name == \"$job_name\") | .databaseId")
                echo -e "    查看日志: gh run view --job=$job_id"
            fi
        else
            echo -e "  ${YELLOW}○ $platform: $job_status${NC}"
            all_success=false
        fi
    done
    
    echo
    
    # 检查构建产物
    echo -e "${BLUE}检查构建产物...${NC}"
    local artifacts=$(gh run download "$run_id" --dir /tmp/gh-artifacts-$run_id 2>&1 || echo "")
    
    if [ -d "/tmp/gh-artifacts-$run_id" ]; then
        echo -e "${GREEN}[OK] Build artifacts downloaded${NC}"
        echo "产物列表:"
        find /tmp/gh-artifacts-$run_id -type f -name "*.zip" -o -name "*.dmg" -o -name "*.tar.gz" | while read -r file; do
            local size=$(du -h "$file" | cut -f1)
            echo -e "  ${GREEN}[OK] $(basename "$file") ($size)${NC}"
        done
        rm -rf /tmp/gh-artifacts-$run_id
    else
        echo -e "${YELLOW}○ 构建产物暂不可用${NC}"
    fi
    
    return $([ "$all_success" = true ] && [ "$job_status" == "completed" ] && echo 0 || echo 1)
}

# 监测 workflow 运行状态
monitor_workflow() {
    local run_id=$1
    local start_time=$(date +%s)
    local elapsed=0
    
    echo -e "${BLUE}开始监测 workflow 运行 (ID: $run_id)${NC}"
    echo -e "查看详情: https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions/runs/$run_id"
    echo
    
    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        local status=$(gh run view "$run_id" --json status,conclusion,jobs --jq -r '.status')
        local conclusion=$(gh run view "$run_id" --json status,conclusion,jobs --jq -r '.conclusion // "null"')
        
        elapsed=$(($(date +%s) - start_time))
        local minutes=$((elapsed / 60))
        local seconds=$((elapsed % 60))
        
        printf "\r${BLUE}[%02d:%02d]${NC} 状态: " $minutes $seconds
        
        case "$status" in
            "queued")
                echo -e "${YELLOW}排队中...${NC}"
                ;;
            "in_progress")
                echo -e "${BLUE}运行中...${NC}"
                # 显示各任务状态
                gh run view "$run_id" --json jobs --jq '.jobs[] | "  - \(.name): \(.status)"' 2>/dev/null | head -4 || true
                ;;
            "completed")
                if [ "$conclusion" == "success" ]; then
                    echo -e "${GREEN}[OK] Completed successfully${NC}\n"
                    verify_all_platforms "$run_id"
                    return $?
                else
                    echo -e "${RED}✗ 失败: $conclusion${NC}\n"
                    verify_all_platforms "$run_id"
                    return 1
                fi
                ;;
            *)
                echo -e "${YELLOW}$status${NC}"
                ;;
        esac
        
        sleep $CHECK_INTERVAL
    done
    
    echo -e "\n${RED}✗ 超时: 超过 $((MAX_WAIT_TIME / 60)) 分钟${NC}"
    return 1
}

# 显示详细结果
show_results() {
    local run_id=$1
    local success=$2
    
    echo -e "\n${BLUE}=== 测试结果 ===${NC}\n"
    
    if [ $success -eq 0 ]; then
        echo -e "${GREEN}[OK] All platforms built successfully${NC}\n"
    else
        echo -e "${RED}✗ 部分平台构建失败${NC}\n"
    fi
    
    # 显示各任务状态
    echo -e "${BLUE}任务状态:${NC}"
    gh run view "$run_id" --json jobs --jq '.jobs[] | "\(.name): \(.status) \(.conclusion // "")"' | while read -r line; do
        if echo "$line" | grep -q "success"; then
            echo -e "  ${GREEN}[OK] $line${NC}"
        elif echo "$line" | grep -q "failure"; then
            echo -e "  ${RED}✗ $line${NC}"
        else
            echo -e "  ${YELLOW}○ $line${NC}"
        fi
    done
    
    echo -e "\n${BLUE}查看详细日志:${NC}"
    echo "  gh run view $run_id"
    echo "  gh run view $run_id --log"
    echo -e "\n${BLUE}在浏览器中查看:${NC}"
    echo "  https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions/runs/$run_id"
}

# 主函数
main() {
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  GitHub Actions Workflow 测试工具   ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}\n"
    
    check_dependencies
    check_git_status
    
    if ! trigger_workflow; then
        exit 1
    fi
    
    # 等待 workflow 启动
    echo -e "${BLUE}等待 workflow 启动...${NC}"
    sleep 5
    
    local run_id=$(get_latest_run_id)
    if [ -z "$run_id" ] || [ "$run_id" == "null" ]; then
        echo -e "${RED}✗ 无法获取运行 ID${NC}"
        exit 1
    fi
    
    if monitor_workflow "$run_id"; then
        show_results "$run_id" 0
        exit 0
    else
        show_results "$run_id" 1
        exit 1
    fi
}

# 运行主函数
main "$@"
