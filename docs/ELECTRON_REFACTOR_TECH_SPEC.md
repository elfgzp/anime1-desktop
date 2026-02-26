# Anime1 Desktop Electron 重构技术方案

## 1. 项目概述

### 1.1 背景
当前 Anime1 Desktop 使用 Flask + pywebview + Vue 3 的混合架构。为提升性能、改善用户体验、降低维护成本，计划使用 Electron + TypeScript 进行完全重构。

### 1.2 目标
- 完全替代 Python 后端，使用 Node.js/Electron 技术栈
- 保持 Vue 3 前端框架，迁移至 TypeScript
- 提供更好的桌面端集成（系统托盘、快捷键、原生菜单等）
- 支持自动更新、崩溃报告等现代化功能
- 保持数据兼容性和功能完整性

### 1.3 技术栈选型

| 层级 | 当前技术 | 目标技术 |
|------|---------|---------|
| 桌面框架 | pywebview | Electron 30+ |
| 后端服务 | Flask (Python) | Electron Main Process + IPC |
| 前端框架 | Vue 3 (JS) | Vue 3 (TypeScript) |
| UI 组件 | Element Plus | Element Plus |
| 构建工具 | Vite | Vite |
| 数据存储 | SQLite (Peewee) | better-sqlite3 |
| HTTP 客户端 | requests | axios / electron-fetch |
| HTML 解析 | BeautifulSoup4 | cheerio / jsdom |
| 打包工具 | PyInstaller | electron-builder |

---

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Application                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Main Process   │  │  Renderer       │  │  Preload     │ │
│  │  (Node.js)      │◄─┤  (Vue 3 + TS)   │◄─┤  (Bridge)    │ │
│  │                 │  │                 │  │              │ │
│  │ • Window Mgmt   │  │ • UI Components │  │ • IPC API    │ │
│  │ • Data Service  │  │ • Router        │  │ • Security   │ │
│  │ • Crawler       │  │ • Pinia Store   │  │              │ │
│  │ • Auto Update   │  │ • Composables   │  │              │ │
│  └────────┬────────┘  └─────────────────┘  └──────────────┘ │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Data Layer                            ││
│  │  • better-sqlite3 (SQLite)                               ││
│  │  • LocalStorage (Settings)                               ││
│  │  • Cache Files                                           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

```
electron-refactor/
├── src/
│   ├── main/                    # Electron 主进程
│   │   ├── index.ts             # 主入口
│   │   ├── window.ts            # 窗口管理
│   │   ├── ipc/                 # IPC 处理器
│   │   │   ├── anime.ts         # 番剧相关 IPC
│   │   │   ├── favorite.ts      # 收藏相关 IPC
│   │   │   ├── settings.ts      # 设置相关 IPC
│   │   │   ├── download.ts      # 下载相关 IPC
│   │   │   └── system.ts        # 系统相关 IPC
│   │   ├── services/            # 核心服务
│   │   │   ├── anime/           # 番剧服务
│   │   │   ├── crawler/         # 爬虫服务
│   │   │   ├── database/        # 数据库服务
│   │   │   ├── download/        # 下载服务
│   │   │   └── update/          # 更新服务
│   │   └── utils/               # 工具函数
│   │
│   ├── preload/                 # Preload 脚本
│   │   ├── index.ts             # 预加载入口
│   │   └── api/                 # 暴露的 API 定义
│   │
│   ├── renderer/                # 渲染进程 (Vue 3)
│   │   ├── main.ts              # Vue 入口
│   │   ├── App.vue              # 根组件
│   │   ├── components/          # 公共组件
│   │   ├── views/               # 页面视图
│   │   ├── composables/         # 组合式函数
│   │   ├── stores/              # Pinia Store
│   │   ├── router/              # 路由配置
│   │   ├── utils/               # 工具函数
│   │   └── types/               # TypeScript 类型
│   │
│   └── shared/                  # 共享代码
│       ├── constants/           # 常量定义
│       ├── types/               # 共享类型
│       └── utils/               # 共享工具
│
├── resources/                   # 资源文件
├── build/                       # 构建配置
└── docs/                        # 文档
```

