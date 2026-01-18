<template>
  <div class="video-player-wrapper" :class="{ loading: loading || isInitialLoading }">
    <!-- 封面层：视频加载完成后隐藏 -->
    <div v-if="poster && !videoLoaded" class="video-cover" :style="{ backgroundImage: `url(${poster})` }" @click="handleCoverClick">
      <div class="play-icon">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>
    <!-- 初始加载状态 -->
    <div v-if="isInitialLoading" class="video-loading-state">
      <div class="loading-spinner"></div>
      <span class="loading-text">加载中...</span>
    </div>
    <video
      ref="videoElement"
      class="video-js vjs-big-play-centered vjs-theme-city vjs-fill"
      playsinline
    />
    <!-- 继续观看气泡提示 -->
    <Transition name="bubble-fade">
      <div v-if="showRestoreBubble && restoreProgress" class="restore-bubble">
        <div class="restore-bubble-content">
          <span class="restore-bubble-text">上次播放到 {{ restoreProgress.position_formatted }}，继续？</span>
          <span class="restore-bubble-countdown">{{ countdown }}s</span>
          <div class="restore-bubble-actions">
            <button class="restore-bubble-btn primary" @click="handleContinue">继续</button>
            <button class="restore-bubble-btn" @click="handleRestart">重新</button>
            <button class="restore-bubble-btn" @click="handleCancel">取消</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  poster: {
    type: String,
    default: ''
  },
  animeId: {
    type: String,
    default: ''
  },
  episodeIndex: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  },
  restoreProgress: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['ready', 'error', 'play', 'pause', 'ended', 'timeupdate', 'restore', 'restart'])

// 是否显示恢复气泡
const showRestoreBubble = ref(false)
const countdown = ref(10)  // 倒计时秒数
let countdownTimer = null
let canceledRestore = false  // 用户是否取消了恢复提示
const videoLoaded = ref(false)  // 视频是否已加载完成
const isInitialLoading = ref(true)  // 初始加载状态（到 canplay 事件为止）

// 处理封面点击
const handleCoverClick = () => {
  if (player) {
    player.play()
  }
}

// 处理继续播放
const handleContinue = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  emit('restore')
  showRestoreBubble.value = false
}

// 处理重新开始
const handleRestart = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  emit('restart')
  showRestoreBubble.value = false
}

// 处理取消
const handleCancel = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  showRestoreBubble.value = false
  countdown.value = 10
  canceledRestore = true  // 标记用户已取消，不再显示提示
}

// 显示气泡（当有进度时）
const showRestoreBubbleIfNeeded = () => {
  if (props.restoreProgress && props.restoreProgress.position_seconds > 10 && !canceledRestore) {
    showRestoreBubble.value = true
    countdown.value = 10
    // 倒计时
    if (countdownTimer) clearInterval(countdownTimer)
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        showRestoreBubble.value = false
        countdown.value = 10
        clearInterval(countdownTimer)
      }
    }, 1000)
  }
}

const videoElement = ref(null)
let player = null
const STORAGE_KEY = 'anime1_video_progress'

// 保存播放进度
const saveProgress = () => {
  if (!player || !props.animeId) return

  const currentTime = player.currentTime()
  const duration = player.duration()

  if (currentTime && duration && currentTime > 5 && currentTime < duration - 10) {
    const key = `${STORAGE_KEY}_${props.animeId}_${props.episodeIndex}`
    localStorage.setItem(key, currentTime.toString())
    console.log(`[VideoPlayer] 已保存播放进度: ${currentTime.toFixed(1)}s`)
  }
}

// 获取保存的播放进度
const getSavedProgress = () => {
  if (!props.animeId) return 0

  const key = `${STORAGE_KEY}_${props.animeId}_${props.episodeIndex}`
  const saved = localStorage.getItem(key)
  return saved ? parseFloat(saved) : 0
}

