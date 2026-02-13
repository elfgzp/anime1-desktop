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
      webkit-playsinline
      x5-playsinline
      crossorigin="anonymous"
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
import { KEYBOARD_KEYS } from '@/constants/keyboard'

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
const isCssFullscreen = ref(false)  // CSS 模拟全屏状态（用于 WebView）

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
let keydownListener = null  // 键盘事件监听器
let resizeListener = null  // 窗口大小变化监听器
let resizeTimeout = null  // 用于延迟检测全屏状态的定时器

// 检测窗口是否处于全屏状态（用于 WebView）
const isWindowFullscreen = () => {
  // macOS 上检测窗口是否全屏
  // 通过比较窗口大小和屏幕大小来判断
  const isMac = /Macintosh/.test(navigator.userAgent)
  if (!isMac) return false

  // 如果窗口尺寸接近屏幕尺寸，认为是全屏
  // 使用一定容差，因为 macOS 全屏时可能有微小差异
  const screenWidth = window.screen.width
  const screenHeight = window.screen.height
  const tolerance = 100  // 像素容差

  return (
    Math.abs(window.outerWidth - screenWidth) < tolerance &&
    Math.abs(window.outerHeight - screenHeight) < tolerance
  )
}

// 处理窗口大小变化
const handleWindowResize = () => {
  const inWebView = isWebView()
  if (!inWebView) return

  // 清除之前的延迟检测定时器
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
    resizeTimeout = null
  }

  // 延迟 300ms 后再检测全屏状态，等待窗口尺寸稳定
  // 这样可以避免在全屏切换过程中误判为退出全屏
  resizeTimeout = setTimeout(() => {
    const currentlyFullscreen = isWindowFullscreen()

    // 检测窗口是否退出了全屏（通过标题栏按钮）
    if (isCssFullscreen.value && !currentlyFullscreen) {
      // 窗口已退出全屏，同步 CSS 全屏状态
      const wrapper = document.querySelector('.video-player-wrapper')
      if (wrapper) {
        wrapper.classList.remove('webview-fullscreen')
      }
      isCssFullscreen.value = false
      // 移除全局样式
      removeGlobalFullscreenStyles()
      console.log('[VideoPlayer] 检测到窗口退出全屏，同步 CSS 全屏状态')
    }

    // 检测窗口进入了全屏（通过标题栏按钮），同步 CSS 全屏状态
    if (!isCssFullscreen.value && currentlyFullscreen) {
      const wrapper = document.querySelector('.video-player-wrapper')
      if (wrapper) {
        wrapper.classList.add('webview-fullscreen')
      }
      isCssFullscreen.value = true
      // 添加全局样式
      addGlobalFullscreenStyles()
      console.log('[VideoPlayer] 检测到窗口进入全屏，同步 CSS 全屏状态')
    }

    resizeTimeout = null
  }, 300)
}

// 键盘快捷键处理
const handleKeydown = (event) => {
  if (!player) return

  // 如果焦点在输入框等元素上，不处理
  const tagName = event.target.tagName.toLowerCase()
  if (tagName === 'input' || tagName === 'textarea' || event.target.isContentEditable) {
    return
  }

  const jumpTime = 10  // 跳10秒

  switch (event.key) {
    case KEYBOARD_KEYS.ARROW_LEFT:
      event.preventDefault()
      const leftTime = Math.max(0, player.currentTime() - jumpTime)
      player.currentTime(leftTime)
      console.log(`[VideoPlayer] 快退: ${leftTime.toFixed(1)}s`)
      break
    case KEYBOARD_KEYS.ARROW_RIGHT:
      event.preventDefault()
      const rightTime = Math.min(player.duration(), player.currentTime() + jumpTime)
      player.currentTime(rightTime)
      console.log(`[VideoPlayer] 快进: ${rightTime.toFixed(1)}s`)
      break
    case KEYBOARD_KEYS.SPACE:
    case KEYBOARD_KEYS.K:
      event.preventDefault()
      if (player.paused()) {
        player.play()
      } else {
        player.pause()
      }
      break
    case KEYBOARD_KEYS.ESCAPE:
      // ESC 退出全屏（原生全屏）
      if (document.fullscreenElement) {
        document.exitFullscreen()
        return
      }
      // 退出 CSS 全屏（WebView 模式）
      if (isCssFullscreen.value) {
        exitCssFullscreen()
        // 同时退出窗口全屏（使用 pywebview API 和全局方法）
        if (window.toggle_fullscreen) {
          window.toggle_fullscreen()
        } else if (window.pywebview?.api?.toggle_fullscreen) {
          window.pywebview.api.toggle_fullscreen()
        }
        return
      }
      // WebView 中使用 Python API 退出窗口全屏
      if (window.toggle_fullscreen) {
        window.toggle_fullscreen()
      } else if (window.pywebview?.api?.toggle_fullscreen) {
        window.pywebview.api.toggle_fullscreen()
      }
      break
  }
}

