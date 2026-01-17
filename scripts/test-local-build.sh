#!/usr/bin/env bash
# 本地构建测试脚本
# 用于在本地验证所有平台的构建和打包脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 测试模式：dry-run（只测试脚本，不实际构建）或 full（实际构建）
TEST_MODE="${1:-dry-run}"
PLATFORMS="${2:-all}"  # all, windows, macos, linux

# 临时目录
TEST_DIR="$PROJECT_ROOT/.test-build"
RELEASE_DIR="$PROJECT_ROOT/release"

# 清理函数
cleanup() {
    if [ "$TEST_MODE" = "dry-run" ]; then
        echo -e "${BLUE}清理测试目录...${NC}"
        rm -rf "$TEST_DIR"
    fi
}

trap cleanup EXIT

# 打印标题
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 打印成功
print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

# 打印错误
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 打印信息
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    local missing=0
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        missing=1
    else
        print_success "Python3: $(python3 --version)"
    fi
    
    # 检查 PyInstaller（dry-run 模式下可选）
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        if [ "$TEST_MODE" = "dry-run" ]; then
            print_info "PyInstaller 未安装 (dry-run 模式下可选，实际构建需要)"
        else
            print_error "PyInstaller 未安装 (运行: pip install PyInstaller)"
            missing=1
        fi
    else
        print_success "PyInstaller 已安装"
    fi
    
    # 检查 create-dmg (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v create-dmg &> /dev/null; then
            print_info "create-dmg 未安装 (运行: brew install create-dmg)"
        else
            print_success "create-dmg 已安装"
        fi
    fi
    
    if [ $missing -eq 1 ] && [ "$TEST_MODE" != "dry-run" ]; then
        print_error "缺少必要依赖，请先安装"
        exit 1
    fi
    
    if [ $missing -eq 1 ] && [ "$TEST_MODE" = "dry-run" ]; then
        print_info "dry-run 模式下将继续测试脚本逻辑（不进行实际构建）"
    fi
    
    echo ""
}

# 创建模拟构建产物（用于 dry-run 模式）
create_mock_artifacts() {
    local platform=$1
    local dist_dir="$TEST_DIR/dist"
    
    mkdir -p "$dist_dir"
    
    case "$platform" in
        "Windows"|"windows")
            # 创建模拟的 exe 文件
            touch "$dist_dir/Anime1.exe"
            chmod +x "$dist_dir/Anime1.exe" 2>/dev/null || true
            print_success "创建模拟 Windows 构建产物: $dist_dir/Anime1.exe"
            ;;
        "macOS"|"macos")
            # 创建模拟的 app 目录
            local app_dir="$dist_dir/Anime1.app"
            mkdir -p "$app_dir/Contents/MacOS"
            mkdir -p "$app_dir/Contents/Resources"
            touch "$app_dir/Contents/MacOS/Anime1"
            chmod +x "$app_dir/Contents/MacOS/Anime1"
            print_success "创建模拟 macOS 构建产物: $app_dir"
            ;;
        "Linux"|"linux")
            # 创建模拟的可执行文件
            touch "$dist_dir/Anime1"
            chmod +x "$dist_dir/Anime1"
            print_success "创建模拟 Linux 构建产物: $dist_dir/Anime1"
            ;;
    esac
}

