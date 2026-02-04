<template>
  <div class="settings-container">
    <el-card shadow="never" class="page-header-card">
      <h1 class="page-title">设置</h1>
    </el-card>

    <!-- 外观设置 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">外观</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>主题模式</span>
        </div>
        <div class="settings-control">
          <el-select v-model="theme" @change="handleThemeChange" class="theme-select">
            <el-option label="跟随系统" :value="THEME.SYSTEM" />
            <el-option label="暗黑模式" :value="THEME.DARK" />
            <el-option label="普通模式" :value="THEME.LIGHT" />
          </el-select>
        </div>
      </div>
    </el-card>

    <!-- 更新设置 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">更新</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>当前版本</span>
          <div class="settings-desc">{{ currentVersion }}</div>
        </div>
        <div class="settings-control">
          <el-button
            type="primary"
            :loading="checkingUpdate"
            @click="handleCheckUpdate"
          >
            {{ checkingUpdate ? '检查中...' : '检查更新' }}
          </el-button>
        </div>
      </div>
      <!-- 发现新版本时显示下载按钮 -->
      <div class="settings-item" v-if="updateInfo.has_update">
        <div class="settings-label">
          <span>发现新版本</span>
          <div class="settings-desc">{{ updateInfo.latest_version || '未知版本' }}</div>
        </div>
        <div class="settings-control">
          <el-button
            v-if="updateInfo.download_url"
            type="success"
            :loading="downloadingUpdate"
            :disabled="downloadProgress.status === 'downloading'"
            @click="handleDownloadUpdate"
          >
            {{ downloadingUpdate ? '下载中...' : '下载新版本' }}
          </el-button>
          <el-button
            v-else
            type="info"
            @click="handleOpenDownloadPage"
          >
            手动下载
          </el-button>
        </div>
      </div>
      <!-- 下载进度条 -->
      <div class="settings-item" v-if="downloadingUpdate && updateInfo.has_update">
        <div class="settings-label">
          <span>下载进度</span>
          <div class="settings-desc">
            {{ downloadProgress.message || '正在获取进度...' }}
            {{ formatBytes(downloadProgress.downloaded_bytes) }} / {{ formatBytes(downloadProgress.total_bytes) }}
          </div>
        </div>
        <div class="settings-control" style="width: 200px;">
          <el-progress
            :percentage="downloadProgress.percent"
            :status="downloadProgress.status === 'completed' ? 'success' : ''"
            :stroke-width="8"
          />
        </div>
      </div>
      <div class="settings-item" v-if="updateInfo.has_update && updateInfo.release_notes">
        <div class="settings-label">
          <span>发布说明</span>
        </div>
        <div class="release-notes" v-html="formatReleaseNotes(updateInfo.release_notes)"></div>
      </div>
    </el-card>

    <!-- 日志 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">日志</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>日志文件夹</span>
        </div>
        <div class="settings-control">
          <el-button
            type="primary"
            :loading="openingLogs"
            @click="handleOpenLogs"
          >
            {{ openingLogs ? '打开中...' : '打开日志文件夹' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 缓存 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">缓存</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>封面缓存</span>
          <div class="settings-desc">{{ cacheInfo.cover_count || 0 }} 条缓存，约 {{ cacheInfo.database_size_formatted || '0 B' }}</div>
        </div>
        <div class="settings-control">
          <el-button
            type="warning"
            :loading="clearingCache"
            @click="handleClearCache('covers')"
          >
            {{ clearingCache ? '清理中...' : '清理封面缓存' }}
          </el-button>
        </div>
      </div>
      <div class="settings-item">
        <div class="settings-label">
          <span>清理所有数据</span>
          <div class="settings-desc">包括封面缓存和播放记录</div>
        </div>
        <div class="settings-control">
          <el-button
            type="danger"
            :loading="clearingAllCache"
            @click="handleClearCache('all')"
          >
            {{ clearingAllCache ? '清理中...' : '清理所有数据' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 关于 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">关于</div>
      </template>
      <div class="about-info" v-if="aboutInfo">
        <p><strong>版本:</strong> {{ aboutInfo.version }}</p>
        <p><strong>更新渠道:</strong> {{ aboutInfo.channel }}</p>
        <p>
          <strong>仓库地址:</strong>
          <el-link :href="aboutInfo.repository" target="_blank" type="primary">
            {{ aboutInfo.repository }}
          </el-link>
        </p>
      </div>
      <el-skeleton v-else :rows="3" animated />
    </el-card>
    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsAPI } from '../utils/api'
import { emitCacheCleared } from '../utils/cacheEventBus'
import { useThemeStore } from '../composables/useTheme'
import { THEME, RESPONSE_FIELDS, REQUEST_PARAMS, ERROR_MESSAGES, UI_TEXT } from '../constants/api'

const SUCCESS_UPDATE_FOUND = '发现新版本'
const SUCCESS_LATEST_VERSION = '已是最新版本'
import { ElMessage, ElMessageBox } from 'element-plus'

const themeStore = useThemeStore()
const theme = ref(THEME.SYSTEM)
const checkingUpdate = ref(false)
const downloadingUpdate = ref(false)
const downloadProgress = ref({
  percent: 0,
  downloaded_bytes: 0,
  total_bytes: 0,
  status: 'idle',
  message: ''
})
let progressPollingInterval = null
const aboutInfo = ref(null)
const openingLogs = ref(false)
const cacheInfo = ref({})
const clearingCache = ref(false)
const clearingAllCache = ref(false)
const THEME_STORAGE_KEY = 'anime1_theme'

// 当前版本和更新信息
const currentVersion = ref('')
const updateInfo = ref({
  has_update: false,
  latest_version: '',
  download_url: '',
  asset_name: '',
  download_size: '',
  release_notes: '',
  is_prerelease: false
})

// 从 localStorage 读取主题设置（同步，立即显示）
const loadThemeFromStorage = () => {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY)
    if (saved && Object.values(THEME).includes(saved)) {
      theme.value = saved
      return true
    }
  } catch (e) {
    console.warn('Failed to load theme from localStorage:', e)
  }
  return false
}

const handleThemeChange = async (value) => {
  await themeStore.saveTheme(value)
  ElMessage.success(UI_TEXT.THEME_UPDATED || '主题已更新')
}

const handleCheckUpdate = async () => {
  checkingUpdate.value = true
  console.log('[UPDATE-FRONTEND] Starting update check...')
  try {
    console.log('[UPDATE-FRONTEND] Calling settingsAPI.checkUpdate()')
    const response = await settingsAPI.checkUpdate()
    const data = response.data
    console.log('[UPDATE-FRONTEND] Update check response:', data)

    // 检查是否是更新检查失败（如速率限制）
    if (data.error_type === 'update_check_failed') {
      console.log('[UPDATE-FRONTEND] Update check failed:', data.error)
      updateInfo.value = {
        has_update: false,
        latest_version: '',
        download_url: '',
        asset_name: '',
        download_size: '',
        release_notes: '',
        is_prerelease: false
      }
      // 根据错误类型显示不同的消息
      if (data.error && data.error.includes('速率限制')) {
        ElMessage.warning(ERROR_MESSAGES.CHECK_UPDATE_RATE_LIMIT)
      } else {
        ElMessage.warning(data.error || ERROR_MESSAGES.CHECK_UPDATE_FAILED)
      }
      return
    }

    if (data[RESPONSE_FIELDS.HAS_UPDATE]) {
      // 保存更新信息，显示下载按钮
      updateInfo.value = {
        has_update: true,
        latest_version: data.latest_version || '',
        download_url: data.download_url || '',
        asset_name: data.asset_name || '',
        download_size: data.download_size || '',
        release_notes: data.release_notes || '',
        is_prerelease: data.is_prerelease || false
      }
      console.log('[UPDATE-FRONTEND] Update available:', data.latest_version, 'current:', data.current_version)
      ElMessage.success(
        `${SUCCESS_UPDATE_FOUND}: ${data.latest_version}\n当前版本: ${data.current_version}`
      )
    } else {
      // 没有更新，隐藏下载按钮
      updateInfo.value = {
        has_update: false,
        latest_version: '',
        download_url: '',
        asset_name: '',
        download_size: '',
        release_notes: '',
        is_prerelease: false
      }
      console.log('[UPDATE-FRONTEND] No update available. current:', data.current_version, 'latest:', data.latest_version)
      ElMessage.info(SUCCESS_LATEST_VERSION)
    }
  } catch (error) {
    console.error('[UPDATE-FRONTEND] 检查更新失败:', error)
    ElMessage.error(ERROR_MESSAGES.CHECK_UPDATE_FAILED || '检查更新失败')
  } finally {
    checkingUpdate.value = false
  }
}

// 格式化字节为可读大小
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 发送日志到后端
const logToBackend = (message, level = 'info') => {
  if (window.js_api && typeof window.js_api.log === 'function') {
    window.js_api.log(message, level)
  }
  console.log(`[UPDATE-FRONTEND] ${message}`)
}

// 开始轮询下载进度
const startProgressPolling = () => {
  logToBackend('开始轮询下载进度')

  // 每 500ms 查询一次进度
  progressPollingInterval = setInterval(async () => {
    try {
      const response = await settingsAPI.getUpdateProgress()
      if (response.data && response.data.data) {
        const data = response.data.data
        const progress = data.progress || data
        const result = data.result || {}

        // 更新进度状态 (兼容新旧 API 格式)
        downloadProgress.value = progress

        // 发送进度到后端日志
        logToBackend(`轮询: status=${progress.status}, percent=${progress.percent}%`)

        // 如果下载完成或失败，处理结果
        if (progress.status === 'completed' || progress.status === 'failed') {
          stopProgressPolling()
          logToBackend(`下载/安装完成, result=${JSON.stringify(result)}`)

          if (result.success && result.restarting) {
            // 需要重启
            logToBackend(`执行重启, updater_type=${result.updater_type}`, 'info')
            if (result.updater_type === 'macos_dmg') {
              logToBackend('macOS DMG 模式，退出应用')
              await settingsAPI.exitApp()
            } else if (result.updater_type === 'windows' && result.updater_path) {
              logToBackend(`Windows 模式，运行更新器: ${result.updater_path}`)
              await settingsAPI.runUpdater(result.updater_path)
              await settingsAPI.exitApp()
            } else if (result.updater_type === 'linux_zip' || result.updater_type === 'macos_zip') {
              logToBackend('ZIP 模式，先退出应用再刷新')
              // 对于 ZIP 模式，需要先退出应用，然后刷新页面
              await settingsAPI.exitApp()
              // 延迟刷新页面，让退出 API 有时间执行
              setTimeout(() => {
                window.location.reload()
              }, 500)
            } else {
              logToBackend(`未知 updater_type: ${result.updater_type}`, 'warning')
              ElMessage.success(result.message || '下载并安装完成，请重启应用')
            }
          } else if (result.success) {
            // 下载完成但不需要重启（可能是手动模式）
            logToBackend('下载完成，无须重启')
            ElMessage.success(result.message || '下载完成')
          } else if (result.error || progress.status === 'failed') {
            // 下载/安装失败
            logToBackend(`下载/安装失败: ${result.error || progress.message}`, 'error')
            ElMessage.error(result.message || progress.message || '操作失败')
          }
        }
      }
    } catch (error) {
      logToBackend(`获取下载进度失败: ${error}`, 'error')
    }
  }, 500)
}

// 停止轮询
const stopProgressPolling = () => {
  if (progressPollingInterval) {
    clearInterval(progressPollingInterval)
    progressPollingInterval = null
  }
}

// 下载更新
const handleDownloadUpdate = async () => {
  if (!updateInfo.value.download_url) {
    ElMessage.warning('没有可用的下载链接')
    return
  }

  // 显示确认对话框
  const version = updateInfo.value.latest_version || ''
  const assetName = updateInfo.value.asset_name || '更新文件'

  const confirmed = await ElMessageBox.confirm(
    `确定要下载并安装更新 v${version} 吗？\n\n${assetName}`,
    '确认更新',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => true).catch(() => false)

  if (!confirmed) {
    return
  }

  downloadingUpdate.value = true
  // 重置进度状态
  downloadProgress.value = {
    percent: 0,
    downloaded_bytes: 0,
    total_bytes: 0,
    status: 'idle',
    message: ''
  }
  // 开始轮询进度
  startProgressPolling()
  console.log('[UPDATE-FRONTEND] 开始下载更新...')
  console.log('[UPDATE-FRONTEND] download_url:', updateInfo.value.download_url)
  try {
    // 使用自动安装模式（默认）
    const response = await settingsAPI.downloadUpdate(updateInfo.value.download_url, true)
    console.log('[UPDATE-FRONTEND] API 返回:', response.data)

    if (response.data.success) {
      // 检查 restarting 字段（可能在 response.data 或 response.data.data 中）
      const isRestarting = response.data.restarting || response.data.data?.restarting
      const updaterType = response.data.updater_type || response.data.data?.updater_type
      const message = response.data.message || response.data.data?.message

      console.log('[UPDATE-FRONTEND] success=true, isRestarting:', isRestarting, 'updaterType:', updaterType)
      console.log('[UPDATE-FRONTEND] message:', message)

      if (isRestarting) {
        // 自动安装模式，后端已完成安装准备
        console.log('[UPDATE-FRONTEND] 自动安装模式，调用 exitApp()...')
        ElMessage.success(message || '更新完成，正在重启...')

        // 根据 updater_type 处理不同的退出逻辑
        if (updaterType === 'macos_dmg') {
          // macOS DMG: 调用 exit API 关闭应用，updater 会在后台完成安装
          console.log('[UPDATE-FRONTEND] macos_dmg 模式，调用 settingsAPI.exitApp()...')
          await settingsAPI.exitApp()
          // 应用将在后端调用 os._exit(0) 后关闭
        } else if (updaterType === 'macos_zip') {
          // macOS ZIP: 后端已启动重启脚本，调用 exit API 关闭当前应用
          console.log('[UPDATE-FRONTEND] macos_zip 模式，调用 settingsAPI.exitApp()...')
          await settingsAPI.exitApp()
        } else if (updaterType === 'windows') {
          // Windows: 调用后端运行 updater 并退出应用
          console.log('[UPDATE-FRONTEND] Windows 模式，调用 runUpdater 然后退出...')
          const updaterPath = response.data.updater_path || response.data.data?.updater_path
          if (updaterPath) {
            await settingsAPI.runUpdater(updaterPath)
          }
          // 退出应用（让后端启动的更新器继续工作）
          if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.exit()
          } else {
            await settingsAPI.exitApp()
          }
        } else {
          // Web 模式：刷新页面
          console.log('[UPDATE-FRONTEND] Web 模式，刷新页面...')
          setTimeout(() => {
            window.location.reload()
          }, 2000)
        }
      } else {
        // 手动模式（不应该发生，因为 auto_install=true）
        console.log('[UPDATE-FRONTEND] 警告: 进入手动模式（auto_install=true 但 restarting=false）')
        console.log('[UPDATE-FRONTEND] response.data:', response.data)
        const confirmed = await ElMessageBox.confirm(
          `更新已下载到: ${response.data.data?.download_path || '未知'}\n\n请手动安装`,
          '下载完成',
          {
            confirmButtonText: '安装',
            cancelButtonText: '关闭',
            type: 'success'
          }
        ).then(() => true).catch(() => false)

        if (confirmed && response.data.data?.open_path) {
          await settingsAPI.openPath(response.data.data.open_path)
        }
      }
    } else {
      console.error('[UPDATE-FRONTEND] API 返回失败:', response.data.error)
      ElMessage.error('下载失败: ' + (response.data.error || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[UPDATE-FRONTEND] 下载更新异常:', error)
      ElMessage.warning('自动下载失败，将打开浏览器下载...')
      window.open(updateInfo.value.download_url, '_blank')
    }
  } finally {
    stopProgressPolling()
    downloadingUpdate.value = false
  }
}

// 手动打开下载页面（当没有匹配的下载链接时）
const handleOpenDownloadPage = () => {
  const repoOwner = aboutInfo.value?.repository?.split('/').slice(-2, -1)[0] || 'gzp'
  const repoName = aboutInfo.value?.repository?.split('/').pop() || 'anime1-desktop'
  const version = updateInfo.value.latest_version || 'latest'
  // 打开 GitHub Releases 页面
  window.open(`https://github.com/${repoOwner}/${repoName}/releases/tag/v${version}`, '_blank')
}

// 格式化发布说明（将 markdown 转换为简单的 HTML）
const formatReleaseNotes = (notes) => {
  if (!notes) return ''
  // 简单的 markdown 转换
  return notes
    .replace(/^### (.*$)/gm, '<h4>$1</h4>')
    .replace(/^## (.*$)/gm, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '<br><br>')
}

const loadTheme = async () => {
  // 优先从 localStorage 读取，如果读取成功则不同步服务器
  if (loadThemeFromStorage()) {
    return
  }

  // 否则从服务器加载
  try {
    const response = await settingsAPI.getTheme()
    if (response.data[RESPONSE_FIELDS.SUCCESS] && response.data[RESPONSE_FIELDS.DATA]) {
      theme.value = response.data[RESPONSE_FIELDS.DATA][REQUEST_PARAMS.THEME]
    }
  } catch (error) {
    console.error('加载主题失败:', error)
  }
}

const loadAbout = async () => {
  try {
    const response = await settingsAPI.getAbout()
    if (response.data[RESPONSE_FIELDS.SUCCESS] && response.data[RESPONSE_FIELDS.DATA]) {
      aboutInfo.value = response.data[RESPONSE_FIELDS.DATA]
    }
  } catch (error) {
    console.error('加载关于信息失败:', error)
  }
}

const handleOpenLogs = async () => {
  openingLogs.value = true
  try {
    await settingsAPI.openLogsFolder()
    ElMessage.success('已打开日志文件夹')
  } catch (error) {
    console.error('打开日志文件夹失败:', error)
    ElMessage.error('打开日志文件夹失败')
  } finally {
    openingLogs.value = false
  }
}

const loadCacheInfo = async () => {
  try {
    const response = await settingsAPI.getCacheInfo()
    if (response.data[RESPONSE_FIELDS.SUCCESS] && response.data[RESPONSE_FIELDS.DATA]) {
      cacheInfo.value = response.data[RESPONSE_FIELDS.DATA]
    }
  } catch (error) {
    console.error('加载缓存信息失败:', error)
  }
}

const handleClearCache = async (type) => {
  // 确认清理
  const confirmed = await ElMessageBox.confirm(
    type === 'all'
      ? '确定要清理所有数据吗？这将删除所有封面缓存和播放记录。'
      : '确定要清理封面缓存吗？播放记录将被保留。',
    '确认清理',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: type === 'all' ? 'danger' : 'warning'
    }
  ).then(() => true).catch(() => false)

  if (!confirmed) return

  if (type === 'all') {
    clearingAllCache.value = true
  } else {
    clearingCache.value = true
  }

  try {
    const response = await settingsAPI.clearCache(type)
    if (response.data[RESPONSE_FIELDS.SUCCESS]) {
      ElMessage.success(response.data[RESPONSE_FIELDS.MESSAGE] || '缓存已清理')
      // 发送缓存清理事件，通知其他组件刷新
      emitCacheCleared(type)
      // 刷新缓存信息
      await loadCacheInfo()
    } else {
      ElMessage.error(response.data[RESPONSE_FIELDS.ERROR] || '清理缓存失败')
    }
  } catch (error) {
    console.error('清理缓存失败:', error)
    ElMessage.error('清理缓存失败')
  } finally {
    clearingCache.value = false
    clearingAllCache.value = false
  }
}

onMounted(() => {
  loadTheme()
  loadAbout()
  loadCacheInfo()
})
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

.page-header-card {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.settings-section {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--el-border-color);
}

.settings-item:last-child {
  border-bottom: none;
}

.settings-label {
  color: var(--el-text-color-primary);
  font-size: 0.95rem;
}

.settings-desc {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.settings-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.theme-select {
  width: 200px;
}

.about-info {
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
  line-height: 1.6;
}

.about-info p {
  margin: 8px 0;
}

.about-info strong {
  color: var(--el-text-color-primary);
  margin-right: 8px;
}

/* 确保在暗色和亮色主题下都有正确的背景色 */
:deep(.el-card) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

:deep(.el-card__header) {
  background-color: var(--el-bg-color);
  border-bottom-color: var(--el-border-color);
}

:deep(.el-card__body) {
  background-color: var(--el-bg-color);
}

.release-notes {
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-top: 10px;
}

.release-notes h3,
.release-notes h4 {
  margin: 10px 0 5px;
  color: var(--el-text-color-primary);
}

.release-notes ul {
  padding-left: 20px;
  margin: 5px 0;
}

.release-notes li {
  margin: 3px 0;
}

.release-notes strong {
  color: var(--el-text-color-primary);
}

.release-notes em {
  color: var(--el-text-color-secondary);
}
</style>