// Safari 兼容处理：捕获全屏和画中画的 Promise rejection
const handleUnhandledRejection = (event) => {
  const message = event.reason?.message || ''
  if (message.includes('InvalidStateError') || message.includes('NotSupportedError')) {
    console.warn('[VideoPlayer] 捕获到 Safari 全屏/PiP 错误:', message)
    event.preventDefault()
  }
}

// 检测是否在 WebView 中（更精确的检测）
const isWebView = () => {
  const ua = navigator.userAgent
  const hasMessageHandlers = !!(window.webkit?.messageHandlers)

  // Chrome/Edge/Opera 浏览器不是 WebView
  const isChrome = /Chrome/.test(ua) || /Edg/.test(ua) || /OPR/.test(ua)
  const isSafari = /Safari/.test(ua) && !isChrome
  const isMac = /Macintosh/.test(ua)
  const isIOS = /iPhone|iPad|iPod/.test(ua)

  // macOS WebView (pywebview): 有 messageHandlers，不是 Chrome，不是 Safari
  const isMacWebView = isMac && hasMessageHandlers && !isChrome && !isSafari

  // iOS WebView: 有 messageHandlers，不是 Safari
  const isIOSWebView = isIOS && hasMessageHandlers && !isSafari

  return isMacWebView || isIOSWebView
}

// Safari 全屏切换函数（供按钮点击和右键菜单使用）
const toggleFullscreen = async () => {
  const inWebView = isWebView()

  // WebView 中使用 CSS 模拟全屏 + 窗口全屏（混合方案）
  if (inWebView) {
    const wrapper = document.querySelector('.video-player-wrapper')
    if (!wrapper) {
      console.warn('[VideoPlayer] 全屏失败：找不到视频容器')
      return
    }

    if (isCssFullscreen.value) {
      // 退出 CSS 全屏
      wrapper.classList.remove('webview-fullscreen')
      isCssFullscreen.value = false
      console.log('[VideoPlayer] CSS 全屏已退出')
      // 移除全局样式
      removeGlobalFullscreenStyles()

      // 同时退出窗口全屏（使用 pywebview API 和全局方法）
      if (window.toggle_fullscreen) {
        window.toggle_fullscreen()
      } else if (window.pywebview?.api?.toggle_fullscreen) {
        try {
          window.pywebview.api.toggle_fullscreen()
        } catch (e) {
          console.warn('[VideoPlayer] 退出窗口全屏失败:', e)
        }
      }
    } else {
      // 添加全局样式（在进入全屏前添加）
      addGlobalFullscreenStyles()

      // 进入 CSS 全屏
      wrapper.classList.add('webview-fullscreen')
      isCssFullscreen.value = true
      console.log('[VideoPlayer] CSS 全屏已启用')

      // 同时进入窗口全屏（使用 pywebview API 和全局方法）
      console.log('[VideoPlayer] 调用窗口全屏: window.toggle_fullscreen=', typeof window.toggle_fullscreen, ', window.pywebview.api=', window.pywebview?.api?.toggle_fullscreen ? 'exists' : 'missing')
      if (window.toggle_fullscreen) {
        console.log('[VideoPlayer] 调用 window.toggle_fullscreen()')
        window.toggle_fullscreen()
      } else if (window.pywebview?.api?.toggle_fullscreen) {
        console.log('[VideoPlayer] 调用 window.pywebview.api.toggle_fullscreen()')
        try {
          window.pywebview.api.toggle_fullscreen()
        } catch (e) {
          console.warn('[VideoPlayer] 进入窗口全屏失败:', e)
        }
      } else {
        console.warn('[VideoPlayer] 没有可用的全屏 API')
      }
    }
    return
  }

  // 浏览器中使用原生全屏 API
  const videoEl = document.querySelector('.video-js video') || document.querySelector('video')

  if (!videoEl) {
    console.warn('[VideoPlayer] 全屏失败：video 元素不存在')
    return
  }

  // 检查视频元素是否准备好
  if (videoEl.readyState < 1) {
    console.warn('[VideoPlayer] 全屏失败：视频尚未准备好')
    return
  }

  // 检查当前是否处于全屏状态
  const isFullscreen = document.fullscreenElement ||
    (document.webkitFullscreenElement !== undefined && document.webkitFullscreenElement)

  try {
    if (isFullscreen) {
      // 退出全屏
      if (document.exitFullscreen) {
        await document.exitFullscreen()
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen()
      }
    } else {
      // 进入全屏
      if (videoEl.requestFullscreen) {
        await videoEl.requestFullscreen()
      } else if (videoEl.webkitRequestFullscreen) {
        await videoEl.webkitRequestFullscreen()
      }
    }
  } catch (e) {
    console.warn('[VideoPlayer] 全屏切换失败:', e.message)
  }
}

