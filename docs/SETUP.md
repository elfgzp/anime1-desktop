# 项目设置和运行指南

## 环境要求

- **Node.js**: 18.x 或 20.x (LTS版本)
  - ⚠️ 不要使用 Node.js 24+ (better-sqlite3 不兼容)
- **npm**: 9.x 或更高
- **Python**: 3.10+ (用于编译原生模块)

## 安装步骤

### 1. 切换 Node.js 版本

使用 nvm:
```bash
nvm install 20
nvm use 20
```

验证版本:
```bash
node -v  # 应显示 v20.x.x
```

### 2. 安装依赖

```bash
cd ~/Github/anime1-desktop-electron
npm install
```

如果遇到 better-sqlite3 编译错误:
```bash
# macOS
brew install python

# 然后重试
npm rebuild better-sqlite3
```

### 3. 运行开发模式

```bash
npm run dev
```

### 4. 构建生产版本

```bash
npm run build
```

## 常见问题

### better-sqlite3 编译失败

**问题**: `use of undeclared identifier 'requires'`

**解决**: 降级 Node.js 到 20.x

```bash
nvm use 20
npm install
```

### 权限错误

```bash
# macOS/Linux
sudo chown -R $(whoami) ~/.npm
```

## 验证安装

运行测试命令:
```bash
# TypeScript 类型检查
npm run typecheck

# 构建
npm run build
```

## 项目结构

```
src/
├── main/           # Electron 主进程
├── preload/        # Preload 脚本
├── renderer/       # Vue 3 前端
└── shared/         # 共享类型和常量
```

## 功能状态

- [x] 基础设施 (类型、配置、窗口管理)
- [x] 数据层 (SQLite 数据库、迁移)
- [x] 爬虫服务 (Anime1、Bangumi)
- [x] 业务服务 (番剧缓存、下载)
- [x] 前端对接 (Store、首页)
- [ ] 完整 UI 组件
- [ ] 播放功能
- [ ] 打包发布
