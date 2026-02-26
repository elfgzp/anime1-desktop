/**
 * 视频代理服务
 * 
 * 解决 Electron 本地文件协议访问外部视频 URL 的 CORS 问题
 * 通过注册自定义 protocol 来代理视频流
 */

import { protocol } from 'electron'
import log from 'electron-log'

const PROXY_PROTOCOL = 'video-proxy'
const PROXY_HOST = 'localhost'

export class VideoProxyService {
  private proxyMap = new Map<string, { url: string; headers?: Record<string, string> }>()
  private idCounter = 0

  /**
   * 初始化视频代理协议
   */
  initialize(): void {
    // 注销旧协议（如果存在）
    if (protocol.isProtocolHandled(PROXY_PROTOCOL)) {
      protocol.unregisterProtocol(PROXY_PROTOCOL)
    }

    // 注册新协议
    protocol.handle(PROXY_PROTOCOL, async (request) => {
      const url = new URL(request.url)
      const proxyId = url.searchParams.get('id')
      
      if (!proxyId || !this.proxyMap.has(proxyId)) {
        return new Response('Invalid proxy ID', { status: 400 })
      }

      const proxyInfo = this.proxyMap.get(proxyId)!
      
      try {
        // 使用 Electron 的 net 模块发起请求
        const response = await this.fetchVideoStream(proxyInfo.url, request.headers, proxyInfo.headers)
        return response
      } catch (error) {
        log.error('[VideoProxy] Failed to fetch video stream:', error)
        return new Response('Failed to fetch video', { status: 500 })
      }
    })

    log.info('[VideoProxy] Service initialized')
  }

  /**
   * 注册代理 URL
   */
  async registerProxyUrl(videoUrl: string, customHeaders?: Record<string, string>): Promise<string> {
    const id = `${Date.now()}_${++this.idCounter}`
    this.proxyMap.set(id, { url: videoUrl, headers: customHeaders })
    
    // 返回代理 URL
    return `${PROXY_PROTOCOL}://${PROXY_HOST}/?id=${id}`
  }

  /**
   * 获取视频流
   */
  private async fetchVideoStream(
    url: string, 
    requestHeaders: Headers,
    customHeaders?: Record<string, string>
  ): Promise<Response> {
    // 构建请求头
    const headers: Record<string, string> = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept': '*/*',
      'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
      'Referer': 'https://anime1.me'
    }
    
    // 处理 customHeaders - 如果是 cookies 对象，转换为 Cookie 头
    if (customHeaders) {
      // 检查是否是 cookies 格式（有 e, p, h 等字段）
      const cookieFields = ['e', 'p', 'h'];
      const hasCookieFields = cookieFields.some(f => customHeaders[f] !== undefined);
      
      if (hasCookieFields) {
        // 转换为 Cookie 头格式
        const cookieStr = Object.entries(customHeaders)
          .map(([k, v]) => `${k}=${v}`)
          .join('; ');
        headers['Cookie'] = cookieStr;
      } else {
        // 普通 headers，直接合并
        Object.assign(headers, customHeaders);
      }
    }

    // 转发 Range 头（用于视频 seek）
    const rangeHeader = requestHeaders.get('Range')
    if (rangeHeader) {
      headers['Range'] = rangeHeader
    }

    // 使用 fetch API（Node.js 18+ 支持）
    const response = await fetch(url, { 
      headers,
      // @ts-ignore - redirect 选项在 Node.js fetch 中可用
      redirect: 'follow'
    })

    // 构建响应头
    const responseHeaders: Record<string, string> = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Range, Accept, Content-Type',
      'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges'
    }

    // 复制重要的响应头
    const contentType = response.headers.get('Content-Type')
    if (contentType) {
      responseHeaders['Content-Type'] = contentType
    }

    const contentLength = response.headers.get('Content-Length')
    if (contentLength) {
      responseHeaders['Content-Length'] = contentLength
    }

    const contentRange = response.headers.get('Content-Range')
    if (contentRange) {
      responseHeaders['Content-Range'] = contentRange
    }

    const acceptRanges = response.headers.get('Accept-Ranges')
    if (acceptRanges) {
      responseHeaders['Accept-Ranges'] = acceptRanges
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders
    })
  }

  /**
   * 清理过期的代理记录
   */
  cleanup(): void {
    // 简单实现：清空所有记录
    this.proxyMap.clear()
    log.info('[VideoProxy] Cleaned up proxy map')
  }
}

// 单例实例
export const videoProxyService = new VideoProxyService()
