/**
 * 轻量级性能追踪工具
 * 仅在开发模式下统计和上报数据
 */

import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals'

// 是否为开发模式
const isDev = import.meta.env.DEV || window.location.port === '5173'

// 是否启用性能追踪
const isTracingEnabled = isDev

// 控制台输出
function logPerf(name, duration, emoji = '⏱️') {
  const color = duration > 2500 ? '#ff4949' : duration > 1000 ? '#ff9900' : '#67c23a'
  console.log(`%c ${emoji} ${name}: ${duration.toFixed(2)}ms`, `color: ${color}`)
}

// 发送到后端（仅开发模式）
function sendToBackend(data, retryCount = 0) {
  if (!isTracingEnabled) return

  const maxRetries = 3

  fetch('/api/performance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).catch((error) => {
    // 如果是连接拒绝错误（后端未启动），尝试重试
    if (error.name === 'TypeError' && error.message.includes('fetch') && retryCount < maxRetries) {
      const delay = Math.pow(2, retryCount) * 500 // 指数退避: 500ms, 1s, 2s
      setTimeout(() => {
        sendToBackend(data, retryCount + 1)
      }, delay)
    }
  })
}

// 上报单个指标
function reportMetric(name) {
  if (!isTracingEnabled) return

  const metricHandlers = {
    cls: onCLS,
    fcp: onFCP,
    inp: onINP,
    lcp: onLCP,
    ttfb: onTTFB
  }

  if (metricHandlers[name]) {
    metricHandlers[name]((metric) => {
      const data = {
        name: `web-vital_${metric.name}`,
        value: Math.round(metric.value),
        rating: metric.rating,
        delta: Math.round(metric.delta),
        id: metric.id,
        page: window.location.pathname,
        timestamp: Date.now()
      }

      sendToBackend(data)
      logPerf(metric.name, metric.value, metric.value > 2500 ? '🐌' : metric.value > 1000 ? '⚠️' : '✅')
    })
  }
}

// 上报所有 Core Web Vitals（仅开发模式）
export function reportAllMetrics() {
  if (!isTracingEnabled) return
  const metrics = ['cls', 'fcp', 'inp', 'lcp', 'ttfb']
  metrics.forEach(reportMetric)
}

// 手动记录耗时（仅开发模式）
export function measure(name) {
  const start = performance.now()

  return {
    end: (metadata = {}) => {
      const duration = performance.now() - start
      logPerf(name, duration)

      if (isTracingEnabled) {
        sendToBackend({
          name: `custom_${name}`,
          value: Math.round(duration),
          rating: duration > 2500 ? 'poor' : duration > 1000 ? 'needs-improvement' : 'good',
          page: window.location.pathname,
          timestamp: Date.now(),
          metadata
        })
      }

      return duration
    }
  }
}

// 记录 API 请求耗时（仅开发模式）
export function measureApi(apiName) {
  const start = performance.now()

  return {
    success: (response) => {
      const duration = performance.now() - start
      logPerf(`API ${apiName}`, duration, '✅')
      return response
    },
    error: (error) => {
      const duration = performance.now() - start
      logPerf(`API ${apiName}`, duration, '❌')
      throw error
    }
  }
}

// 链路追踪上下文
let currentTraceId = null
let currentSpanId = null

// 开始链路追踪
export function startTrace(traceName = 'page') {
  if (!isTracingEnabled) return null

  currentTraceId = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  currentSpanId = null

  console.group(`%c[链路追踪] ${traceName}`, 'color: #7c5cff; font-weight: bold')
  console.log(`TraceId: ${currentTraceId}`)
  console.groupEnd()

  return currentTraceId
}

// 结束链路追踪
export function endTrace() {
  if (!isTracingEnabled || !currentTraceId) return

  console.log(`%c[链路追踪结束] TraceId: ${currentTraceId}`, 'color: #ff6b9d')
  currentTraceId = null
  currentSpanId = null
}

// 获取当前 trace ID
export function getCurrentTraceId() {
  return currentTraceId
}

// 获取当前 span ID
export function getCurrentSpanId() {
  return currentSpanId
}

// 测量带链路追踪的函数
export function tracedMeasure(name) {
  const start = performance.now()
  const spanId = `span_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
  const parentSpanId = currentSpanId

  return {
    end: (metadata = {}) => {
      const duration = performance.now() - start
      currentSpanId = spanId

      logPerf(name, duration, '🔗')

      if (isTracingEnabled) {
        sendToBackend({
          name: `trace_${name}`,
          value: Math.round(duration),
          rating: duration > 2500 ? 'poor' : duration > 1000 ? 'needs-improvement' : 'good',
          page: window.location.pathname,
          timestamp: Date.now(),
          trace_id: currentTraceId,
          parent_span_id: parentSpanId,
          metadata: {
            ...metadata,
            span_id: spanId
          }
        })
      }

      return duration
    }
  }
}

export default {
  reportAllMetrics,
  measure,
  measureApi,
  startTrace,
  endTrace,
  tracedMeasure,
  isDev
}
