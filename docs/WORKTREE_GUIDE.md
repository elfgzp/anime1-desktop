# Git Worktree 开发指南

## 📁 目录结构

```
~/Github/
├── anime1-desktop/              # 原项目目录 - main 分支
│   ├── src/                     # Python Flask 后端
│   ├── frontend/                # Vue 3 前端
│   └── ...
│
└── anime1-desktop-electron/     # Worktree - feature/electron-refactor 分支
    ├── src/                     # Electron + TypeScript (新)
    ├── ...
```

## 🚀 快速开始

### 1. 同时打开两个项目

```bash
# 终端 1: 原项目 (参考用)
code ~/Github/anime1-desktop

# 终端 2: Electron 重构项目 (开发用)
code ~/Github/anime1-desktop-electron
```

### 2. 对比逻辑

```bash
# 方法 1: 使用 VS Code 对比
# 在 VS Code 中打开文件夹对比功能

# 方法 2: 使用命令行对比特定文件
diff ~/Github/anime1-desktop/src/parser/anime1_parser.py \
     ~/Github/anime1-desktop-electron/src/main/services/crawler/anime1.ts

# 方法 3: 使用 git diff
cd ~/Github/anime1-desktop
git diff main feature/electron-refactor -- src/parser/anime1_parser.py
```

## 📋 Worktree 常用命令

```bash
# 查看所有 worktree
cd ~/Github/anime1-desktop
git worktree list

# 输出:
# /Users/gzp/Github/anime1-desktop           f9292b3 [main]
# /Users/gzp/Github/anime1-desktop-electron  f9292b3 [feature/electron-refactor]

# 在 main 分支新建终端
cd ~/Github/anime1-desktop
git checkout main

# 在 electron 分支新建终端
cd ~/Github/anime1-desktop-electron
# 已经在 feature/electron-refactor 分支

# 清理 worktree (当开发完成后)
cd ~/Github/anime1-desktop
git worktree remove ../anime1-desktop-electron
# 或强制删除 (如果有未提交修改)
git worktree remove -f ../anime1-desktop-electron
```

## 🔧 开发工作流

### 场景 1: 参考原逻辑实现新功能

```bash
# 1. 在 electron 项目中开发
cd ~/Github/anime1-desktop-electron

# 2. 需要参考原代码时，在另一个编辑器/窗口打开
code ~/Github/anime1-desktop/src/parser/anime1_parser.py

# 3. 在新项目中实现
code ~/Github/anime1-desktop-electron/src/main/services/crawler/anime1.ts
```

### 场景 2: 修复原项目的 Bug

```bash
# 1. 切换到原项目
cd ~/Github/anime1-desktop
git checkout main

# 2. 创建修复分支
git checkout -b fix/bug-name

# 3. 修复并提交
# ...

# 4. 切回 electron 开发
cd ~/Github/anime1-desktop-electron
```

### 场景 3: 同步原项目的更新

```bash
# 1. 原项目拉取最新代码
cd ~/Github/anime1-desktop
git pull origin main

# 2. Electron 项目同步
cd ~/Github/anime1-desktop-electron
git pull origin main
# 如果有冲突，解决冲突
```

## 📁 文件对应参考

| 原项目路径 | Electron 项目路径 | 说明 |
|-----------|------------------|------|
| `src/app.py` | `src/main/index.ts` | 应用入口 |
| `src/desktop.py` | `src/main/window.ts` | 桌面窗口管理 |
| `src/config.py` | `src/main/config/index.ts` | 配置管理 |
| `src/routes/anime.py` | `src/main/ipc/anime.ts` | 番剧 API |
| `src/routes/favorite.py` | `src/main/ipc/favorite.ts` | 收藏 API |
| `src/routes/settings.py` | `src/main/ipc/settings.ts` | 设置 API |
| `src/models/anime.py` | `src/shared/types/anime.ts` | 数据模型 |
| `src/models/database.py` | `src/main/services/database/index.ts` | 数据库 |
| `src/models/favorite.py` | `src/main/services/database/favorite.ts` | 收藏模型 |
| `src/parser/anime1_parser.py` | `src/main/services/crawler/anime1.ts` | Anime1 爬虫 |
| `src/parser/cover_finder.py` | `src/main/services/crawler/bangumi.ts` | Bangumi 爬虫 |
| `src/services/anime_cache_service.py` | `src/main/services/anime/cache.ts` | 缓存服务 |
| `src/services/video_downloader.py` | `src/main/services/download/index.ts` | 下载服务 |
| `src/services/update_checker.py` | `src/main/services/update/index.ts` | 更新服务 |
| `frontend/src/App.vue` | `src/renderer/App.vue` | Vue 根组件 |
| `frontend/src/views/Home.vue` | `src/renderer/views/Home.vue` | 首页 |
| `frontend/src/views/Detail.vue` | `src/renderer/views/Detail.vue` | 详情页 |
| `frontend/src/views/Favorites.vue` | `src/renderer/views/Favorites.vue` | 收藏页 |
| `frontend/src/composables/useTheme.js` | `src/renderer/composables/useTheme.ts` | 主题组合式 |
| `frontend/src/components/VideoPlayer.vue` | `src/renderer/components/VideoPlayer.vue` | 播放器 |

## 💡 开发技巧

### 1. 使用 VS Code 多根工作区

创建 `.vscode/anime1-refactor.code-workspace`:

```json
{
  "folders": [
    {
      "name": "📦 Original (Python)",
      "path": "../../anime1-desktop"
    },
    {
      "name": "⚡ Electron (TypeScript)",
      "path": ".."
    }
  ],
  "settings": {
    "files.exclude": {
      "**/node_modules": true,
      "**/.git": true
    }
  }
}
```

### 2. 快速跳转

```bash
# 添加别名到 ~/.zshrc 或 ~/.bashrc
alias anime1-original='cd ~/Github/anime1-desktop'
alias anime1-electron='cd ~/Github/anime1-desktop-electron'
alias anime1-compare='code ~/Github/anime1-desktop && code ~/Github/anime1-desktop-electron'
```

### 3. 文件搜索技巧

在 VS Code 中:
- `Cmd+T` - 快速打开文件
- 使用前缀区分项目:
  - `src/p` - 原项目的 parser
  - `main/s` - Electron 的 services

### 4. Git 对比

```bash
# 对比两个分支的特定目录
git diff main feature/electron-refactor -- src/parser/ > parser-changes.diff

# 对比特定文件
git diff main:src/parser/anime1_parser.py feature/electron-refactor:src/main/services/crawler/anime1.ts

# 查看某个文件的历史
cd ~/Github/anime1-desktop
git log -p --follow -- src/parser/anime1_parser.py
```

## ⚠️ 注意事项

1. **不要删除原目录**: worktree 依赖原仓库的 `.git` 目录
2. **分支独立性**: 两个目录的修改是独立的，提交前确认当前目录
3. **依赖隔离**: Python 和 Node.js 依赖完全独立
4. **IDE 配置**: 建议分别配置 VS Code workspace 设置

## 🔍 调试对比

### 运行原项目

```bash
cd ~/Github/anime1-desktop
make dev
# 或
python -m src.app --debug
```

### 运行 Electron 项目

```bash
cd ~/Github/anime1-desktop-electron
pnpm dev
```

### 同时运行对比

```bash
# 终端 1
cd ~/Github/anime1-desktop && make dev

# 终端 2
cd ~/Github/anime1-desktop-electron && pnpm dev
```

访问:
- 原项目: http://localhost:5172 或 webview
- Electron: Electron 窗口自动打开
