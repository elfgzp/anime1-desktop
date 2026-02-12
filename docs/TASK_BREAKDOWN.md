# Electron 重构任务拆分

> 按依赖关系和优先级排序，每个任务都可独立执行

---

## 🚀 快速开始（先执行这个）

```bash
# 1. 进入项目
cd ~/Github/anime1-desktop-electron

# 2. 安装依赖
pnpm install

# 3. 验证运行
pnpm dev
```

---

## Phase 1: 基础设施 (Week 1)

### Task 1.1: 完善 TypeScript 类型定义
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: 无

**输入** (参考原项目):
- `src/models/anime.py` - Anime 数据模型
- `src/models/favorite.py` - 收藏模型
- `src/models/playback_history.py` - 播放历史

**输出** (新实现):
- `src/shared/types/anime.ts` - 完善已有类型
- `src/shared/types/api.ts` - API 请求/响应类型
- `src/shared/types/settings.ts` - 设置相关类型

**检查点**:
- [ ] 所有类型定义完整
- [ ] 与原模型字段一一对应
- [ ] 导出到 `src/shared/types/index.ts`

---

### Task 1.2: 创建配置文件和常量
**状态**: ⏳ 待开始  
**预计耗时**: 1h  
**依赖**: 无

**输入** (参考原项目):
- `src/config.py` - 配置项
- `src/constants/*.py` - 常量定义

**输出** (新实现):
- `src/shared/constants/app.ts` - 应用常量
- `src/shared/constants/api.ts` - API 端点
- `src/main/config/index.ts` - 运行时配置

**检查点**:
- [ ] 所有 URL、端口、超时配置迁移
- [ ] 支持环境变量覆盖

---

### Task 1.3: 完善窗口管理功能
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: 无

**输入** (参考原项目):
- `src/desktop.py` - 窗口相关代码

**输出** (新实现):
- `src/main/window.ts` - 补充系统托盘
- 窗口状态持久化 (electron-store)
- 全局快捷键注册

**检查点**:
- [ ] 最小化到托盘
- [ ] 窗口尺寸/位置记忆
- [ ] Cmd/Ctrl + Shift + D 显示/隐藏

---

## Phase 2: 数据层 (Week 1-2)

### Task 2.1: 数据库服务完善
**状态**: ⏳ 待开始  
**预计耗时**: 3h  
**依赖**: Task 1.1

**输入** (参考原项目):
- `src/models/database.py`
- `src/models/favorite.py`
- `src/models/cover_cache.py`
- `src/models/playback_history.py`

**输出** (新实现):
- `src/main/services/database/index.ts` - 完善已有骨架

**具体功能**:
```typescript
// 需要实现的方法
- getFavorites()           // 获取收藏列表
- addFavorite()            // 添加收藏
- removeFavorite()         // 移除收藏
- isFavorite()             // 检查是否已收藏
- getCoverCache()          // 获取封面缓存
- setCoverCache()          // 设置封面缓存
- getPlaybackHistory()     // 获取播放历史
- addPlaybackHistory()     // 添加播放记录
- getSetting() / setSetting()  // 设置读写
```

**检查点**:
- [ ] 所有方法单元测试通过
- [ ] 与原数据库 schema 兼容

---

### Task 2.2: 数据迁移脚本
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 2.1

**输入**:
- 原项目 SQLite 数据库文件路径

**输出**:
- `src/main/services/database/migrate.ts`
- 自动检测原数据库并导入

**检查点**:
- [ ] 能读取原数据库
- [ ] 数据无损迁移
- [ ] 迁移后原数据不受影响

---

## Phase 3: 爬虫服务 (Week 2)

### Task 3.1: HTTP 客户端封装
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: 无

**输入** (参考原项目):
- `src/utils/http.py` - HttpClient 类

**输出** (新实现):
- `src/main/services/crawler/http-client.ts`

**功能**:
- 统一的 axios 实例
- 自动重试机制
- 请求/响应拦截器
- User-Agent 轮换
- Cookie 管理

**检查点**:
- [ ] 能成功请求 anime1.me
- [ ] 自动处理 503 重试

---

### Task 3.2: Anime1 列表解析
**状态**: ⏳ 待开始  
**预计耗时**: 3h  
**依赖**: Task 3.1

