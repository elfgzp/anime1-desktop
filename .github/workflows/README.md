# GitHub Actions Workflows

## build.yml

主 CI/CD 工作流，处理测试、构建和发布。

### 触发条件

- **Push 到 main/master**: 运行测试并构建
- **Pull Request**: 运行测试
- **Tag (v*)**: 运行完整流程并发布到 GitHub Releases

### 任务

1. **test**: 运行单元测试和 E2E 测试
2. **build**: 在三个平台 (macOS, Ubuntu, Windows) 上构建应用
3. **release**: 创建 GitHub Release 并上传构建产物

### 环境变量

| 变量 | 说明 |
|------|------|
| `GITHUB_TOKEN` | 自动提供，用于发布到 GitHub Releases |

### Secrets (可选，用于代码签名)

#### macOS 签名

- `MACOS_CERTIFICATE`: Base64 编码的 Developer ID 证书
- `MACOS_CERTIFICATE_PWD`: 证书密码
- `MACOS_CERTIFICATE_NAME`: 证书名称
- `MACOS_NOTARIZATION_APPLE_ID`: Apple ID
- `MACOS_NOTARIZATION_TEAM_ID`: 开发者团队 ID
- `MACOS_NOTARIZATION_PWD`: 应用专用密码

#### Windows 签名

- `WINDOWS_CERTIFICATE`: Base64 编码的代码签名证书
- `WINDOWS_CERTIFICATE_PASSWORD`: 证书密码

## 添加 Secrets

1. 前往 GitHub 仓库设置: `Settings > Secrets and variables > Actions`
2. 点击 "New repository secret"
3. 添加所需的 secrets

## 本地测试

使用 [act](https://github.com/nektos/act) 本地测试工作流:

```bash
# 运行测试任务
act -j test

# 运行构建任务 (需要 Docker)
act -j build
```
