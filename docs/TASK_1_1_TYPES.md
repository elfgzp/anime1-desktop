# Task 1.1: 完善 TypeScript 类型定义

## 执行步骤

### Step 1: 查看原项目参考代码

```bash
# 在另一个窗口打开参考
open ~/Github/anime1-desktop/src/models/anime.py
open ~/Github/anime1-desktop/src/models/favorite.py
open ~/Github/anime1-desktop/src/models/playback_history.py
open ~/Github/anime1-desktop/src/models/cover_cache.py
```

### Step 2: 分析已有类型

当前 `src/shared/types/anime.ts` 已有基础类型，需要补充：
- API 请求/响应类型
- 设置类型
- 下载任务完整类型

### Step 3: 实现

我会帮你完成以下文件的完善：
1. `src/shared/types/anime.ts` - 补充缺失类型
2. `src/shared/types/api.ts` - 新建：API 类型
3. `src/shared/types/settings.ts` - 新建：设置类型
4. `src/shared/types/index.ts` - 统一导出

### Step 4: 验证

```bash
cd ~/Github/anime1-desktop-electron
pnpm typecheck
```

---

需要我现在执行 **Task 1.1** 吗？或者你想从其他任务开始？

## 可选任务

| 任务 | 预计时间 | 说明 |
|-----|---------|------|
| **Task 1.1** | 2h | 类型定义（基础） |
| **Task 1.2** | 1h | 配置文件（基础） |
| **Task 2.1** | 3h | 数据库服务（核心） |
| **Task 3.1** | 2h | HTTP 客户端（基础） |
| **Task 3.2** | 3h | Anime1 列表解析（核心） |

建议从 **Task 1.1** 或 **Task 2.1** 开始，这两个是后续所有任务的基础。
