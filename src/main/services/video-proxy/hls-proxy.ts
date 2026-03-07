/**
 * HLS/m3u8 原生解析代理服务
 * 不依赖 hls.js，使用 Node.js 原生解析 m3u8 文件
 * 参考 Python 版本: src/routes/proxy.py - proxy_hls_playlist
 */

import http from "http";
import log from "electron-log";

export class HlsProxyService {
  private server: http.Server | null = null;
  private proxyMap = new Map<
    string,
    { url: string; headers?: Record<string, string> }
  >();
  private idCounter = 0;
  private port = 0;

  async initialize(): Promise<void> {
    await this.startServer();
    log.info("[HlsProxy] HLS proxy service initialized on port " + this.port);
  }

  private async startServer(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.server = http.createServer((req, res) =>
        this.handleRequest(req, res),
      );

      this.server.listen(0, "127.0.0.1", () => {
        const addr = this.server?.address() as { port: number };
        this.port = addr.port;
        log.info(`[HlsProxy] Server started on port ${this.port}`);
        resolve();
      });

      this.server.on("error", reject);
    });
  }

  registerProxyUrl(videoUrl: string, headers?: Record<string, string>): string {
    const id = `hls_${++this.idCounter}`;
    this.proxyMap.set(id, { url: videoUrl, headers });

    log.info(`[HlsProxy] Registered proxy: ${videoUrl} -> ${id}`);

    // 10 分钟后清理
    setTimeout(() => {
      if (this.proxyMap.has(id)) {
        this.proxyMap.delete(id);
        log.info(`[HlsProxy] Cleaned up proxy: ${id}`);
      }
    }, 600000);

    return `http://127.0.0.1:${this.port}/hls-proxy/${id}`;
  }

  private async handleRequest(
    req: http.IncomingMessage,
    res: http.ServerResponse,
  ) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
    res.setHeader(
      "Access-Control-Allow-Headers",
      "Range, Accept, Content-Type, Origin, Referer, User-Agent",
    );
    res.setHeader(
      "Access-Control-Expose-Headers",
      "Content-Range, Content-Length, Accept-Ranges",
    );

    if (req.method === "OPTIONS") {
      res.writeHead(200);
      res.end();
      return;
    }

    const url = req.url?.toString();

    if (!url) {
      res.writeHead(400);
      res.end("Missing URL");
      return;
    }

    const parts = url.split("/");
    const proxyId = parts[3];
    const proxyData = this.proxyMap.get(proxyId);

    if (!proxyData) {
      res.writeHead(404);
      res.end("Proxy not found or expired");
      return;
    }

    const targetUrl = proxyData.url;
    const path = parts.slice(4).join("/");

    try {
      const response = await fetch(`${targetUrl}${path ? `/${path}` : ""}`, {
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0 Safari/537.36",
          Accept: "*/*",
          "Accept-Language": "zh-TW,zh-CN;q=0.03",
          Referer: "https://anime1.me/",
          ...proxyData.headers,
        },
      });

      if (!response.ok) {
        res.writeHead(response.status);
        res.end(`HTTP ${response.status}`);
        return;
      }

      const content = await response.text();

      // 检查是否为 HLS 播放列表（.m3u8 文件）
      if (
        path.includes(".m3u8") ||
        content.includes("#EXTM3U") ||
        content.includes("#EXT-X-STREAM-INF")
      ) {
        const rewrittenContent = this.rewriteHlsContent(content, proxyId);
        res.setHeader("Content-Type", "application/vnd.apple.mpegurl");
        res.end(rewrittenContent);
      } else {
        res.setHeader("Content-Type", "video/mp2t");
        res.end(content);
      }
    } catch (error) {
      log.error("[HlsProxy] Error fetching:", error);
      res.writeHead(500);
      res.end("Internal server error");
    }
  }

  private rewriteHlsContent(content: string, proxyId: string): string {
    let result = content;

    // 重写 .m3u8 片段 URI 为代理 URL
    if (content.includes("#EXTM3U")) {
      const lines = content.split("\n");

      for (const line of lines) {
        if (line.includes('URI="') && !line.startsWith("#")) {
          const match = line.match(/URI="([^"]+)"/);
          if (match) {
            const relativePath = match[1];

            if (
              !relativePath.startsWith("http://") &&
              !relativePath.startsWith("//")
            ) {
              const proxyUrl = `http://127.0.0.1:${this.port}/hls-proxy/${proxyId}/${encodeURIComponent(relativePath)}`;
              result = result.replace(relativePath, proxyUrl);
            }
          }
        } else if (line.includes(".m3u8") && !line.startsWith("#")) {
          result = result.replace(/\.m3u8/g, `.m3u8?proxy=${proxyId}`);
        }
      }
    }

    return result;
  }

  cleanup(): void {
    if (this.server) {
      this.server.close();
      this.proxyMap.clear();
      log.info("[HlsProxy] Service cleaned up");
    }
  }
}

export const hlsProxyService = new HlsProxyService();