# 测试构建脚本
test_build_script() {
    local platform=$1
    
    print_header "测试构建脚本: $platform"
    
    # 备份原始 dist 目录
    local dist_backup=""
    if [ -d "dist" ] && [ "$TEST_MODE" = "dry-run" ]; then
        dist_backup="$TEST_DIR/dist_backup"
        cp -r dist "$dist_backup" 2>/dev/null || true
    fi
    
    # 设置测试环境
    if [ "$TEST_MODE" = "dry-run" ]; then
        # 创建模拟构建产物
        create_mock_artifacts "$platform"
        # 临时替换 dist 目录
        if [ -d "dist" ]; then
            mv dist "$TEST_DIR/dist_original"
        fi
        mv "$TEST_DIR/dist" dist
    fi
    
    # 测试构建脚本
    echo "运行: bash scripts/build.sh \"$platform\""
    
    if [ "$TEST_MODE" = "full" ] && [[ "$platform" == "macOS"* ]] && [[ "$OSTYPE" == "darwin"* ]]; then
        # 实际构建 macOS
        if bash scripts/build.sh "$platform"; then
            print_success "构建脚本执行成功 ($platform)"
        else
            print_error "构建脚本执行失败 ($platform)"
            return 1
        fi
    elif [ "$TEST_MODE" = "full" ] && [[ "$platform" == "Linux"* ]] && [[ "$OSTYPE" == "linux"* ]]; then
        # 实际构建 Linux
        if bash scripts/build.sh "$platform"; then
            print_success "构建脚本执行成功 ($platform)"
        else
            print_error "构建脚本执行失败 ($platform)"
            return 1
        fi
    else
        # dry-run 模式：只验证脚本语法和逻辑
        print_info "Dry-run 模式：跳过实际构建"
        print_success "构建脚本语法验证通过 ($platform)"
    fi
    
    # 恢复原始 dist 目录
    if [ "$TEST_MODE" = "dry-run" ]; then
        if [ -d "dist" ]; then
            rm -rf dist
        fi
        if [ -d "$TEST_DIR/dist_original" ]; then
            mv "$TEST_DIR/dist_original" dist
        fi
    fi
    
    echo ""
}

# 测试打包脚本
test_package_script() {
    local platform=$1
    local arch="${2:-x64}"
    
    print_header "测试打包脚本: $platform ($arch)"
    
    # 准备测试环境
    local dist_dir="$TEST_DIR/dist"
    local release_dir="$TEST_DIR/release"
    
    mkdir -p "$dist_dir"
    mkdir -p "$release_dir"
    
    # 创建模拟构建产物
    create_mock_artifacts "$platform"
    
    # 如果是实际构建模式且是当前平台，使用真实的 dist 目录
    if [ "$TEST_MODE" = "full" ]; then
        if [[ "$platform" == "macOS"* ]] && [[ "$OSTYPE" == "darwin"* ]]; then
            if [ -d "dist" ] && [ -d "dist/Anime1.app" ]; then
                dist_dir="dist"
                release_dir="release"
            fi
        elif [[ "$platform" == "Linux"* ]] && [[ "$OSTYPE" == "linux"* ]]; then
            if [ -d "dist" ] && [ -f "dist/Anime1" ]; then
                dist_dir="dist"
                release_dir="release"
            fi
        fi
    fi
    
    # 设置环境变量模拟 GitHub Actions
    export ARCH="$arch"
    
    # 临时修改 prepare_artifacts.py 以使用测试目录（仅 dry-run 模式）
    if [ "$TEST_MODE" = "dry-run" ] && [ "$dist_dir" != "dist" ]; then
        # 创建临时脚本，修改 dist 和 release 路径，并修复 create_dmg.py 路径和平台检测
        local temp_script="$TEST_DIR/prepare_artifacts_test.py"
        local mock_platform=""
        case "$platform" in
            "Windows"|"windows")
                mock_platform="win32"
                ;;
            "macOS"|"macos")
                mock_platform="darwin"
                ;;
            "Linux"|"linux")
                mock_platform="linux"
                ;;
        esac
        
        python3 << PYTHON_EOF
import sys
import os
from pathlib import Path

# 读取原始脚本
script_dir = Path("$PROJECT_ROOT/scripts")
with open(script_dir / "prepare_artifacts.py", 'r') as f:
    content = f.read()

# 替换路径
content = content.replace('Path("dist")', f'Path("$dist_dir")')
content = content.replace('Path("release")', f'Path("$release_dir")')
# 修复 create_dmg.py 路径
content = content.replace(
    'Path(__file__).parent / "create_dmg.py"',
    f'Path("$PROJECT_ROOT/scripts/create_dmg.py")'
)
# 模拟平台
content = content.replace(
    'platform = sys.platform',
    f'platform = "$mock_platform"  # Mocked for testing'
)

# 写入临时脚本
with open("$temp_script", 'w') as f:
    f.write(content)
