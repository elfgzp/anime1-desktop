#!/bin/bash
# 自动更新功能 Mock 测试脚本
# 用于快速测试各种更新场景

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助
show_help() {
    cat << EOF
自动更新功能 Mock 测试脚本

用法: $0 [选项] [场景]

场景:
    no-update       - 无可用更新
    has-update      - 有可用更新 (默认)
    check-error     - 检查更新时出错
    download-error  - 下载时出错
    downloaded      - 已下载等待安装

选项:
    -h, --help      - 显示帮助
    -l, --list      - 列出所有场景
    -v, --version   - 指定模拟版本号 (默认: 9.9.9)
    -d, --delay     - 指定检查延迟 (毫秒, 默认: 2000)
    -t, --test      - 运行单元测试
    --devtools      - 打开 DevTools

示例:
    $0                          # 使用默认场景 (has-update)
    $0 no-update                # 测试无更新场景
    $0 download-error           # 测试下载失败场景
    $0 -v 2.0.0 has-update      # 自定义版本号
    $0 -t                       # 运行单元测试
    $0 --devtools has-update    # 打开 DevTools 测试

EOF
}

# 列出场景
list_scenarios() {
    cat << EOF
可用测试场景:

  no-update       模拟已是最新版本，无可用更新
  has-update      模拟发现新版本 v9.9.9，可测试完整更新流程 (默认)
  check-error     模拟网络错误，检查更新时失败
  download-error  模拟下载到 50% 时失败
  downloaded      模拟更新已下载完成，等待安装

EOF
}

# 运行单元测试
run_tests() {
    print_info "运行 Mock Updater 单元测试..."
    npm test -- tests/unit/updater.mock.test.js --reporter=verbose
}

# 启动应用
start_app() {
    local scenario=$1
    local version=$2
    local delay=$3
    local devtools=$4
    
    print_info "启动 Mock Updater 测试..."
    print_info "场景: $scenario"
    print_info "版本: $version"
    print_info "延迟: ${delay}ms"
    
    if [ "$devtools" = true ]; then
        print_info "DevTools: 已启用"
    fi
    
    echo ""
    print_success "应用启动后，你可以:"
    echo "  1. 在应用内触发检查更新"
    echo "  2. 打开 DevTools 控制台执行:"
    echo "     await electron.ipcRenderer.invoke('mock-updater:get-scenarios')"
    echo "     await electron.ipcRenderer.invoke('mock-updater:set-scenario', 'no-update')"
    echo ""
    
    # 设置环境变量并启动
    export MOCK_UPDATER=true
    export MOCK_UPDATER_SCENARIO="$scenario"
    export MOCK_UPDATER_VERSION="$version"
    export MOCK_CHECK_DELAY="$delay"
    
    if [ "$devtools" = true ]; then
        export DEVTOOLS=true
    fi
    
    npm start
}

# 主函数
main() {
    local scenario="has-update"
    local version="9.9.9"
    local delay=2000
    local devtools=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                list_scenarios
                exit 0
                ;;
            -t|--test)
                run_tests
                exit 0
                ;;
            -v|--version)
                version="$2"
                shift 2
                ;;
            -d|--delay)
                delay="$2"
                shift 2
                ;;
            --devtools)
                devtools=true
                shift
                ;;
            no-update|has-update|check-error|download-error|downloaded)
                scenario="$1"
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查是否在正确目录
    if [ ! -f "package.json" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 启动应用
    start_app "$scenario" "$version" "$delay" "$devtools"
}

# 运行主函数
main "$@"