**输入** (参考原项目):
- `src/parser/anime1_parser.py` - parse_page / parse_anime_list

**输出** (新实现):
- `src/main/services/crawler/anime1.ts` - fetchAnimeList()

**功能**:
```typescript
// 从 Anime1 API 获取番剧列表
async fetchAnimeList(): Promise<Anime[]>
```

**检查点**:
- [ ] 能正确解析 JSON API 返回
- [ ] 处理 anime1.pw 外链情况
- [ ] 生成正确的唯一 ID

---

### Task 3.3: Anime1 详情解析
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 3.2

**输入** (参考原项目):
- `src/parser/anime1_parser.py` - parse_anime_detail / parse_episode_list

**输出** (新实现):
- `src/main/services/crawler/anime1.ts` - fetchAnimeDetail() / fetchEpisodes()

**功能**:
```typescript
async fetchAnimeDetail(url: string): Promise<{ year, season, subtitleGroup }>
async fetchEpisodes(url: string): Promise<Episode[]>
```

**检查点**:
- [ ] 正确提取年份、季节、字幕组
- [ ] 正确提取剧集列表（分页处理）
- [ ] 处理单集页面（剧场版等）

---

### Task 3.4: Bangumi 信息获取
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 3.1

**输入** (参考原项目):
- `src/parser/cover_finder.py` - get_bangumi_info

**输出** (新实现):
- `src/main/services/crawler/bangumi.ts`

**功能**:
```typescript
async searchByTitle(title: string): Promise<BangumiSearchResult[]>
async getSubjectInfo(subjectId: number): Promise<BangumiInfo>
```

**检查点**:
- [ ] 能搜索到正确结果
- [ ] 匹配算法（标题相似度）
- [ ] 请求频率限制

---

## Phase 4: 业务服务 (Week 3)

### Task 4.1: 番剧缓存服务
**状态**: ⏳ 待开始  
**预计耗时**: 4h  
**依赖**: Task 2.1, Task 3.2

**输入** (参考原项目):
- `src/services/anime_cache_service.py`

**输出** (新实现):
- `src/main/services/anime/index.ts` - 完善骨架
- `src/main/services/anime/cache.ts` - 缓存管理

**功能**:
```typescript
// 核心方法
async initialize(): Promise<void>           // 初始化缓存
async getList(page, pageSize): Promise<AnimePage>
async getDetail(animeId): Promise<Anime>
async search(keyword, page): Promise<AnimePage>
async refreshCache(): Promise<void>         // 后台刷新
getCacheStatus(): CacheStatus
```

**检查点**:
- [ ] 启动时快速加载列表
- [ ] 后台获取详情不阻塞
- [ ] 缓存状态实时更新

---

### Task 4.2: 下载服务
**状态**: ⏳ 待开始  
**预计耗时**: 4h  
**依赖**: Task 2.1

**输入** (参考原项目):
- `src/services/video_downloader.py`
- `src/services/auto_download_service.py`

**输出** (新实现):
- `src/main/services/download/index.ts` - 完善骨架

**功能**:
```typescript
// 下载任务管理
addTask(url, filename): Promise<DownloadTask>
pauseTask(taskId): void
resumeTask(taskId): void
cancelTask(taskId): void
getTasks(): DownloadTask[]

// 事件
onProgress(callback)
onComplete(callback)
onError(callback)
```

**检查点**:
- [ ] 能正确下载 m3u8 视频
- [ ] 显示下载速度/进度
- [ ] 支持断点续传

---

### Task 4.3: 收藏服务封装
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 2.1

**输出** (新实现):
- `src/main/services/favorite/index.ts`

**功能**: 在数据库服务上的一层封装，处理业务逻辑

---

## Phase 5: 前端对接 (Week 4)

### Task 5.1: Pinia Store 实现
**状态**: ⏳ 待开始  
**预计耗时**: 4h  
**依赖**: Task 4.1

**输入** (参考原项目):
- `frontend/src/composables/` - 原 composables

**输出** (新实现):
- `src/renderer/stores/anime.ts`
- `src/renderer/stores/favorite.ts`
- `src/renderer/stores/settings.ts`