// 初始化播放器
const initPlayer = async () => {
  console.log('[VideoPlayer] initPlayer 被调用, src=', props.src ? props.src.substring(0, 80) + '...' : 'empty')
  console.log('[VideoPlayer] poster=', props.poster ? props.poster.substring(0, 80) + '...' : 'empty')
  console.log('[VideoPlayer] loading=', props.loading)
  if (!props.src) {
    console.log('[VideoPlayer] src 为空，跳过初始化')
    return
  }
  if (!videoElement.value) {
    console.log('[VideoPlayer] videoElement 不存在')
    return
  }

  // 清理旧播放器
  if (player) {
    console.log('[VideoPlayer] 销毁旧播放器')
    player.dispose()
    player = null
  }

  const savedTime = getSavedProgress()
  console.log('[VideoPlayer] 创建播放器, savedTime=', savedTime)

  player = videojs(videoElement.value, {
    autoplay: false,
    controls: true,
    responsive: true,
    fluid: true,
    poster: props.poster,
    preload: 'metadata',
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    sources: props.src ? [{
      src: props.src,
      type: props.src.includes('.m3u8') ? 'application/x-mpegURL' : 'video/mp4'
    }] : [],
    // VHS (HTTP Streaming) 配置，用于正确处理代理的 HLS 流
    html5: {
      vhs: {
        withCredentials: true,  // 发送 cookies 用于认证
        useDevicePixelRatio: true
      },
      nativeAudioTracks: false,  // 禁用原生音频轨道，使用 VHS 处理
      nativeVideoTracks: false   // 禁用原生视频轨道，使用 VHS 处理
    },
    // 自定义控制栏
    controlBar: {
      children: [
        'playToggle',
        'volumePanel',
        'currentTimeDisplay',
        'durationDisplay',
        'progressControl',
        'playbackRateMenuButton',
        'fullscreenToggle',
        'pictureInPictureToggle'
      ]
    }
  })

  // 恢复播放进度
  if (savedTime > 0) {
    player.currentTime(savedTime)
    console.log(`[VideoPlayer] 已恢复播放进度: ${savedTime.toFixed(1)}s`)
  }

  // 事件监听
  player.on('ready', () => {
    console.log('[VideoPlayer] 播放器就绪')
    emit('ready')
  })

  // 视频加载完成（可以流畅播放），隐藏封面和加载状态
  // 使用 canplaythrough 而不是 canplay，因为 canplay 会在每个 variant stream 时触发多次
  player.on('canplaythrough', () => {
    videoLoaded.value = true
    isInitialLoading.value = false  // 关闭初始加载状态
    // 隐藏 video.js 自带的 poster，确保封面完全隐藏
    const el = player.el?.() || player.el
    const posterEl = el?.querySelector?.('.vjs-poster')
    if (posterEl) {
      posterEl.style.display = 'none'
    }
    console.log('[VideoPlayer] 视频加载完成 (canplaythrough), videoLoaded:', videoLoaded.value)
  })

  // 实际开始播放时，隐藏播放按钮
  player.on('playing', () => {
    videoElement.value?.parentElement?.classList.add('video-playing')
    console.log('[VideoPlayer] 开始播放 (playing)')
  })

  // 缓冲等待时
  player.on('waiting', () => {
    console.log('[VideoPlayer] 等待缓冲 (waiting)')
    videoElement.value?.parentElement?.classList.remove('video-playing')
  })

  // 错误处理
  player.on('error', (e) => {
    console.error('[VideoPlayer] 播放错误:', player.error())
    emit('error', player.error())
  })

  // 加载元数据
  player.on('loadedmetadata', () => {
    console.log('[VideoPlayer] 元数据加载完成')
  })

  // 暂停时重新显示播放按钮
  player.on('pause', () => {
    videoElement.value?.parentElement?.classList.remove('video-playing')
  })

  player.on('play', () => {
    showRestoreBubbleIfNeeded()
    emit('play')
  })

  player.on('pause', () => {
    saveProgress()
    emit('pause')
  })

  player.on('ended', () => {
    saveProgress()
    emit('ended')
  })

  player.on('timeupdate', () => {
    if (player) {
      emit('timeupdate', player.currentTime())
    }
  })

  // 定期保存进度（每10秒）
  setInterval(saveProgress, 10000)
}

// 更新视频源
watch(() => props.src, async (newSrc) => {
  console.log('[VideoPlayer] src 变化检测: newSrc=', newSrc ? newSrc.substring(0, 80) + '...' : 'empty', ', player=', !!player)
  if (!newSrc) {
    console.log('[VideoPlayer] src 为空，不处理')
    return
  }
  if (!player) {
    console.log('[VideoPlayer] player 不存在，调用 initPlayer')
    initPlayer()
    return
  }

  console.log('[VideoPlayer] 视频源更新:', newSrc)
  videojs.log('[VideoPlayer] 切换到新视频')

  // 重置状态
  canceledRestore = false
  videoLoaded.value = false  // 重置封面显示状态
  isInitialLoading.value = true  // 重置初始加载状态

  // 暂停并保存当前进度
  if (!player.paused()) {
    player.pause()
  }
  saveProgress()

  // 获取新视频的保存进度
  const savedTime = getSavedProgress()

  // 更新源
  player.src({ src: newSrc, type: newSrc.includes('.m3u8') ? 'application/x-mpegURL' : 'video/mp4' })

  // 恢复进度
  if (savedTime > 0) {
    await nextTick()
    player.currentTime(savedTime)
    console.log(`[VideoPlayer] 已恢复播放进度: ${savedTime.toFixed(1)}s`)
  }
})

