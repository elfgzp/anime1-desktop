/**
 * HTTP 客户端
 * 
 * 对应原项目: src/utils/http.py - HttpClient 类
 * 技术栈: axios (替代 requests)
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import log from 'electron-log'
import { HTTP_CONFIG, REQUEST_HEADERS } from '@shared/constants'

export interface HttpClientOptions {
  timeout?: number
  retries?: number
  retryDelay?: number
  headers?: Record<string, string>
}

export class HttpClient {
  private client: AxiosInstance
  private options: HttpClientOptions
  private retryCount = 0

  constructor(options: HttpClientOptions = {}) {
    this.options = {
      timeout: HTTP_CONFIG.DEFAULT_TIMEOUT,
      retries: HTTP_CONFIG.MAX_RETRIES,
      retryDelay: HTTP_CONFIG.RETRY_BACKOFF,
      ...options
    }

    this.client = axios.create({
      timeout: this.options.timeout,
      headers: {
        ...REQUEST_HEADERS.DEFAULT,
        ...options.headers
      }
    })

    this.setupInterceptors()
  }

  /**
   * 设置拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        log.debug(`[HTTP] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        log.error('[HTTP] Request error:', error.message)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const config = error.config
        
        // 检查是否需要重试
        if (this.shouldRetry(error)) {
          this.retryCount++
          const delay = this.options.retryDelay! * this.retryCount
          
          log.warn(`[HTTP] Retrying (${this.retryCount}/${this.options.retries}) ${config.url} after ${delay}ms`)
          
          await this.sleep(delay)
          return this.client(config)
        }
        
        log.error(`[HTTP] Request failed: ${config?.url}`, error.message)
        return Promise.reject(error)
      }
    )
  }

  /**
   * 判断是否应该重试
   */
  private shouldRetry(error: any): boolean {
    // 超过最大重试次数
    if (this.retryCount >= this.options.retries!) {
      return false
    }

    // 网络错误或超时
    if (!error.response) {
      return true
    }

    // 特定的状态码重试
    const retryStatusCodes = HTTP_CONFIG.RETRY_STATUS_CODES
    if (retryStatusCodes.includes(error.response.status)) {
      return true
    }

    return false
  }

  /**
   * 延迟
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * GET 请求
   */
  async get<T = string>(url: string, config?: AxiosRequestConfig): Promise<T> {
    this.retryCount = 0
    const response: AxiosResponse<T> = await this.client.get(url, config)
    return response.data
  }

  /**
   * POST 请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    this.retryCount = 0
    const response: AxiosResponse<T> = await this.client.post(url, data, config)
    return response.data
  }

  /**
   * 获取原始响应
   */
  async getRaw(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    this.retryCount = 0
    return this.client.get(url, config)
  }

  /**
   * 设置请求头
   */
  setHeader(key: string, value: string): void {
    this.client.defaults.headers.common[key] = value
  }

  /**
   * 设置 Cookie
   */
  setCookie(cookie: string): void {
    this.setHeader('Cookie', cookie)
  }

  /**
   * 设置 Referer
   */
  setReferer(referer: string): void {
    this.setHeader('Referer', referer)
  }

  /**
   * 关闭客户端
   */
  close(): void {
    // axios 不需要显式关闭
    log.info('[HTTP] Client closed')
  }
}

/**
 * 创建默认 HTTP 客户端
 */
export function createDefaultHttpClient(): HttpClient {
  return new HttpClient()
}

/**
 * 创建 Anime1 专用的 HTTP 客户端
 */
export function createAnime1HttpClient(): HttpClient {
  return new HttpClient({
    headers: REQUEST_HEADERS.ANIME1
  })
}

/**
 * 创建 API 专用的 HTTP 客户端
 */
export function createApiHttpClient(): HttpClient {
  return new HttpClient({
    headers: REQUEST_HEADERS.API
  })
}
