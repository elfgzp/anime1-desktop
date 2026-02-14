# Build & Release Setup Checklist

## ✅ 已完成的配置

### 基础配置
- [x] `package.json` - 添加 repository 信息
- [x] `forge.config.js` - 优化构建配置，支持代码签名
- [x] `entitlements.plist` - macOS 签名权限配置
- [x] `.github/workflows/build.yml` - CI/CD 工作流
- [x] `@electron-forge/publisher-github` - GitHub 发布器

### 文档
- [x] `README.md` - 项目主文档
- [x] `BUILD.md` - 详细构建指南
- [x] `BUILD_CHECKLIST.md` - 本文件
- [x] `assets/README.md` - 图标资源说明
- [x] `.github/workflows/README.md` - 工作流说明
- [x] `scripts/setup-secrets.sh` - Secrets 设置辅助脚本

---

## 🔧 发布前需要完成的步骤

### 1. 添加应用图标

```bash
# 在 assets/ 目录下放置以下图标文件:
assets/
├── icon.ico      # Windows 图标 (256x256 多尺寸)
├── icon.icns     # macOS 图标 (1024x1024 多尺寸)
├── icon.png      # Linux 图标 (1024x1024)
└── installer.gif # (可选) Windows 安装动画
```

创建图标的详细方法见 `assets/README.md`。

### 2. 配置 GitHub Secrets (可选但推荐)

用于代码签名，确保应用不被系统安全警告拦截。

#### macOS 签名证书

1. 加入 [Apple Developer Program](https://developer.apple.com/programs/) ($99/年)
2. 创建 Developer ID Application 证书
3. 导出为 .p12 文件
4. 编码并添加到 GitHub Secrets:

```bash
# 编码证书
base64 -i certificate.p12 -o certificate.base64

# 或使用脚本
./scripts/setup-secrets.sh
```

需要添加的 Secrets:
- `MACOS_CERTIFICATE` - .p12 文件的 base64 编码
- `MACOS_CERTIFICATE_PWD` - 证书密码
- `MACOS_CERTIFICATE_NAME` - 证书名称
- `MACOS_NOTARIZATION_APPLE_ID` - Apple ID
- `MACOS_NOTARIZATION_TEAM_ID` - 团队 ID
- `MACOS_NOTARIZATION_PWD` - 应用专用密码

#### Windows 签名证书

1. 从可信 CA 购买代码签名证书
2. 导出为 .pfx 文件
3. 编码并添加到 GitHub Secrets:

需要添加的 Secrets:
- `WINDOWS_CERTIFICATE` - .pfx 文件的 base64 编码
- `WINDOWS_CERTIFICATE_PASSWORD` - 证书密码

> **注意**: 没有签名证书也可以构建和发布，但用户在安装时会看到安全警告。

### 3. 测试构建

本地测试构建是否正常工作:

```bash
# 安装依赖
npm install

# 运行测试
npm test

# 构建当前平台
npm run make
```

检查 `out/make/` 目录下是否生成了安装包。

### 4. 首次发布

```bash
# 更新版本号
npm version patch  # 1.0.0 -> 1.0.1

# 或者
npm version minor  # 1.0.0 -> 1.1.0

# 或者
npm version major  # 1.0.0 -> 2.0.0

# 推送标签触发构建
git push origin main --tags
```

GitHub Actions 将自动:
1. 运行测试
2. 构建所有平台 (Windows, macOS, Linux)
3. 签名应用 (如果配置了 Secrets)
4. 创建 GitHub Release
5. 上传构建产物

### 5. 验证自动更新

1. 安装旧版本应用
2. 发布新版本 (tag)
3. 检查应用是否检测到更新
4. 测试更新安装流程

---

## 📋 快速参考

### 常用命令

```bash
# 开发
npm start

# 测试
npm test
npm run test:e2e

# 构建
npm run make
npm run package

# 发布 (本地测试)
npm run publish
```

### 构建输出

构建产物保存在 `out/make/` 目录:

```
out/make/
├── squirrel.windows/
│   ├── Anime1Desktop-1.0.0 Setup.exe    # Windows 安装包
│   └── ...
├── zip/
│   └── darwin/
│       └── Anime1Desktop-1.0.0.zip      # macOS 压缩包
├── deb/
│   └── anime1-desktop_1.0.0_amd64.deb   # Debian/Ubuntu 安装包
└── rpm/
    └── anime1-desktop-1.0.0.x86_64.rpm  # Fedora/RHEL 安装包
```

### 故障排除

#### 构建失败

```bash
# 清理并重新安装
rm -rf node_modules out
npm install
npm run make
```

#### 内存不足

```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run make
```

#### 原生模块问题

```bash
npx electron-rebuild
```

---

## 📝 版本规范

使用 [语义化版本](https://semver.org/lang/zh-CN/):

- `MAJOR.MINOR.PATCH` (例如: `1.2.3`)
- **MAJOR**: 不兼容的 API 更改
- **MINOR**: 向后兼容的功能添加
- **PATCH**: 向后兼容的问题修复

预发布版本:
- `1.0.0-alpha.1`
- `1.0.0-beta.2`
- `1.0.0-rc.1`

---

## 🔗 相关链接

- [Electron Forge 文档](https://www.electronforge.io/)
- [electron-updater 文档](https://www.electron.build/auto-update.html)
- [Apple Developer 文档](https://developer.apple.com/documentation/xcode/notarizing_macos_software_before_distribution)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
