<template>
  <div class="detail-container">
    <el-button
      :icon="ArrowLeft"
      @click="$router.push(ROUTES.HOME)"
      class="back-btn"
    >
      返回番剧列表
    </el-button>

    <!-- 页面主体结构 - 立即显示 -->
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
            <div v-else class="sidebar-cover-placeholder">
              <el-icon :size="40"><Picture /></el-icon>
            </div>
          </div>

          <div class="sidebar-info">
            <!-- 收藏按钮 -->
            <el-button
              :icon="isFavorite ? StarFilled : Star"
              circle
              class="detail-favorite-btn"
              :class="{ active: isFavorite }"
              :loading="favoriteLoading"
              @click="toggleFavorite"
            />

            <!-- 标题 -->
            <div class="sidebar-title">
              <el-skeleton v-if="loadingTitle" style="width: 80%" animated>
                <template #template>
                  <el-skeleton-item variant="text" style="width: 100%" />
                </template>
              </el-skeleton>
              <span v-else-if="animeData?.anime?.title">{{ animeData.anime.title }}</span>
              <span v-else class="text-placeholder">加载中...</span>
            </div>

            <!-- 元信息 -->
            <div class="sidebar-meta">
              <div class="meta-item">
                <span class="meta-label">年份</span>
                <el-skeleton v-if="loadingTitle" style="width: 60%" animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 100%" />
                  </template>
                </el-skeleton>
                <span class="meta-value" v-else>{{ animeData?.anime?.year || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">季度</span>
                <el-skeleton v-if="loadingTitle" style="width: 60%" animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 100%" />
                  </template>
                </el-skeleton>
                <span class="meta-value" v-else>{{ animeData?.anime?.season || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">字幕</span>
                <el-skeleton v-if="loadingTitle" style="width: 60%" animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 100%" />
                  </template>
                </el-skeleton>
                <span class="meta-value" v-else>{{ animeData?.anime?.subtitle_group || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">更新</span>
                <el-skeleton v-if="loadingEpisodes" style="width: 80%" animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 100%" />
                  </template>
                </el-skeleton>
                <span class="meta-value" v-else>
                  {{ (animeData?.episodes?.length || pwEpisodes.length) > 0 ? `共 ${animeData?.episodes?.length || pwEpisodes.length} 话` : '暂无更新' }}
                </span>
              </div>
            </div>

            <!-- Bangumi 番剧信息 -->
            <div class="bangumi-info" v-if="bangumiInfo">
              <div class="bangumi-rating" v-if="bangumiInfo.rating">
                <span class="rating-value">{{ bangumiInfo.rating.toFixed(1) }}</span>
                <span class="rating-label">分</span>
                <span v-if="bangumiInfo.rank" class="rank-value">#{{ bangumiInfo.rank }}</span>
              </div>
              <div class="bangumi-tags" v-if="bangumiInfo.date || bangumiInfo.type">
                <span v-if="bangumiInfo.date" class="meta-tag">{{ bangumiInfo.date }}</span>
                <span v-if="bangumiInfo.type" class="meta-tag">{{ bangumiInfo.type }}</span>
              </div>
              <div class="bangumi-summary" v-if="bangumiInfo.summary">
                <div class="summary-text">{{ truncateText(bangumiInfo.summary, 100) }}</div>
                <el-link v-if="bangumiInfo.summary.length > 100" :href="bangumiInfo.subject_url" target="_blank" class="more-link">
                  查看更多
                </el-link>
              </div>
              <div class="bangumi-staff" v-if="bangumiInfo.staff?.length">
                <span v-for="(item, idx) in bangumiInfo.staff.slice(0, 2)" :key="idx" class="staff-item">
                  {{ item.role }}: {{ item.name }}
                </span>
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
      <el-main class="detail-main">
        <!-- 视频播放器 -->
        <el-card class="video-section" shadow="never">
          <template #header>
            <div class="video-header">
              <div class="video-title">
                <el-skeleton v-if="!animeData?.episodes?.length && !pwEpisodesLoading" style="width: 150px" animated>
                  <template #template>
                    <el-skeleton-item variant="text" style="width: 100%" />
                  </template>
                </el-skeleton>
                <span v-else-if="currentEpisode">{{ `第 ${currentEpisode.episode} 话` }}</span>
                <span v-else>选择剧集观看</span>
              </div>
              <div class="video-meta">
                {{ currentEpisode?.date || '' }}
              </div>
            </div>
          </template>
          <div class="video-container">
            <!-- Loading overlay -->
            <div v-if="videoLoading" class="video-loading">
              <el-icon class="is-loading" :size="50"><Loading /></el-icon>
              <div class="loading-text">{{ loadingText }}</div>
              <div class="loading-percent">{{ loadingPercent }}%</div>
            </div>
            <!-- Error overlay -->
            <div v-if="videoError" class="video-error">
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
              v-else-if="videoSrc && (animeData?.episodes?.length > 0 || pwEpisodes.length > 0)"
              ref="videoPlayerRef"
              :src="videoSrc"
              :anime-id="animeId"
              :episode-index="currentEpisodeIndex"
              :poster="animeData?.anime?.cover_url"
              @ready="onPlayerReady"
              @error="onPlayerError"
              @timeupdate="onTimeUpdate"
            />
            <!-- 视频播放器骨架屏 -->
            <div v-else-if="pwEpisodesLoading" class="video-placeholder loading">
              <el-icon class="is-loading" :size="60"><Loading /></el-icon>
              <div>正在加载剧集信息...</div>
            </div>
            <div v-else-if="(animeData?.episodes?.length === 0 || !animeData?.episodes) && !pwEpisodesLoading" class="video-placeholder">
              <el-icon :size="60"><VideoCamera /></el-icon>
              <div>视频还未上架，请等待更新</div>
            </div>
            <div v-else class="video-placeholder">
              <el-icon :size="60"><VideoPlay /></el-icon>
            </div>
          </div>
        </el-card>

        <!-- 全部剧集 -->
        <el-card class="episodes-section" shadow="never">
          <template #header>
            <div class="section-title">
              <span>全部剧集</span>
              <el-skeleton v-if="!animeData?.episodes && !pwEpisodesLoading" style="width: 100px; display: inline-block" animated>
                <template #template>
                  <el-skeleton-item variant="text" style="width: 100%" />
                </template>
              </el-skeleton>
              <span class="total-episodes" v-else>
                {{ (animeData?.episodes?.length || pwEpisodes.length) > 0 ? `共 ${animeData?.episodes?.length || pwEpisodes.length} 话` : '暂无剧集' }}
              </span>
            </div>
          </template>

          <!-- 剧集加载中 -->
          <div v-if="pwEpisodesLoading" class="episode-grid loading">
            <div v-for="n in 12" :key="n" class="episode-card skeleton-episode">
              <el-skeleton variant="text" style="width: 60%" />
              <el-skeleton variant="text" style="width: 40%; margin-top: 8px" />
            </div>
          </div>

          <!-- 剧集列表 -->
          <div v-else class="episode-grid">
            <div
              v-for="(ep, idx) in (animeData?.episodes || pwEpisodes)"
              :key="idx"
              class="episode-card"
              :class="{ active: currentEpisodeIndex === idx }"
              :style="getEpisodeCardStyle(ep.id)"
              @click="playEpisode(idx)"
            >
              <div class="episode-card-num">第{{ ep.episode }}集</div>
              <div class="episode-card-date">{{ ep.date }}</div>
            </div>
            <el-empty
              v-if="(animeData?.episodes?.length === 0 || !animeData?.episodes) && !pwEpisodesLoading"
              :description="UI_TEXT.NO_EPISODES"
              :image-size="80"
            />
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Star, StarFilled, VideoPlay, VideoCamera, Loading, Refresh, Link, Picture } from '@element-plus/icons-vue'
import { animeAPI, favoriteAPI, playbackAPI } from '../utils/api'
import { ROUTES, API_ENDPOINTS, REQUEST_PARAMS, RESPONSE_FIELDS, ERROR_MESSAGES, UI_TEXT } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import VideoPlayer from '../components/VideoPlayer.vue'

const route = useRoute()
const animeId = computed(() => route.params.id)

// 加载状态
const loadError = ref(false)
const loadErrorMessage = ref('加载失败，请稍后重试')
const animeData = ref(null)
const loadingTitle = ref(true)  // 标题骨架屏状态
const loadingEpisodes = ref(true)  // 剧集骨架屏状态
const pwEpisodes = ref([])
const pwEpisodesLoading = ref(false)
const currentEpisodeIndex = ref(0)
const videoSrc = ref('')
const videoLoading = ref(false)
const loadingText = ref('正在加载视频...')
const loadingPercent = ref(0)
const videoError = ref(false)
const videoErrorTitle = ref('')
const videoErrorMessage = ref('')
const videoErrorLink = ref(null)
const isFavorite = ref(false)
const favoriteLoading = ref(false)
const videoPlayerRef = ref(null)
const bangumiInfo = ref(null)
const bangumiLoading = ref(true)
const episodeProgressMap = ref({})
const saveTimer = ref(null)
const lastSavedTime = ref(0)

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

// 获取单集播放进度
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

// 检查并询问是否恢复播放
const checkAndRestorePlayback = async (episodeId, episodeIndex) => {
  const progress = getEpisodeProgress(episodeId)
  console.log('[Detail] checkAndRestorePlayback:', { episodeId, episodeIndex, progress })

  // 先清除旧的 localStorage（避免 VideoPlayer 恢复旧进度）
  const STORAGE_KEY = 'anime1_video_progress'
  const storageKey = `${STORAGE_KEY}_${animeId.value}_${episodeIndex}`
  localStorage.removeItem(storageKey)

  if (progress && progress.position_seconds > 10) {
    // 延迟一点时间等待播放器加载
    setTimeout(async () => {
      try {
        await ElMessageBox.confirm(
          `上次播放到 ${progress.position_formatted}，是否继续？`,
          '继续观看',
          {
            confirmButtonText: '继续播放',
            cancelButtonText: '重新开始',
            type: 'info',
            lockScroll: false
          }
        )
        // 用户选择继续播放
        if (videoPlayerRef.value && videoPlayerRef.value.setCurrentTime) {
          videoPlayerRef.value.setCurrentTime(progress.position_seconds)
          console.log('[Detail] 已跳转到进度:', progress.position_seconds)
        }
      } catch {
        // 用户选择重新开始或取消 - 已经清除了 localStorage
        console.log('[Detail] 用户选择重新开始')
        // 清除前端状态
        episodeProgressMap.value[episodeId] = null
        // 清除 VideoPlayer 进度
        if (videoPlayerRef.value && videoPlayerRef.value.setCurrentTime) {
          videoPlayerRef.value.setCurrentTime(0)
        }
        console.log('[Detail] 已清除播放进度')
      }
    }, 1000)
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
  console.log('[Detail] fetchData 开始, animeId:', animeId.value)
  loadError.value = false

  try {
    console.log('[Detail] 调用 API /anime/' + animeId.value + '/episodes')
    const response = await animeAPI.getEpisodes(animeId.value)
    console.log('[Detail] API 响应成功, requires_frontend_fetch:', response.data.requires_frontend_fetch)

    // 检查是否需要通过前端获取 anime1.pw 页面
    if (response.data.requires_frontend_fetch) {
      console.log('[Detail] anime1.pw 需要前端获取页面:', response.data.fetch_url)
      // 保存基本信息
      animeData.value = sanitizeAnimeData(response.data)
      // 关闭标题骨架屏（基本信息已加载）
      loadingTitle.value = false
      // 开始加载剧集（不阻塞页面）
      pwEpisodesLoading.value = true
      fetchPwEpisodes().catch(err => {
        console.error('[Detail] 获取 anime1.pw 剧集失败:', err)
      })
      // 并行加载非关键数据
      loadBackgroundData()
      return
    }

    console.log('[Detail] 设置 animeData, episodes 数量:', response.data.episodes?.length || 0)
    // 净化数据防止 XSS
    animeData.value = sanitizeAnimeData(response.data)
    // 数据加载完成，关闭骨架屏
    loadingTitle.value = false
    loadingEpisodes.value = false

    // 并行加载非关键数据（不阻塞页面显示）
    loadBackgroundData()

    // 自动播放第一集
    if (animeData.value.episodes.length > 0) {
      console.log('[Detail] 自动播放第 0 集')
      playEpisode(0)
    }
  } catch (error) {
    loadError.value = true
    console.error('[Detail] 获取番剧详情失败:', error)
    console.error('[Detail] 错误详情:', error.response?.data || error.message)
    // 区分 404 和其他错误
    if (error.response?.status === 404) {
      loadErrorMessage.value = '未找到该番剧，可能已被删除或链接有误'
    } else {
      loadErrorMessage.value = '加载失败，请稍后重试'
    }
  }
}

// 后台并行加载非关键数据
const loadBackgroundData = () => {
  // 并行加载收藏状态、播放进度、Bangumi 信息
  Promise.all([
    // 检查收藏状态
    favoriteAPI.isFavorite(animeId.value).then(favResponse => {
      isFavorite.value = favResponse.data[RESPONSE_FIELDS.SUCCESS] &&
                         favResponse.data[RESPONSE_FIELDS.DATA]?.[RESPONSE_FIELDS.IS_FAVORITE]
    }).catch(err => console.error('[Detail] 获取收藏状态失败:', err)),

    // 加载播放进度（异步，不阻塞）
    loadEpisodeProgress().catch(err => console.error('[Detail] 加载播放进度失败:', err)),

    // 加载 Bangumi 信息（异步，不阻塞）
    fetchBangumiInfo().catch(err => console.error('[Detail] 获取 Bangumi 信息失败:', err))
  ])
}

// 重试加载
const retryLoad = () => {
  // 重置加载状态
  loadingTitle.value = true
  loadingEpisodes.value = true
  loadError.value = false
  fetchData()
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
    return
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
        console.warn('[Detail] anime1.pw TLS 错误')
        // 不阻塞显示，只显示错误提示
        pwEpisodesLoading.value = false
        return
      }
      pwEpisodesLoading.value = false
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
    } else {
      pwEpisodesLoading.value = false
    }
  } catch (error) {
    console.error('[Detail] 获取 anime1.pw 集数失败:', error)
    pwEpisodesLoading.value = false
  }
}

const playEpisode = async (idx) => {
  const episodes = animeData.value?.episodes || pwEpisodes.value
  if (!episodes || idx < 0 || idx >= episodes.length) return

  currentEpisodeIndex.value = idx
  const ep = episodes[idx]

  videoLoading.value = true
  loadingText.value = '获取视频中...'
  loadingPercent.value = 0
  videoSrc.value = ''
  videoError.value = false

  // 停止之前的进度保存
  stopProgressSaving()

  try {
    // 获取视频 URL - 使用 fetch 直接请求代理端点（避免 /api 前缀问题）
    const apiUrl = `${API_ENDPOINTS.PROXY.EPISODE_API}?${REQUEST_PARAMS.URL}=${encodeURIComponent(ep.url)}`
    console.log('[Video] 请求API:', apiUrl)
    const response = await fetch(apiUrl)
    console.log('[Video] API响应状态:', response.status)
    const data = await response.json()
    console.log('[Video] API返回数据:', data)

    if (data[RESPONSE_FIELDS.ERROR]) {
      showError('无法获取视频', data[RESPONSE_FIELDS.ERROR] || '未知错误')
      return
    }

    if (!data[RESPONSE_FIELDS.URL]) {
      showError('无法获取视频', '视频地址为空，请稍后重试')
      return
    }

    loadingText.value = '加载视频...'

    // 处理视频 URL，使用代理避免 CORS
    let videoUrl = data[RESPONSE_FIELDS.URL]
    const ANIME1_DOMAIN = '.anime1.me'
    if (videoUrl.includes(ANIME1_DOMAIN)) {
      const cookiesParam = data[REQUEST_PARAMS.COOKIES]
        ? encodeURIComponent(JSON.stringify(data[REQUEST_PARAMS.COOKIES]))
        : ''
      videoUrl = `${API_ENDPOINTS.PROXY.VIDEO_STREAM}?${REQUEST_PARAMS.URL}=${encodeURIComponent(data[RESPONSE_FIELDS.URL])}&${REQUEST_PARAMS.COOKIES}=${cookiesParam}`
    }
    console.log('[Video] 最终视频URL:', videoUrl)

    // 设置视频源，VideoPlayer 组件会自动处理播放
    videoSrc.value = videoUrl

    // 播放开始后，检查是否需要恢复播放
    setTimeout(() => {
      checkAndRestorePlayback(ep.id, idx)
    }, 1500)
  } catch (error) {
    showError('加载失败', error.message || '网络连接错误，请检查网络后重试')
  }
}

// 播放器就绪事件
const onPlayerReady = () => {
  console.log('[Detail] 播放器就绪')
  videoLoading.value = false
  loadingPercent.value = 100

  // 开始保存播放进度
  startProgressSaving()
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

// 获取 Bangumi 番剧信息
const fetchBangumiInfo = async () => {
  if (!animeId.value) {
    bangumiLoading.value = false
    return
  }

  bangumiLoading.value = true
  try {
    const response = await animeAPI.getBangumiInfo(animeId.value)
    if (response.data && !response.data.error) {
      bangumiInfo.value = response.data
    }
  } catch (error) {
    console.error('获取 Bangumi 信息失败:', error)
  } finally {
    bangumiLoading.value = false
  }
}

onMounted(() => {
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
}

.back-btn {
  margin-bottom: 20px;
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
  max-height: calc(100vh - 110px);
  align-self: flex-start;
  /* 确保 sticky 计算正确 */
  will-change: transform;
}

.sidebar-header {
  padding: 15px;
  border-bottom: 1px solid var(--el-border-color);
  background: linear-gradient(135deg, rgba(124, 92, 255, 0.15) 0%, rgba(255, 107, 157, 0.15) 100%);
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
}

.detail-favorite-btn {
  position: absolute;
  top: 0;
  right: 0;
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  backdrop-filter: blur(4px);
}

.detail-favorite-btn.active {
  background: rgba(255, 107, 157, 0.8);
  color: #fff;
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
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
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
  margin-bottom: 10px;
  line-height: 1.6;
}

.summary-text {
  font-size: 0.8rem;
  color: var(--el-text-color-primary);
  text-align: justify;
}

.more-link {
  font-size: 0.75rem;
  margin-top: 4px;
}

.bangumi-staff {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.staff-item {
  display: block;
  margin-bottom: 4px;
}

.staff-item .staff-role {
  color: var(--el-text-secondary);
}

.staff-item .staff-name {
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

.video-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  gap: 15px;
}

.loading-text {
  font-size: 0.9rem;
}

.loading-percent {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(90deg, #ff6b9d, #7c5cff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
  color: var(--el-text-color-secondary);
  gap: 15px;
}

.video-placeholder.loading {
  color: var(--el-text-color-primary);
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
}

.episode-grid.loading {
  opacity: 0.7;
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
  /* 进度条效果：左深右浅渐变，不影响文字 */
  background: linear-gradient(
    to right,
    hsl(260, 60%, 75%) var(--progress-percent, 0%),
    var(--el-fill-color-light) var(--progress-percent, 0%)
  );
  border-color: hsl(260, 50%, 80%);
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

.skeleton-video-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 8px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-episodes {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.skeleton-episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.skeleton-episode-card {
  aspect-ratio: 1.5;
  border-radius: 10px;
  background: linear-gradient(90deg, var(--el-skeleton-color) 25%, var(--el-skeleton-to-color) 50%, var(--el-skeleton-color) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
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
}
</style>