// 退出 CSS 全屏（供 ESC 键使用）
const exitCssFullscreen = () => {
  if (isCssFullscreen.value) {
    const wrapper = document.querySelector('.video-player-wrapper')
    if (wrapper) {
      wrapper.classList.remove('webview-fullscreen')
      isCssFullscreen.value = false
      console.log('[VideoPlayer] ESC 退出 CSS 全屏')
    }
    // 移除全局样式
    removeGlobalFullscreenStyles()
  }
}

// 添加全局全屏样式
const addGlobalFullscreenStyles = () => {
  const styleId = 'webview-fullscreen-global-styles'
  if (document.getElementById(styleId)) return // 已存在

  const style = document.createElement('style')
  style.id = styleId
  style.textContent = `
    /* WebView 全屏模式 - 隐藏所有页面元素 */
    body:has(.video-player-wrapper.webview-fullscreen) {
      overflow: hidden !important;
    }

    body:has(.video-player-wrapper.webview-fullscreen) .el-aside,
    body:has(.video-player-wrapper.webview-fullscreen) .sidebar,
    body:has(.video-player-wrapper.webview-fullscreen) .layout-container > .el-aside {
      display: none !important;
    }

    body:has(.video-player-wrapper.webview-fullscreen) .el-main,
    body:has(.video-player-wrapper.webview-fullscreen) .main-content,
    body:has(.video-player-wrapper.webview-fullscreen) .main-container {
      padding: 0 !important;
      margin: 0 !important;
      overflow: hidden !important;
      background: #000 !important;
    }

    /* 隐藏 Detail 页面的特定元素 */
    body:has(.video-player-wrapper.webview-fullscreen) .breadcrumb-nav,
    body:has(.video-player-wrapper.webview-fullscreen) .back-with-breadcrumb,
    body:has(.video-player-wrapper.webview-fullscreen) .back-btn,
    body:has(.video-player-wrapper.webview-fullscreen) .episode-sidebar,
    body:has(.video-player-wrapper.webview-fullscreen) .episodes-section,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-sidebar,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-header,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-info,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-container > .breadcrumb-nav,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-container > .back-with-breadcrumb {
      display: none !important;
    }

    /* 隐藏视频卡片的外层边框 */
    body:has(.video-player-wrapper.webview-fullscreen) .video-section,
    body:has(.video-player-wrapper.webview-fullscreen) .video-section .el-card__header,
    body:has(.video-player-wrapper.webview-fullscreen) .video-section .el-card__body,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-main .el-card,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-main .video-section {
      border: none !important;
      box-shadow: none !important;
      background: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
    }

    /* 隐藏视频卡片头部（标题等） */
    body:has(.video-player-wrapper.webview-fullscreen) .video-header,
    body:has(.video-player-wrapper.webview-fullscreen) .video-title,
    body:has(.video-player-wrapper.webview-fullscreen) .video-meta {
      display: none !important;
    }

    /* 确保视频容器填满整个屏幕 */
    body:has(.video-player-wrapper.webview-fullscreen) .video-container {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      padding: 0 !important;
      margin: 0 !important;
      aspect-ratio: auto !important;
      border-radius: 0 !important;
      z-index: 99998 !important;
      background: #000 !important;
    }

    /* 确保 detail-main 也填满 */
    body:has(.video-player-wrapper.webview-fullscreen) .detail-main,
    body:has(.video-player-wrapper.webview-fullscreen) .detail-content {
      padding: 0 !important;
      margin: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      background: #000 !important;
    }

    /* 隐藏 detail-container 的 padding */
    body:has(.video-player-wrapper.webview-fullscreen) .detail-container {
      padding: 0 !important;
    }
  `
  document.head.appendChild(style)
  console.log('[VideoPlayer] 全局全屏样式已添加')
}