---

## 3. 模块详细设计

### 3.1 主进程模块 (Main Process)

#### 3.1.1 窗口管理 (`main/window.ts`)

```typescript
// 功能职责
- 创建和管理主窗口
- 处理窗口状态（最大化、最小化、全屏）
- 系统托盘集成
- 多显示器支持
- 窗口尺寸和位置记忆

// 核心接口
interface WindowManager {
  createMainWindow(): BrowserWindow;
  showWindow(): void;
  hideWindow(): void;
  minimizeToTray(): void;
  toggleFullscreen(): void;
  getWindowState(): WindowState;
  setWindowState(state: WindowState): void;
}

// 配置
const WINDOW_CONFIG = {
  width: 1280,
  height: 800,
  minWidth: 900,
  minHeight: 600,
  titleBarStyle: 'hiddenInset', // macOS
  webPreferences: {
    preload: path.join(__dirname, '../preload/index.js'),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
  }
};
```

#### 3.1.2 IPC 通信层 (`main/ipc/`)

**API 映射表**

| 原 Flask API | Electron IPC Channel | Handler |
|-------------|---------------------|---------|
| `GET /api/anime` | `anime:list` | `anime.ts` |
| `GET /api/anime/:id` | `anime:detail` | `anime.ts` |
| `GET /api/anime/:id/episodes` | `anime:episodes` | `anime.ts` |
| `GET /api/anime/search` | `anime:search` | `anime.ts` |
| `GET /api/favorite/list` | `favorite:list` | `favorite.ts` |
| `POST /api/favorite/add` | `favorite:add` | `favorite.ts` |
| `POST /api/favorite/remove` | `favorite:remove` | `favorite.ts` |
| `GET /api/settings/theme` | `settings:getTheme` | `settings.ts` |
| `POST /api/settings/theme` | `settings:setTheme` | `settings.ts` |
| `GET /proxy/*` | `proxy:fetch` | `proxy.ts` |

```typescript
// IPC 基础接口设计
interface IPCRequest<T = unknown> {
  id: string;
  data: T;
}

interface IPCResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

// 注册示例
ipcMain.handle('anime:list', async (_, request: IPCRequest<ListParams>) => {
  try {
    const result = await animeService.getList(request.data);
    return { success: true, data: result };
  } catch (error) {
    return { 
      success: false, 
      error: { code: 'FETCH_ERROR', message: error.message } 
    };
  }
});
```

### 3.2 核心服务层 (`main/services/`)

#### 3.2.1 番剧服务 (`services/anime/`)

```typescript
// 服务职责
- 番剧列表管理
- 番剧详情获取
- 剧集列表获取
- Bangumi 信息获取
- 封面缓存管理
- 本地搜索

// 核心类型
interface Anime {
  id: string;
  title: string;
  detailUrl: string;
  episode: number;
  coverUrl?: string;
  year?: string;
  season?: string;
  subtitleGroup?: string;
  matchScore?: number;
  matchSource?: string;
}

interface Episode {
  id: string;
  title: string;
  episode: string;
  url: string;
  date: string;
}

interface AnimeService {
  // 列表
  getList(page: number, pageSize: number): Promise<AnimePage>;
  getAllAnime(): Promise<Map<string, Anime>>;
  
  // 详情
  getDetail(animeId: string): Promise<Anime>;
  getEpisodes(animeId: string): Promise<Episode[]>;
  
  // 搜索
  search(keyword: string, page: number): Promise<AnimePage>;
  
  // 缓存
  refreshCache(): Promise<void>;
  getCacheStatus(): CacheStatus;
}
```

#### 3.2.2 爬虫服务 (`services/crawler/`)

