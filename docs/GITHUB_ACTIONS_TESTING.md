# GitHub Actions 测试指南

## 🔧 前置准备

### 1. 安装 GitHub CLI

```bash
# macOS
brew install gh

# Windows (winget)
winget install --id GitHub.cli

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### 2. 登录 GitHub CLI

```bash
gh auth login
# 选择:
# - GitHub.com
# - HTTPS
# - 浏览器登录 (推荐)
```

### 3. 验证仓库连接

```bash
# 检查当前仓库
gh repo view

# 应该显示: elfgzp/anime1-desktop 或 gzp/anime1-desktop
```

---

## 🚀 测试 Actions 的方法

### 方法一：推送到分支触发 Actions（推荐）

```bash
# 1. 确保所有更改已提交
git add .
git commit -m "feat: add CI/CD build and release workflow

- Add GitHub Actions workflow for automated builds
- Configure Electron Forge for cross-platform packaging
- Add code signing support for macOS and Windows
- Integrate auto-updater with GitHub Releases
- Add mock updater testing system"

# 2. 推送到当前分支 (electron-forge)
git push origin electron-forge

# 3. 使用 gh 命令查看 workflow 运行状态
gh run list --limit 5

# 4. 实时监控最新运行
gh run watch
```

### 方法二：创建 PR 触发 Actions

```bash
# 1. 推送分支
git push origin electron-forge

# 2. 创建 PR
gh pr create --title "Add CI/CD Build and Release Workflow" \
  --body "This PR adds:
- GitHub Actions workflow for automated builds
- Cross-platform packaging (Windows, macOS, Linux)
- Auto-updater integration
- Mock testing system for updater"

# 3. PR 创建后会自动触发 Actions，查看状态
gh pr checks

# 4. 查看详细日志
gh run view $(gh run list --limit 1 --json databaseId -q '.[0].databaseId')
```

### 方法三：本地测试 Workflow（使用 act）

```bash
# 1. 安装 act (本地 GitHub Actions 运行器)
brew install act

# 2. 测试 workflow 语法
act -l

# 3. 运行测试 job
act -j test

# 4. 运行构建 job（特定平台）
act -j build --matrix os:ubuntu-latest

# 5. 完整测试（会下载大镜像，耗时较长）
act push
```

---

## 📋 详细的测试步骤

### Step 1: 验证 Workflow 文件语法

```bash
# 使用 GitHub API 验证（无需推送）
gh api repos/:owner/:repo/actions/workflows | jq '.workflows[] | {name, path, state}'

# 或者使用 actionlint 工具
brew install actionlint
actionlint .github/workflows/build.yml
```

### Step 2: 提交并推送代码

```bash
# 添加所有新文件
git add .github/ assets/ docs/ entitlements.plist scripts/ src/
git add forge.config.js package.json README.md BUILD*.md RELEASE*.md

# 提交
git commit -m "feat: add complete CI/CD and auto-updater system

Build System:
- Add GitHub Actions workflow for automated builds
- Configure Electron Forge for cross-platform packaging
- Add code signing support (macOS & Windows)
- Configure artifact upload and release creation

Auto Updater:
- Integrate electron-updater with GitHub Releases
- Add comprehensive mock testing system
- Create UI testing panel for updater
- Add 20 unit tests for mock updater

Documentation:
- Add BUILD.md with detailed build instructions
- Add BUILD_CHECKLIST.md for release preparation
- Add CI/CD architecture documentation
- Create updater testing guides"

# 推送
git push origin electron-forge
```

### Step 3: 使用 gh 命令监控 Actions

```bash
# 查看最近的工作流运行
gh run list

# 查看最新运行的详细信息
gh run view

# 查看特定工作流的日志
gh run view --log

# 查看失败的步骤
gh run view --log-failed

# 下载构建产物（artifact）
gh run download <run-id> --name build-ubuntu-latest

