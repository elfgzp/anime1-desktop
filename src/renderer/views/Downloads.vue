<template>
  <div class="downloads-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1>下载管理</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" circle @click="refreshAll" :loading="loading" />
        <el-button type="primary" :icon="Setting" @click="showConfigDialog = true">
          自动下载规则
        </el-button>
        <el-button :icon="Plus" @click="showAddDialog = true">
          手动下载
        </el-button>
      </div>
    </header>

    <!-- 自动下载状态卡片 -->
    <div class="status-section">
      <el-card class="status-card" shadow="hover">
        <div class="status-header">
          <div class="status-title">
            <el-icon :size="20"><Timer /></el-icon>
            <span>自动下载</span>
            <el-tag :type="autoDownloadStatus?.enabled ? 'success' : 'info'" size="small">
              {{ autoDownloadStatus?.enabled ? '已启用' : '已禁用' }}
            </el-tag>
          </div>
          <el-switch
            v-model="configForm.enabled"
            @change="toggleAutoDownload"
            :loading="savingConfig"
          />
        </div>
        <div class="status-info" v-if="autoDownloadStatus">
          <div class="status-item">
            <span class="label">下载路径:</span>
            <span class="value">{{ autoDownloadStatus.downloadPath || '默认下载目录' }}</span>
          </div>
          <div class="status-item">
            <span class="label">检查间隔:</span>
            <span class="value">{{ autoDownloadStatus.checkIntervalHours }} 小时</span>
          </div>
          <div class="status-item">
            <span class="label">最大并发:</span>
            <span class="value">{{ autoDownloadStatus.filters?.maxConcurrentDownloads || 2 }} 个</span>
          </div>
          <div class="status-stats">
            <el-statistic title="待下载" :value="autoDownloadStatus.statusCounts?.pending || 0" />
            <el-statistic title="下载中" :value="autoDownloadStatus.statusCounts?.downloading || 0" />
            <el-statistic title="已完成" :value="autoDownloadStatus.statusCounts?.completed || 0" />
            <el-statistic title="失败" :value="autoDownloadStatus.statusCounts?.failed || 0" />
          </div>
        </div>
      </el-card>
    </div>

    <main class="main-content">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 当前下载任务 -->
        <el-tab-pane label="当前下载" name="current">
          <div v-if="loading" class="loading-state">
            <el-skeleton :rows="5" animated />
          </div>

          <el-empty v-else-if="tasks.length === 0" description="暂无下载任务">
            <template #image>
              <el-icon :size="80" color="#dcdfe6"><Download /></el-icon>
            </template>
          </el-empty>

          <div v-else class="download-list">
            <el-card
              v-for="task in tasks"
              :key="task.id"
              class="download-card"
              shadow="hover"
            >
              <div class="task-header">
                <div class="task-info">
                  <h4 class="task-title" :title="task.title">{{ task.title }}</h4>
                  <p class="task-episode">{{ task.episodeTitle }}</p>
                </div>
                <el-tag :type="getStatusType(task.status)" size="small">
                  {{ getStatusText(task.status) }}
                </el-tag>
              </div>

              <div class="task-progress">
                <el-progress
                  :percentage="Math.round(task.progress)"
                  :status="task.status === 'error' ? 'exception' : ''"
                />
                <div class="progress-stats">
                  <span>{{ formatSize(task.downloadedSize) }} / {{ formatSize(task.totalSize) }}</span>
                  <span v-if="task.speed > 0">{{ formatSpeed(task.speed) }}</span>
                </div>
              </div>

              <div class="task-actions">
                <template v-if="task.status === 'downloading'">
                  <el-button :icon="VideoPause" circle @click="pauseTask(task.id)" />
                </template>
                <template v-else-if="task.status === 'paused'">
                  <el-button type="primary" :icon="VideoPlay" circle @click="resumeTask(task.id)" />
                </template>
                <template v-if="task.status !== 'completed'">
                  <el-button :icon="CircleClose" circle @click="cancelTask(task.id)" />
                </template>
                <el-button v-else :icon="FolderOpened" circle @click="openFolder(task)" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 自动下载历史 -->
        <el-tab-pane label="下载历史" name="history">
          <div v-if="loadingHistory" class="loading-state">
            <el-skeleton :rows="5" animated />
          </div>

          <el-empty v-else-if="downloadHistory.length === 0" description="暂无下载历史">
            <template #image>
              <el-icon :size="80" color="#dcdfe6"><Document /></el-icon>
            </template>
          </el-empty>

          <div v-else class="history-list">
            <el-card
              v-for="record in downloadHistory"
              :key="record.episodeId"
              class="history-card"
              shadow="hover"
            >
              <div class="history-item">
                <div class="history-info">
                  <h4 class="history-title">{{ record.animeTitle }}</h4>
                  <p class="history-episode">第 {{ record.episodeNum }} 集</p>
                </div>
                <div class="history-meta">
                  <el-tag :type="getRecordStatusType(record.status)" size="small">
                    {{ getRecordStatusText(record.status) }}
                  </el-tag>
                  <span class="history-time">{{ formatTime(record.createdAt) }}</span>
                </div>
              </div>
              <div v-if="record.errorMessage" class="history-error">
                {{ record.errorMessage }}
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 手动下载对话框 -->
    <el-dialog v-model="showAddDialog" title="手动下载" width="500px">
      <el-form :model="newTask" label-width="80px">
        <el-form-item label="视频URL">
          <el-input
            v-model="newTask.url"
            placeholder="请输入视频下载链接"
          />
        </el-form-item>
        <el-form-item label="文件名">
          <el-input
            v-model="newTask.filename"
            placeholder="可选，默认使用原文件名"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addTask" :loading="adding">
          开始下载
        </el-button>
      </template>
    </el-dialog>

    <!-- 自动下载规则配置对话框 -->
    <el-dialog
      v-model="showConfigDialog"
      title="自动下载规则配置"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="configForm" label-width="120px" class="config-form">
        <!-- 基本设置 -->
        <el-divider content-position="left">基本设置</el-divider>
        
        <el-form-item label="启用自动下载">
          <el-switch v-model="configForm.enabled" />
        </el-form-item>

        <el-form-item label="下载路径">
          <el-input
            v-model="configForm.downloadPath"
            placeholder="留空使用默认下载目录"
            clearable
          >
            <template #append>
              <el-button @click="selectDownloadPath">选择</el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="检查间隔">
          <el-slider v-model="configForm.checkIntervalHours" :min="1" :max="72" show-stops :marks="{6: '6h', 12: '12h', 24: '24h'}" />
          <span class="slider-value">{{ configForm.checkIntervalHours }} 小时</span>
        </el-form-item>

        <el-form-item label="最大并发数">
          <el-slider v-model="configForm.maxConcurrentDownloads" :min="1" :max="5" show-stops />
          <span class="slider-value">{{ configForm.maxConcurrentDownloads }} 个</span>
        </el-form-item>

        <!-- 下载模式 -->
        <el-divider content-position="left">下载模式</el-divider>

        <el-form-item>
          <el-checkbox v-model="configForm.autoDownloadNew">
            自动下载新番（根据筛选条件）
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="configForm.autoDownloadFavorites">
            自动下载追番列表中的番剧
          </el-checkbox>
        </el-form-item>

        <!-- 筛选条件 -->
        <el-divider content-position="left">筛选条件</el-divider>

        <el-form-item label="年份范围">
          <div class="year-range">
            <el-input-number
              v-model="configForm.filters.minYear"
              :min="2000"
              :max="2030"
              placeholder="最小年份"
              controls-position="right"
              style="width: 120px"
            />
            <span class="range-separator">至</span>
            <el-input-number
              v-model="configForm.filters.maxYear"
              :min="2000"
              :max="2030"
              placeholder="最大年份"
              controls-position="right"
              style="width: 120px"
            />
          </div>
        </el-form-item>

        <el-form-item label="特定年份">
          <el-select
            v-model="configForm.filters.specificYears"
            multiple
            collapse-tags
            placeholder="选择特定年份"
            style="width: 100%"
          >
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year + '年'"
              :value="year"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="季度">
          <el-checkbox-group v-model="configForm.filters.seasons">
            <el-checkbox label="冬季">冬季 (1月)</el-checkbox>
            <el-checkbox label="春季">春季 (4月)</el-checkbox>
            <el-checkbox label="夏季">夏季 (7月)</el-checkbox>
            <el-checkbox label="秋季">秋季 (10月)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="最少集数">
          <el-input-number
            v-model="configForm.filters.minEpisodes"
            :min="1"
            :max="100"
            placeholder="最少集数"
            controls-position="right"
          />
        </el-form-item>

        <el-form-item label="标题包含">
          <el-input
            v-model="includePatternInput"
            placeholder="输入正则表达式，回车添加"
            @keyup.enter="addIncludePattern"
          >
            <template #append>
              <el-button @click="addIncludePattern">添加</el-button>
            </template>
          </el-input>
          <div class="pattern-tags">
            <el-tag
              v-for="(pattern, index) in configForm.filters.includePatterns"
              :key="index"
              closable
              @close="removeIncludePattern(index)"
              class="pattern-tag"
            >
              {{ pattern }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="标题排除">
          <el-input
            v-model="excludePatternInput"
            placeholder="输入正则表达式，回车添加"
            @keyup.enter="addExcludePattern"
          >
            <template #append>
              <el-button @click="addExcludePattern">添加</el-button>
            </template>
          </el-input>
          <div class="pattern-tags">
            <el-tag
              v-for="(pattern, index) in configForm.filters.excludePatterns"
              :key="index"
              closable
              @close="removeExcludePattern(index)"
              class="pattern-tag"
              type="danger"
            >
              {{ pattern }}
            </el-tag>
          </div>
        </el-form-item>

        <!-- 预览 -->
        <el-divider content-position="left">筛选预览</el-divider>

        <el-form-item>
          <el-button type="primary" :icon="View" @click="previewFilter" :loading="previewLoading">
            预览匹配结果
          </el-button>
          <span v-if="previewResult" class="preview-result">
            共 {{ previewResult.totalAnime }} 部番剧，匹配 {{ previewResult.matchedCount }} 部
          </span>
        </el-form-item>

        <div v-if="previewResult?.matchedAnime?.length" class="preview-list">
          <el-tag
            v-for="anime in previewResult.matchedAnime.slice(0, 10)"
            :key="anime.id"
            class="preview-item"
          >
            {{ anime.title }}
          </el-tag>
          <span v-if="previewResult.matchedCount > 10" class="more-text">
            还有 {{ previewResult.matchedCount - 10 }} 部...
          </span>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="savingConfig">
          保存配置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { 
  Refresh, Plus, Download, VideoPause, VideoPlay, 
  CircleClose, FolderOpened, Setting, View, Document, Timer
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { AutoDownloadConfig, DownloadRecord } from '@shared/types'
import { DownloadRecordStatus } from '@shared/types'

interface DownloadTask {
  id: string
  animeId: string
  episodeId: string
  title: string
  episodeTitle: string
  url: string
  status: 'pending' | 'downloading' | 'paused' | 'completed' | 'error'
  progress: number
  speed: number
  totalSize: number
  downloadedSize: number
  errorMessage?: string
  createdAt: number
  updatedAt: number
}

interface AutoDownloadStatus {
  enabled: boolean
  running: boolean
  downloadPath: string
  checkIntervalHours: number
  filters: any
  recentDownloads: DownloadRecord[]
  statusCounts: {
    pending: number
    downloading: number
    completed: number
    failed: number
    skipped: number
  }
}

const tasks = ref<DownloadTask[]>([])
const downloadHistory = ref<DownloadRecord[]>([])
const loading = ref(false)
const loadingHistory = ref(false)
const activeTab = ref('current')

// 手动下载对话框
const showAddDialog = ref(false)
const adding = ref(false)
const newTask = ref({ url: '', filename: '' })

// 自动下载配置对话框
const showConfigDialog = ref(false)
const savingConfig = ref(false)
const previewLoading = ref(false)
const previewResult = ref<any>(null)
const autoDownloadStatus = ref<AutoDownloadStatus | null>(null)

// 配置表单
const configForm = reactive<AutoDownloadConfig>({
  enabled: false,
  downloadPath: '',
  checkIntervalHours: 24,
  maxConcurrentDownloads: 2,
  filters: {
    specificYears: [],
    seasons: [],
    includePatterns: [],
    excludePatterns: []
  },
  autoDownloadNew: true,
  autoDownloadFavorites: false
})

// 年份选项
const yearOptions = Array.from({ length: 15 }, (_, i) => 2020 + i)

// 正则输入
const includePatternInput = ref('')
const excludePatternInput = ref('')

// 格式化文件大小
const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatSpeed = (bytesPerSecond: number) => formatSize(bytesPerSecond) + '/s'

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 状态文本和类型
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中', downloading: '下载中', paused: '已暂停',
    completed: '已完成', error: '失败'
  }
  return map[status] || status
}

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info', downloading: 'primary', paused: 'warning',
    completed: 'success', error: 'danger'
  }
  return map[status] || ''
}