```typescript
// 迁移自: src/parser/anime1_parser.py
// 技术栈: cheerio + axios

interface CrawlerService {
  // Anime1.me 数据获取
  fetchAnimeList(): Promise<Anime[]>;
  fetchAnimeDetail(url: string): Promise<DetailInfo>;
  fetchEpisodes(url: string): Promise<Episode[]>;
  
  // Bangumi API
  fetchBangumiInfo(title: string): Promise<BangumiInfo>;
  
  // 视频提取
  extractVideoUrl(episodeUrl: string): Promise<VideoSource>;
  
  // HTTP 客户端管理
  getHttpClient(): AxiosInstance;
}

// 爬虫配置
const CRAWLER_CONFIG = {
  baseUrl: 'https://anime1.me',
  apiUrl: 'https://d1zquzjgwo9yb.cloudfront.net/',
  timeout: 10000,
  retries: 3,
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
};
```

#### 3.2.3 数据库服务 (`services/database/`)

```typescript
// 迁移自: src/models/database.py (Peewee -> better-sqlite3)

// 数据模型
interface FavoriteAnime {
  id: number;
  animeId: string;
  title: string;
  coverUrl?: string;
  detailUrl: string;
  createdAt: number;
}

interface CoverCache {
  animeId: string;
  coverUrl?: string;
  year?: string;
  season?: string;
  subtitleGroup?: string;
  bangumiInfo?: string; // JSON
  cachedAt: number;
}

interface PlaybackHistory {
  id: number;
  animeId: string;
  episodeId: string;
  title: string;
  episodeTitle: string;
  progress: number; // 播放进度秒数
  duration: number; // 总时长
  playedAt: number;
}

interface DatabaseService {
  // 连接管理
  connect(): Database;
  close(): void;
  
  // 收藏
  getFavorites(): FavoriteAnime[];
  addFavorite(anime: FavoriteAnime): void;
  removeFavorite(animeId: string): void;
  isFavorite(animeId: string): boolean;
  
  // 封面缓存
  getCoverCache(animeId: string): CoverCache | null;
  setCoverCache(cache: CoverCache): void;
  getBangumiInfo(animeId: string): BangumiInfo | null;
  setBangumiInfo(animeId: string, info: BangumiInfo): void;
  
  // 播放历史
  getPlaybackHistory(): PlaybackHistory[];
  addPlaybackHistory(history: PlaybackHistory): void;
  clearPlaybackHistory(): void;
  
  // 设置
  getSetting(key: string): string | null;
  setSetting(key: string, value: string): void;
}

// 数据库初始化 SQL
const INIT_SQL = `
CREATE TABLE IF NOT EXISTS favorite_anime (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anime_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  cover_url TEXT,
  detail_url TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cover_cache (
  anime_id TEXT PRIMARY KEY,
  cover_url TEXT,
  year TEXT,
  season TEXT,
  subtitle_group TEXT,
  bangumi_info TEXT,
  cached_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS playback_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anime_id TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  title TEXT NOT NULL,
  episode_title TEXT NOT NULL,
  progress INTEGER DEFAULT 0,
  duration INTEGER DEFAULT 0,
  played_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
`;
```

#### 3.2.4 下载服务 (`services/download/`)

```typescript
// 迁移自: src/services/video_downloader.py

interface DownloadTask {
  id: string;
  animeId: string;
  episodeId: string;
  title: string;
  episodeTitle: string;
  url: string;
  status: 'pending' | 'downloading' | 'paused' | 'completed' | 'error';
  progress: number; // 0-100
  speed: number; // bytes/s
  totalSize: number;
  downloadedSize: number;
  errorMessage?: string;
  createdAt: number;
  updatedAt: number;
}

interface DownloadService {
  // 任务管理
  addTask(url: string, filename: string): Promise<DownloadTask>;
  pauseTask(taskId: string): void;
  resumeTask(taskId: string): void;
  cancelTask(taskId: string): void;
  removeTask(taskId: string): void;
  
  // 查询
  getTasks(): DownloadTask[];
  getTask(taskId: string): DownloadTask | null;
  
  // 自动下载
  setAutoDownloadConfig(config: AutoDownloadConfig): void;
  getAutoDownloadConfig(): AutoDownloadConfig;
  checkAndDownload(): Promise<void>;
  
  // 事件
  onProgress(callback: (task: DownloadTask) => void): void;
  onComplete(callback: (task: DownloadTask) => void): void;
  onError(callback: (task: DownloadTask, error: Error) => void): void;
}
```

#### 3.2.5 更新服务 (`services/update/`)

```typescript
// 迁移自: src/services/update_checker.py, src/cli/update_check.py

interface UpdateInfo {
  version: string;
  downloadUrl: string;
  releaseNotes: string;
  releaseDate: string;
  isMandatory: boolean;
}

interface UpdateService {
  // 检查更新
  checkForUpdates(): Promise<UpdateInfo | null>;
  
  // 自动更新
  downloadUpdate(updateInfo: UpdateInfo): Promise<void>;
  installUpdate(): Promise<void>;
  
  // 配置
  setUpdateChannel(channel: 'stable' | 'test'): void;
  getUpdateChannel(): 'stable' | 'test';
  setAutoCheck(enabled: boolean): void;
  isAutoCheckEnabled(): boolean;
  
  // 事件
  onUpdateAvailable(callback: (info: UpdateInfo) => void): void;
  onDownloadProgress(callback: (progress: number) => void): void;
  onUpdateDownloaded(callback: () => void): void;
}
```

### 3.3 渲染进程模块 (Renderer Process)

#### 3.3.1 Store 设计 (`renderer/stores/`)

```typescript
// 使用 Pinia + TypeScript

// Anime Store
export const useAnimeStore = defineStore('anime', () => {
  // State
  const animeList = ref<Anime[]>([]);
  const currentAnime = ref<Anime | null>(null);
  const episodes = ref<Episode[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  // Getters
  const getAnimeById = computed(() => (id: string) => 
    animeList.value.find(a => a.id === id)
  );
  
  // Actions
  async function fetchAnimeList(page: number) {
    loading.value = true;
    try {
      const result = await window.api.anime.getList({ page });
      animeList.value = result.animeList;
    } finally {
      loading.value = false;
    }
  }
  
  async function fetchAnimeDetail(id: string) {
    const result = await window.api.anime.getDetail({ id });
    currentAnime.value = result;
  }
  
  return {
    animeList, currentAnime, episodes, loading, error,
    getAnimeById, fetchAnimeList, fetchAnimeDetail
  };
});

// Favorite Store
export const useFavoriteStore = defineStore('favorite', () => {
  const favorites = ref<FavoriteAnime[]>([]);
  
  async function loadFavorites() {
    favorites.value = await window.api.favorite.getList();
  }
  
  async function addFavorite(anime: Anime) {
    await window.api.favorite.add({ animeId: anime.id });
    await loadFavorites();
  }
  
  async function removeFavorite(animeId: string) {
    await window.api.favorite.remove({ animeId });
    await loadFavorites();
  }
  
  const isFavorite = computed(() => (animeId: string) => 
    favorites.value.some(f => f.animeId === animeId)
  );
  
  return { favorites, loadFavorites, addFavorite, removeFavorite, isFavorite };
});

// Settings Store
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark' | 'system'>('system');
  const downloadPath = ref<string>('');
  
  async function loadSettings() {
    const settings = await window.api.settings.getAll();
    theme.value = settings.theme;
    downloadPath.value = settings.downloadPath;
  }
  
  async function setTheme(value: typeof theme.value) {
    theme.value = value;
    await window.api.settings.set({ key: 'theme', value });
    applyTheme(value);
  }
  
  return { theme, downloadPath, loadSettings, setTheme };
});
```

#### 3.3.2 Composables 设计 (`renderer/composables/`)

```typescript
// useTheme.ts - 主题管理
export function useTheme() {
  const store = useSettingsStore();
  
  const isDark = computed(() => {
    if (store.theme === 'dark') return true;
    if (store.theme === 'light') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  
  watch(isDark, (dark) => {
    document.documentElement.classList.toggle('dark', dark);
  }, { immediate: true });
  
  return { theme: store.theme, isDark, setTheme: store.setTheme };
}

// useVideoPlayer.ts - 视频播放器
export function useVideoPlayer() {
  const playerRef = ref<HTMLVideoElement | null>(null);
  const isPlaying = ref(false);
  const currentTime = ref(0);
  const duration = ref(0);
  const volume = ref(1);
  
  function play() {
    playerRef.value?.play();
  }
  
  function pause() {
    playerRef.value?.pause();
  }
  
  function seek(time: number) {
    if (playerRef.value) {
      playerRef.value.currentTime = time;
    }
  }
  
  function setVolume(vol: number) {
    if (playerRef.value) {
      playerRef.value.volume = Math.max(0, Math.min(1, vol));
      volume.value = playerRef.value.volume;
    }
  }
  
  // 键盘快捷键
  useEventListener('keydown', (e: KeyboardEvent) => {
    if (e.code === 'Space') {
      isPlaying.value ? pause() : play();
    } else if (e.code === 'ArrowLeft') {
      seek(currentTime.value - 10);
    } else if (e.code === 'ArrowRight') {
      seek(currentTime.value + 10);
    } else if (e.code === 'ArrowUp') {
      setVolume(volume.value + 0.1);
    } else if (e.code === 'ArrowDown') {
      setVolume(volume.value - 0.1);
    }
  });
  
  return {
    playerRef, isPlaying, currentTime, duration, volume,
    play, pause, seek, setVolume
  };
}

// useScrollRestore.ts - 滚动位置恢复
export function useScrollRestore() {
  const scrollPositions = new Map<string, number>();
  const route = useRoute();
  
  onBeforeUnmount(() => {
    scrollPositions.set(route.fullPath, window.scrollY);
  });
  
  onMounted(() => {
    const saved = scrollPositions.get(route.fullPath);
    if (saved !== undefined) {
      window.scrollTo(0, saved);
    }
  });
}
```

### 3.4 共享模块 (Shared)

```typescript
// shared/types/anime.ts
export interface Anime {
  id: string;
  title: string;
  detailUrl: string;
  episode: number;
  coverUrl?: string;
  year?: string;
  season?: string;
  subtitleGroup?: string;
  matchScore?: number;
  matchSource?: string;
}

export interface Episode {
  id: string;
  title: string;
  episode: string;
  url: string;
  date: string;
}

export interface AnimePage {
  animeList: Anime[];
  currentPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface BangumiInfo {
  title: string;
  subjectUrl: string;
  coverUrl?: string;
  rating?: number;
  rank?: number;
  type?: string;
  date?: string;
  summary?: string;
  genres: string[];
  staff: Array<{ name: string; role: string }>;
  cast: Array<{ name: string; character: string }>;
}

// shared/constants/api.ts
export const IPC_CHANNELS = {
  ANIME: {
    LIST: 'anime:list',
    DETAIL: 'anime:detail',
    EPISODES: 'anime:episodes',
    SEARCH: 'anime:search',
    BANGUMI: 'anime:bangumi',
    CACHE_STATUS: 'anime:cache:status',
    CACHE_REFRESH: 'anime:cache:refresh',
  },
  FAVORITE: {
    LIST: 'favorite:list',
    ADD: 'favorite:add',
    REMOVE: 'favorite:remove',
    CHECK: 'favorite:check',
  },
  SETTINGS: {
    GET: 'settings:get',
    SET: 'settings:set',
    GET_ALL: 'settings:getAll',
  },
  DOWNLOAD: {
    LIST: 'download:list',
    ADD: 'download:add',
    PAUSE: 'download:pause',
    RESUME: 'download:resume',
    CANCEL: 'download:cancel',
    PROGRESS: 'download:progress',
  },
  SYSTEM: {
    MINIMIZE: 'system:minimize',
    MAXIMIZE: 'system:maximize',
    CLOSE: 'system:close',
    TOGGLE_FULLSCREEN: 'system:toggleFullscreen',
    OPEN_EXTERNAL: 'system:openExternal',
    SHOW_ITEM_IN_FOLDER: 'system:showItemInFolder',
  },
} as const;

// shared/constants/app.ts
export const APP_CONFIG = {
  name: 'Anime1 Desktop',
  version: '2.0.0',
  
  // 分页
  pageSize: 24,
  
  // 缓存
  cacheRefreshInterval: 300, // 5 minutes
  coverCacheExpiry: 7 * 24 * 60 * 60 * 1000, // 7 days
  
  // 下载
  maxConcurrentDownloads: 3,
  downloadRetryAttempts: 3,
  
  // 更新
  updateCheckInterval: 24 * 60 * 60 * 1000, // 24 hours
} as const;
```

---

## 4. 数据迁移方案

### 4.1 SQLite 数据库迁移

```typescript
// main/services/database/migration.ts

// 从 Python Peewee 迁移到 better-sqlite3
// 原数据库路径: ~/Library/Application Support/Anime1/anime1.db (macOS)
//              %APPDATA%/Anime1/anime1.db (Windows)

const MIGRATIONS = [
  {
    version: 1,
    description: 'Initial schema from v1.x',
    up: `
      -- 原表已存在，无需创建
      -- 验证表结构
    `,
  },
  {
    version: 2,
    description: 'Add indices for performance',
    up: `
      CREATE INDEX IF NOT EXISTS idx_favorite_anime_id ON favorite_anime(anime_id);
      CREATE INDEX IF NOT EXISTS idx_cover_cache_anime_id ON cover_cache(anime_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_anime_id ON playback_history(anime_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_played_at ON playback_history(played_at);
    `,
  },
];

export function runMigrations(db: Database) {
  // 创建迁移记录表
  db.exec(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version INTEGER PRIMARY KEY,
      applied_at INTEGER NOT NULL
    )
  `);
  
  // 获取当前版本
  const currentVersion = db.prepare(
    'SELECT MAX(version) as version FROM schema_migrations'
  ).get() as { version: number | null };
  
  const fromVersion = currentVersion?.version ?? 0;
  
  // 执行待执行的迁移
  for (const migration of MIGRATIONS) {
    if (migration.version > fromVersion) {
      console.log(`Running migration ${migration.version}: ${migration.description}`);
      db.exec(migration.up);
      db.prepare(
        'INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)'
      ).run(migration.version, Date.now());
    }
  }
}
```

### 4.2 配置文件迁移

```typescript
// 从 Python config 迁移到 Electron Store
// 原配置: src/config.py

interface AppConfig {
  // 主题设置
  theme: 'light' | 'dark' | 'system';
  
  // 下载设置
  downloadPath: string;
  autoDownloadEnabled: boolean;
  autoDownloadFilters: {
    years: string[];
    seasons: string[];
  };
  
  // 播放设置
  autoPlayNext: boolean;
  rememberPlaybackPosition: boolean;
  defaultVolume: number;
  
  // 窗口设置
  windowState: {
    width: number;
    height: number;
    x?: number;
    y?: number;
    maximized: boolean;
  };
  
  // 更新设置
  updateChannel: 'stable' | 'test';
  autoCheckUpdates: boolean;
}

// 默认值
const DEFAULT_CONFIG: AppConfig = {
  theme: 'system',
  downloadPath: '', // 使用系统下载目录
  autoDownloadEnabled: false,
  autoDownloadFilters: { years: [], seasons: [] },
  autoPlayNext: true,
  rememberPlaybackPosition: true,
  defaultVolume: 1,
  windowState: { width: 1280, height: 800, maximized: false },
  updateChannel: 'stable',
  autoCheckUpdates: true,
};
```

---

## 5. 构建与打包

### 5.1 electron-builder 配置

```yaml
# electron-builder.yml
appId: com.elfgzp.anime1-desktop
productName: Anime1 Desktop
copyright: Copyright © 2024 elfgzp

directories:
  output: release
  buildResources: resources

files:
  - dist/
  - dist-electron/
  - resources/
  - '!**/*.map'

asar: true
asarUnpack:
  - '**/node_modules/better-sqlite3/**/*'
  - '**/node_modules/better-sqlite3/build/Release/*.node'

extraResources:
  - from: resources/
    to: resources/

mac:
  category: public.app-category.entertainment
  icon: resources/icon.icns
  target:
    - target: dmg
      arch: [x64, arm64]
    - target: zip
      arch: [x64, arm64]
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist

win:
  icon: resources/icon.ico
  target:
    - target: nsis
      arch: [x64]
    - target: portable
      arch: [x64]

linux:
  icon: resources/icon.png
  target:
    - target: AppImage
      arch: [x64]
    - target: tar.gz
      arch: [x64, arm64]
  category: AudioVideo

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: always
  createStartMenuShortcut: true

dmg:
  sign: false

publish:
  provider: github
  owner: elfgzp
  repo: anime1-desktop
  releaseType: draft
```

### 5.2 开发脚本

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build && electron-builder",
    "build:mac": "vue-tsc --noEmit && vite build && electron-builder --mac",
    "build:win": "vue-tsc --noEmit && vite build && electron-builder --win",
    "build:linux": "vue-tsc --noEmit && vite build && electron-builder --linux",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.ts,.tsx --fix",
    "typecheck": "vue-tsc --noEmit"
  }
}
```

---

## 6. 测试策略

### 6.1 单元测试

```typescript
// 主进程服务测试
// tests/main/services/anime.service.test.ts

describe('AnimeService', () => {
  let service: AnimeService;
  
  beforeEach(() => {
    service = new AnimeService(mockDatabase, mockCrawler);
  });
  
  describe('getList', () => {
    it('should return paginated anime list', async () => {
      const result = await service.getList(1, 24);
      expect(result.animeList).toHaveLength(24);
      expect(result.currentPage).toBe(1);
      expect(result.hasNext).toBe(true);
    });
  });
  
  describe('search', () => {
    it('should search with keyword', async () => {
      const result = await service.search('鬼灭', 1);
      expect(result.animeList.every(a => 
        a.title.includes('鬼灭') || a.title.includes('鬼滅')
      )).toBe(true);
    });
  });
});
```

### 6.2 E2E 测试

```typescript
// tests/e2e/app.spec.ts

describe('Anime1 Desktop E2E', () => {
  let app: ElectronApplication;
  
  beforeAll(async () => {
    app = await electron.launch({
      args: ['dist-electron/main/index.js']
    });
  });
  
  afterAll(async () => {
    await app.close();
  });
  
  test('should display anime list on startup', async () => {
    const page = await app.firstWindow();
    await expect(page.locator('.anime-card')).toHaveCount(24);
  });
  
  test('should navigate to detail page', async () => {
    const page = await app.firstWindow();
    await page.click('.anime-card:first-child');
    await expect(page.locator('.anime-detail')).toBeVisible();
  });
});
```

---

## 7. 性能优化

### 7.1 启动优化

```typescript
// main/index.ts

// 1. 延迟加载非必要模块
const lazyServices = {
  get crawler() {
    if (!this._crawler) {
      this._crawler = new CrawlerService();
    }
    return this._crawler;
  },
  _crawler: null as CrawlerService | null,
};

// 2. 预加载关键数据
async function preloadEssentialData() {
  // 优先加载番剧列表（仅基础信息）
  await animeService.loadBasicList();
  // 详情在后台加载
  animeService.loadDetailsInBackground();
}

// 3. 窗口提前显示
function createWindow() {
  const window = new BrowserWindow({
    show: false, // 先不显示
    // ...
  });
  
  window.once('ready-to-show', () => {
    window.show();
    // 加载完成后再加载数据
    preloadEssentialData();
  });
}
```

### 7.2 渲染优化

```typescript
// 虚拟滚动
import { useVirtualList } from '@vueuse/core';

const { list, containerProps, wrapperProps } = useVirtualList(
  animeList,
  { itemHeight: 280 }
);

// 图片懒加载
<img v-lazy="anime.coverUrl" :src="placeholderUrl" />

// 组件懒加载
const DetailView = defineAsyncComponent(() => 
  import('./views/Detail.vue')
);
```

### 7.3 内存优化

```typescript
// 限制缓存大小
const MAX_CACHE_SIZE = 1000;
const lruCache = new LRUCache<string, Anime>({ max: MAX_CACHE_SIZE });

// 定期清理
setInterval(() => {
  global.gc && global.gc(); // 强制 GC（开发模式）
}, 60000);

// 限制并发
const pQueue = new PQueue({ concurrency: 5 });
```

---

## 8. 安全策略

### 8.1 内容安全策略

```typescript
// main/window.ts
const window = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, '../preload/index.js'),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    allowRunningInsecureContent: false,
    experimentalFeatures: false,
  },
});

// CSP Header
window.webContents.session.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': [
        "default-src 'self';",
        "script-src 'self' 'unsafe-inline';",
        "style-src 'self' 'unsafe-inline';",
        "img-src 'self' https: data:;",
        "media-src 'self' https: blob:;",
        "connect-src 'self' https://anime1.me https://*.cloudfront.net https://api.bgm.tv;",
      ].join(' '),
    },
  });
});
```

### 8.2 IPC 安全

```typescript
// preload/index.ts
import { contextBridge, ipcRenderer } from 'electron';

// 白名单 API
const validChannels = Object.values(IPC_CHANNELS).flatMap(Object.values);

const api = {
  invoke: (channel: string, ...args: any[]) => {
    if (validChannels.includes(channel)) {
      return ipcRenderer.invoke(channel, ...args);
    }
    throw new Error(`Invalid channel: ${channel}`);
  },
  
  on: (channel: string, callback: Function) => {
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_, ...args) => callback(...args));
    }
  },
};

contextBridge.exposeInMainWorld('api', api);
```

---

## 9. 开发计划

### Phase 1: 基础架构 (2 周)
- [ ] Electron 项目初始化
- [ ] TypeScript 配置
- [ ] 目录结构搭建
- [ ] 基础 IPC 通信
- [ ] 窗口管理

### Phase 2: 数据层 (2 周)
- [ ] 数据库服务 (better-sqlite3)
- [ ] 数据模型迁移
- [ ] 数据库迁移脚本
- [ ] 配置管理

### Phase 3: 核心服务 (3 周)
- [ ] HTTP 客户端
- [ ] 爬虫服务 (Anime1 + Bangumi)
- [ ] 番剧服务
- [ ] 缓存服务
- [ ] 下载服务

### Phase 4: 前端迁移 (3 周)
- [ ] Vue 3 + TS 配置
- [ ] Store 重构 (Pinia)
- [ ] 组件迁移
- [ ] 路由配置
- [ ] 页面重构

### Phase 5: 功能完善 (2 周)
- [ ] 收藏功能
- [ ] 播放历史
- [ ] 自动下载
- [ ] 系统托盘
- [ ] 自动更新

### Phase 6: 测试与优化 (2 周)
- [ ] 单元测试
- [ ] E2E 测试
- [ ] 性能优化
- [ ] Bug 修复

### Phase 7: 发布 (1 周)
- [ ] 打包配置
- [ ] 签名配置
- [ ] CI/CD
- [ ] 文档更新

---

## 10. 风险与应对

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 爬虫反制 | 高 | 实现请求限速、User-Agent轮换、失败重试 |
| 数据迁移失败 | 高 | 备份原数据库、提供回滚方案 |
| 性能问题 | 中 | 性能基准测试、渐进式优化 |
| 打包体积过大 | 中 | Tree-shaking、按需加载、代码分割 |
| 兼容性问题 | 中 | 多平台测试、虚拟机验证 |

---

## 附录

### A. 依赖清单

```json
{
  "dependencies": {
    "electron": "^30.0.0",
    "better-sqlite3": "^9.0.0",
    "axios": "^1.6.0",
    "cheerio": "^1.0.0-rc.12",
    "electron-store": "^8.1.0",
    "electron-updater": "^6.1.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "electron-builder": "^24.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-electron": "^0.28.0",
    "vue": "^3.4.0",
    "vue-tsc": "^1.8.0"
  }
}
```

### B. 参考资源

- [Electron 官方文档](https://www.electronjs.org/docs/)
- [Vue 3 + TypeScript 指南](https://vuejs.org/guide/typescript/)
- [better-sqlite3 文档](https://github.com/WiseLibs/better-sqlite3)
- [electron-builder 文档](https://www.electron.build/)
