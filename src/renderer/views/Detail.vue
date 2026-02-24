<template>
  <div class="detail-container" data-testid="anime-detail">
    <!-- 面包屑导航 -->
    <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="goBack" class="back-btn">
        返回
      </el-button>
      <el-breadcrumb separator="/" class="breadcrumb-nav">
        <el-breadcrumb-item>
          <router-link to="/">番剧列表</router-link>
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="anime?.title">
          {{ anime.title }}
        </el-breadcrumb-item>
        <el-breadcrumb-item v-else-if="loading">
          加载中...
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误状态 -->
    <el-alert
      v-else-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      class="error-alert"
    >
      <template #default>
        <el-button type="primary" size="small" @click="loadData" style="margin-top: 10px;">
          重新加载
        </el-button>
      </template>
    </el-alert>

    <!-- 主要内容 -->
    <div v-else-if="anime" class="detail-content">
      <!-- 番剧信息侧边栏 -->
      <el-aside class="info-sidebar">
        <div class="sidebar-content">
          <!-- 封面 -->
          <div class="cover-wrapper">
            <el-image
              :src="anime.coverUrl || defaultCover"
              class="cover-image"
              fit="cover"
            >
              <template #error>
                <div class="cover-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <!-- 收藏按钮 -->
            <el-button
              :icon="isFavorite ? StarFilled : Star"
              circle
              class="favorite-btn"
              :class="{ active: isFavorite }"
              :loading="favoriteLoading"
              @click="toggleFavorite"
            />
          </div>

          <!-- 信息区 -->
          <div class="info-section">
            <h2 class="anime-title">{{ anime.title }}</h2>
            
            <div class="meta-list">
              <div class="meta-item">
                <span class="meta-label">年份</span>
                <span class="meta-value">{{ anime.year || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">季度</span>
                <span class="meta-value">{{ anime.season || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">字幕</span>
                <span class="meta-value">{{ anime.subtitleGroup || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">更新</span>
                <span class="meta-value">
                  {{ episodes.length > 0 ? `共 ${episodes.length} 话` : '暂无更新' }}
                </span>
              </div>
            </div>

            <!-- Bangumi 信息 -->
            <div v-if="bangumiInfo" class="bangumi-section">
              <div v-if="bangumiInfo.rating" class="rating">
                <span class="rating-value">{{ bangumiInfo.rating.toFixed(1) }}</span>
                <span class="rating-label">分</span>
                <span v-if="bangumiInfo.rank" class="rank">#{{ bangumiInfo.rank }}</span>
              </div>
              
              <div v-if="bangumiInfo.summary" class="summary">
                <h4>简介</h4>
                <p>{{ summaryExpanded ? bangumiInfo.summary : truncateText(bangumiInfo.summary, 150) }}</p>
                <el-link v-if="bangumiInfo.summary.length > 150" @click="summaryExpanded = !summaryExpanded">
                  {{ summaryExpanded ? '收起' : '展开' }}
                </el-link>
              </div>

              <div v-if="bangumiInfo.genres?.length" class="genres">
                <h4>类型</h4>
                <div class="genre-tags">
                  <el-tag v-for="genre in bangumiInfo.genres" :key="genre" size="small">
                    {{ genre }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- Bangumi 加载中 -->
            <div v-else-if="bangumiLoading" class="bangumi-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载 Bangumi 信息...</span>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <!-- 视频播放器 -->
        <el-card class="video-section" shadow="never">
          <template #header>
            <div class="video-header">
              <span v-if="currentEpisode">
                第 {{ currentEpisode.episode }} 话 - {{ currentEpisode.title || '' }}
              </span>
              <span v-else>选择剧集观看</span>
            </div>
          </template>
          
          <div class="video-container">
            <!-- 视频加载中 -->
            <div v-if="videoLoading" class="video-loading">
              <el-icon class="is-loading" :size="40"><Loading /></el-icon>
              <span>正在加载视频...</span>
            </div>
            
            <!-- 视频错误 -->
            <div v-else-if="videoError" class="video-error">
              <el-icon :size="48" color="#f56c6c"><Warning /></el-icon>
              <p>{{ videoError }}</p>
              <el-button type="primary" @click="retryVideo">重新加载</el-button>
            </div>
            
            <!-- 视频播放器 -->
            <video
              v-else-if="videoUrl"
              ref="videoPlayer"
              :src="videoUrl"
              controls
              class="video-player"
              @play="onVideoPlay"
              @pause="onVideoPause"
              @timeupdate="onTimeUpdate"
              @error="onVideoError"
            ></video>
            
            <!-- 空状态 -->
            <div v-else class="video-placeholder">
              <el-icon :size="60"><VideoPlay /></el-icon>
              <p>选择下方剧集开始观看</p>
            </div>
          </div>
        </el-card>

        <!-- 剧集列表 -->
        <el-card class="episodes-section" shadow="never">
          <template #header>
            <div class="section-header">
              <span>全部剧集</span>
              <span class="episode-count">共 {{ episodes.length }} 话</span>
            </div>
          </template>

          <div v-if="episodes.length > 0" class="episode-grid">
            <div
              v-for="(ep, idx) in episodes"
              :key="ep.id"
              class="episode-card"
              :class="{ active: currentEpisodeIndex === idx }"
              @click="playEpisode(idx)"
            >
              <div class="episode-num">第{{ ep.episode }}集</div>
              <div class="episode-date">{{ ep.date }}</div>
            </div>
          </div>

          <el-empty v-else description="暂无剧集数据" />
        </el-card>
      </el-main>
    </div>

    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Star, StarFilled, Picture, Loading, Warning, VideoPlay } from '@element-plus/icons-vue'
import { useAnimeStore, useFavoritesStore } from '../stores'
import type { Anime, Episode, BangumiInfo } from '../../shared/types'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const animeStore = useAnimeStore()
const favoritesStore = useFavoritesStore()

const animeId = computed(() => route.params.id as string)

// 状态
const loading = ref(true)
const error = ref('')
const anime = ref<Anime | null>(null)
const episodes = ref<Episode[]>([])
const bangumiInfo = ref<BangumiInfo | null>(null)
const bangumiLoading = ref(false)

// 视频播放
const videoPlayer = ref<HTMLVideoElement | null>(null)
const currentEpisodeIndex = ref(0)
const videoUrl = ref('')
const videoLoading = ref(false)
const videoError = ref('')
const isPlaying = ref(false)

// 收藏
const isFavorite = ref(false)
const favoriteLoading = ref(false)

// UI
const summaryExpanded = ref(false)

const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="300"%3E%3Crect fill="%23f0f0f0" width="200" height="300"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" dy=".3em" text-anchor="middle" x="100" y="150"%3E暂无封面%3C/text%3E%3C/svg%3E'

const currentEpisode = computed(() => {
  if (episodes.value.length === 0) return null
  return episodes.value[currentEpisodeIndex.value]
})

// 截断文本
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 加载数据
const loadData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // 获取番剧详情
    const detailResult = await window.api.anime.getDetail({ id: animeId.value })
    if (!detailResult.success) {
      throw new Error(detailResult.error?.message || '获取番剧详情失败')
    }
    anime.value = detailResult.data
    
    // 获取剧集列表
    const episodesResult = await window.api.anime.getEpisodes({ id: animeId.value })
    if (episodesResult.success) {
      episodes.value = episodesResult.data || []
    }
    
    // 检查收藏状态
    await checkFavoriteStatus()
    
    // 加载 Bangumi 信息（异步）
    loadBangumiInfo()
    
    // 自动播放第一集
    if (episodes.value.length > 0) {
      playEpisode(0)
    }
  } catch (err: any) {
    error.value = err.message || '加载失败'
    console.error('[Detail] 加载失败:', err)
  } finally {
    loading.value = false
  }
}

// 加载 Bangumi 信息
const loadBangumiInfo = async () => {
  if (!anime.value) return
  
  bangumiLoading.value = true
  try {
    const result = await window.api.anime.getBangumiInfo({ id: animeId.value })
    if (result.success) {
      bangumiInfo.value = result.data
    }
  } catch (err) {
    console.error('[Detail] 加载 Bangumi 信息失败:', err)
  } finally {
    bangumiLoading.value = false
  }
}

// 检查收藏状态
const checkFavoriteStatus = async () => {
  try {
    const result = await window.api.favorite.check({ animeId: animeId.value })
    if (result.success) {
      isFavorite.value = result.data
    }
  } catch (err) {
    console.error('[Detail] 检查收藏状态失败:', err)
  }
}

// 切换收藏
const toggleFavorite = async () => {
  if (!anime.value) return
  
  favoriteLoading.value = true
  try {
    if (isFavorite.value) {
      await window.api.favorite.remove({ animeId: animeId.value })
      isFavorite.value = false
      ElMessage.success('已取消收藏')
    } else {
      await window.api.favorite.add({
        animeId: animeId.value,
        title: anime.value.title,
        coverUrl: anime.value.coverUrl,
        detailUrl: anime.value.detailUrl
      })
      isFavorite.value = true
      ElMessage.success('已添加到收藏')
    }
    // 刷新收藏列表
    await favoritesStore.loadFavorites()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    favoriteLoading.value = false
  }
}

// 播放剧集
const playEpisode = async (idx: number) => {
  if (idx < 0 || idx >= episodes.value.length) return
  
  currentEpisodeIndex.value = idx
  const ep = episodes.value[idx]
  
  videoLoading.value = true
  videoError.value = ''
  videoUrl.value = ''
  
  try {
    // 调用爬虫服务提取视频 URL
    const result = await window.api.anime.extractVideo({ episodeUrl: ep.url })
    
    if (!result.success) {
      throw new Error(result.error?.message || '提取视频失败')
    }
    
    videoUrl.value = result.data.url
    videoLoading.value = false
    
    // 视频加载后自动播放
    setTimeout(() => {
      videoPlayer.value?.play().catch(() => {
        // 自动播放被阻止，用户需要手动点击
      })
    }, 100)
  } catch (err: any) {
    videoError.value = err.message || '视频加载失败'
    videoLoading.value = false
  }
}

// 重新加载视频
const retryVideo = () => {
  if (currentEpisode.value) {
    playEpisode(currentEpisodeIndex.value)
  }
}

// 播放进度保存定时器
let saveProgressTimer: number | null = null

// 视频事件处理
const onVideoPlay = () => {
  isPlaying.value = true
  // 启动定时保存
  if (!saveProgressTimer) {
    saveProgressTimer = window.setInterval(() => {
      saveProgress()
    }, 10000) // 每 10 秒保存一次
  }
}

const onVideoPause = () => {
  isPlaying.value = false
  // 停止定时保存
  if (saveProgressTimer) {
    clearInterval(saveProgressTimer)
    saveProgressTimer = null
  }
  // 暂停时立即保存一次
  saveProgress()
}

const saveProgress = async () => {
  if (!videoPlayer.value || !currentEpisode.value || !anime.value) return
  
  const currentTime = videoPlayer.value.currentTime
  const duration = videoPlayer.value.duration || 0
  
  // 只保存有效进度（大于5秒）
  if (currentTime < 5) return
  
  try {
    await window.api.history.save({
      animeId: animeId.value,
      animeTitle: anime.value.title,
      episodeId: currentEpisode.value.id,
      episodeNum: parseInt(currentEpisode.value.episode) || 0,
      positionSeconds: currentTime,
      totalSeconds: duration,
      coverUrl: anime.value.coverUrl
    })
  } catch (err) {
    console.error('[Video] 保存进度失败:', err)
  }
}

const onTimeUpdate = (e: Event) => {
  const video = e.target as HTMLVideoElement
  // 每 30 秒保存一次（由定时器处理）
}

const onVideoError = () => {
  videoError.value = '视频加载失败，请稍后重试'
}

// 组件卸载时清理
onUnmounted(() => {
  if (saveProgressTimer) {
    clearInterval(saveProgressTimer)
    saveProgressTimer = null
  }
})

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.detail-container {
  min-height: 100%;
  background: var(--el-bg-color-page);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}

.back-btn {
  flex-shrink: 0;
}

.breadcrumb-nav {
  flex: 1;
}

.loading-state {
  padding: 40px;
}

.error-alert {
  margin: 24px;
}

.detail-content {
  display: flex;
  gap: 24px;
  padding: 24px;
}

.info-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.sidebar-content {
  background: var(--el-bg-color);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--el-border-color);
}

.cover-wrapper {
  position: relative;
}

.cover-image {
  width: 100%;
  aspect-ratio: 2/3;
  display: block;
}

.cover-placeholder {
  width: 100%;
  aspect-ratio: 2/3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
}

.favorite-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
}

.favorite-btn.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.15);
}

