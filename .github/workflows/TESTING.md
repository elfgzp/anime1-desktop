# GitHub Actions 测试指南

本文档说明如何测试 GitHub Actions workflow 和脚本配置。

## 官方推荐的测试方式

根据 [GitHub 官方文档](https://docs.github.com/en/actions/how-tos/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow)，推荐使用以下方式测试：

### 1. 使用 workflow_dispatch 手动触发（推荐）

这是 GitHub 官方推荐的方式，无需打 tag 即可测试。

#### 在 GitHub Web UI 中测试

1. 进入仓库的 **Actions** 标签页
2. 选择 **Build and Release** 或 **Test Build** workflow
3. 点击右侧的 **Run workflow** 按钮
4. 选择分支（通常是 `main` 或 `master`）
5. 填写参数（可选）：
   - **version**: 测试版本号，例如 `1.0.0-test`
   - **create_release**: 是否创建 Release（测试时建议设为 `false`）
   - **test_mode**: 是否只测试单个平台（暂未实现，未来可优化）
6. 点击 **Run workflow** 开始构建

#### 使用 GitHub CLI 测试

```bash
# 安装 GitHub CLI（如果还没有）
# macOS: brew install gh
# Linux: 参考 https://cli.github.com/manual/installation

# 登录 GitHub
gh auth login

# 手动触发 workflow
gh workflow run "Build and Release" \
  --ref main \
  -f version=1.0.0-test \
  -f create_release=false

# 查看运行状态
gh run list --workflow="Build and Release"
```

#### 使用 REST API 测试

```bash
# 需要 GitHub Personal Access Token (PAT)
# 创建 token: https://github.com/settings/tokens
# 需要 workflow 权限

curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/release.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "version": "1.0.0-test",
      "create_release": "false"
    }
  }'
```

### 2. 使用测试分支触发

推送到 `test-build` 分支会自动触发 **Test Build** workflow：

```bash
git checkout -b test-build
git push origin test-build
```

### 3. 创建测试 Tag（不推荐用于日常测试）

如果必须测试 tag 触发流程：

```bash
# 创建测试 tag
git tag v0.0.1-test
git push origin v0.0.1-test

# 测试完成后删除
git push origin --delete v0.0.1-test
git tag -d v0.0.1-test
```

## 测试检查清单

测试时请检查以下内容：

### ✅ 构建阶段

- [ ] 所有平台的构建是否成功
- [ ] 构建产物是否正确生成：
  - Windows: `anime1-windows-x64.zip`
  - macOS: `anime1-macos-x64.dmg` 和 `anime1-macos-arm64.dmg`
  - Linux: `anime1-linux-x64.tar.gz`
- [ ] 脚本是否正常执行：
  - `scripts/prepare_artifacts.py` 是否正确打包
  - `scripts/create_dmg.py` 是否正确创建 DMG（macOS）
  - `scripts/prepare_release_assets.py` 是否正确收集文件

### ✅ Release 阶段（如果启用）

- [ ] Release 是否创建成功
- [ ] Release 说明是否正确（从 CHANGELOG.md 提取）
- [ ] 所有构建产物是否都上传到 Release
- [ ] Release 链接和下载说明是否正确

### ✅ 脚本功能

- [ ] 架构检测是否正确（x64 vs arm64）
- [ ] 文件命名是否正确（包含架构信息）
- [ ] DMG 创建是否成功（macOS）
- [ ] ZIP/TAR.GZ 打包是否正确

## 常见问题

### Q: 手动触发时 Release 没有创建？

A: 这是正常的。Release 只在以下情况创建：
- Push tag 触发时自动创建
- 手动触发且勾选 "create_release" 选项

### Q: 如何只测试单个平台？

A: 可以临时修改 workflow 文件，注释掉其他平台的 matrix 配置，只保留一个平台。

### Q: 测试时如何避免创建真实的 Release？

A: 手动触发时，确保 `create_release` 参数设为 `false`（默认值）。

## 参考文档

- [GitHub Actions: 手动运行 workflow](https://docs.github.com/en/actions/how-tos/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow)
- [GitHub Actions: 触发 workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [GitHub CLI: workflow 命令](https://cli.github.com/manual/gh_workflow)
