# Anime1 Desktop (Electron 重构版)

使用 Electron + Vue 3 + TypeScript 重构的 Anime1 Desktop 应用。

## 📁 项目结构

```
├── src/
│   ├── main/                    # Electron 主进程
│   │   ├── index.ts             # 入口
│   │   ├── window.ts            # 窗口管理
│   │   ├── ipc/                 # IPC 处理器
│   │   └── services/            # 核心服务
│   │       ├── anime/           # 番剧服务
│   │       ├── crawler/         # 爬虫服务 (axios + cheerio)
│   │       ├── database/        # 数据库 (better-sqlite3)
│   │       ├── download/        # 下载服务
│   │       └── update/          # 更新服务
│   │
│   ├── preload/                 # Preload 脚本
│   │   └── index.ts             # IPC API 暴露
│   │
│   ├── renderer/                # 渲染进程 (Vue 3)
│   │   ├── main.ts              # Vue 入口
│   │   ├── App.vue              # 根组件
│   │   ├── views/               # 页面视图
│   │   ├── router/              # 路由
│   │   └── stores/              # Pinia Store
│   │
│   └── shared/                  # 共享代码
│       └── types/               # TypeScript 类型
│
├── docs/                        # 文档
│   ├── ELECTRON_REFACTOR_TECH_SPEC.md   # 技术方案
│   ├── ELECTRON_REFACTOR_TODO.md        # 任务清单
│   └── WORKTREE_GUIDE.md                # Worktree 使用指南
│
├── resources/                   # 资源文件
└── build/                       # 构建配置
```

## 🚀 开发指南

### 环境准备

```bash
# 安装 Node.js 20+
nvm use 20

# 安装依赖
pnpm install
# 或
npm install
```

### 开发模式

```bash
# 同时启动 Electron 和 Vite 开发服务器
pnpm dev
```

### 构建

```bash
# 构建所有平台
pnpm build

# 构建特定平台
pnpm build:mac
pnpm build:win
pnpm build:linux
```

## 📋 开发任务

详见 [ELECTRON_REFACTOR_TODO.md](./docs/ELECTRON_REFACTOR_TODO.md)

## 🔧 与原项目的对应关系

| 原项目 (Python/Flask) | 新项目 (Electron/TS) | 说明 |
|---------------------|---------------------|------|
| `src/app.py` | `src/main/index.ts` | 应用入口 |
| `src/desktop.py` | `src/main/window.ts` | 窗口管理 |
| `src/routes/*.py` | `src/main/ipc/*.ts` | API 接口 |
| `src/models/*.py` | `src/shared/types/*.ts` | 数据模型 |
| `src/parser/*.py` | `src/main/services/crawler/*.ts` | 爬虫 |
| `src/services/*.py` | `src/main/services/*/*.ts` | 服务层 |
| `frontend/src/*.vue` | `src/renderer/*.vue` | 前端组件 |

## 📚 相关文档

- [技术方案文档](./docs/ELECTRON_REFACTOR_TECH_SPEC.md) - 详细的技术架构设计
- [Worktree 使用指南](./docs/WORKTREE_GUIDE.md) - 如何与原项目对比开发

## 🔄 Worktree 开发工作流

本项目使用 Git Worktree 与原项目并行开发：

```bash
# 原项目（参考用）
~/Github/anime1-desktop              # main 分支

# 新项目（开发用）  
~/Github/anime1-desktop-electron     # feature/electron-refactor 分支
```

同时打开两个目录进行对比开发：

```bash
# 终端 1: 原项目（启动旧版本参考）
cd ~/Github/anime1-desktop
make dev

# 终端 2: 新项目（开发新版本）
cd ~/Github/anime1-desktop-electron
pnpm dev
```

## 📝 注意事项

1. **类型安全**: 使用 TypeScript 严格模式，确保类型安全
2. **IPC 安全**: 所有 IPC 通信通过 Preload 脚本白名单控制
3. **数据库迁移**: 自动迁移原项目 SQLite 数据
4. **依赖管理**: 使用 pnpm 进行依赖管理

## 📄 License

MIT