onMounted(() => {
  console.log('[VideoPlayer] onMounted 调用, src=', props.src ? props.src.substring(0, 80) + '...' : 'empty')
  initPlayer()
})

onUnmounted(() => {
  // 保存进度
  saveProgress()
  // 销毁播放器
  if (player) {
    player.dispose()
    player = null
  }
})

// 暴露方法给父组件
defineExpose({
  play: () => player?.play(),
  pause: () => player?.pause(),
  getCurrentTime: () => player?.currentTime() || 0,
  getDuration: () => player?.duration() || 0,
  setCurrentTime: (time) => {
    if (player && time !== undefined) {
      player.currentTime(time)
    }
  },
  currentTime: (time) => {
    if (player) {
      if (time !== undefined) {
        player.currentTime(time)
      } else {
        return player.currentTime()
      }
    }
  },
  fullscreen: () => player?.requestFullscreen(),
  pip: () => player?.requestPictureInPicture()
})
</script>

<style>
.video-player-wrapper {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
  position: relative;
  z-index: 10;
}

/* 确保 video.js 播放器填满容器 */
.video-player-wrapper :deep(.video-js) {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0;
  left: 0;
}

/* 确保 VHS 播放器正确布局 */
.video-player-wrapper :deep(.vjs-tech) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}

/* 封面层 */
.video-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.video-cover::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
}

.play-icon {
  position: relative;
  z-index: 1;
  width: 80px;
  height: 80px;
  background: rgba(124, 92, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.play-icon svg {
  width: 40px;
  height: 40px;
  margin-left: 4px;
}

.video-cover:hover .play-icon {
  transform: scale(1.1);
  background: rgba(124, 92, 255, 1);
}

/* 播放时隐藏 video.js 的播放按钮 */
.video-player-wrapper.video-playing .vjs-big-play-button {
  display: none !important;
}

/* 大播放按钮 - 使用项目主题色 anime-primary */
.video-js .vjs-big-play-button {
  background-color: var(--anime-primary, #7c5cff) !important;
  border-color: var(--anime-primary, #7c5cff) !important;
  border-radius: 50%;
  width: 80px;
  height: 80px;
  line-height: 80px;
  font-size: 40px;
}

.video-js:hover .vjs-big-play-button,
.video-js .vjs-big-play-button:hover {
  background-color: var(--anime-primary-hover, #6a4fd6) !important;
  border-color: var(--anime-primary-hover, #6a4fd6) !important;
  transform: scale(1.05);
  transition: transform 0.2s ease;
}

/* 加载中时隐藏 video.js 的 loading spinner */
.video-player-wrapper.loading .vjs-loading-spinner {
  display: none !important;
  visibility: hidden !important;
}

/* 初始加载时隐藏大播放按钮 */
.video-player-wrapper.loading .vjs-big-play-button {
  display: none !important;
}

/* 没有封面时的加载状态 */
.video-loading-state {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  z-index: 5;
}

.video-loading-state .loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(124, 92, 255, 0.3);
  border-top-color: #7c5cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.video-loading-state .loading-text {
  margin-top: 12px;
  color: #999;
  font-size: 14px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 控制栏样式 */
.video-js .vjs-control-bar {
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 20;
}

.video-js .vjs-slider {
  background-color: rgba(255, 255, 255, 0.3);
}

/* 进度条颜色 */
.video-js .vjs-play-progress {
  background-color: #7c5cff;
}

.video-js .vjs-load-progress {
  background-color: rgba(255, 255, 255, 0.3);
}

/* 音量条 */
.video-js .vjs-volume-level {
  background-color: #7c5cff;
}

/* 全屏按钮 */
.video-js .vjs-fullscreen-control {
  cursor: pointer;
}

/* 继续观看气泡提示 */
.restore-bubble {
  position: absolute;
  bottom: 50px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(30, 30, 40, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  padding: 8px 12px;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(124, 92, 255, 0.4);
}

.restore-bubble-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.restore-bubble-text {
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
}

.restore-bubble-countdown {
  color: rgba(124, 92, 255, 0.8);
  font-size: 11px;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.restore-bubble-actions {
  display: flex;
  gap: 6px;
}

.restore-bubble-btn {
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: transparent;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.restore-bubble-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.restore-bubble-btn.primary {
  background: var(--anime-primary, #7c5cff);
  border-color: var(--anime-primary, #7c5cff);
}

.restore-bubble-btn.primary:hover {
  background: var(--anime-primary-hover, #6a4fd6);
}

/* 气泡动画 */
.bubble-fade-enter-active,
.bubble-fade-leave-active {
  transition: all 0.25s ease;
}

.bubble-fade-enter-from,
.bubble-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
</style>
