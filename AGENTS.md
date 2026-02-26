# Anime1 Desktop 项目约定

## ⚠️ 重要：Preload 文件约定

### 唯一真相源
- **唯一文件**: `src/preload/index.cjs`
- **禁止创建**: `src/preload/index.ts` 或任何其他 preload 文件

### 为什么只有 .cjs 文件？
1. Electron preload 必须是 CommonJS 格式
2. Vite 构建流程直接复制此文件，不做编译
3. 创建 .ts 文件会导致类型和实际运行代码不同步

### 修改 Preload API 的正确流程

1. **修改 IPC 频道** (`src/preload/index.cjs`):
   ```javascript
   // 1. 在 validChannels 数组中添加频道
   const validChannels = [
     'anime:list',
     'anime:newApi',  // <-- 添加新频道
   ]
   
   // 2. 在 api 对象中添加方法
   anime: {
     getList: (params) => invoke('anime:list', params),
     newApi: (params) => invoke('anime:newApi', params),  // <-- 添加新方法
   }
   ```

2. **更新类型定义** (`src/shared/types/api.ts`):
   ```typescript
   export interface ElectronAPI {
     anime: {
       getList: (params) => Promise<any>
       newApi: (params) => Promise<any>  // <-- 添加类型
     }
   }
   ```

3. **添加 IPC 处理程序** (`src/main/ipc/index.ts`):
   ```typescript
   ipcMain.handle('anime:newApi', async (_, params) => {
     // 处理逻辑
   })
   ```

### 构建流程
```
1. npm run dev/build
2. vite-plugin-electron 触发 copyPreloadPlugin
3. 复制 src/preload/index.cjs → dist-electron/preload/index.cjs
4. 删除可能生成的 dist-electron/preload/index.js
5. verify-preload.cjs 检查是否存在重复的 .ts 文件
```

### 常见错误
```
TypeError: window.api.anime.xxx is not a function
```
**原因**: 只修改了 TypeScript 文件，没有修改 .cjs 文件  
**解决**: 只修改 `src/preload/index.cjs`，删除任何 .ts 文件

## 技术栈
- Electron 40.4.0
- Vue 3.5.28
- TypeScript 5.9.3
- Vite 5.4.21
- better-sqlite3 / libsql
