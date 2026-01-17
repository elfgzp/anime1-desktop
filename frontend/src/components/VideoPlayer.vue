<template>
  <div class="video-player-wrapper">
    <video
      ref="videoElement"
      class="video-js vjs-big-play-centered vjs-theme-city"
    />
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
  }
})

const emit = defineEmits(['ready', 'error', 'play', 'pause', 'ended', 'timeupdate'])

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
  if (!videoElement.value) return

  // 清理旧播放器
  if (player) {
    player.dispose()
    player = null
  }

  const savedTime = getSavedProgress()

  player = videojs(videoElement.value, {
    autoplay: false,
    controls: true,
    responsive: true,
    fluid: true,
    poster: props.poster,
    preload: 'metadata',
    playbackRates: [0.5, 1, 1.25, 1.5, 2],
    sources: [{
      src: props.src,
      type: props.src.includes('.m3u8') ? 'application/x-mpegURL' : 'video/mp4'
    }],
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

  player.on('error', (e) => {
    console.error('[VideoPlayer] 播放错误:', e)
    emit('error', player.error())
  })

  player.on('play', () => {
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
  if (!player || !newSrc) return

  console.log('[VideoPlayer] 视频源更新:', newSrc)
  videojs.log('[VideoPlayer] 切换到新视频')

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

/* 自定义 video.js 主题 */
.video-js .vjs-big-play-button {
  background-color: rgba(124, 92, 255, 0.8);
  border-color: rgba(124, 92, 255, 0.8);
  border-radius: 50%;
  width: 80px;
  height: 80px;
  line-height: 80px;
  font-size: 40px;
}

.video-js:hover .vjs-big-play-button {
  background-color: rgba(124, 92, 255, 1);
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

/* loading 时隐藏大播放按钮 */
.video-player-wrapper.loading .vjs-big-play-button {
  display: none !important;
}
</style>