.info-section {
  padding: 16px;
}

.anime-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
  line-height: 1.4;
}

.meta-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.meta-label {
  color: var(--el-text-color-secondary);
}

.meta-value {
  color: var(--el-text-color-primary);
}

.bangumi-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color);
}

.rating {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}

.rating-value {
  font-size: 32px;
  font-weight: 700;
  color: #ff6b9d;
}

.rating-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.rank {
  margin-left: 8px;
  padding: 2px 8px;
  background: rgba(124, 92, 255, 0.1);
  color: #7c5cff;
  border-radius: 4px;
  font-size: 12px;
}

.summary, .genres {
  margin-bottom: 16px;
}

.summary h4, .genres h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--el-text-color-primary);
}

.summary p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
  margin: 0 0 8px;
}

.genre-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.bangumi-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.main-content {
  flex: 1;
  min-width: 0;
  padding: 0;
}

.video-section {
  margin-bottom: 24px;
}

.video-header {
  font-weight: 500;
}

.video-container {
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-player {
  width: 100%;
  height: 100%;
}

.video-loading,
.video-error,
.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #fff;
}

.video-error {
  text-align: center;
  padding: 24px;
}

.video-error p {
  margin: 0;
  color: #f56c6c;
}

.video-placeholder {
  color: var(--el-text-color-secondary);
}

.video-placeholder p {
  margin: 0;
}

.episodes-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.episode-count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.episode-card {
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.episode-card:hover {
  background: var(--el-fill-color);
  transform: translateY(-2px);
}

.episode-card.active {
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.15) 0%, rgba(124, 92, 255, 0.15) 100%);
  border: 1px solid #7c5cff;
}

.episode-num {
  font-weight: 500;
  margin-bottom: 4px;
}

.episode-date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 900px) {
  .detail-content {
    flex-direction: column;
  }
  
  .info-sidebar {
    width: 100%;
  }
  
  .sidebar-content {
    display: flex;
    gap: 16px;
  }
  
  .cover-wrapper {
    width: 150px;
    flex-shrink: 0;
  }
  
  .info-section {
    flex: 1;
  }
}
</style>