const getRecordStatusText = (status: DownloadRecordStatus) => {
  const map: Record<string, string> = {
    [DownloadRecordStatus.PENDING]: '等待中',
    [DownloadRecordStatus.DOWNLOADING]: '下载中',
    [DownloadRecordStatus.COMPLETED]: '已完成',
    [DownloadRecordStatus.FAILED]: '失败',
    [DownloadRecordStatus.SKIPPED]: '已跳过'
  }
  return map[status] || status
}

const getRecordStatusType = (status: DownloadRecordStatus) => {
  const map: Record<string, any> = {
    [DownloadRecordStatus.PENDING]: 'info',
    [DownloadRecordStatus.DOWNLOADING]: 'primary',
    [DownloadRecordStatus.COMPLETED]: 'success',
    [DownloadRecordStatus.FAILED]: 'danger',
    [DownloadRecordStatus.SKIPPED]: 'warning'
  }
  return map[status] || ''
}

// 加载数据
const loadTasks = async () => {
  loading.value = true
  try {
    const result = await window.api.download.getList()
    if (result.success) tasks.value = result.data || []
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  loadingHistory.value = true
  try {
    const result = await window.api.autoDownload.getHistory({ limit: 50 })
    if (result.success) downloadHistory.value = result.data || []
  } catch (err: any) {
    console.error('加载历史失败:', err)
  } finally {
    loadingHistory.value = false
  }
}

const loadAutoDownloadStatus = async () => {
  try {
    const result = await window.api.autoDownload.getStatus()
    if (result.success && result.data) {
      autoDownloadStatus.value = result.data
      // 同步到表单
      Object.assign(configForm, result.data)
    }
  } catch (err: any) {
    console.error('加载状态失败:', err)
  }
}

const refreshAll = () => {
  loadTasks()
  loadHistory()
  loadAutoDownloadStatus()
}

// 手动下载任务
const addTask = async () => {
  if (!newTask.value.url.trim()) {
    ElMessage.warning('请输入视频URL')
    return
  }
  adding.value = true
  try {
    const result = await window.api.download.add({
      url: newTask.value.url.trim(),
      filename: newTask.value.filename.trim() || 'download.mp4'
    })
    if (result.success) {
      ElMessage.success('下载任务已创建')
      showAddDialog.value = false
      newTask.value = { url: '', filename: '' }
      await loadTasks()
    }
  } catch (err: any) {
    ElMessage.error(err.message || '创建失败')
  } finally {
    adding.value = false
  }
}

const pauseTask = async (taskId: string) => {
  try {
    await window.api.download.pause({ taskId })
    ElMessage.success('已暂停')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

const resumeTask = async (taskId: string) => {
  try {
    await window.api.download.resume({ taskId })
    ElMessage.success('开始下载')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

const cancelTask = async (taskId: string) => {
  try {
    await window.api.download.cancel({ taskId })
    ElMessage.success('已取消')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

const openFolder = async (task: DownloadTask) => {
  try {
    const path = task.episodeTitle 
      ? `/Users/${process.env.USER || ''}/Downloads/${task.episodeTitle}.mp4`
      : ''
    if (path) await window.api.system.showItemInFolder({ path })
  } catch {
    ElMessage.info('请在下载文件夹中查看')
  }
}

// 自动下载配置
const toggleAutoDownload = async () => {
  await saveConfig()
}

const selectDownloadPath = async () => {
  // 这里应该打开文件夹选择对话框
  ElMessage.info('文件夹选择功能需要额外实现')
}

const addIncludePattern = () => {
  if (!includePatternInput.value.trim()) return
  configForm.filters.includePatterns.push(includePatternInput.value.trim())
  includePatternInput.value = ''
}

const removeIncludePattern = (index: number) => {
  configForm.filters.includePatterns.splice(index, 1)
}

const addExcludePattern = () => {
  if (!excludePatternInput.value.trim()) return
  configForm.filters.excludePatterns.push(excludePatternInput.value.trim())
  excludePatternInput.value = ''
}

const removeExcludePattern = (index: number) => {
  configForm.filters.excludePatterns.splice(index, 1)
}

const previewFilter = async () => {
  previewLoading.value = true
  try {
    const result = await window.api.autoDownload.previewFilter({
      filters: configForm.filters
    })
    if (result.success) {
      previewResult.value = result.data
    }
  } catch (err: any) {
    ElMessage.error(err.message || '预览失败')
  } finally {
    previewLoading.value = false
  }
}

const saveConfig = async () => {
  savingConfig.value = true
  try {
    const result = await window.api.autoDownload.updateConfig({
      config: { ...configForm }
    })
    if (result.success) {
      ElMessage.success('配置已保存')
      showConfigDialog.value = false
      await loadAutoDownloadStatus()
    } else {
      ElMessage.error('保存失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    savingConfig.value = false
  }
}

// 自动刷新
let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadTasks()
  loadHistory()
  loadAutoDownloadStatus()
  refreshTimer = setInterval(() => {
    loadTasks()
  }, 2000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.downloads-page {
  min-height: 100%;
  background: var(--el-bg-color-page);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.status-section {
  padding: 20px 40px 0;
}

.status-card {
  margin-bottom: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.status-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  gap: 8px;
}

.status-item .label {
  color: var(--el-text-color-secondary);
  width: 80px;
}

.status-stats {
  display: flex;
  gap: 32px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.main-content {
  padding: 0 40px 24px;
}

.loading-state {
  padding: 40px;
}

.download-list,
.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 0;
}

.download-card,
.history-card {
  transition: transform 0.2s;
}

.download-card:hover,
.history-card:hover {
  transform: translateY(-2px);
}

.task-header,
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.task-info,
.history-info {
  flex: 1;
  min-width: 0;
}

.task-title,
.history-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-episode,
.history-episode {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.task-progress {
  margin-bottom: 16px;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.task-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.history-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.history-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.history-error {
  margin-top: 8px;
  padding: 8px;
  background: var(--el-color-danger-light-9);
  border-radius: 4px;
  font-size: 12px;
  color: var(--el-color-danger);
}

/* 配置表单样式 */
.config-form {
  max-height: 60vh;
  overflow-y: auto;
}

.year-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-separator {
  color: var(--el-text-color-secondary);
}

.slider-value {
  margin-left: 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.pattern-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pattern-tag {
  margin-right: 0;
}

.preview-result {
  margin-left: 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.preview-list {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-item {
  margin-right: 0;
}

.more-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
    flex-direction: column;
    gap: 12px;
  }
  
  .status-section {
    padding: 16px 20px 0;
  }
  
  .main-content {
    padding: 0 20px 16px;
  }
  
  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
