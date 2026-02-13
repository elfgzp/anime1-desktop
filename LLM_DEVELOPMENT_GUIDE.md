# LLM 开发测试指南 - Anime1 Desktop (Electron Forge)

> **文档类型**: Machine-Readable Development Guide  
> **目标读者**: AI Code Assistants / LLMs  
> **项目路径**: `/Users/gzp/Github/anime1-desktop-electron-forge`

---

## 1. 项目上下文

### 1.1 技术栈
```yaml
framework: Electron Forge + Webpack 5
frontend: Vue 3 + Element Plus + Vue Router (hash mode)
backend_services:
  - electron-store (database)
  - axios + cheerio (scraping)
  - electron-updater (auto-update)
build_tool: @electron-forge/plugin-webpack v7.11.1
node_version: 24.13.0 (via n)
electron_version: 40.4.0
```

### 1.2 关键文件路径
```
project_root: /Users/gzp/Github/anime1-desktop-electron-forge
├── src/
│   ├── main.js                 # Main process entry
│   ├── preload.js              # Preload script (contextBridge)
│   ├── renderer.js             # Renderer entry (Vue init)
│   ├── services/
│   │   ├── scraper.js          # Anime1.me JSON API scraper
│   │   ├── bangumi.js          # Bangumi cover API
│   │   ├── videoProxy.js       # Video URL extraction
│   │   ├── database.js         # electron-store wrapper
│   │   ├── updater.js          # Auto-updater
│   │   └── autoDownload.js     # Download service
│   ├── views/
│   │   ├── Home.vue            # Anime list page
│   │   ├── Detail.vue          # Anime detail + player
│   │   ├── Favorites.vue       # Favorites list
│   │   └── PlaybackHistory.vue # History page
│   └── utils/api.js            # IPC API wrapper
├── e2e-test-cdp.js             # Playwright CDP test script
├── forge.config.js             # Electron Forge config
└── TODO.md                     # Task tracking
```

### 1.3 端口配置
```yaml
webpack_dev_server: 9000
electron_renderer: 3000
cdp_debugging: 9222
```

---

## 2. 开发工作流

### 2.1 启动开发环境
```bash
# Context: Working directory must be project_root
cd /Users/gzp/Github/anime1-desktop-electron-forge

# Start development server
npm start

# Expected output:
# - Webpack dev server on :9000
# - Electron window opens
# - DevTools available on ws://localhost:9222
```

### 2.2 开发模式特征
- Hot reload enabled for renderer process
- Main process requires manual restart (type `rs` in terminal)
- DevTools auto-open (can be disabled in main.js)

---

## 3. 自动化测试 (Playwright + CDP)

### 3.1 前置条件
```bash
# Dependencies must be installed
npm list @playwright/test  # Should be installed

# If not installed:
npm install -D @playwright/test
npx playwright install chromium
```

### 3.2 测试脚本使用
**File**: `e2e-test-cdp.js`

**Usage Pattern**:
```bash
# Terminal 1: Start app
npm start

# Terminal 2: Run test (after app is ready)
node e2e-test-cdp.js
```

**Test Script API**:
```javascript
// The script performs these actions:
1. Connect to Electron via CDP (port 9222)
2. Find main window (url contains 'main_window')
3. Close DevTools if present
4. Set viewport: 1280x800
5. Wait for networkidle
6. Capture screenshots: /tmp/anime1-home.png, /tmp/anime1-detail.png
7. Click first anime card
8. Click first episode
9. Check video player status
```

### 3.3 验证点清单
When testing, verify these elements:
```yaml
home_page:
  selector: ".anime-card"
  expected_count: "> 0"
  attributes: [cover_url, title, episode]

detail_page:
  selectors:
    title: "h1, h2"
    episodes: "button:has-text('第'), .episode-item"
    video_player: "video"
  expected:
    episode_count: "> 0"
    video_src: "should exist after clicking episode"

console_logs:
  success_indicators:
    - "[Scraper] Fetched N anime from API"
    - "[API] getAnimeList response"
    - "[API] getVideoInfo response: {success: true}"
  error_indicators:
    - "electronAPI not available"
    - "Request failed with status code 404"
    - "MEDIA_ERR_SRC_NOT_SUPPORTED"
```