// 移除全局全屏样式
const removeGlobalFullscreenStyles = () => {
  const styleId = 'webview-fullscreen-global-styles'
  const style = document.getElementById(styleId)
  if (style) {
    style.remove()
    console.log('[VideoPlayer] 全局全屏样式已移除')
  }
}

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

// HLS 代理缓存
let hlsBlobUrl = null

// 清理 HLS Blob URL
const cleanupHlsBlob = () => {
  if (hlsBlobUrl) {
    URL.revokeObjectURL(hlsBlobUrl)
    hlsBlobUrl = null
  }
}

// 通过代理获取 HLS 播放列表
const fetchHlsViaProxy = async (hlsUrl) => {
  try {
    console.log('[VideoPlayer] Fetching HLS via proxy:', hlsUrl.substring(0, 80) + '...')
    
    // Check if we're in Electron environment
    if (!window.electronAPI?.proxyHlsPlaylist) {
      console.log('[VideoPlayer] HLS proxy not available, using original URL')
      return hlsUrl
    }
    
    const result = await window.electronAPI.proxyHlsPlaylist({ url: hlsUrl, cookies: {} })
    
    if (!result.success) {
      console.error('[VideoPlayer] HLS proxy failed:', result.error)
      return hlsUrl
    }
    
    if (!result.isPlaylist) {
      // Not a playlist (shouldn't happen for .m3u8 URLs)
      console.log('[VideoPlayer] HLS proxy returned non-playlist content')
      return hlsUrl
    }
    
    // Create blob URL from rewritten playlist
    const blob = new Blob([result.content], { type: 'application/vnd.apple.mpegurl' })
    hlsBlobUrl = URL.createObjectURL(blob)
    
    console.log('[VideoPlayer] HLS playlist proxied successfully')
    return hlsBlobUrl
    
  } catch (error) {
    console.error('[VideoPlayer] Error fetching HLS via proxy:', error)
    return hlsUrl
  }
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
  
  // 清理旧的 HLS Blob URL
  cleanupHlsBlob()

  const savedTime = getSavedProgress()
  console.log('[VideoPlayer] 创建播放器, savedTime=', savedTime)

  const isM3U8 = props.src.includes('.m3u8')
  const videoType = isM3U8 ? 'application/x-mpegURL' : 'video/mp4'
  
  // 对于 HLS，通过代理获取重写的播放列表
  let videoSrc = props.src
  if (isM3U8 && window.electronAPI?.proxyHlsPlaylist) {
    videoSrc = await fetchHlsViaProxy(props.src)
  }

  // 检测是否为 Safari
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent) || /iPad|iPhone|iPod/.test(navigator.userAgent)

  player = videojs(videoElement.value, {
    autoplay: false,
    controls: true,
    responsive: true,
    fluid: true,
    poster: props.poster,
    preload: 'metadata',
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    sources: videoSrc ? [{
      src: videoSrc,
      type: videoType
    }] : [],
    // VHS (HTTP Streaming) 配置
    // Safari 原生支持 HLS，不需要 VHS，使用原生播放更流畅
    html5: isM3U8 ? {
      vhs: {
        withCredentials: true,
        useDevicePixelRatio: true,
        // Enable overrideNative to use VHS instead of native HLS on Safari
        // This allows our proxied URLs to work
        overrideNative: !isSafari,
        limitRenditionByPlayerDimensions: true,
        useBandwidthFromLocalStorage: true,
      },
      // Safari 强制使用原生播放器
      ...(isSafari ? {} : {
        nativeAudioTracks: false,
        nativeVideoTracks: false
      })
    } : false,
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

  // Safari 全屏兼容处理
  // video.js 的全屏按钮在 Safari 上可能不工作，需要自定义处理
  // 完全重写 player.requestFullscreen 方法，阻止 video.js 内部调用 webkitEnterFullScreen
  // 重写 player.requestFullscreen 以支持 WebView CSS 全屏（混合方案）
  player.requestFullscreen = async function() {
    // 检测是否在 WebView 中（更精确的检测）
    const ua = navigator.userAgent
    const hasMessageHandlers = !!(window.webkit?.messageHandlers)
    const isChrome = /Chrome/.test(ua) || /Edg/.test(ua) || /OPR/.test(ua)
    const isSafari = /Safari/.test(ua) && !isChrome
    const isMac = /Macintosh/.test(ua)
    const isIOS = /iPhone|iPad|iPod/.test(ua)
    const isMacWebView = isMac && hasMessageHandlers && !isChrome && !isSafari
    const isIOSWebView = isIOS && hasMessageHandlers && !isSafari
    const inWebView = isMacWebView || isIOSWebView

    // WebView 中使用 CSS 模拟全屏 + 窗口全屏（混合方案）
    if (inWebView) {
      const wrapper = document.querySelector('.video-player-wrapper')
      if (!wrapper) {
        console.warn('[VideoPlayer] 全屏失败：找不到视频容器')
        return
      }

      if (isCssFullscreen.value) {
        // 退出 CSS 全屏
        wrapper.classList.remove('webview-fullscreen')
        isCssFullscreen.value = false
        console.log('[VideoPlayer] CSS 全屏已退出')
        // 移除全局样式
        removeGlobalFullscreenStyles()
        // 同时退出窗口全屏（使用 pywebview API 和全局方法）
        if (window.toggle_fullscreen) {
          window.toggle_fullscreen()
        } else if (window.pywebview?.api?.toggle_fullscreen) {
          try {
            window.pywebview.api.toggle_fullscreen()
          } catch (e) {
            console.warn('[VideoPlayer] 退出窗口全屏失败:', e)
          }
        }
      } else {
        // 添加全局样式
        addGlobalFullscreenStyles()
        // 进入 CSS 全屏
        wrapper.classList.add('webview-fullscreen')
        isCssFullscreen.value = true
        console.log('[VideoPlayer] CSS 全屏已启用')
        // 同时进入窗口全屏（使用 pywebview API 和全局方法）
        if (window.toggle_fullscreen) {
          window.toggle_fullscreen()
        } else if (window.pywebview?.api?.toggle_fullscreen) {
          try {
            window.pywebview.api.toggle_fullscreen()
          } catch (e) {
            console.warn('[VideoPlayer] 进入窗口全屏失败:', e)
          }
        }
      }
      return
    }

    // 浏览器中使用原生全屏 API
    const videoEl = document.querySelector('.video-js video') || document.querySelector('video')

    if (!videoEl) {
      console.warn('[VideoPlayer] 全屏失败：video 元素不存在')
      return
    }

    // 检查视频元素是否准备好
    if (videoEl.readyState < 1) {
      console.warn('[VideoPlayer] 全屏失败：视频尚未准备好')
      return
    }

    // 检查当前是否处于全屏状态
    const isFullscreen = document.fullscreenElement ||
      (document.webkitFullscreenElement !== undefined && document.webkitFullscreenElement)

    try {
      if (isFullscreen) {
        // 退出全屏
        if (document.exitFullscreen) {
          await document.exitFullscreen()
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen()
        }
      } else {
        // 进入全屏
        if (videoEl.requestFullscreen) {
          await videoEl.requestFullscreen()
        } else if (videoEl.webkitRequestFullscreen) {
          await videoEl.webkitRequestFullscreen()
        }
      }
    } catch (e) {
      console.warn('[VideoPlayer] 全屏切换失败:', e.message)
    }
  }

  // 重写 player.exitFullscreen 以支持 CSS 全屏退出
  player.exitFullscreen = async function() {
    const ua = navigator.userAgent
    const hasMessageHandlers = !!(window.webkit?.messageHandlers)
    const isChrome = /Chrome/.test(ua) || /Edg/.test(ua) || /OPR/.test(ua)
    const isSafari = /Safari/.test(ua) && !isChrome
    const isMac = /Macintosh/.test(ua)
    const isIOS = /iPhone|iPad|iPod/.test(ua)
    const isMacWebView = isMac && hasMessageHandlers && !isChrome && !isSafari
    const isIOSWebView = isIOS && hasMessageHandlers && !isSafari
    const inWebView = isMacWebView || isIOSWebView

    // WebView 中使用 CSS 全屏退出
    if (inWebView && isCssFullscreen.value) {
      const wrapper = document.querySelector('.video-player-wrapper')
      if (wrapper) {
        wrapper.classList.remove('webview-fullscreen')
      }
      isCssFullscreen.value = false
      // 移除全局样式
      removeGlobalFullscreenStyles()
      // 使用 pywebview API 和全局方法
      if (window.toggle_fullscreen) {
        window.toggle_fullscreen()
      } else if (window.pywebview?.api?.toggle_fullscreen) {
        window.pywebview.api.toggle_fullscreen()
      }
      return
    }

    // 浏览器中使用原生 API
    if (document.exitFullscreen) {
      await document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    }
  }

  // 重写 player.isFullscreen 以支持 CSS 全屏状态检测
  player.isFullscreen = function() {
    const ua = navigator.userAgent
    const hasMessageHandlers = !!(window.webkit?.messageHandlers)
    const isChrome = /Chrome/.test(ua) || /Edg/.test(ua) || /OPR/.test(ua)
    const isSafari = /Safari/.test(ua) && !isChrome
    const isMac = /Macintosh/.test(ua)
    const isIOS = /iPhone|iPad|iPod/.test(ua)
    const isMacWebView = isMac && hasMessageHandlers && !isChrome && !isSafari
    const isIOSWebView = isIOS && hasMessageHandlers && !isSafari
    const inWebView = isMacWebView || isIOSWebView

    if (inWebView) {
      return isCssFullscreen.value
    }

    return !!(document.fullscreenElement || document.webkitFullscreenElement)
  }

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
  // 使用 loadedmetadata，因为它在 Safari 上更可靠
  const onVideoReady = (event) => {
    console.log('[VideoPlayer] 收到事件:', event.type, 'isInitialLoading:', isInitialLoading.value)
    if (!isInitialLoading.value) return
    videoLoaded.value = true
    isInitialLoading.value = false
    console.log('[VideoPlayer] 视频加载完成, videoLoaded:', videoLoaded.value)
    // 隐藏 video.js 自带的 poster，确保封面完全隐藏
    const el = player.el?.() || player.el
    const posterEl = el?.querySelector?.('.vjs-poster')
    if (posterEl) {
      posterEl.style.display = 'none'
    }
  }
  player.on('loadedmetadata', onVideoReady)
  player.on('canplay', onVideoReady)
  player.on('canplaythrough', onVideoReady)

  // 监听所有可能的事件来调试
  player.on('error', (e) => {
    console.error('[VideoPlayer] 播放错误:', player.error())
    console.error('[VideoPlayer] 错误详情:', player.error()?.message, player.error()?.code)
  })

  player.on('loadeddata', () => {
    console.log('[VideoPlayer] loadeddata 事件触发')
  })

  player.on('play', () => {
    console.log('[VideoPlayer] play 事件触发')
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
  
  // 清理旧的 HLS Blob URL
  cleanupHlsBlob()

  // 获取新视频的保存进度
  const savedTime = getSavedProgress()
  
  // 对于 HLS，通过代理获取重写的播放列表
  let videoSrc = newSrc
  const isM3U8 = newSrc.includes('.m3u8')
  if (isM3U8 && window.electronAPI?.proxyHlsPlaylist) {
    videoSrc = await fetchHlsViaProxy(newSrc)
  }

  // 更新源
  player.src({ src: videoSrc, type: isM3U8 ? 'application/x-mpegURL' : 'video/mp4' })

  // 恢复进度
  if (savedTime > 0) {
    await nextTick()
    player.currentTime(savedTime)
    console.log(`[VideoPlayer] 已恢复播放进度: ${savedTime.toFixed(1)}s`)
  }
})

onMounted(() => {
  console.log('[VideoPlayer] onMounted 调用, src=', props.src ? props.src.substring(0, 80) + '...' : 'empty')
  // 添加 Safari 全屏/PiP 错误处理
  window.addEventListener('unhandledrejection', handleUnhandledRejection)
  // 添加全局键盘事件监听
  keydownListener = (e) => handleKeydown(e)
  window.addEventListener('keydown', keydownListener)
  // 监听窗口大小变化，处理窗口全屏状态变化
  resizeListener = () => handleWindowResize()
  window.addEventListener('resize', resizeListener)
  initPlayer()
})

onUnmounted(() => {
  // 移除 Safari 全屏/PiP 错误处理
  window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  // 移除键盘事件监听
  if (keydownListener) {
    window.removeEventListener('keydown', keydownListener)
    keydownListener = null
  }
  // 移除窗口大小变化监听
  if (resizeListener) {
    window.removeEventListener('resize', resizeListener)
    resizeListener = null
  }
  // 清理 HLS Blob URL
  cleanupHlsBlob()
  // 清理 CSS 全屏状态
  if (isCssFullscreen.value) {
    const wrapper = document.querySelector('.video-player-wrapper')
    if (wrapper) {
      wrapper.classList.remove('webview-fullscreen')
    }
    isCssFullscreen.value = false
    removeGlobalFullscreenStyles()
  }
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
  fullscreen: async () => {
    // 使用统一的 toggleFullscreen 函数
    await toggleFullscreen()
  },
  pip: async () => {
    const videoEl = document.querySelector('.video-js video') || document.querySelector('video')

    if (!videoEl) {
      console.warn('[VideoPlayer] 画中画失败：video 元素不存在')
      return
    }

    if (videoEl.readyState < 2) {
      console.warn('[VideoPlayer] 画中画失败：视频尚未准备好')
      return
    }

    try {
      if (videoEl.requestPictureInPicture) {
        await videoEl.requestPictureInPicture()
      }
    } catch (e) {
      console.warn('[VideoPlayer] 画中画请求失败:', e.message)
    }
  }
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

/* WebView 环境下的 CSS 全屏模拟 */
.video-player-wrapper.webview-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 99999 !important;
  border-radius: 0 !important;
  background: #000 !important;
  max-width: none !important;
  max-height: none !important;
  min-width: auto !important;
  min-height: auto !important;
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}

/* 全局全屏样式现在通过 JS 动态添加，确保能正确应用到整个页面 */

.video-player-wrapper.webview-fullscreen :deep(.video-js) {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
}

.video-player-wrapper.webview-fullscreen :deep(.vjs-tech) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
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
