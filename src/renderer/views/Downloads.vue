<template>
  <div class="downloads-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1>下载管理</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" circle @click="refreshDownloads" :loading="loading" />
        <el-button type="primary" :icon="Plus" @click="showAddDialog = true">
          新建下载
        </el-button>
      </div>
    </header>

    <main class="main-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <el-empty
        v-else-if="tasks.length === 0"
        description="暂无下载任务"
      >
        <template #image>
          <el-icon :size="80" color="#dcdfe6"><Download /></el-icon>
        </template>
        <el-button type="primary" @click="showAddDialog = true">新建下载</el-button>
      </el-empty>

      <!-- 下载列表 -->
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
    </main>

    <!-- 新建下载对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="新建下载"
      width="500px"
    >
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, Plus, Download, VideoPause, VideoPlay, CircleClose, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

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
}

const tasks = ref<DownloadTask[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const adding = ref(false)

const newTask = ref({
  url: '',
  filename: ''
})

// 格式化文件大小
const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化速度
const formatSpeed = (bytesPerSecond: number) => {
  return formatSize(bytesPerSecond) + '/s'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    downloading: '下载中',
    paused: '已暂停',
    completed: '已完成',
    error: '失败'
  }
  return statusMap[status] || status
}

// 获取状态类型（用于 tag 颜色）
const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    pending: 'info',
    downloading: 'primary',
    paused: 'warning',
    completed: 'success',
    error: 'danger'
  }
  return typeMap[status] || ''
}

// 加载下载任务
const loadTasks = async () => {
  loading.value = true
  try {
    const result = await window.api.download.getList()
    if (result.success) {
      tasks.value = result.data || []
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载下载任务失败')
  } finally {
    loading.value = false
  }
}

// 刷新下载列表
const refreshDownloads = () => {
  loadTasks()
}

// 添加下载任务
const addTask = async () => {
  if (!newTask.value.url.trim()) {
    ElMessage.warning('请输入视频URL')
    return
  }
  
  adding.value = true
  try {
    const filename = newTask.value.filename.trim()
    const result = await window.api.download.add({
      url: newTask.value.url.trim(),
      filename: filename || 'download.mp4'
    })
    if (result.success) {
      ElMessage.success('下载任务已创建')
      showAddDialog.value = false
      newTask.value = { url: '', filename: '' }
      await loadTasks()
    }
  } catch (err: any) {
    ElMessage.error(err.message || '创建下载任务失败')
  } finally {
    adding.value = false
  }
}

// 暂停下载
const pauseTask = async (taskId: string) => {
  try {
    await window.api.download.pause({ taskId })
    ElMessage.success('已暂停')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

// 恢复下载
const resumeTask = async (taskId: string) => {
  try {
    await window.api.download.resume({ taskId })
    ElMessage.success('开始下载')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

// 取消下载
const cancelTask = async (taskId: string) => {
  try {
    await window.api.download.cancel({ taskId })
    ElMessage.success('已取消')
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

// 打开文件夹
const openFolder = (_task: DownloadTask) => {
  // TODO: 实现打开文件夹功能
  ElMessage.info('功能开发中...')
}

onMounted(() => {
  loadTasks()
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

.main-content {
  padding: 24px 40px;
}

.loading-state {
  padding: 40px;
}

.download-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.download-card {
  transition: transform 0.2s;
}

.download-card:hover {
  transform: translateY(-2px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-episode {
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

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .main-content {
    padding: 16px 20px;
  }
}
</style>
