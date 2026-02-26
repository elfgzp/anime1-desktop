# 功能对比文档

## API/路由功能对比

### Anime 路由 (/api/anime)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 获取番剧列表 | GET / | anime:list | ✅ | 完整实现 |
| 获取番剧列表(带进度) | - | anime:listWithProgress | ✅ | Electron 新增 |
| 获取番剧详情 | GET /<id> | anime:detail | ✅ | 完整实现 |
| 获取剧集列表 | GET /<id>/episodes | anime:episodes | ✅ | 完整实现 |
| 获取 Bangumi 信息 | GET /<id>/bangumi | anime:bangumi | ✅ | 完整实现 |
| 解析 pw 剧集 | POST /pw/episodes | anime:pwEpisodes | ✅ | 完整实现 |
| 批量获取封面 | GET /covers | - | ⚠️ | 通过 list 返回 |
| 搜索番剧 | GET /search | anime:search | ✅ | 完整实现 |
| 搜索番剧(带进度) | - | anime:searchWithProgress | ✅ | Electron 新增 |
| 缓存状态 | GET /cache/status | anime:cache:status | ✅ | 完整实现 |
| 刷新缓存 | POST /cache/refresh | anime:cache:refresh | ✅ | 完整实现 |
| 强制刷新缓存 | POST /cache/force-refresh | ❌ | ❌ | **缺失** |
| 提取播放器 | GET /api/extract-player | ❌ | ❌ | **缺失** |

### Favorite 路由 (/api/favorite)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 添加收藏 | POST /add | favorite:add | ✅ | 完整实现 |
| 移除收藏 | POST /remove | favorite:remove | ✅ | 完整实现 |
| 获取收藏列表 | GET /list | favorite:list | ✅ | 完整实现(带进度) |
| 检查更新 | GET /check | ❌ | ⚠️ | 在 list 中返回 hasUpdate |
| 检查是否已收藏 | GET /is_favorite | favorite:check | ✅ | 完整实现 |
| 批量检查收藏状态 | GET /batch_status | favorite:batchStatus | ✅ | 完整实现 |

### Playback 路由 (/api/playback)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 更新播放进度 | POST /update | history:save | ✅ | 完整实现 |
| 获取播放历史 | GET /list | history:list | ✅ | 完整实现 |
| 获取单集进度 | GET /episode | history:progress | ✅ | 完整实现 |
| 获取最新播放 | GET /latest | - | ⚠️ | 在 list 中处理 |
| 获取番剧播放历史 | GET /anime/<id> | history:byAnime | ✅ | 完整实现 |
| 批量获取进度 | GET /batch | history:batchProgress | ✅ | 完整实现 |
| 删除播放历史 | POST /delete | history:delete | ✅ | 完整实现 |

### Update 路由 (/api/update)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 检查更新 | GET /check | update:check | ✅ | electron-updater 实现 |
| 获取更新信息 | GET /info | update:check | ✅ | 包含在 check 响应中 |
| 下载更新 | - | update:download | ✅ | electron-updater 实现 |
| 安装更新 | - | update:install | ✅ | electron-updater 实现 |
| 下载进度 | - | update:onProgress | ✅ | Electron 新增 |
| 更新通道 | - | update:setChannel | ✅ | 支持 stable/beta |

### Settings 路由 (/api/settings)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 获取主题 | GET /theme | settings:get | ✅ | 完整实现 |
| 设置主题 | POST /theme | settings:set | ✅ | 完整实现 |
| 检查更新 | GET /check_update | - | ⚠️ | 移动到 update |
| 获取所有设置 | - | settings:getAll | ✅ | Electron 新增 |

### Proxy 路由 (/proxy)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 代理剧集 API | GET /episode-api | anime:video | ✅ | 完整实现 |
| 代理视频 URL | GET /video | anime:video:proxy | ✅ | 完整实现 |
| 代理 M3U8 | GET /m3u8 | - | ❌ | **缺失** |
| 代理视频流 | GET /video-stream | - | ❌ | **缺失** |

