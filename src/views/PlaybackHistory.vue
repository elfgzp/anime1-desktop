<template>
  <div class="playback-history-container">
    <el-card shadow="never" class="page-header-card">
      <h1 class="page-title">观看历史</h1>
    </el-card>

    <!-- 加载中 -->
    <el-skeleton v-if="loading" :rows="10" animated />

    <!-- 历史列表 -->
    <div v-else-if="historyList.length > 0" class="history-list">
      <el-card
        v-for="item in historyList"
        :key="item.id"
        class="history-card"
        shadow="hover"
      >
        <router-link :to="ROUTES.ANIME_DETAIL(item.anime_id)" class="card-link">
          <div class="card-cover" :class="{ 'cover-loading': !item.cover_url && !item._coverFailed }">
            <el-image
              v-if="item.cover_url"
              :src="item.cover_url"
              :alt="item.anime_title"
              fit="cover"
              loading="lazy"
              :preview-src-list="[]"
              @error="handleImageError(item)"
            />
            <div v-else-if="item._coverFailed" class="no-cover">📺</div>
            <div v-else class="cover-placeholder">
              <el-icon><Picture /></el-icon>
            </div>
          </div>
          <div class="card-content">
            <div class="card-title">{{ item.anime_title }}</div>
            <div class="card-meta">
              <el-tag size="small" type="info">第{{ item.episode_num }}集</el-tag>
              <el-tag size="small" type="primary">
                看到 {{ item.position_formatted }}
              </el-tag>
              <el-tag
                size="small"
                :type="getProgressTagType(item)"
              >
                {{ getProgressPercent(item) }}%
              </el-tag>
            </div>
          </div>
        </router-link>
        <div class="progress-bar-container">
          <el-progress
            :percentage="getProgressPercent(item)"
            :stroke-width="6"
            :show-text="false"
            :color="getProgressColor(item)"
          />
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无观看历史" />
    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { playbackAPI, animeAPI } from '../utils/api'
import { ROUTES, ERROR_MESSAGES } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const historyList = ref([])

// 安全转义文本 - 防止 XSS
const escapeText = (text) => {
  if (text == null) return ''
  return DOMPurify.sanitize(String(text), { ALLOWED_TAGS: [], KEEP_CONTENT: true })
}

// 获取播放进度百分比
const getProgressPercent = (item) => {
  if (item.total_seconds > 0) {
    return Math.min(100, Math.round((item.position_seconds / item.total_seconds) * 100))
  }
  // 如果没有总时长，根据进度条显示为中等
  return 50
}

// 获取进度标签类型
const getProgressTagType = (item) => {
  const percent = getProgressPercent(item)
  if (percent >= 90) return 'success'
  if (percent >= 50) return 'primary'
  return 'info'
}

// 获取进度条颜色
const getProgressColor = (item) => {
  const percent = getProgressPercent(item)
  if (percent >= 90) return '#67c23a'
  if (percent >= 50) return '#409eff'
  return '#909399'
}

const fetchHistory = async () => {
  loading.value = true
  try {
    const response = await playbackAPI.getList(50)
    if (response.success && response.data) {
      // 净化数据防止 XSS
      historyList.value = response.data.map(item => ({
        ...item,
        anime_title: escapeText(item.anime_title)
      }))

      // 异步获取封面（后台加载，不阻塞显示）
      if (historyList.value.length > 0) {
        historyList.value.forEach(item => {
          if (!item.cover_url) {
            animeAPI.getCover(item.anime_title).then(response => {
              if (response.data && response.data.coverUrl) {
                item.cover_url = response.data.coverUrl
              }
            }).catch(() => {}) // 静默处理
          }
        })
      }
    }
  } catch (error) {
    console.error('获取观看历史失败:', error)
    ElMessage.error(ERROR_MESSAGES.NETWORK_ERROR)
  } finally {
    loading.value = false
  }
}

const handleImageError = (item) => {
  item._coverFailed = true
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.playback-history-container {
  max-width: 1400px;
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  transition: transform 0.3s, box-shadow 0.3s;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.history-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 20px rgba(124, 92, 255, 0.15);
  border-color: var(--el-color-primary);
}

.card-link {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-cover {
  width: 80px;
  height: 107px;
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.card-cover .el-image {
  width: 100%;
  height: 100%;
}

.no-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: linear-gradient(135deg, #252542 0%, #1a1a2e 100%);
  color: var(--el-text-color-placeholder);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--el-text-color-placeholder);
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
}

.cover-loading {
  background: linear-gradient(90deg,
    var(--el-fill-color-light) 25%,
    var(--el-fill-color) 50%,
    var(--el-fill-color-light) 75%
  );
  background-size: 200% 100%;
  animation: cover-loading 1.5s infinite;
}

@keyframes cover-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 10px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.progress-bar-container {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0 15px 12px;
}

.progress-bar-container :deep(.el-progress) {
  margin-top: 8px;
}

@media (max-width: 600px) {
  .card-link {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-cover {
    width: 100%;
    height: auto;
    aspect-ratio: 2/3;
  }

  .history-card {
    padding-bottom: 40px;
  }
}
</style>
