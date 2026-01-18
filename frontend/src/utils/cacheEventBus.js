/**
 * 缓存事件总线 - 用于通知缓存清理事件
 */
import { onMounted, onUnmounted } from 'vue'

// Event name for cache clear
export const CACHE_CLEARED_EVENT = 'cache-cleared'

/**
 * 发送缓存清理事件
 * @param {string} type - 清理类型 ('covers' | 'all')
 */
export function emitCacheCleared(type) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(CACHE_CLEARED_EVENT, {
      detail: { type, timestamp: Date.now() }
    }))
  }
}

/**
 * 监听缓存清理事件
 * @param {Function} callback - 回调函数
 * @returns {Function} 取消监听函数
 */
export function onCacheCleared(callback) {
  if (typeof window === 'undefined') {
    return () => {}
  }

  const handler = (event) => {
    callback(event.detail)
  }

  window.addEventListener(CACHE_CLEARED_EVENT, handler)

  // Return cleanup function
  return () => {
    window.removeEventListener(CACHE_CLEARED_EVENT, handler)
  }
}

/**
 * Vue 组合式函数 - 在组件中监听缓存清理事件
 * @param {Function} handler - 处理函数
 */
export function useCacheCleared(handler) {
  const cleanup = onCacheCleared(handler)

  onUnmounted(() => {
    cleanup()
  })
}