### Auto Download 路由 (/api/auto-download)

| 原 Python 功能 | 方法 | Electron IPC | 状态 | 备注 |
|---------------|------|-------------|------|------|
| 获取配置 | GET /config | autoDownload:getConfig | ✅ | 完整实现 |
| 更新配置 | POST /config | autoDownload:updateConfig | ✅ | 完整实现 |
| 开始下载 | POST /start | download:add | ⚠️ | 基础实现 |
| 获取进度 | GET /progress | autoDownload:getStatus | ✅ | 完整实现 |
| 获取下载列表 | GET /list | download:list | ✅ | 完整实现 |
| 取消下载 | POST /cancel | download:cancel | ✅ | 完整实现 |
| 获取下载历史 | GET /history | autoDownload:getHistory | ✅ | 新增 |
| 预览筛选结果 | POST /filter/preview | autoDownload:previewFilter | ✅ | 新增 |
| 手动执行检查 | POST /check | autoDownload:runCheck | ✅ | 新增 |

## 页面功能对比

### Home.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 番剧列表展示 | ✅ | ✅ | 完成 |
| 搜索功能 | ✅ | ✅ | 完成 |
| 分页功能 | ✅ | ✅ | 完成 |
| 收藏按钮 | ✅ | ✅ | 完成 |
| 封面懒加载 | ✅ | ✅ | 完成 |
| 成人内容标记(🔞) | ✅ | ✅ | 完成 |
| 滚动位置恢复 | ✅ | ✅ | 完成 |
| 批量检查收藏状态 | ✅ | ✅ | 完成 |

### Detail.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 番剧信息展示 | ✅ | ✅ | 完成 |
| Bangumi 信息 | ✅ | ✅ | 完成 |
| 剧集列表 | ✅ | ✅ | 完成 |
| 视频播放 | ✅ | ✅ | 完成 |
| 播放进度保存 | ✅ | ✅ | 完成 |
| 收藏功能 | ✅ | ✅ | 完成 |
| anime1.pw 特殊处理 | ✅ | ✅ | 完成 |

### Favorites.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 收藏列表展示 | ✅ | ✅ | 完成 |
| 更新提醒 | ✅ | ✅ | 完成 |
| 播放进度显示 | ✅ | ✅ | 完成 |
| 取消收藏 | ✅ | ✅ | 完成 |

### Downloads.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 下载列表 | ✅ | ✅ | 完成 |
| 进度显示 | ✅ | ✅ | 完成 |
| 暂停/恢复 | ✅ | ✅ | 完成 |
| 取消下载 | ✅ | ✅ | 完成 |
| 打开文件夹 | ✅ | ⚠️ | 需要完善 |
| 自动刷新 | - | ✅ | Electron 新增 |

### History.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 播放历史列表 | ✅ | ✅ | 完成 |
| 播放进度显示 | ✅ | ✅ | 完成 |
| 相对时间显示 | ✅ | ✅ | 完成 |
| 清空历史 | ✅ | ✅ | 完成 |

### Settings.vue

| 功能 | 原 Python | Electron | 状态 |
|------|----------|----------|------|
| 主题设置 | ✅ | ✅ | 完成 |
| 播放设置 | ✅ | ✅ | 完成 |
| 下载设置 | ✅ | ⚠️ | 基础实现 |
| 更新检查 | ✅ | ⚠️ | 需要重新设计 |
| 关于信息 | ✅ | ✅ | 完成 |

## 缺失功能清单

### 高优先级
1. **anime1.pw 剧集解析** - 原项目有特殊处理，Electron 版本缺失
2. **更新功能重新设计** - 使用 Electron 成熟方案 + GitHub Releases
3. **播放历史管理** - 删除历史、批量获取进度

### 中优先级
4. **自动下载配置** - 配置页面和完整功能
5. **强制刷新缓存** - 阻塞式完整刷新
6. **M3U8/视频流代理** - 如果需要支持 HLS

### 低优先级
7. **性能追踪 API** - 原项目有详细的 trace 功能
8. **详细设置选项** - 更多配置项
