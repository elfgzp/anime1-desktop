# 更好的方案：移除 SQLite，使用纯 JSON 存储

## 问题分析

better-sqlite3 的问题：
- ❌ 维护滞后，跟不上 Node.js 更新
- ❌ 需要编译原生模块，安装困难
- ❌ Electron 打包复杂

## 更好的方案：electron-store

对于 Anime1 Desktop 这种应用：
- 收藏数据：几百条
- 播放历史：几千条
- 设置：几十条

**数据量很小，JSON 文件完全够用！**

### 优势

| 特性 | better-sqlite3 | electron-store |
|------|---------------|----------------|
| 安装 | 需要编译 ❌ | 纯 JS，即装即用 ✅ |
| Node.js 兼容 | 滞后 ❌ | 完美支持 ✅ |
| 打包 | 复杂 ❌ | 简单 ✅ |
| 备份 | 需要工具 ❌ | 直接复制 JSON ✅ |
| 调试 | 需要 DB 工具 ❌ | 直接看 JSON ✅ |
| 性能（小数据） | 快 | 一样快 |

### 实现方案

```typescript
// 用 electron-store 替代 SQLite
import Store from 'electron-store'

interface StoreSchema {
  favorites: FavoriteAnime[]
  playbackHistory: PlaybackHistory[]
  coverCache: Record<string, CoverCache>
  settings: AppSettings
}

const store = new Store<StoreSchema>({
  defaults: {
    favorites: [],
    playbackHistory: [],
    coverCache: {},
    settings: DEFAULT_APP_SETTINGS
  }
})

// 使用
store.get('favorites')
store.set('favorites', [...])
```

## 数据持久化方案对比

### 当前方案（SQLite）
```
主进程 (Node.js) 
    ↓
better-sqlite3 (C++)
    ↓
anime1.db (二进制)
```

### 新方案（JSON）
```
主进程 (Node.js)
    ↓
electron-store (纯 JS)
    ↓
config.json (文本)
```

## 迁移计划

1. 移除 better-sqlite3 依赖
2. 使用 electron-store 重新实现数据层
3. 保留数据迁移功能（从旧 SQLite 导入）

## 结论

**对于中小型桌面应用，JSON 存储是更好的选择：**
- 零编译
- 零配置
- 易于调试
- 备份简单
- 性能足够

SQLite 只在大数据量（10万+ 条记录）时才显出优势。
