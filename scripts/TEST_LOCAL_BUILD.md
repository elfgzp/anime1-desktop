# 本地构建测试指南

本指南介绍如何在本地验证和测试所有平台的构建和打包脚本，无需推送到 GitHub Actions。

## 快速开始

### 1. Dry-Run 模式（推荐用于快速验证）

Dry-run 模式会创建模拟的构建产物来测试脚本逻辑，不会进行实际构建：

```bash
# 测试所有平台
make test-local-build

# 或直接运行脚本
bash scripts/test-local-build.sh dry-run all

# 测试指定平台
bash scripts/test-local-build.sh dry-run macos
bash scripts/test-local-build.sh dry-run windows
bash scripts/test-local-build.sh dry-run linux
```

### 2. Full 模式（实际构建测试）

Full 模式会进行实际构建，适合在本地验证完整的构建流程：

```bash
# 测试所有平台（会实际构建当前平台）
make test-local-build-full

# 或直接运行脚本
bash scripts/test-local-build.sh full all

# 测试指定平台
bash scripts/test-local-build.sh full macos
```

## 测试内容

脚本会测试以下内容：

1. **依赖检查**
   - Python3 是否安装
   - PyInstaller 是否安装
   - create-dmg 是否安装（macOS）

2. **构建脚本测试** (`scripts/build.sh`)
   - 脚本语法验证
   - 平台参数处理
   - 构建命令执行（full 模式）

3. **打包脚本测试** (`scripts/prepare_artifacts.py`)
   - Windows: 验证 `.zip` 文件创建
   - macOS: 验证 `.dmg` 文件创建（arm64 和 x64）
   - Linux: 验证 `.tar.gz` 文件创建

## 平台说明

### macOS

在 macOS 上可以：
- ✅ 实际构建 macOS arm64 版本
- ✅ 测试 macOS x64 打包逻辑（dry-run）
- ⚠️ 无法实际构建 macOS x64（需要 Intel Mac 或 GitHub Actions）

### Linux

在 Linux 上可以：
- ✅ 实际构建 Linux x64 版本
- ✅ 测试所有平台的打包逻辑（dry-run）

### Windows

在 Windows 上可以：
- ✅ 实际构建 Windows x64 版本
- ✅ 测试所有平台的打包逻辑（dry-run）

## 使用场景

### 场景 1: 修改脚本后快速验证

```bash
# 修改了 build.sh 或 prepare_artifacts.py 后
make test-local-build
```

### 场景 2: 验证新平台的打包逻辑

```bash
# 添加了新平台的打包逻辑后
bash scripts/test-local-build.sh dry-run all
```

### 场景 3: 本地完整测试（macOS）

```bash
# 在 macOS 上完整测试构建和打包流程
make test-local-build-full
# 或指定平台
bash scripts/test-local-build.sh full macos
```

## 输出说明

脚本会显示：
- ✅ 绿色：成功
- ❌ 红色：失败
- ℹ️ 黄色：信息提示

测试完成后会显示：
- 所有测试的总结
- 生成的构建产物列表（full 模式）
- 使用提示

## 故障排除

### 问题 1: PyInstaller 未安装

```bash
pip install PyInstaller
# 或
make install
```

### 问题 2: create-dmg 未安装（macOS）

```bash
brew install create-dmg
# 或
make install-dmg
```

### 问题 3: 权限错误

```bash
chmod +x scripts/test-local-build.sh
```

### 问题 4: 测试目录冲突

脚本会自动清理测试目录（`.test-build`），如果遇到问题可以手动删除：

```bash
rm -rf .test-build
```

## 与 GitHub Actions 的关系

本地测试脚本模拟了 GitHub Actions 的工作流程：

1. **构建阶段**: 对应 `Build application` 步骤
2. **打包阶段**: 对应 `Prepare artifacts` 步骤

通过本地测试，可以在推送到 GitHub 之前验证脚本的正确性，节省 CI/CD 时间。

## 高级用法

### 只测试打包脚本（不构建）

```bash
# 先手动构建
make build

# 然后只测试打包
bash scripts/test-local-build.sh dry-run macos
```

### 测试特定架构

```bash
# 测试 macOS arm64
ARCH=arm64 bash scripts/test-local-build.sh dry-run macos

# 测试 macOS x64
ARCH=x64 bash scripts/test-local-build.sh dry-run macos
```

## 注意事项

1. **Dry-run 模式**不会实际构建，只验证脚本逻辑
2. **Full 模式**会进行实际构建，可能需要较长时间
3. 在非 macOS 系统上无法实际构建 macOS 应用
4. 测试脚本会创建临时目录 `.test-build`，测试完成后会自动清理