**检查点**:
- [ ] 状态管理正确
- [ ] IPC 调用封装
- [ ] 加载状态处理

---

### Task 5.2: 首页 - 番剧列表
**状态**: ⏳ 待开始  
**预计耗时**: 4h  
**依赖**: Task 5.1

**输入** (参考原项目):
- `frontend/src/views/Home.vue`
- `frontend/src/components/AnimeCard.vue`
- `frontend/src/components/AnimeGrid.vue`

**输出** (新实现):
- `src/renderer/views/Home.vue` - 替换当前占位
- `src/renderer/components/AnimeCard.vue`
- `src/renderer/components/AnimeGrid.vue`

**功能**:
- 番剧列表展示
- 分页加载
- 封面懒加载
- 点击跳转详情

---

### Task 5.3: 搜索功能
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 5.2

**输入** (参考原项目):
- `frontend/src/components/SearchBar.vue`

**输出** (新实现):
- `src/renderer/components/SearchBar.vue`

---

### Task 5.4: 详情页
**状态**: ⏳ 待开始  
**预计耗时**: 4h  
**依赖**: Task 5.2

**输入** (参考原项目):
- `frontend/src/views/Detail.vue`
- `frontend/src/components/VideoPlayer.vue`

**输出** (新实现):
- `src/renderer/views/Detail.vue` - 替换当前占位
- `src/renderer/components/VideoPlayer.vue`

**功能**:
- 番剧信息展示
- Bangumi 信息
- 剧集列表
- 视频播放

---

### Task 5.5: 收藏页
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 5.1

**输入** (参考原项目):
- `frontend/src/views/Favorites.vue`

**输出** (新实现):
- `src/renderer/views/Favorites.vue` - 替换当前占位

---

### Task 5.6: 设置页
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 5.1

**输入** (参考原项目):
- `frontend/src/views/Settings.vue`

**输出** (新实现):
- `src/renderer/views/Settings.vue` - 完善当前占位

---

## Phase 6: 功能完善 (Week 5)

### Task 6.1: 自动更新
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: 无

**输入** (参考原项目):
- `src/services/update_checker.py`
- `src/cli/update_check.py`

**输出** (新实现):
- `src/main/services/update/index.ts` - 完善骨架

---

### Task 6.2: 下载管理页
**状态**: ⏳ 待开始  
**预计耗时**: 3h  
**依赖**: Task 4.2

**输出**:
- `src/renderer/views/Downloads.vue` - 替换当前占位
- 下载列表展示
- 进度条
- 操作按钮（暂停/恢复/取消）

---

### Task 6.3: 播放历史
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: Task 2.1

**输出**:
- `src/renderer/views/History.vue` - 替换当前占位

---

### Task 6.4: 打包与签名
**状态**: ⏳ 待开始  
**预计耗时**: 2h  
**依赖**: 所有功能完成

**输出**:
- 修改 `electron-builder.yml`
- 添加签名证书配置
- CI/CD 脚本

---

## 📋 本周推荐执行顺序

如果你是这周开始开发，建议按这个顺序：

### 第 1 天：环境 + 类型
1. ✅ Task 1.1: 完善 TypeScript 类型
2. ✅ Task 1.2: 配置文件

### 第 2 天：数据库
3. ✅ Task 2.1: 数据库服务完善
4. ✅ Task 2.2: 数据迁移脚本

### 第 3 天：爬虫基础
5. ✅ Task 3.1: HTTP 客户端
6. ✅ Task 3.2: Anime1 列表解析

### 第 4 天：爬虫进阶
7. ✅ Task 3.3: Anime1 详情解析
8. ✅ Task 3.4: Bangumi 信息获取

### 第 5 天：业务服务
9. ✅ Task 4.1: 番剧缓存服务

---

## 🎯 执行模板

每个任务的执行流程：

```bash
# 1. 查看参考代码
code ~/Github/anime1-desktop/src/xxx/xxx.py

# 2. 查看对应位置
code ~/Github/anime1-desktop-electron/src/xxx/xxx.ts

# 3. 实现代码
# ...coding...

# 4. 验证
pnpm typecheck
pnpm dev

# 5. 提交
git add .
git commit -m "feat: xxx"
```

需要我从哪个 Task 开始帮你实现？
