# AI Agent 开发指引

本文档为 AI Agent（如 Kimi、Claude 等）提供开发指引，帮助快速理解和修改本项目。

## 项目概述

Anime1 Desktop 是一个基于 Electron + Vue 3 的桌面应用，用于浏览和播放 Anime1 的番剧内容。

### 技术栈

- **Electron 40.x** - 桌面应用框架
- **Vue 3.5** + **TypeScript** - 前端框架
- **Vite 5.x** - 构建工具
- **SQLite (libsql)** - 本地数据库
- **Playwright** - E2E 测试

### 目录结构

```
├── src/
│   ├── main/           # Electron 主进程
│   │   ├── index.ts    # 入口文件
│   │   ├── ipc/        # IPC 处理器
│   │   ├── services/   # 业务服务
│   │   └── window.ts   # 窗口管理
│   ├── renderer/       # 渲染进程 (Vue 应用)
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/     # Pinia Store
│   │   └── router/     # Vue Router
│   ├── preload/        # Preload 脚本
│   │   └── index.cjs   # CommonJS 格式!
│   └── shared/         # 共享类型和工具
├── e2e/                # Playwright E2E 测试
├── scripts/            # 构建和工具脚本
└── dist-electron/      # 构建输出
```

## 关键注意事项

### ⚠️ Preload 脚本格式（重要！）

**`src/preload/index.cjs` 必须是纯 JavaScript + CommonJS 格式！**

```javascript
// ✅ 正确 - 使用 CommonJS
const { contextBridge, ipcRenderer } = require('electron')

// ❌ 错误 - 不要使用 ES Module
// import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // ...
})
```

**原因**：
- Vite 构建 preload 时会产生 ESM 格式的问题
- Electron 要求 preload 使用 CommonJS
- 项目使用 `verify-preload.cjs` 确保格式正确

**验证方法**：
```bash
npm run dev
# 检查控制台是否显示: window.api should be available
```

### ⚠️ MCP 工具无法直接测试 Electron

**Chrome DevTools MCP 工具无法直接连接到 Electron 渲染进程！**

原因：
- MCP 连接的是普通浏览器页面
- Electron 的 `window.api` 只在真实渲染进程中存在
- 直接访问 `http://localhost:5173/` 会看到 `window.api is undefined` 的错误

**正确的测试方式**：
1. 使用 Playwright E2E 测试（见下文）
2. 手动在 Electron 窗口中按 `Cmd+Option+I` 打开 DevTools 检查

## 测试方法

### 1. Playwright E2E 测试（推荐）

项目已配置 Playwright 测试，可以直接测试真实 Electron 应用：

```bash
# 运行冒烟测试
npm run test:e2e:smoke

# 运行所有测试
npm run test:e2e

# 有头模式（可以看到窗口）
npm run test:e2e:headed

# 调试模式
npm run test:e2e:debug
```

**测试文件位置**：`e2e/tests/`

**关键测试**：
- `smoke.spec.ts` - 冒烟测试，验证应用基本功能
- `test-preload.spec.ts` - Preload 脚本测试

### 2. 手动验证

在真实 Electron 窗口中验证：

1. 启动应用：`npm run dev`
2. 按 `Cmd+Option+I` 打开 DevTools
3. 在 Console 中输入：
   ```javascript
   window.api
   // 应该返回完整的 API 对象，不是 undefined
   
   await window.api.anime.getList({ page: 1 })
   // 应该返回番剧列表
   ```

### 3. 主进程日志

查看 Electron 主进程的日志输出：
- 启动时会显示 `[Preload] API exposed successfully`
- 如果没有，说明 preload 脚本有问题

## 常见问题和解决方案

### Preload 脚本不生效

**症状**：`window.api is undefined`

**解决**：
```bash
# 1. 停止应用
# 2. 清理构建产物
rm -rf dist-electron/preload/

# 3. 验证并重新启动
npm run dev
```

### Vite HMR 覆盖 Preload

**症状**：修改后 preload 恢复成错误格式

**解决**：项目已配置 `verify-preload.cjs` 在 `npm run dev` 前自动运行，确保 preload 文件正确。

### TypeScript 类型错误

**症状**：修改后出现类型错误

**解决**：
```bash
# 运行类型检查
npm run typecheck

# 自动修复
npm run lint
```

## 开发流程

### 添加新功能

1. **主进程**（如果需要）：
   - 在 `src/main/ipc/index.ts` 添加 IPC 处理器
   - 在 `src/preload/index.cjs` 暴露 API

2. **渲染进程**：
   - 在 `src/renderer/views/` 添加页面（如需要）
   - 在 `src/renderer/stores/` 添加 Store 逻辑
   - 更新路由（如需要）

3. **测试**：
   - 在 `e2e/tests/` 添加测试用例
   - 运行 `npm run test:e2e:smoke` 验证

### 调试技巧

**主进程调试**：
```bash
# 启动时启用调试
ELECTRON_ENABLE_LOGGING=1 npm run dev
```

**渲染进程调试**：
- 窗口内按 `Cmd+Option+I` 打开 DevTools
- 或使用 Playwright 的 `page.pause()` 断点

**Preload 调试**：
```javascript
// 在 preload 中添加日志
console.log('[Preload] Script executing...')
console.log('[Preload] API:', api)
```

## 重要文件

| 文件 | 说明 |
|------|------|
| `src/preload/index.cjs` | Preload 脚本（CommonJS 格式！） |
| `src/main/index.ts` | 主进程入口 |
| `src/main/window.ts` | 窗口创建逻辑 |
| `src/renderer/stores/anime.ts` | 番剧 Store |
| `vite.config.ts` | Vite 配置（含 preload 处理） |
| `scripts/verify-preload.cjs` | Preload 验证脚本 |
| `e2e/fixtures/index.ts` | Playwright Fixtures |

## 联系方式

如有问题，请查看：
- `docs/` 目录下的技术文档
- `e2e/README.md` 测试文档
- GitHub Issues
