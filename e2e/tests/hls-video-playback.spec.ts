/**
 * HLS m3u8 视频播放测试
 *
 * 测试剧场版（m3u8格式）视频的HLS代理和播放功能
 */
import { test, expect } from "../fixtures";

test.describe("HLS m3u8 视频播放", () => {
  test("应该能够获取HLS代理URL", async ({ window }) => {
    const proxyResult = await window.evaluate(async () => {
      try {
        const result = await window.api.anime.getHlsProxyUrl({
          episodeUrl: "https://example.com/episode",
          videoUrl: "https://cdn.example.com/real-playlist.m3u8",
        });
        return { ...result, tested: true };
      } catch (e) {
        return { error: String(e), success: false, tested: false };
      }
    });

    expect(proxyResult.tested).toBe(true);
    expect(proxyResult.success).toBe(true);
  });

  test("应该识别m3u8格式的视频", async ({ window }) => {
    const testCases = [
      "https://cdn.example.com/real-playlist.m3u8",
      "https://cdn.example.com/playlist.m3u8?token=abc123",
      "https://cdn.example.com/index.m3u8#EXTM3U",
    ];

    for (const testUrl of testCases) {
      const result = await window.evaluate(async (url) => {
        return await window.api.anime.getHlsProxyUrl({
          episodeUrl: "https://example.com/episode",
          videoUrl: url,
        });
      }, testUrl);

      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.data.isM3u8).toBe(true);
    }
  });

  test("应该识别非m3u8格式的视频", async ({ window }) => {
    const testCases = [
      "https://cdn.example.com/video.mp4",
      "https://cdn.example.com/video.mkv",
      "https://cdn.example.com/video.webm",
    ];

    for (const testUrl of testCases) {
      const result = await window.evaluate(async (url) => {
        return await window.api.anime.getHlsProxyUrl({
          episodeUrl: "https://example.com/episode",
          videoUrl: url,
        });
      }, testUrl);

      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.data.isM3u8).toBe(false);
    }
  });

  test("HLS代理URL应该包含本地代理地址", async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getHlsProxyUrl({
        episodeUrl: "https://example.com/episode",
        videoUrl: "https://cdn.example.com/real-playlist.m3u8",
      });
    });

    expect(result).toBeDefined();
    expect(result.success).toBe(true);

    const proxyUrl = result.data.url;
    expect(proxyUrl).toMatch(/^http:\/\/127\.0\.0\.1:/);
    expect(proxyUrl).toMatch(/\/hls-proxy\/hls_\d+$/);
  });

  test("应该处理无效的episodeUrl", async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getHlsProxyUrl({
        episodeUrl: "",
      });
    });

    expect(result).toBeDefined();
    expect(result.success).toBe(false);
  });
});
