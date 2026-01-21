<template>
  <div class="detail-container">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/" class="breadcrumb-nav">
      <el-breadcrumb-item>
        <router-link to="/">番剧列表</router-link>
      </el-breadcrumb-item>
      <el-breadcrumb-item v-if="animeData?.anime?.title">
        {{ animeData.anime.title }}
      </el-breadcrumb-item>
      <el-breadcrumb-item v-else-if="loadError">
        加载失败
      </el-breadcrumb-item>
      <el-breadcrumb-item v-else-if="detailLoading">
        <span class="loading-text">加载中...</span>
      </el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 返回按钮和面包屑放在同一行 -->
    <div class="back-with-breadcrumb">
      <el-button
        :icon="ArrowLeft"
        @click="goBack"
        class="back-btn"
        :disabled="loadError && !animeData?.anime"
      >
        返回
      </el-button>
    </div>

    <!-- 页面主体结构 -->
    <div class="detail-content">
      <!-- 侧边栏 - 番剧信息 -->
      <el-aside class="episode-sidebar">
        <div class="sidebar-header">
          <!-- 封面 -->
          <div class="sidebar-cover-wrapper">
            <el-image
              v-if="animeData?.anime?.cover_url"
              :src="animeData.anime.cover_url"
              class="sidebar-cover"
              fit="cover"
              :preview-src-list="[]"
            />
            <div v-else-if="loadError" class="sidebar-cover-placeholder">
              <el-icon :size="40"><Warning /></el-icon>
            </div>
            <div v-else-if="detailLoading" class="sidebar-cover-placeholder loading">
              <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            </div>
            <div v-else class="sidebar-cover-placeholder">
              <el-icon :size="40"><Picture /></el-icon>
            </div>
            <!-- 收藏按钮（加载完成且无错误时显示） -->
            <el-button
              v-if="!detailLoading && !loadError && animeData?.anime"
              :icon="isFavorite ? StarFilled : Star"
              circle
              class="detail-favorite-btn"
              :class="{ active: isFavorite }"
              :loading="favoriteLoading"
              @click="toggleFavorite"
            />
          </div>

          <!-- 侧边栏信息区域 -->
          <div class="sidebar-info">
            <!-- 加载中状态 -->
            <div v-if="detailLoading" class="sidebar-loading">
              <el-icon class="is-loading" :size="20"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
            <!-- 错误状态 -->
            <div v-else-if="loadError" class="sidebar-error">
              <el-icon :size="24"><Warning /></el-icon>
              <span>加载失败</span>
              <el-button size="small" @click="retryLoad">重试</el-button>
            </div>
            <!-- 正常内容 -->
            <div v-else-if="animeData?.anime">
              <!-- 标题 -->
              <div class="sidebar-title">
                {{ animeData.anime.title }}
              </div>

              <!-- 元信息 -->
              <div class="sidebar-meta">
                <div class="meta-item">
                  <span class="meta-label">年份</span>
                  <span class="meta-value">{{ animeData?.anime?.year || '-' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">季度</span>
                  <span class="meta-value">{{ animeData?.anime?.season || '-' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">字幕</span>
                  <span class="meta-value">{{ animeData?.anime?.subtitle_group || '-' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">更新</span>
                  <span class="meta-value">
                    {{ (animeData?.episodes?.length || pwEpisodes.length) > 0 ? `共 ${animeData?.episodes?.length || pwEpisodes.length} 话` : '暂无更新' }}
                  </span>
                </div>
              </div>

              <!-- Bangumi 番剧信息 -->
              <div v-if="bangumiInfo" class="bangumi-info">
                <!-- 评分和排名 -->
                <div class="bangumi-rating" v-if="bangumiInfo.rating">
                  <span class="rating-value">{{ bangumiInfo.rating.toFixed(1) }}</span>
                  <span class="rating-label">分</span>
                  <span v-if="bangumiInfo.rank" class="rank-value">#{{ bangumiInfo.rank }}</span>
                </div>
                <!-- 日期和类型标签 -->
                <div class="bangumi-tags" v-if="bangumiInfo.date || bangumiInfo.type">
                  <span v-if="bangumiInfo.date" class="meta-tag">{{ bangumiInfo.date }}</span>
                  <span v-if="bangumiInfo.type" class="meta-tag">{{ bangumiInfo.type }}</span>
                </div>
                <!-- 简介 -->
                <div class="bangumi-summary" v-if="bangumiInfo.summary">
                  <div class="summary-header">简介</div>
                  <div class="summary-content" :class="{ expanded: summaryExpanded }">
                    {{ summaryExpanded ? bangumiInfo.summary : truncateText(bangumiInfo.summary, 150) }}
                  </div>
                  <el-link v-if="bangumiInfo.summary.length > 150" @click="summaryExpanded = !summaryExpanded" class="more-link">
                    {{ summaryExpanded ? '收起' : '展开' }}
                  </el-link>
                  <el-link :href="bangumiInfo.subject_url" target="_blank" class="more-link">
                    在 Bangumi 查看
                  </el-link>
                </div>
                <!--  genres -->
                <div class="bangumi-genres" v-if="bangumiInfo.genres?.length">
                  <div class="genres-label">类型</div>
                  <div class="genres-list">
                    <span v-for="(genre, idx) in bangumiInfo.genres" :key="idx" class="genre-tag">
                      {{ genre }}
                    </span>
                  </div>
                </div>
                <!-- 制作人员 -->
                <div class="bangumi-staff" v-if="bangumiInfo.staff?.length">
                  <div class="staff-label">制作</div>
                  <div class="staff-list">
                    <span v-for="(item, idx) in bangumiInfo.staff.slice(0, 5)" :key="idx" class="staff-item">
                      {{ item.role }}: {{ item.name }}
                    </span>
                  </div>
                </div>
                <!-- 声优 -->
                <div class="bangumi-cast" v-if="bangumiInfo.cast?.length">
                  <div class="cast-label">声优</div>
                  <div class="cast-list">
                    <span v-for="(item, idx) in bangumiInfo.cast.slice(0, 5)" :key="idx" class="cast-item">
                      {{ item.name }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Bangumi 加载中（在内容区域显示加载状态） -->
              <div v-if="!bangumiInfo && !loadError" class="bangumi-loading-inline">
                <el-icon class="is-loading" :size="16"><Loading /></el-icon>
                <span>正在加载 Bangumi 信息...</span>
              </div>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="detail-main">
        <!-- 视频播放器 -->
        <el-card class="video-section" shadow="never">
          <template #header>
            <div class="video-header">
              <div class="video-title">
                <span v-if="currentEpisode">{{ `第 ${currentEpisode.episode} 话` }}</span>
                <span v-else>选择剧集观看</span>
              </div>
              <div class="video-meta">
                {{ currentEpisode?.date || '' }}
              </div>
            </div>
          </template>
          <div class="video-container">
            <!-- 骨架屏：页面加载中 -->
            <div v-if="detailLoading" class="video-skeleton">
              <div class="skeleton-video-placeholder"></div>
            </div>
            <!-- 加载动画：前端获取剧集中 -->
            <div v-else-if="pwEpisodesLoading" class="video-loading-overlay">
              <div class="video-loading-content">
                <el-icon class="is-loading" :size="40"><Loading /></el-icon>
                <span class="video-loading-text">正在加载剧集...</span>
              </div>
            </div>
            <!-- 视频加载中 -->
            <div v-else-if="videoLoading" class="video-loading">
              <div class="video-loading-content">
                <el-icon class="is-loading" :size="50"><Loading /></el-icon>
                <span class="video-loading-text">{{ loadingText }}</span>
              </div>
            </div>
            <!-- 播放器错误 -->
            <div v-else-if="videoError" class="video-error">
              <div class="video-error-icon">&#9888;</div>
              <div class="video-error-title">{{ videoErrorTitle }}</div>
              <div class="video-error-message">{{ videoErrorMessage }}</div>
              <div class="video-error-suggestion">
                可能的原因：视频源限制、版权问题或网络连接问题
              </div>
              <!-- External link button for SSL errors -->
              <el-button
                v-if="videoErrorLink"
                type="primary"
                plain
                round
                size="large"
                style="margin-top: 16px;"
                @click="openExternalLink(videoErrorLink)"
              >
                <el-icon style="margin-right: 8px;"><Link /></el-icon>
                在浏览器中打开
              </el-button>
              <el-button
                plain
                round
                size="large"
                :style="videoErrorLink ? 'margin-top: 10px;' : 'margin-top: 20px;'"
                @click="playEpisode(currentEpisodeIndex)"
              >
                <el-icon style="margin-right: 8px;"><Refresh /></el-icon>
                重新加载
              </el-button>
            </div>
            <!-- Video.js 播放器 -->
            <VideoPlayer
              v-else-if="videoSrc"
              ref="videoPlayerRef"
              :src="videoSrc"
              :anime-id="animeId"
              :episode-index="currentEpisodeIndex"
              :poster="animeData?.anime?.cover_url"
              :loading="videoLoading"
              :restore-progress="currentProgress"
              @ready="onPlayerReady"
              @error="onPlayerError"
              @timeupdate="onTimeUpdate"
              @play="onPlayerPlay"
              @pause="onPlayerPause"
              @restore="onRestorePlayback"
              @restart="onRestartPlayback"
            />
            <!-- 有剧集但没有视频源时显示占位 -->
            <div v-else-if="!videoSrc && !detailLoading && !videoLoading && !videoError && hasAnyEpisodes" class="video-placeholder">
              <el-icon :size="60"><VideoPlay /></el-icon>
            </div>
          </div>
        </el-card>

        <!-- 全部剧集 -->
        <el-card class="episodes-section" shadow="never">
          <template #header>
            <div class="section-title">
              <span>全部剧集</span>
              <span class="total-episodes">
                {{ detailLoading || pwEpisodesLoading ? '加载中...' : (animeData?.episodes?.length || pwEpisodes.length) > 0 ? `共 ${animeData?.episodes?.length || pwEpisodes.length} 话` : '暂无剧集' }}
              </span>
            </div>
          </template>

          <!-- 剧集列表 -->
          <div class="episode-grid">
            <!-- 骨架屏：主加载中 -->
            <template v-if="detailLoading">
              <div v-for="n in (animeData?.episodes?.length || pwEpisodes.length || 8)" :key="n" class="episode-skeleton-card"></div>
            </template>
            <!-- 加载动画：前端获取剧集中 -->
            <template v-else-if="pwEpisodesLoading">
              <div class="loading-episodes-inline">
                <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                <span>正在加载剧集...</span>
              </div>
            </template>
            <!-- 有剧集数据：显示列表 -->
            <template v-else-if="(animeData?.episodes || pwEpisodes).length > 0">
              <div
                v-for="(ep, idx) in (animeData?.episodes || pwEpisodes)"
                :key="idx"
                class="episode-card"
                :class="{
                  active: currentEpisodeIndex === idx,
                  'loading-progress': episodeProgressLoading
                }"
                :style="episodeProgressLoading ? {} : getEpisodeCardStyle(ep.id)"
                @click="playEpisode(idx)"
              >
                <div class="episode-card-num">第{{ ep.episode }}集</div>
                <div class="episode-card-date">{{ ep.date }}</div>
              </div>
            </template>
            <!-- 加载完成：无剧集数据 -->
            <!-- 注意：只有加载完成（detailLoading=false 且 pwEpisodesLoading=false）且确实没有数据时才显示 -->
            <template v-else-if="!isEpisodesLoading">
              <el-empty
                :description="UI_TEXT.NO_EPISODES"
                :image-size="80"
              />
            </template>
          </div>
        </el-card>
      </el-main>
    </div>

    <!-- 错误状态 - 当加载失败且没有数据时显示 -->
    <div v-if="loadError && !animeData?.anime" class="error-state">
      <el-empty :description="loadErrorMessage">
        <el-button type="primary" @click="retryLoad">重新加载</el-button>
      </el-empty>
    </div>
    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Star, StarFilled, VideoPlay, VideoCamera, Loading, Refresh, Link, Picture, Warning } from '@element-plus/icons-vue'
import { animeAPI, favoriteAPI, playbackAPI } from '../utils/api'
import { ROUTES, API_ENDPOINTS, REQUEST_PARAMS, RESPONSE_FIELDS, ERROR_MESSAGES, UI_TEXT } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage, ElNotification } from 'element-plus'
import VideoPlayer from '../components/VideoPlayer.vue'
import { measure, measureApi, tracedMeasure, startTrace, endTrace } from '../utils/performance'
import { onCacheCleared } from '../utils/cacheEventBus'

const route = useRoute()
const router = useRouter()
const animeId = computed(() => route.params.id)

// 加载状态
const loadError = ref(false)
const loadErrorMessage = ref('加载失败，请稍后重试')
const detailLoading = ref(true)  // 详情页主加载状态（骨架屏）
const animeData = ref(null)
const pwEpisodes = ref([])
const pwEpisodesLoading = ref(false)
const isPlaying = ref(false)  // 视频是否正在播放
const pwEpisodesLoadComplete = ref(false)  // 标记首次加载是否完成
const pwEpisodesLoadError = ref(false)     // 标记是否有加载错误
const anime1PwUrl = ref('')  // anime1.pw 详情页 URL
const initialVideoLoaded = ref(false)  // 标记首次视频加载是否开始
const currentEpisodeIndex = ref(0)
const videoSrc = ref('')
const videoLoading = ref(false)
const loadingText = ref('正在加载视频...')
const videoError = ref(false)
const videoErrorTitle = ref('')
const videoErrorMessage = ref('')
const videoErrorLink = ref(null)
const isFavorite = ref(false)
const favoriteLoading = ref(false)
const videoPlayerRef = ref(null)
const bangumiInfo = ref(null)
const summaryExpanded = ref(false)  // 简介展开状态
const episodeProgressMap = ref({})
const episodeProgressLoading = ref(true)  // 播放进度加载中状态
const saveTimer = ref(null)
const lastSavedTime = ref(0)
const adultContentSourceUrl = ref(null)  // 18x内容源站点URL（TLS错误时使用）

// 调试：监听 detailLoading 变化
watch(detailLoading, (newVal, oldVal) => {
  console.log('[Detail] detailLoading 变化:', oldVal, '->', newVal, ', animeData:', animeData.value ? `已加载 (${animeData.value.episodes?.length || 0} 集)` : 'null')
}, { immediate: true })

// 调试：监听 pwEpisodesLoading 变化
watch(pwEpisodesLoading, (newVal, oldVal) => {
  console.log('[Detail] pwEpisodesLoading 变化:', oldVal, '->', newVal, ', pwEpisodes:', pwEpisodes.value.length, '集')
}, { immediate: true })

// 调试：监听 animeData 变化
watch(() => animeData.value, (newVal) => {
  console.log('[Detail] animeData 变化:', newVal ? `已加载 (${newVal.episodes?.length || 0} 集)` : 'null')
}, { immediate: true })

// 调试：监听 pwEpisodes 变化
watch(pwEpisodes, (newVal) => {
  console.log('[Detail] pwEpisodes 变化:', newVal.length, '集')
}, { immediate: true })

// 调试：监听 videoSrc 变化
watch(videoSrc, (newVal, oldVal) => {
  console.log('[Detail] videoSrc 变化:', oldVal ? '有值' : 'null', '->', newVal ? `有值 (len=${newVal.length})` : 'empty')
  console.log('[Detail] 条件检查: videoLoading=', videoLoading.value, ', videoError=', videoError.value, ', !!videoSrc=', !!newVal)
  console.log('[Detail] 预期渲染: VideoPlayer =', !videoLoading.value && !videoError.value && !!newVal)
}, { immediate: true })

// 计算是否没有任何剧集数据
const hasAnyEpisodes = computed(() => {
  const animeCount = animeData.value?.episodes?.length || 0
  const pwCount = pwEpisodes.value.length
  const total = animeCount || pwCount
  console.log('[Detail] hasAnyEpisodes 计算:', { animeCount, pwCount, total, result: total > 0 })
  return total > 0
})

// 调试：video-container 的渲染条件
const videoContainerState = computed(() => {
  return {
    detailLoading: detailLoading.value,
    pwEpisodesLoading: pwEpisodesLoading.value,
    videoLoading: videoLoading.value,
    videoError: videoError.value,
    hasVideoSrc: !!videoSrc.value,
    hasAnyEpisodes: hasAnyEpisodes.value,
    渲染结果: detailLoading.value ? '骨架屏'
      : pwEpisodesLoading.value ? '加载剧集中'
      : videoLoading.value ? '视频加载中'
      : videoError.value ? '播放器错误'
      : videoSrc.value ? 'VideoPlayer'
      : hasAnyEpisodes.value ? 'video-placeholder'
      : '暂无剧集'
  }
})

// 监听 video-container 状态变化
watch(videoContainerState, (newState) => {
  console.log('[Detail] video-container 渲染:', newState.渲染结果, newState)
}, { immediate: true })

// 计算是否正在加载剧集（用于模板条件判断）
const isEpisodesLoading = computed(() => detailLoading.value || pwEpisodesLoading.value)

// 播放进度保存间隔（毫秒）
const SAVE_INTERVAL = 5000

// 安全转义文本 - 防止 XSS
const escapeText = (text) => {
  if (text == null) return ''
  return DOMPurify.sanitize(String(text), { ALLOWED_TAGS: [], KEEP_CONTENT: true })
}

// 截断文本
const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const currentEpisode = computed(() => {
  const episodes = animeData.value?.episodes || pwEpisodes.value
  if (!episodes || episodes.length === 0) return null
  return episodes[currentEpisodeIndex.value]
})

// 当前剧集的播放进度
const currentProgress = computed(() => {
  if (!currentEpisode.value) return null
  return getEpisodeProgress(currentEpisode.value.id)
})

// 查找未看完的集数（进度 > 10% 且 < 90%）
const findUnfinishedEpisode = (episodes) => {
  if (!episodes || episodes.length === 0) return -1

  const UNFINISHED_THRESHOLD = 0.9  // 90% 视为看完
  const UNSTARTED_THRESHOLD = 0.1  // 10% 以下视为未开始

  let lastUnfinishedIdx = -1
  let lastUnfinishedProgress = null

  for (let i = episodes.length - 1; i >= 0; i--) {
    const ep = episodes[i]
    const progress = episodeProgressMap.value[ep.id]

    if (progress && progress.total_seconds > 0) {
      const percent = progress.position_seconds / progress.total_seconds

      // 检查是否未看完
      if (percent > UNSTARTED_THRESHOLD && percent < UNFINISHED_THRESHOLD) {
        console.log(`[Detail] 找到未看完集数: 第${ep.episode}集, 进度${(percent * 100).toFixed(1)}%`)
        return i
      }

      // 记录最后一集有进度的集数（作为备选）
      if (percent >= UNFINISHED_THRESHOLD) {
        if (lastUnfinishedIdx === -1) {
          lastUnfinishedIdx = i
          lastUnfinishedProgress = percent
        }
      }
    }
  }

  // 如果所有集数都看完了，但最后一集有进度，返回最后一集
  if (lastUnfinishedIdx !== -1 && lastUnfinishedProgress >= 0.99) {
    // 最后一集已看完 >99%，从下一集开始
    if (lastUnfinishedIdx < episodes.length - 1) {
      console.log(`[Detail] 上一集看完，从第${episodes[lastUnfinishedIdx + 1].episode}集开始`)
      return lastUnfinishedIdx + 1
    }
  }

  // 没有找到未看完的集数
  console.log('[Detail] 没有找到未看完的集数')
  return -1
}
const getEpisodeProgress = (episodeId) => {
  return episodeProgressMap.value[episodeId] || null
}

// 获取进度百分比
const getProgressPercent = (progress) => {
  if (progress.total_seconds > 0) {
    return Math.min(100, Math.round((progress.position_seconds / progress.total_seconds) * 100))
  }
  return 0
}

// 获取集数卡片的样式（进度条效果：左深右浅）
const getEpisodeCardStyle = (episodeId) => {
  const progress = getEpisodeProgress(episodeId)
  if (!progress) return {}

  const percent = getProgressPercent(progress)
  // 进度条效果：左半边深色(已看)，右半边浅色(未看)
  // 使用 CSS 渐变实现
  return {
    '--progress-percent': `${percent}%`
  }
}

// 保存播放进度
const savePlaybackProgress = async (currentTime) => {
  if (!animeData.value || !currentEpisode.value) return
  console.log('[Detail] savePlaybackProgress 被调用', { animeId: animeId.value, currentTime })
  if (Math.abs(currentTime - lastSavedTime.value) < 2) {
    console.log('[Detail] 进度变化小于2秒，跳过保存')
    return // 进度变化小于2秒不保存
  }

  lastSavedTime.value = currentTime
  const ep = currentEpisode.value

  // 获取视频总时长
  let totalSeconds = 0
  if (videoPlayerRef.value) {
    totalSeconds = videoPlayerRef.value.getDuration() || 0
    console.log('[Detail] 视频总时长:', totalSeconds)
  }

  try {
    console.log('[Detail] 正在调用 playbackAPI.update...')
    await playbackAPI.update({
      anime_id: animeId.value,
      anime_title: animeData.value.anime.title,
      episode_id: ep.id,
      episode_num: parseInt(ep.episode) || 0,
      position_seconds: currentTime,
      total_seconds: totalSeconds,
      cover_url: animeData.value.anime.cover_url || ''
    })
    console.log('[Detail] 播放进度保存成功:', currentTime, '/', totalSeconds)

    // 更新本地缓存
    episodeProgressMap.value[ep.id] = {
      ...episodeProgressMap.value[ep.id],
      position_seconds: currentTime,
      total_seconds: totalSeconds,
      position_formatted: formatTime(currentTime)
    }
  } catch (error) {
    console.error('[Detail] 保存播放进度失败:', error)
  }
}

// 格式化时间
const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 加载该番剧的所有集数进度
const loadEpisodeProgress = async () => {
  if (!animeData.value || animeData.value.episodes.length === 0) return

  episodeProgressLoading.value = true
  console.log('[Detail] 开始加载播放进度')

  try {
    // 构建批量查询 ID
    const ids = animeData.value.episodes
      .map(ep => `${animeId.value}:${ep.id}`)
      .join(',')

    console.log('[Detail] 正在加载播放进度，ids:', ids)
    const response = await playbackAPI.batchProgress(ids)
    console.log('[Detail] 加载播放进度响应:', response.data)

    if (response.data.success && response.data.data) {
      // 转换为 map 格式
      const progressMap = {}
      for (const [key, value] of Object.entries(response.data.data)) {
        const [, episodeId] = key.split(':')
        progressMap[episodeId] = value
      }
      episodeProgressMap.value = progressMap
      console.log('[Detail] 播放进度已加载:', episodeProgressMap.value)
    }
  } catch (error) {
    console.error('[Detail] 加载播放进度失败:', error)
  } finally {
    episodeProgressLoading.value = false
    console.log('[Detail] 播放进度加载完成')
  }
}

// 启动进度保存定时器
const startProgressSaving = () => {
  console.log('[Detail] 启动进度保存定时器')
  stopProgressSaving()
  saveTimer.value = setInterval(() => {
    if (videoPlayerRef.value && videoPlayerRef.value.getCurrentTime) {
      const currentTime = videoPlayerRef.value.getCurrentTime()
      console.log('[Detail] 定时器检查当前时间:', currentTime)
      if (currentTime > 5) { // 至少播放5秒才保存
        savePlaybackProgress(currentTime)
      }
    } else {
      console.log('[Detail] videoPlayerRef.value 或 getCurrentTime 不存在')
    }
  }, SAVE_INTERVAL)
}

// 停止进度保存定时器
const stopProgressSaving = () => {
  if (saveTimer.value) {
    clearInterval(saveTimer.value)
    saveTimer.value = null
  }
}

// 净化番剧数据
const sanitizeAnimeData = (data) => {
  if (!data || !data.anime) return data

  const anime = data.anime
  return {
    ...data,
    anime: {
      ...anime,
      title: escapeText(anime.title),
      year: escapeText(anime.year),
      season: escapeText(anime.season),
      subtitle_group: escapeText(anime.subtitle_group)
    },
    episodes: (data.episodes || []).map(ep => ({
      ...ep,
      episode: escapeText(ep.episode),
      date: escapeText(ep.date)
    }))
  }
}

const fetchData = async () => {
  // 开始链路追踪 - 用于前后端关联
  startTrace('Detail_page')

  const timer = tracedMeasure('Detail_fetchData')
  loadError.value = false

  // 设置 pwEpisodesLoading=true，确保在 API 请求期间显示 loading 状态
  pwEpisodesLoading.value = true
  console.log('[Detail] fetchData 开始, detailLoading=', detailLoading.value, ', pwEpisodesLoading=true')

  try {
    // 1. 调用 API 获取剧集
    const apiTimer = measureApi('getEpisodes')
    const response = await animeAPI.getEpisodes(animeId.value)
    apiTimer.success(response)

    console.log('[Detail] API 返回数据:', {
      hasAnime: !!response.data.anime,
      episodesCount: response.data.episodes?.length || 0,
      requiresFrontendFetch: response.data.requires_frontend_fetch
    })

    // 2. 保存和净化数据
    const sanitizeTimer = tracedMeasure('sanitizeAnimeData')
    animeData.value = sanitizeAnimeData(response.data)
    sanitizeTimer.end({ episodeCount: animeData.value.episodes?.length || 0 })

    console.log('[Detail] 净化后 animeData:', {
      animeEpisodesCount: animeData.value.episodes?.length || 0,
      pwEpisodesCount: pwEpisodes.value.length
    })

    // 检查是否需要通过前端获取 anime1.pw 页面
    if (response.data.requires_frontend_fetch) {
      console.log('[Detail] 需要前端获取 anime1.pw, 设置 pwEpisodesLoading=true')
      // 开始加载剧集（不阻塞页面）
      pwEpisodesLoading.value = true

      // 并行加载：pwEpisodes 和 backgroundData
      const [pwResult, bgResult] = await Promise.allSettled([
        fetchPwEpisodes().catch(err => ({ error: err.message })),
        loadBackgroundData().catch(err => ({ error: err.message }))
      ])

      if (pwResult.error) {
        console.error('[Detail] 获取 anime1.pw 剧集失败:', pwResult.error)
      }

      // 注意：detailLoading 由 playEpisode 关闭（首次加载视频时）
      console.log('[Detail] API数据已加载，等待播放第一集时关闭骨架屏')

      timer.end({
        animeId: animeId.value,
        requiresFrontendFetch: true,
        episodeCount: animeData.value.episodes?.length || 0,
        hasPwError: !!pwResult.error,
        hasBgError: !!bgResult.error
      })
      endTrace()
      return
    }

    // 关闭剧集加载状态
    console.log('[Detail] API 直接返回剧集数据, 设置 pwEpisodesLoading=false')
    pwEpisodesLoading.value = false

    // 确保 Vue 完成响应式更新后再继续（避免模板渲染时 animeData 还没更新）
    await nextTick()

    // 3. 后台加载非关键数据（不阻塞页面）
    loadBackgroundData().catch(err => {
      console.error('[Detail] 后台数据加载失败:', err)
    })

    // 4. 等待进度加载完成后，自动播放
    await loadEpisodeProgress()

    // 获取剧集列表
    const animeEpisodesCount = animeData.value.episodes?.length || 0
    const pwEpisodesCount = pwEpisodes.value.length
    const totalEpisodes = animeEpisodesCount || pwEpisodesCount
    console.log('[Detail] 检查剧集数据:', { animeEpisodesCount, pwEpisodesCount, totalEpisodes })

    if (totalEpisodes > 0) {
      const episodes = animeData.value.episodes || pwEpisodes.value

      // 查找未看完的集数
      const unfinishedIdx = findUnfinishedEpisode(episodes)

      // 如果有未看完的集数，播放该集；否则播放第一集
      const targetIdx = unfinishedIdx >= 0 ? unfinishedIdx : 0
      console.log(`[Detail] 自动播放第${episodes[targetIdx].episode}集 (${unfinishedIdx >= 0 ? '未看完续播' : '从头开始'})`)

      const playTimer = tracedMeasure('playAutoEpisode')
      playEpisode(targetIdx)
      playTimer.end({ episodeId: episodes[targetIdx]?.id, reason: unfinishedIdx >= 0 ? 'unfinished' : 'first' })
    } else {
      // 没有剧集数据时，直接关闭骨架屏，显示空状态
      console.log('[Detail] 没有剧集数据，直接关闭骨架屏')
      detailLoading.value = false
      initialVideoLoaded.value = true
    }

    timer.end({
      animeId: animeId.value,
      episodeCount: animeData.value.episodes?.length || 0
    })
    endTrace()
  } catch (error) {
    timer.end({ error: error.message })
    loadError.value = true
    // 加载失败时关闭骨架屏，显示错误状态
    detailLoading.value = false
    initialVideoLoaded.value = true  // 标记已尝试加载，避免后续干扰
    nextTick(() => {
      console.log('[Detail] 加载失败，detailLoading=false')
    })
    console.error('[Detail] 获取番剧详情失败:', error)
    console.error('[Detail] 错误详情:', error.response?.data || error.message)
    // 区分 404 和其他错误
    if (error.response?.status === 404) {
      loadErrorMessage.value = '未找到该番剧，可能已被删除或链接有误'
    } else {
      loadErrorMessage.value = '加载失败，请稍后重试'
    }
    endTrace()
  }
}

// 后台并行加载非关键数据
const loadBackgroundData = () => {
  // 并行加载收藏状态、播放进度、Bangumi 信息
  return Promise.all([
    // 1. 检查收藏状态
    (async () => {
      const timer = tracedMeasure('checkFavoriteStatus')
      try {
        const favResponse = await favoriteAPI.isFavorite(animeId.value)
        isFavorite.value = favResponse.data[RESPONSE_FIELDS.SUCCESS] &&
                           favResponse.data[RESPONSE_FIELDS.DATA]?.[RESPONSE_FIELDS.IS_FAVORITE]
        timer.end({ isFavorite: isFavorite.value })
      } catch (err) {
        timer.end({ error: err.message })
        console.error('[Detail] 获取收藏状态失败:', err)
      }
    })(),

    // 2. 加载播放进度（异步，不阻塞）
    (async () => {
      const timer = tracedMeasure('loadEpisodeProgress')
      try {
        await loadEpisodeProgress()
        timer.end({})
      } catch (err) {
        timer.end({ error: err.message })
        console.error('[Detail] 加载播放进度失败:', err)
      }
    })(),

    // 3. 加载 Bangumi 信息（异步，不阻塞）
    (async () => {
      const timer = tracedMeasure('fetchBangumiInfo')
      try {
        await fetchBangumiInfo()
        timer.end({})
      } catch (err) {
        timer.end({ error: err.message })
        console.error('[Detail] 获取 Bangumi 信息失败:', err)
      }
    })()
  ])
}

// 重试加载
const retryLoad = () => {
  // 重置加载状态
  loadError.value = false
  detailLoading.value = true
  initialVideoLoaded.value = false  // 重置首次加载标记
  animeData.value = null
  pwEpisodes.value = []
  pwEpisodesLoading.value = false
  console.log('[Detail] 重试加载')
  fetchData()
}

// 重试加载剧集
const retryLoadEpisodes = () => {
  pwEpisodesLoadError.value = false
  adultContentSourceUrl.value = null  // 重试时清除源站点链接
  pwEpisodesLoading.value = true
  fetchPwEpisodes().catch(err => {
    console.error('[Detail] 重试获取 anime1.pw 剧集失败:', err)
  })
}

// 获取 anime1.pw 页面内容并解析集数
const fetchPwEpisodes = async () => {
  console.log('[Detail] fetchPwEpisodes 开始')

  // 如果 anime1.pw URL 来自 animeData，则获取它
  if (!anime1PwUrl.value && animeData.value?.anime?.detail_url?.includes('anime1.pw')) {
    anime1PwUrl.value = animeData.value.anime.detail_url
  }

  if (!anime1PwUrl.value) {
    console.log('[Detail] fetchPwEpisodes 跳过: 没有 anime1.pw URL')
    pwEpisodesLoading.value = false
    return Promise.resolve()
  }

  try {
    console.log('[Detail] 准备获取 anime1.pw 页面:', anime1PwUrl.value)

    // 检测可用的 pywebview API
    const getPywebviewApi = () => {
      // 方式1: window.pywebview.api (pywebview 5.x)
      if (window.pywebview && window.pywebview.api) {
        console.log('[Detail] window.pywebview.api 存在')
        return window.pywebview.api
      }
      // 方式2: window.external (某些版本)
      if (window.external && typeof window.external.invoke === 'function') {
        console.log('[Detail] 使用 window.external')
        return { invoke: window.external.invoke }
      }
      console.log('[Detail] 没有可用的 pywebview API')
      return null
    }

    const pywebviewApi = getPywebviewApi()
    const hasEvaluateJs = pywebviewApi && typeof pywebviewApi.evaluate_js === 'function'

    // 导航到 anime1.pw 页面
    if (pywebviewApi && typeof pywebviewApi.navigate === 'function') {
      try {
        pywebviewApi.navigate(anime1PwUrl.value)
        console.log('[Detail] 导航命令已执行')
        await new Promise(resolve => setTimeout(resolve, 2000))
      } catch (e) {
        console.warn('[Detail] 导航失败:', e)
      }
    } else if (pywebviewApi && hasEvaluateJs) {
      try {
        await pywebviewApi.evaluate_js(`window.location.href = '${anime1PwUrl.value}'`)
        await new Promise(resolve => setTimeout(resolve, 2000))
      } catch (e) {
        console.warn('[Detail] 导航失败:', e)
      }
    }

    // 获取页面 HTML
    const getPageHtml = async () => {
      if (pywebviewApi && hasEvaluateJs) {
        try {
          const html = await pywebviewApi.evaluate_js(`
            (function() {
              try {
                return document.documentElement.outerHTML;
              } catch (e) {
                return '<html></html>';
              }
            })()
          `)
          console.log('[Detail] pywebview 获取成功, 长度:', html?.length || 0)
          return html
        } catch (e) {
          console.warn('[Detail] pywebview 获取失败:', e)
        }
      }

      // 备用方法：直接使用 fetch
      try {
        const response = await fetch(anime1PwUrl.value)
        if (response.ok) {
          const text = await response.text()
          console.log('[Detail] fetch 获取成功, 长度:', text.length)
          return text
        }
      } catch (e) {
        console.warn('[Detail] fetch 获取失败 (CORS/SSL 限制):', e.message)
      }

      return null
    }

    const htmlContent = await getPageHtml()
    console.log('[Detail] htmlContent:', htmlContent ? htmlContent.substring(0, 200) + '...' : 'null')

    if (!htmlContent) {
      const isTLSDomain = anime1PwUrl.value.includes('anime1.pw')
      if (isTLSDomain) {
        console.warn('[Detail] anime1.pw TLS 错误 - 可能需要跳转源站点')
        // 标记加载完成，但有错误
        pwEpisodesLoading.value = false
        pwEpisodesLoadComplete.value = true
        pwEpisodesLoadError.value = true
        // 保存源站点URL用于跳转
        adultContentSourceUrl.value = anime1PwUrl.value
        return
      }
      // 其他情况也标记加载完成
      pwEpisodesLoading.value = false
      pwEpisodesLoadComplete.value = true
      return
    }

    console.log('[Detail] 获取到 HTML 内容，长度:', htmlContent.length)

    // 发送到后端解析
    console.log('[Detail] 发送到后端 /anime/pw/episodes 解析')
    const parseResponse = await animeAPI.fetchPwEpisodes(htmlContent, animeId.value)
    console.log('[Detail] 后端解析完成, episodes:', parseResponse.data.episodes?.length || 0)

    if (parseResponse.data.episodes && parseResponse.data.episodes.length > 0) {
      console.log('[Detail] 解析成功，更新 pwEpisodes')
      // 保存剧集数据到 pwEpisodes
      pwEpisodes.value = (parseResponse.data.episodes || []).map(ep => ({
        id: ep.id,
        episode: escapeText(ep.episode),
        date: escapeText(ep.date),
        url: ep.url
      }))
      pwEpisodesLoading.value = false

      // 加载播放进度（异步，不阻塞）
      loadEpisodeProgress().catch(err => console.error('[Detail] 加载播放进度失败:', err))

      // 自动播放第一集
      playEpisode(0)
      pwEpisodesLoadComplete.value = true
    } else {
      pwEpisodesLoading.value = false
      pwEpisodesLoadComplete.value = true
    }
  } catch (error) {
    console.error('[Detail] 获取 anime1.pw 集数失败:', error)
    pwEpisodesLoading.value = false
    pwEpisodesLoadComplete.value = true
    pwEpisodesLoadError.value = true
  }
}

// 获取所有剧集
const getAllEpisodes = () => {
  return animeData.value?.episodes || pwEpisodes.value
}

const playEpisode = async (idx, retryCount = 0) => {
  const episodes = getAllEpisodes()
  if (!episodes || idx < 0 || idx >= episodes.length) {
    console.log('[Detail] playEpisode 跳过: episodes=', !!episodes, ', idx=', idx, ', episodes.length=', episodes?.length)
    return
  }

  const MAX_RETRIES = 4
  const LOADING_MESSAGES = [
    '正在加载视频...',
    '视频加载中，请稍候...',
    '视频仍在处理中，请稍候...',
    '视频上传中，请耐心等待...'
  ]

  currentEpisodeIndex.value = idx
  const ep = episodes[idx]

  console.log('[Detail] playEpisode 被调用:', {
    idx,
    episodeCount: episodes.length,
    initialVideoLoaded: initialVideoLoaded.value,
    detailLoading: detailLoading.value,
    animeEpisodesCount: animeData.value?.episodes?.length || 0,
    pwEpisodesCount: pwEpisodes.value.length
  })

  // 首次加载视频：关闭骨架屏
  if (!initialVideoLoaded.value) {
    initialVideoLoaded.value = true
    detailLoading.value = false
    console.log('[Detail] 首次加载视频，关闭骨架屏, 当前剧集数:', episodes.length)
  }

  videoLoading.value = true
  loadingText.value = LOADING_MESSAGES[Math.min(retryCount, LOADING_MESSAGES.length - 1)]
  videoSrc.value = ''
  videoError.value = false

  // 停止之前的进度保存
  stopProgressSaving()

  // 提前确保播放进度已加载（同步等待）
  const progress = getEpisodeProgress(ep.id)
  if (!progress) {
    console.log('[Detail] 播放进度未加载，同步获取...')
    await loadEpisodeProgress()
  }

  try {
    // 获取视频 URL - 使用 fetch 直接请求代理端点（避免 /api 前缀问题）
    const apiUrl = `${API_ENDPOINTS.PROXY.EPISODE_API}?${REQUEST_PARAMS.URL}=${encodeURIComponent(ep.url)}`
    console.log('[Video] 请求API:', apiUrl)
    const response = await fetch(apiUrl)
    console.log('[Video] API响应状态:', response.status)
    const data = await response.json()
    console.log('[Video] API返回数据:', data)

    if (data[RESPONSE_FIELDS.ERROR]) {
      console.log('[Video] API返回错误:', data[RESPONSE_FIELDS.ERROR])
      // 如果是临时错误（视频还在处理中），重试
      const errorMsg = (data[RESPONSE_FIELDS.ERROR] || '').toLowerCase()
      const shouldRetry = errorMsg.includes('not found') ||
                          errorMsg.includes('not available') ||
                          errorMsg.includes('不存在') ||
                          errorMsg.includes('上架') ||
                          errorMsg.includes('处理中') ||
                          errorMsg.includes('loading') ||
                          errorMsg.includes('wait') ||
                          errorMsg.includes('404') ||
                          errorMsg.includes('empty') ||
                          !data[RESPONSE_FIELDS.URL]

      if (shouldRetry && retryCount < MAX_RETRIES) {
        console.log('[Video] 临时错误，' + (3000 * (retryCount + 1)) + 'ms 后重试')
        loadingText.value = LOADING_MESSAGES[Math.min(retryCount, LOADING_MESSAGES.length - 1)]
        setTimeout(() => {
          playEpisode(idx, retryCount + 1)
        }, 3000 * (retryCount + 1))
        return
      }
      showError('无法获取视频', '请稍后重试')
      return
    }

    if (!data[RESPONSE_FIELDS.URL]) {
      console.log('[Video] 视频URL为空')
      if (retryCount < MAX_RETRIES) {
        console.log('[Video] URL为空，' + (3000 * (retryCount + 1)) + 'ms 后重试')
        loadingText.value = LOADING_MESSAGES[Math.min(retryCount, LOADING_MESSAGES.length - 1)]
        setTimeout(() => {
          playEpisode(idx, retryCount + 1)
        }, 3000 * (retryCount + 1))
        return
      }
      showError('无法获取视频', '请稍后重试')
      return
    }

    console.log('[Video] 获取视频成功，设置 videoSrc')
    loadingText.value = '加载视频...'

    // 关键：设置 videoLoading=false，让 VideoPlayer 组件能够渲染
    // 注意：VideoPlayer 内部的 loading 状态由组件自己管理
    videoLoading.value = false
    console.log('[Video] videoLoading=false, 准备渲染 VideoPlayer')

    // 处理视频 URL，使用代理避免 CORS
    let videoUrl = data[RESPONSE_FIELDS.URL]
    const ANIME1_DOMAIN = '.anime1.me'
    if (videoUrl.includes(ANIME1_DOMAIN)) {
      const cookiesParam = data[REQUEST_PARAMS.COOKIES]
        ? encodeURIComponent(JSON.stringify(data[REQUEST_PARAMS.COOKIES]))
        : ''
      // 对于 HLS playlist (m3u8)，使用 /proxy/hls 来正确重写相对路径
      if (videoUrl.includes('.m3u8')) {
        videoUrl = `${API_ENDPOINTS.PROXY.HLS}?${REQUEST_PARAMS.URL}=${encodeURIComponent(videoUrl)}&${REQUEST_PARAMS.COOKIES}=${cookiesParam}`
      } else {
        videoUrl = `${API_ENDPOINTS.PROXY.VIDEO_STREAM}?${REQUEST_PARAMS.URL}=${encodeURIComponent(videoUrl)}&${REQUEST_PARAMS.COOKIES}=${cookiesParam}`
      }
    }
    console.log('[Video] 最终视频URL:', videoUrl)

    // 设置视频源，VideoPlayer 组件会自动处理播放
    videoSrc.value = videoUrl
  } catch (error) {
    console.log('[Video] 请求异常:', error.message)
    if (retryCount < MAX_RETRIES) {
      console.log('[Video] 网络错误，' + (3000 * (retryCount + 1)) + 'ms 后重试')
      loadingText.value = LOADING_MESSAGES[Math.min(retryCount, LOADING_MESSAGES.length - 1)]
      setTimeout(() => {
        playEpisode(idx, retryCount + 1)
      }, 3000 * (retryCount + 1))
      return
    }
    showError('加载失败', error.message || '网络连接错误，请检查网络后重试')
  }
}

// 播放器就绪事件
const onPlayerReady = () => {
  console.log('[Detail] 播放器就绪, videoLoading=false')
  videoLoading.value = false

  // 开始保存播放进度
  startProgressSaving()
}

// 播放器播放事件
const onPlayerPlay = () => {
  isPlaying.value = true
}

// 播放器暂停事件
const onPlayerPause = () => {
  isPlaying.value = false
}

// 继续播放（气泡提示中选择继续）
const onRestorePlayback = () => {
  const ep = currentEpisode.value
  const progress = currentProgress.value
  if (ep && progress && videoPlayerRef.value) {
    videoPlayerRef.value.setCurrentTime(progress.position_seconds)
    console.log('[Detail] 气泡提示选择继续播放，跳转到:', progress.position_seconds)
  }
}

// 重新开始（气泡提示中选择重新）
const onRestartPlayback = () => {
  const ep = currentEpisode.value
  if (ep && videoPlayerRef.value) {
    videoPlayerRef.value.setCurrentTime(0)
    episodeProgressMap.value[ep.id] = null
    console.log('[Detail] 气泡提示选择重新开始')
  }
}

// 时间更新事件
const onTimeUpdate = (currentTime) => {
  // 实时保存（可选：这里定时器会自动处理）
}

// 播放器错误事件
const onPlayerError = (error) => {
  console.error('[Detail] 播放器错误:', error)
  showError('播放错误', error?.message || '视频播放失败，请尝试重新加载')
}

const showError = (title, message, externalLink = null) => {
  videoLoading.value = false
  videoError.value = true
  videoErrorTitle.value = title || '无法播放视频'
  videoErrorMessage.value = message || '未知错误'
  videoErrorLink.value = externalLink
}

// 打开外部链接
const openExternalLink = (url) => {
  if (url && window.pywebview && window.pywebview.api && window.pywebview.api.navigate) {
    window.pywebview.api.navigate(url)
  } else {
    window.open(url, '_blank')
  }
}

// 返回上一页，保留搜索和分页状态
const goBack = () => {
  // 使用 router.back() 返回上一页，保留 URL 参数
  router.back()
}

const toggleFavorite = async () => {
  favoriteLoading.value = true
  try {
    if (isFavorite.value) {
      await favoriteAPI.remove(animeId.value)
      ElMessage.success(UI_TEXT.FAVORITE_REMOVED)
    } else {
      await favoriteAPI.add(animeId.value)
      ElMessage.success(UI_TEXT.FAVORITE_ADDED)
    }
    isFavorite.value = !isFavorite.value
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    ElMessage.error(ERROR_MESSAGES.OPERATION_FAILED)
  } finally {
    favoriteLoading.value = false
  }
}

// 获取 Bangumi 番剧信息（后台加载，不阻塞页面）
const fetchBangumiInfo = async () => {
  if (!animeId.value) {
    return
  }

  try {
    const response = await animeAPI.getBangumiInfo(animeId.value)
    if (response.data && !response.data.error) {
      bangumiInfo.value = response.data
    }
  } catch (error) {
    console.error('获取 Bangumi 信息失败:', error)
  }
}

onMounted(() => {
  console.log('[Detail] onMounted, 设置 detailLoading=true, pwEpisodesLoading=false')
  // 设置主加载状态
  detailLoading.value = true
  // 确保 pwEpisodesLoading 也是 false（避免初始渲染时为 undefined）
  pwEpisodesLoading.value = false

  // 监听缓存清理事件，清理后刷新当前番剧数据
  onCacheCleared(() => {
    console.log('[Detail] 收到缓存清理事件，刷新番剧数据...')
    // 清除封面缓存，重新获取
    if (animeData.value?.anime) {
      animeData.value.anime.cover_url = null
      animeData.value.anime.year = null
      animeData.value.anime.season = null
      animeData.value.anime.subtitle_group = null
    }
    // 重新获取番剧数据
    detailLoading.value = true
    fetchData()
  })

  // 获取番剧数据（主加载）
  fetchData()
})

// 组件卸载时保存进度并清理
onUnmounted(() => {
  // 保存当前播放进度
  if (videoPlayerRef.value && videoPlayerRef.value.getCurrentTime) {
    const currentTime = videoPlayerRef.value.getCurrentTime()
    if (currentTime > 5) {
      savePlaybackProgress(currentTime)
    }
  }
  // 停止定时器
  stopProgressSaving()
})
</script>

<style scoped>
.detail-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  /* 确保容器高度正确 */
  min-height: 100%;
  box-sizing: border-box;
  position: relative;
}

/* 页面整体加载遮罩 - 半透明遮罩，底下的元素仍可见 */
.page-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--el-overlay-color, rgba(255, 255, 255, 0.7));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  border-radius: 16px;
}

.page-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 统一的主题色转圈圈动画 */
.page-loading-overlay .is-loading,
.sidebar-loading .is-loading,
.bangumi-loading .is-loading,
.video-loading .is-loading,
.video-loading-overlay .is-loading,
.loading-episodes .is-loading {
  color: var(--el-color-primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.breadcrumb-nav {
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.breadcrumb-nav :deep(.el-breadcrumb__inner) {
  color: var(--el-text-color-secondary);
}

.breadcrumb-nav :deep(.el-breadcrumb__inner a) {
  color: var(--el-text-color-secondary);
  transition: color 0.3s;
}

.breadcrumb-nav :deep(.el-breadcrumb__inner a:hover) {
  color: var(--el-color-primary);
}

.breadcrumb-nav :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.back-with-breadcrumb {
  margin-bottom: 20px;
}

.back-btn {
  margin-bottom: 0;
}

.detail-content {
  display: flex;
  gap: 30px;
  align-items: flex-start;
  /* 确保 sticky 元素在正确的滚动容器内 */
}

.episode-sidebar {
  flex-shrink: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 70px;
  align-self: flex-start;
  /* 确保 sticky 计算正确 */
  will-change: transform;
}

.sidebar-header {
  padding: 15px;
  border-bottom: 1px solid var(--el-border-color);
  background: linear-gradient(135deg, rgba(124, 92, 255, 0.15) 0%, rgba(255, 107, 157, 0.15) 100%);
  overflow-y: auto;
  max-height: calc(100vh - 110px);
  /* 平滑滚动 */
  scroll-behavior: smooth;
  /* 自定义滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

.sidebar-header::-webkit-scrollbar {
  width: 6px;
}

.sidebar-header::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-header::-webkit-scrollbar-thumb {
  background-color: var(--el-border-color);
  border-radius: 3px;
}

.sidebar-header::-webkit-scrollbar-thumb:hover {
  background-color: var(--el-text-color-secondary);
}

.episode-sidebar {
  width: 280px;
  transition: width 0.3s ease;
}

.episode-sidebar.collapsed {
  width: 0;
  padding: 0;
  border: none;
  overflow: hidden;
}

.sidebar-cover {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 8px;
  margin-bottom: 10px;
}

.sidebar-cover-wrapper {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-fill-color-light);
  margin-bottom: 10px;
}

.sidebar-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
  color: var(--el-text-color-placeholder);
}

.sidebar-info {
  position: relative;
  padding: 15px;
}

.detail-favorite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 36px;
  height: 36px;
  background: rgba(124, 92, 255, 0.85);
  border: 2px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  color: #fff;
  box-shadow: 0 2px 8px rgba(124, 92, 255, 0.4);
  transition: all 0.3s;
  z-index: 20;
}

.detail-favorite-btn:hover {
  background: rgba(124, 92, 255, 1);
  transform: scale(1.15);
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.6);
}

.detail-favorite-btn.active {
  background: rgba(255, 107, 157, 0.95);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 2px 8px rgba(255, 107, 157, 0.5);
}

/* 侧边栏加载状态样式 */
.sidebar-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 15px;
  gap: 10px;
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}

.sidebar-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 15px;
  gap: 10px;
  color: var(--el-color-danger);
}

.sidebar-error .el-button {
  margin-top: 8px;
}

.sidebar-cover-placeholder.loading {
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
}

.sidebar-cover-placeholder.loading .el-icon {
  color: var(--el-text-color-secondary);
}

/* 骨架屏样式 */
.sidebar-skeleton {
  padding: 15px;
}

.sidebar-skeleton .skeleton-cover {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  margin-bottom: 12px;
}

.sidebar-skeleton .skeleton-title {
  height: 20px;
  width: 80%;
  margin-bottom: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.sidebar-skeleton .skeleton-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-skeleton .skeleton-line {
  height: 14px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.sidebar-skeleton .skeleton-line.short {
  width: 60%;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.sidebar-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 100px;
}

.sidebar-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  line-height: 1.3;
}

.sidebar-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.meta-label {
  color: var(--el-text-color-secondary);
  min-width: 50px;
}

.meta-value {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

/* Bangumi 侧边栏信息样式 */
.bangumi-info {
  padding: 12px 15px;
  border-top: 1px solid var(--el-border-color);
  margin-top: 5px;
}

.bangumi-loading {
  padding: 12px 15px;
  border-top: 1px solid var(--el-border-color);
  margin-top: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
}

.bangumi-loading-inline {
  padding: 12px 15px;
  border-top: 1px solid var(--el-border-color);
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}

.bangumi-rating {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.rating-value {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(90deg, #ff6b9d, #7c5cff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.rating-label {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}

.rank-value {
  font-size: 0.85rem;
  color: #ff6b9d;
  font-weight: 600;
  margin-left: 6px;
}

.bangumi-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.meta-tag {
  padding: 3px 10px;
  background: var(--el-fill-color-light);
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.bangumi-summary {
  margin-bottom: 12px;
  line-height: 1.6;
}

.summary-header {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.summary-content {
  font-size: 0.8rem;
  color: var(--el-text-color-primary);
  text-align: justify;
  max-height: 80px;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.summary-content.expanded {
  max-height: 300px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

.summary-content.expanded::-webkit-scrollbar {
  width: 4px;
}

.summary-content.expanded::-webkit-scrollbar-track {
  background: transparent;
}

.summary-content.expanded::-webkit-scrollbar-thumb {
  background-color: var(--el-border-color);
  border-radius: 2px;
}

.summary-content.expanded::-webkit-scrollbar-thumb:hover {
  background-color: var(--el-text-color-secondary);
}

.more-link {
  font-size: 0.75rem;
  margin-top: 6px;
  margin-right: 12px;
}

.bangumi-genres {
  margin-bottom: 10px;
}

.genres-label, .staff-label, .cast-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.genres-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.genre-tag {
  padding: 2px 8px;
  background: var(--el-fill-color);
  border-radius: 8px;
  font-size: 0.7rem;
  color: var(--el-text-color-secondary);
}

.bangumi-staff, .bangumi-cast {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.staff-list, .cast-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.staff-item, .cast-item {
  display: block;
  line-height: 1.4;
}

.staff-item .staff-role {
  color: var(--el-text-secondary);
}

.staff-item .staff-name, .cast-item {
  color: var(--el-text-color-primary);
  margin-left: 4px;
}

.detail-main {
  flex: 1;
  min-width: 0;
  padding: 0;
}

.video-section {
  margin-bottom: 25px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.video-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.video-meta {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
}

.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

/* 确保 VideoPlayer 填满容器 - 对所有子组件生效 */
.video-container :deep(.video-player-wrapper) {
  position: absolute !important;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
}

/* 确保 video-js 填满 VideoPlayer wrapper */
.video-container :deep(.video-js) {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0;
  left: 0;
}

.video-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

.video-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #fff;
}

.video-loading-text {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
}

.video-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  background: rgba(0, 0, 0, 0.3);
}

/* 视频骨架屏 */
.video-skeleton {
  width: 100%;
  height: 100%;
}

.skeleton-video-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.video-player {
  width: 100%;
  height: 100%;
  background: #000;
}

.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* 透明背景 */
  background-color: transparent;
  gap: 15px;
}

/* video-placeholder - 复刻 vjs-big-play-button 的完整样式，但用灰色区分 */
.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  gap: 15px;
}

/* 复刻 vjs-big-play-button 的样式 - 用灰色区分 */
.video-placeholder .el-icon {
  width: 80px !important;
  height: 80px !important;
  /* placeholder 用灰色，与紫色的 vjs-big-play-button 区分 */
  background-color: var(--el-fill-color, #f0f0f0) !important;
  border: 3px solid var(--el-border-color, #dcdfe6) !important;
  border-radius: 50%;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 0 !important;
  position: relative;
}

/* 用伪元素画播放三角形图标 - 灰色 */
.video-placeholder .el-icon::before {
  content: '';
  display: block;
  width: 0;
  height: 0;
  /* 播放三角形：向右的箭头 - 灰色 */
  border-top: 14px solid transparent;
  border-bottom: 14px solid transparent;
  border-left: 24px solid var(--el-text-color-secondary, #909399);
  /* 微调位置居中 */
  margin-left: 4px;
}

.video-placeholder .el-icon svg {
  display: none !important;
}

/* hover 效果 - 稍微变深 */
.video-placeholder:hover .el-icon {
  background-color: var(--el-fill-color-light, #e5e5ea) !important;
  border-color: var(--el-border-color-hover, #c0c4cc) !important;
  transform: scale(1.05);
  transition: transform 0.2s ease;
}

/* 暗色模式适配 - 使用深色灰色 */
html.dark .video-placeholder .el-icon {
  background-color: var(--el-fill-color-dark, #2c2c3e) !important;
  border-color: var(--el-border-color-dark, #4a4a5e) !important;
}

/* 暗色模式三角形图标 - 浅灰色 */
html.dark .video-placeholder .el-icon::before {
  border-left-color: var(--el-text-color-secondary, #909399);
}

.adult-error-message {
  text-align: center;
  margin-bottom: 8px;
}

.adult-error-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--el-color-warning);
  margin-bottom: 6px;
}

.adult-error-desc {
  font-size: 0.9rem;
  color: var(--el-text-color-secondary);
}

.error-action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.error-action-buttons .el-button {
  min-width: 140px;
}

.video-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  z-index: 20;
  padding: 40px;
  box-sizing: border-box;
}

.video-error-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.video-error-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #ff6b9d;
  margin-bottom: 12px;
  text-align: center;
}

.video-error-message {
  font-size: 1rem;
  color: #aaa;
  text-align: center;
  max-width: 500px;
  line-height: 1.6;
}

.video-error-suggestion {
  margin-top: 25px;
  padding: 15px 25px;
  background: rgba(124, 92, 255, 0.2);
  border: 1px solid rgba(124, 92, 255, 0.4);
  border-radius: 10px;
  font-size: 0.95rem;
  color: #ccc;
  text-align: center;
}

.episodes-section {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.total-episodes {
  font-size: 0.9rem;
  font-weight: normal;
  color: var(--el-text-color-secondary);
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  min-height: 60px;
}

/* 剧集骨架卡片 */
.episode-skeleton-card {
  aspect-ratio: 1.5;
  border-radius: 10px;
  /* 使用固定颜色，确保可见 */
  background: linear-gradient(90deg, #e0e0e0 25%, #f5f5f5 50%, #e0e0e0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

/* 暗色模式 */
html.dark .episode-skeleton-card {
  background: linear-gradient(90deg, #3a3a4a 25%, #4a4a5a 50%, #3a3a4a 75%);
}

.episode-grid.loading {
  opacity: 0.7;
}

.loading-episodes {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  min-height: 100px;
}

/* 剧集列表加载中（带文字） */
.loading-episodes-inline {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 30px;
  color: var(--el-text-color-secondary);
  font-size: 0.9rem;
}

.episode-card.skeleton-episode {
  background: var(--el-fill-color-light);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  border: 2px solid var(--el-border-color);
}

.episode-card {
  background: var(--el-fill-color-light);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  border: 2px solid var(--el-border-color);
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  /* 进度条效果：左深右浅渐变，不影响文字 */
  background: linear-gradient(
    to right,
    hsl(260, 60%, 75%) var(--progress-percent, 0%),
    var(--el-fill-color-light) var(--progress-percent, 0%)
  );
  border-color: hsl(260, 50%, 80%);
}

/* 播放进度加载中状态 */
.episode-card.loading-progress {
  background: linear-gradient(
    to right,
    hsl(260, 60%, 80%) 0%,
    var(--el-fill-color-light) 0%
  );
}

/* 加载中动画效果 - 在卡片底部显示流动的进度条动画 */
.episode-card.loading-progress::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  height: 4px;
  width: 100%;
  background: linear-gradient(90deg, transparent 0%, #7c5cff 30%, #7c5cff 70%, transparent 100%);
  background-size: 200% 100%;
  animation: progress-skeleton-loading 1.5s infinite ease-in-out;
  border-radius: 0 0 8px 8px;
}

@keyframes progress-skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.episode-card:hover {
  transform: translateY(-3px);
  border-color: var(--el-color-primary);
  box-shadow: 0 6px 20px rgba(124, 92, 255, 0.15);
}

.episode-card.active {
  border-color: var(--el-color-primary) !important;
  /* 当前播放的集数使用更强的边框 */
  border-width: 3px;
}

.episode-card-num {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 6px;
  position: relative;
  z-index: 1;
}

.episode-card-date {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  position: relative;
  z-index: 1;
}

/* 暗色模式适配 */
html.dark .episode-card {
  /* 暗色模式下渐变色 */
  background: linear-gradient(
    to right,
    hsl(260, 50%, 45%) var(--progress-percent, 0%),
    var(--el-fill-color-dark) var(--progress-percent, 0%)
  );
  border-color: hsl(260, 30%, 40%);
}

html.dark .episode-card.active {
  border-color: var(--el-color-primary) !important;
  border-width: 3px;
}

html.dark .episode-card-num {
  color: var(--el-text-color-primary);
}

/* 骨架屏样式 */
.skeleton-sidebar {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 70px;
  max-height: calc(100vh - 110px);
  align-self: flex-start;
  width: 280px;
}

.skeleton-cover {
  width: 100%;
  aspect-ratio: 2/3;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-info {
  padding: 15px;
}

.skeleton-title {
  height: 24px;
  width: 80%;
  margin-bottom: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  height: 16px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-video {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  margin-bottom: 25px;
}

.error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.detail-main {
  flex: 1;
  width: 100%;
  min-width: 0;
  padding: 0;
}

@media (max-width: 1000px) {
  .detail-content {
    flex-direction: column;
  }

  .episode-sidebar {
    width: 100% !important;
    max-height: none;
    position: static;
  }

  .episode-sidebar.collapsed {
    width: 0 !important;
    height: 0;
  }

  /* 小屏幕下限制封面大小，确保视频区域有足够空间 */
  .sidebar-header {
    max-height: none;
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: 15px;
    padding: 15px;
  }

  .sidebar-cover-wrapper {
    width: 80px;
    flex-shrink: 0;
    aspect-ratio: 2/3;
  }

  .sidebar-info {
    flex: 1;
    min-width: 0;
    padding: 0;
  }

  /* Bangumi 信息区域限制高度，避免简介过长 */
  .bangumi-info {
    max-height: 120px;
    overflow-y: auto;
  }

  .summary-content {
    max-height: 40px;
  }

  .summary-content.expanded {
    max-height: 100px;
  }
}

@media (max-width: 600px) {
  /* 更小屏幕优化 - 视频优先 */
  .detail-content {
    padding: 10px;
  }

  .detail-main {
    width: 100%;
  }

  /* 侧边栏更紧凑 */
  .sidebar-header {
    gap: 10px;
    padding: 10px;
  }

  .sidebar-cover-wrapper {
    width: 60px;
  }

  .sidebar-title {
    font-size: 0.9rem;
    margin-bottom: 4px;
  }

  .sidebar-meta {
    display: none;
  }

  .bangumi-info {
    display: none;
  }

  /* 视频区域全宽 */
  .video-section {
    margin-bottom: 15px;
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .video-container {
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: 0;
  }

  /* 剧集区域 */
  .episodes-section {
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .episode-grid {
    grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
    gap: 8px;
  }

  .episode-card {
    padding: 8px 4px;
  }

  .episode-card-num {
    font-size: 0.8rem;
  }

  .episode-card-date {
    font-size: 0.65rem;
  }
}
</style>
