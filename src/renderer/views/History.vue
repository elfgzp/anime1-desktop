<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1>观看历史</h1>
      <div class="header-actions">
        <el-button :icon="Delete" @click="clearHistory" :disabled="history.length === 0">
          清空历史
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
        v-else-if="history.length === 0"
        description="还没有观看记录"
      >
        <template #image>
          <el-icon :size="80" color="#dcdfe6"><Clock /></el-icon>
        </template>
        <el-button type="primary" @click="goToHome">去浏览番剧</el-button>
      </el-empty>

      <!-- 历史列表 -->
      <div v-else class="history-list">
        <div
          v-for="item in history"
          :key="`${item.animeId}-${item.episodeId}`"
          class="history-item"
          @click="goToDetail(item.animeId, item.episodeId)"
        >
          <div class="item-cover">
            <el-image :src="item.coverUrl || defaultCover" fit="cover" />
          </div>
          <div class="item-info">
            <h4 class="item-title">{{ item.title }}</h4>
            <p class="item-episode">{{ item.episodeTitle }}</p>
            <div class="item-meta">
              <el-progress
                :percentage="getProgressPercent(item)"
                :show-text="false"
                class="progress-bar"
              />
              <span class="progress-text">{{ formatTime(item.progress) }} / {{ formatTime(item.duration) }}</span>
            </div>
          </div>
          <div class="item-time">
            {{ formatDate(item.playedAt) }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Delete, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface PlaybackHistory {
  id: number
  animeId: string
  episodeId: string
  title: string
  episodeTitle: string
  progress: number
  duration: number
  coverUrl?: string
  playedAt: number
}

const router = useRouter()

const history = ref<PlaybackHistory[]>([])
const loading = ref(false)

const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="300"%3E%3Crect fill="%23f0f0f0" width="200" height="300"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" dy=".3em" text-anchor="middle" x="100" y="150"%3E暂无封面%3C/text%3E%3C/svg%3E'

// 格式化日期
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return minutes < 1 ? '刚刚' : `${minutes}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  }
  
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}

// 格式化时间
const formatTime = (seconds: number) => {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 获取进度百分比
const getProgressPercent = (item: PlaybackHistory) => {
  if (!item.duration) return 0
  return Math.min(100, Math.round((item.progress / item.duration) * 100))
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const result = await window.api.history.getList({ limit: 100 })
    if (result.success) {
      history.value = result.data.map((item: any) => ({
        id: item.id,
        animeId: item.animeId,
        episodeId: item.episodeId,
        title: item.animeTitle,
        episodeTitle: `第 ${item.episodeNum} 话`,
        progress: item.positionSeconds,
        duration: item.totalSeconds,
        coverUrl: item.coverUrl,
        playedAt: item.lastWatchedAt
      }))
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载历史记录失败')
  } finally {
    loading.value = false
  }
}

// 跳转到详情页
const goToDetail = (animeId: string, episodeId?: string) => {
  router.push({
    path: `/anime/${animeId}`,
    query: episodeId ? { episode: episodeId } : undefined
  })
}

// 跳转到首页
const goToHome = () => {
  router.push('/')
}

// 清空历史
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有观看历史吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await window.api.history.clear()
    if (result.success) {
      history.value = []
      ElMessage.success('已清空观看历史')
    }
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '操作失败')
    }
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-page {
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

.main-content {
  padding: 24px 40px;
}

.loading-state {
  padding: 40px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.item-cover {
  width: 120px;
  aspect-ratio: 2/3;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.item-cover :deep(.el-image) {
  width: 100%;
  height: 100%;
}

.item-cover :deep(.el-image__inner) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-episode {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 150px;
}

.progress-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.item-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .main-content {
    padding: 16px 20px;
  }
  
  .history-item {
    padding: 12px;
    gap: 12px;
  }
  
  .item-cover {
    width: 80px;
  }
  
  .item-title {
    font-size: 14px;
  }
  
  .item-episode {
    font-size: 12px;
  }
  
  .progress-bar {
    width: 100px;
  }
  
  .progress-text {
    display: none;
  }
}
</style>