---

## 4. 常见问题与解决方案

### 4.1 端口占用
```bash
# Kill existing processes on ports 9000, 3000, 9222
lsof -ti:9000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
ps aux | grep "Electron.app" | grep -v grep | awk '{print $2}' | xargs kill -9
```

### 4.2 electronAPI not available (Browser Context)
**Symptom**: Testing via `localhost:3000` in browser shows "electronAPI not available"
**Cause**: Browser lacks Electron preload context
**Solution**: Must use Playwright CDP connection, not direct browser access

### 4.3 Webpack Cache Issues
```bash
# Clear webpack cache
rm -rf .webpack
npm start
```

---

## 5. 代码修改快速参考

### 5.1 IPC Handler Pattern
**Location**: `src/main.js`
```javascript
// Add new IPC handler
ipcMain.handle('service:action', async (event, params) => {
  try {
    const result = await someService.action(params);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

### 5.2 Preload Exposure Pattern
**Location**: `src/preload.js`
```javascript
contextBridge.exposeInMainWorld('electronAPI', {
  // Existing APIs...
  newAction: (params) => ipcRenderer.invoke('service:action', params),
});
```

### 5.3 Frontend API Pattern
**Location**: `src/utils/api.js`
```javascript
export const serviceAPI = {
  action: (params) => callElectron('newAction', params),
};
```

---

## 6. 日志位置

```yaml
main_process_logs: ~/Library/Logs/anime1-desktop-electron-forge/main.log
scraping_logs: Terminal stdout (prefix: [Scraper], [Bangumi], [VideoProxy])
renderer_logs: Electron DevTools Console
```

---

## 7. 测试验证命令

```bash
# Verify app is running
ps aux | grep "Electron.app/Contents/MacOS/Electron"

# Verify CDP endpoint
curl -s http://localhost:9222/json/list | grep "Anime1 Desktop"

# Check recent errors
tail -50 ~/Library/Logs/anime1-desktop-electron-forge/main.log | grep -i error

# Verify webpack build
ls -la .webpack/renderer/main_window/
```

---

## 8. 架构决策记录

### 8.1 IPC Architecture
- **Pattern**: contextBridge + ipcRenderer.invoke
- **Security**: contextIsolation: true, nodeIntegration: false
- **Data Format**: All responses use `{ success: boolean, data?: any, error?: string }`

### 8.2 Data Flow
```
Anime1.me (JSON API)
    ↓
scraper.js (Cheerio parsing)
    ↓
main.js (IPC handlers)
    ↓
preload.js (contextBridge)
    ↓
api.js (wrapper)
    ↓
Vue Components
```

### 8.3 State Management
- **Frontend**: Vue 3 Composition API + ref/reactive
- **Persistent**: electron-store (JSON file storage)
- **Cache**: In-memory Map with TTL

---

## 9. LLM Agent Instructions

When working on this project:

1. **Always check if app is running** before testing: `ps aux | grep Electron`
2. **Use CDP test script** for automation, not browser direct access
3. **Follow existing patterns**: IPC handlers → Preload → API.js → Components
4. **Maintain error format**: `{ success: false, error: message }`
5. **Log important events** using console with prefixes like `[ServiceName]`
6. **Update TODO.md** when completing tasks
7. **Screenshots saved to**: `/tmp/anime1-*.png`

---

## 10. 扩展开发模板

### Adding New Service
```javascript
// 1. Create service: src/services/newService.js
export class NewService {
  async init() { /* init */ }
  async action() { /* logic */ }
}

// 2. Add IPC handler: src/main.js
ipcMain.handle('newService:action', async () => {
  return { success: true, data: result };
});

// 3. Expose in preload: src/preload.js
newServiceAction: () => ipcRenderer.invoke('newService:action'),

// 4. Add API wrapper: src/utils/api.js
export const newServiceAPI = {
  action: () => callElectron('newServiceAction'),
};
```

---

*Document Version: 1.0*  
*Last Updated: 2026-02-13*  
*Maintainer: AI Code Assistant*