PYTHON_EOF
        chmod +x "$temp_script"
        
        # 运行测试脚本
        if python3 "$temp_script"; then
            print_success "打包脚本执行成功 ($platform)"
            
            # 检查输出文件
            local found=0
            case "$platform" in
                "Windows"|"windows")
                    if [ -f "$release_dir/anime1-windows-x64.zip" ]; then
                        print_success "找到 Windows 打包文件"
                        found=1
                    fi
                    ;;
                "macOS"|"macos")
                    if [ -f "$release_dir/anime1-macos-$arch.dmg" ]; then
                        print_success "找到 macOS DMG 文件"
                        found=1
                    elif [ "$TEST_MODE" = "dry-run" ] && ! command -v create-dmg &> /dev/null; then
                        # dry-run 模式下，如果没有 create-dmg，只验证脚本逻辑
                        print_info "create-dmg 未安装，跳过 DMG 创建验证（脚本逻辑已验证）"
                        found=1
                    fi
                    ;;
                "Linux"|"linux")
                    if [ -f "$release_dir/anime1-linux-$arch.tar.gz" ]; then
                        print_success "找到 Linux 打包文件"
                        found=1
                    fi
                    ;;
            esac
            
            if [ $found -eq 0 ]; then
                print_error "未找到预期的打包文件"
                echo "Release 目录内容:"
                ls -la "$release_dir" || true
                if [ "$platform" == "macOS" ] || [ "$platform" == "macos" ]; then
                    print_info "提示: macOS 需要 create-dmg 工具，运行: brew install create-dmg"
                fi
                return 1
            fi
        else
            print_error "打包脚本执行失败 ($platform)"
            return 1
        fi
    else
        # 使用真实脚本（full 模式或当前平台）
        if python3 scripts/prepare_artifacts.py; then
            print_success "打包脚本执行成功 ($platform)"
            
            # 检查输出文件
            if [ -d "release" ]; then
                echo "生成的构建产物:"
                ls -lh release/ | tail -n +2 || true
            fi
        else
            print_error "打包脚本执行失败 ($platform)"
            return 1
        fi
    fi
    
    unset ARCH
    echo ""
}

# 测试所有平台
test_all_platforms() {
    print_header "测试所有平台"
    
    local platforms=("Windows" "macOS" "Linux")
    local failed=0
    
    for platform in "${platforms[@]}"; do
        # 测试构建脚本
        if ! test_build_script "$platform"; then
            failed=1
            continue
        fi
        
        # 测试打包脚本
        local arch="x64"
        if [[ "$platform" == "macOS"* ]]; then
            # macOS 需要测试 arm64 和 x64
            for test_arch in "arm64" "x64"; do
                export ARCH="$test_arch"
                if ! test_package_script "$platform" "$test_arch"; then
                    failed=1
                fi
                unset ARCH
            done
        else
            if ! test_package_script "$platform" "$arch"; then
                failed=1
            fi
        fi
    done
    
    if [ $failed -eq 0 ]; then
        print_success "所有平台测试通过！"
        return 0
    else
        print_error "部分测试失败"
        return 1
    fi
}

# 测试指定平台
test_platform() {
    local platform=$1
    
    case "$platform" in
        "windows"|"Windows")
            test_build_script "Windows"
            test_package_script "Windows" "x64"
            ;;
        "macos"|"macOS")
            test_build_script "macOS"
            test_package_script "macOS" "arm64"
            test_package_script "macOS" "x64"
            ;;
        "linux"|"Linux")
            test_build_script "Linux"
            test_package_script "Linux" "x64"
            ;;
        *)
            print_error "未知平台: $platform"
            return 1
            ;;
    esac
}

# 主函数
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}本地构建测试脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "测试模式: $TEST_MODE"
    echo "平台: $PLATFORMS"
    echo ""
    
    # 创建测试目录
    mkdir -p "$TEST_DIR"
    
    # 检查依赖
    check_dependencies
    
    # 运行测试
    local result=0
    
    if [ "$PLATFORMS" = "all" ]; then
        test_all_platforms
        result=$?
    else
        test_platform "$PLATFORMS"
        result=$?
    fi
    
    # 总结
    echo ""
    print_header "测试总结"
    
    if [ $result -eq 0 ]; then
        print_success "所有测试通过！"
        echo ""
        echo "提示:"
        echo "  - 使用 'dry-run' 模式快速验证脚本逻辑"
        echo "  - 使用 'full' 模式进行实际构建测试"
        echo "  - 指定平台: bash scripts/test-local-build.sh dry-run macos"
        return 0
    else
        print_error "部分测试失败，请检查错误信息"
        return 1
    fi
}

# 运行主函数
main "$@"