# 重新运行失败的工作流
gh run rerun <run-id>
```

### Step 4: 测试特定功能

```bash
# 只运行测试 job（如果支持 workflow_dispatch）
gh workflow run build.yml --ref electron-forge

# 查看 workflow 定义
gh workflow view build

# 启用/禁用 workflow
gh workflow enable build
gh workflow disable build
```

---

## 🧪 测试场景

### 场景 1: 测试基本构建（Push 到分支）

```bash
# 推送后会自动触发 build workflow
git push origin electron-forge

# 查看运行状态（等待 Test job 完成）
gh run watch

# 预期结果：
# ✓ Test job 通过（运行单元测试和 E2E 测试）
# ✓ Build jobs 为三个平台生成安装包
```

### 场景 2: 测试 Release 流程（创建 Tag）

```bash
# 创建测试 tag（注意：这会真的发布 Release）
git tag -a v0.1.0-test -m "Test release workflow"
git push origin v0.1.0-test

# 监控发布流程
gh run watch

# 查看创建的 Release
gh release list
gh release view v0.1.0-test

# 如果测试成功，删除测试 tag 和 release
gh release delete v0.1.0-test --cleanup-tag -y
```

### 场景 3: 测试 PR 流程

```bash
# 创建 PR
gh pr create --fill

# 查看 PR 的 checks
gh pr checks

# 查看详细日志
gh pr checks --watch
```

---

## 🔍 常见问题排查

### 问题 1: Workflow 未触发

```bash
# 检查 workflow 文件是否存在语法错误
cat .github/workflows/build.yml | yq '.'

# 检查是否正确推送
git log --oneline -5

# 查看 GitHub 上的 workflow 状态
gh api repos/:owner/:repo/actions/workflows | jq
```

### 问题 2: Test job 失败

```bash
# 查看失败日志
gh run view --log-failed

# 本地运行测试验证
npm test
npm run test:e2e

# 检查是否有未提交的更改
gh run view --log | grep -A 20 "Run unit tests"
```

### 问题 3: Build job 失败

```bash
# 下载失败日志
gh run view --log > /tmp/run.log
cat /tmp/run.log | grep -i error

# 本地构建测试
npm run make
```

### 问题 4: 权限错误

```bash
# 检查仓库权限
gh api repos/:owner/:repo | jq '.permissions'

# 检查 GITHUB_TOKEN 权限
gh run view --log | grep -i "token\|permission\|403"
```

---

## 📊 验证清单

推送代码后，验证以下项目：

- [ ] `gh run list` 显示新的 workflow run
- [ ] Test job 成功完成（绿色 ✓）
- [ ] Build jobs 为三个平台都成功
- [ ] Artifacts 被正确上传（非 tag push）
- [ ] 如果推送了 tag，Release 被正确创建

---

## 🔐 安全注意事项

1. **Secrets**: 代码签名相关的 secrets 不会显示在日志中
2. **GITHUB_TOKEN**: 自动提供，无需手动设置
3. **分支保护**: 建议在合并前要求 checks 通过

---

## 💡 实用技巧

### 使用 gh alias 简化命令

```bash
# 创建快捷命令
gh alias set runs 'run list'
gh alias set watch 'run watch'
gh alias set logs 'run view --log'

# 使用
gh runs
gh watch
gh logs
```

### 自动监控推送

```bash
# 推送并立即监控
git push origin electron-forge && gh run watch
```

### 筛选失败的运行

```bash
gh run list --status failure
```

---

## 📚 参考文档

- [GitHub CLI 文档](https://cli.github.com/manual/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [act 本地测试工具](https://github.com/nektos/act)

---

## ✅ 快速测试命令汇总

```bash
# 1. 推送代码
git push origin electron-forge

# 2. 查看运行列表
gh run list

# 3. 查看最新运行的日志
gh run view --log

# 4. 实时监控
gh run watch

# 5. 下载构建产物
gh run download <run-id> -n build-ubuntu-latest
```
