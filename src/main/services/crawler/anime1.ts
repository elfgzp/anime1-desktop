/**
 * Anime1.me 爬虫
 *
 * 对应原项目: src/parser/anime1_parser.py
 */

import * as cheerio from "cheerio";
import * as https from "https";
import { exec } from "child_process";
import { promisify } from "util";
import log from "electron-log";
import type { Anime, Episode } from "@shared/types";
import {
  URLS,
  PATTERNS,
  VIDEO_API,
  DOMAINS,
  ADULT_CONTENT,
} from "@shared/constants";
import { HttpClient, createAnime1HttpClient } from "./http-client";

const execAsync = promisify(exec);

export class Anime1Crawler {
  private httpClient: HttpClient;

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createAnime1HttpClient();
  }

  /**
   * 使用 curl 获取页面（用于处理 anime1.pw 的 SSL 问题）
   * 对应原项目: src/utils/http.py - fetch_page_with_curl
   */
  private async fetchWithCurl(
    url: string,
    timeout: number = 30,
  ): Promise<string> {
    const curlCommands = [
      // Approach 1: Standard curl with modern TLS
      [
        "curl",
        "-s",
        "-L",
        "--max-time",
        String(timeout),
        "--connect-timeout",
        "10",
        "-A",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H",
        "Accept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        url,
      ],
      // Approach 2: Allow insecure (don't verify SSL)
      [
        "curl",
        "-k",
        "-s",
        "-L",
        "--max-time",
        String(timeout),
        "--connect-timeout",
        "10",
        "-A",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        url,
      ],
      // Approach 3: Try legacy TLS versions
      [
        "curl",
        "-s",
        "-L",
        "--max-time",
        String(timeout),
        "--connect-timeout",
        "10",
        "--tlsv1.0",
        "--tlsv1.1",
        "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        url,
      ],
    ];

    for (let i = 0; i < curlCommands.length; i++) {
      try {
        const cmd = curlCommands[i];
        const { stdout } = await execAsync(cmd.join(" "), {
          timeout: timeout * 1000 + 5000,
        });
        if (stdout && stdout.trim()) {
          log.debug(`[Anime1] Curl approach ${i + 1} succeeded for ${url}`);
          return stdout;
        }
        log.debug(`[Anime1] Curl approach ${i + 1} returned empty for ${url}`);
      } catch (error: any) {
        log.debug(
          `[Anime1] Curl approach ${i + 1} failed for ${url}: ${error.message}`,
        );
      }
    }

    throw new Error(`All curl approaches failed for ${url}`);
  }

  /**
   * 使用 HTTPS 获取页面（跳过 SSL 验证）
   */
  private async fetchWithIgnoreSsl(
    url: string,
    timeout: number = 30,
  ): Promise<string> {
    return new Promise((resolve, reject) => {
      const httpsAgent = new https.Agent({
        rejectUnauthorized: false, // 跳过 SSL 验证
      });

      const options = {
        agent: httpsAgent,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          Accept: "text/html,*/*",
          "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
          Referer: URLS.ANIME1_BASE,
        },
      };

      const req = https.get(url, options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      });

      req.on("error", reject);
      req.setTimeout(timeout * 1000, () => {
        req.destroy();
        reject(new Error("Request timeout"));
      });
    });
  }

  /**
   * 获取页面内容（自动处理 anime1.pw 的 SSL 问题）
   */
  private async fetchPage(url: string): Promise<string> {
    const isPwDomain = url.includes(DOMAINS.ANIME1_PW);

    if (isPwDomain) {
      // 对于 anime1.pw，尝试 curl（Python 方案）
      try {
        return await this.fetchWithCurl(url);
      } catch (curlError: any) {
        log.warn(
          `[Anime1] Curl failed for ${url}, trying with ignore SSL: ${curlError.message}`,
        );
        // 回退到忽略 SSL 验证的方式
        try {
          return await this.fetchWithIgnoreSsl(url);
        } catch (sslError: any) {
          log.error(
            `[Anime1] All fetch approaches failed for ${url}: ${sslError.message}`,
          );
          throw sslError;
        }
      }
    }

    // 对于其他域名，使用原生 fetch
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        Accept: "text/html,*/*",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        Referer: URLS.ANIME1_BASE,
      },
      redirect: "follow",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.status}`);
    }

    return response.text();
  }

  /**
   * 获取番剧列表
   * 对应: src/parser/anime1_parser.py - parse_page / parse_anime_list
   */
  async fetchAnimeList(): Promise<Anime[]> {
    log.info("[Anime1] Fetching anime list...");

    // axios 会自动解析 JSON，所以直接获取 any 类型
    const data = await this.httpClient.get<any[]>(URLS.ANIME1_API);
    const animeList = this.parseAnimeData(data);

    log.info(`[Anime1] Fetched ${animeList.length} anime`);
    return animeList;
  }

  /**
   * 解析番剧列表
   */
  private parseAnimeData(data: any[]): Anime[] {
    const animeList: Anime[] = [];
    const seenIds = new Set<string>();

    try {
      if (!Array.isArray(data)) {
        log.warn("[Anime1] Response is not an array");
        return animeList;
      }

      for (const item of data) {
        if (!Array.isArray(item) || item.length < 2) continue;

        const catId = String(item[0]);
        const titleRaw = String(item[1]);

        // 提取纯文本标题
        const title = this.extractTitle(titleRaw);
        if (!title) continue;

        // 跳过重复
        const uniqueId = this.generateId(catId, title);
        if (seenIds.has(uniqueId)) continue;
        seenIds.add(uniqueId);

        // 提取集数
        const episodeStr = item[2] ? String(item[2]) : "0";
        const episodeMatch = episodeStr.match(/\((\d+)\)/);
        const episode = episodeMatch ? parseInt(episodeMatch[1], 10) : 0;

        // 提取年份、季节、字幕组（如果有）
        const year = item[3] ? String(item[3]) : "";
        const season = item[4] ? String(item[4]) : "";
        const subtitleGroup = item[5] ? String(item[5]) : "";

        // 构建详情 URL
        let detailUrl: string;
        if (catId === "0" || !catId) {
          // anime1.pw 外链
          const linkMatch = titleRaw.match(/href="([^"]+)"/);
          if (!linkMatch) continue;
          detailUrl = linkMatch[1];
        } else {
          detailUrl = `${URLS.ANIME1_BASE}/?cat=${catId}`;
        }

        // 检测是否为成人内容
        const isAdult = this.checkIsAdult(title, detailUrl);

        animeList.push({
          id: uniqueId,
          title,
          detailUrl,
          episode,
          year,
          season,
          subtitleGroup,
          coverUrl: "",
          matchScore: 0,
          matchSource: "",
          isAdult,
        });
      }
    } catch (error) {
      log.error("[Anime1] Failed to parse anime list:", error);
    }

    return animeList;
  }

  /**
   * 提取标题（去除 HTML 标签）
   */
  private extractTitle(titleRaw: string): string {
    // 移除 HTML 标签
    let title = titleRaw.replace(/<[^>]+>/g, "").trim();

    // 解码 HTML 实体
    const entities: Record<string, string> = {
      "&amp;": "&",
      "&lt;": "<",
      "&gt;": ">",
      "&quot;": '"',
      "&#39;": "'",
    };

    for (const [entity, char] of Object.entries(entities)) {
      title = title.replace(new RegExp(entity, "g"), char);
    }

    return title.trim();
  }

  /**
   * 生成唯一 ID
   */
  private generateId(catId: string, title: string): string {
    if (catId && catId !== "0") {
      return catId;
    }
    // 对于 anime1.pw 外链，使用标题哈希
    let hash = 0;
    for (let i = 0; i < title.length; i++) {
      const char = title.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return String(Math.abs(hash) % 1000000);
  }

  /**
   * 获取番剧详情
   * 对应: src/parser/anime1_parser.py - parse_anime_detail
   */
  async fetchAnimeDetail(url: string): Promise<{
    year: string;
    season: string;
    subtitleGroup: string;
  }> {
    log.info(`[Anime1] Fetching anime detail: ${url}`);

    const html = await this.httpClient.get<string>(url);
    const $ = cheerio.load(html);

    // 提取页面文本
    const text = $.text();

    return {
      year: this.extractYear(text),
      season: this.extractSeason(text),
      subtitleGroup: this.extractSubtitleGroup(text),
    };
  }

  /**
   * 提取年份
   */
  private extractYear(text: string): string {
    const match = text.match(PATTERNS.YEAR);
    return match ? match[0] : "";
  }

  /**
   * 提取季节
   */
  private extractSeason(text: string): string {
    const seasons = ["冬季", "春季", "夏季", "秋季"];
    for (const season of seasons) {
      if (text.includes(season)) {
        return season;
      }
    }
    return "";
  }

  /**
   * 提取字幕组
   */
  private extractSubtitleGroup(text: string): string {
    const keywords = ["字幕組", "字幕", "翻譯", "翻"];
    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        // 尝试提取字幕组名称
        const patterns = [
          new RegExp(`([^\\s【】]+)${keyword}`),
          new RegExp(`${keyword}[:：]?\\s*([^\\s]+)`),
        ];
        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match) {
            return match[1] || match[0];
          }
        }
        return keyword;
      }
    }
    return "";
  }

  /**
   * 获取剧集列表
   * 对应: src/parser/anime1_parser.py - parse_episode_list / _extract_episodes
   */
  async fetchEpisodes(detailUrl: string): Promise<Episode[]> {
    log.info(`[Anime1] Fetching episodes: ${detailUrl}`);

    const episodes: Episode[] = [];
    const seenIds = new Set<string>();

    // 获取第一页
    const firstPageHtml = await this.httpClient.get<string>(detailUrl);
    const firstPageEpisodes = this.extractEpisodes(firstPageHtml);

    for (const ep of firstPageEpisodes) {
      if (!seenIds.has(ep.id)) {
        seenIds.add(ep.id);
        episodes.push(ep);
      }
    }

    // 获取总页数
    const totalPages = this.getTotalEpisodePages(firstPageHtml);

    // 限制最大页数
    const maxPages = Math.min(totalPages, 5);

    // 获取后续页面
    for (let page = 2; page <= maxPages; page++) {
      try {
        const pageUrl = this.buildPageUrl(detailUrl, page);
        const pageHtml = await this.httpClient.get<string>(pageUrl);
        const pageEpisodes = this.extractEpisodes(pageHtml);

        for (const ep of pageEpisodes) {
          if (!seenIds.has(ep.id)) {
            seenIds.add(ep.id);
            episodes.push(ep);
          }
        }
      } catch (error) {
        log.warn(`[Anime1] Failed to fetch page ${page}:`, error);
        break;
      }
    }

    // 按集数降序排列（最新的在前）
    episodes.sort((a, b) => {
      const numA = parseFloat(a.episode) || 0;
      const numB = parseFloat(b.episode) || 0;
      return numB - numA;
    });

    log.info(`[Anime1] Fetched ${episodes.length} episodes`);
    return episodes;
  }

  /**
   * 提取剧集
   */
  private extractEpisodes(html: string): Episode[] {
    const $ = cheerio.load(html);
    const episodes: Episode[] = [];

    // 标准列表格式: <h2 class="entry-title"><a href="https://anime1.me/27788">Title [37]</a></h2>
    $('h2.entry-title a[href*="/"]').each((_, elem) => {
      const $elem = $(elem);
      const href = $elem.attr("href") || "";
      const titleText = $elem.text().trim();

      // 跳过分类链接
      if (href.includes("/?cat=") || href.includes("/category/")) {
        return;
      }

      // 提取剧集 ID
      const idMatch = href.match(/\/(\d+)$/);
      if (!idMatch) return;
      const episodeId = idMatch[1];

      // 提取集数序号 [N] 格式
      const epMatch = titleText.match(/\[(\d+(?:\.\d+)?)\]$/);
      if (!epMatch) return;
      const episodeNum = epMatch[1];

      // 清理标题
      const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, "").trim();

      // 提取日期
      const $article = $elem.closest("article");
      const date = $article.find("time.entry-date").text().trim();

      episodes.push({
        id: episodeId,
        title,
        episode: episodeNum,
        url: href,
        date,
      });
    });

    // 如果没有找到，检查是否是单集页面
    if (episodes.length === 0) {
      const singleEpisode = this.extractSingleEpisode(html);
      if (singleEpisode) {
        episodes.push(singleEpisode);
      }
    }

    return episodes;
  }

  /**
   * 提取单集（剧场版或单集页面）
   */
  private extractSingleEpisode(html: string): Episode | null {
    const $ = cheerio.load(html);

    // 检查是否是单篇文章页面
    const $article = $("article.post");
    if (!$article.length) return null;

    // 必须有视频标签
    const $video = $("video");
    if (!$video.length) return null;

    // 提取标题
    const titleText = $("h2.entry-title").text().trim();
    const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, "").trim();

    // 提取日期
    const date = $("time.entry-date").text().trim();

    // 从文章 class 提取 ID (e.g., "post-27546")
    let episodeId = "";
    const classAttr = $article.attr("class") || "";
    const idMatch = classAttr.match(/post-(\d+)/);
    if (idMatch) {
      episodeId = idMatch[1];
    }

    // 从 canonical 链接提取
    if (!episodeId) {
      const canonical = $('link[rel="canonical"]').attr("href") || "";
      const urlMatch = canonical.match(/\/(\d+)$/);
      if (urlMatch) {
        episodeId = urlMatch[1];
      }
    }

    if (!episodeId) return null;

    return {
      id: episodeId,
      title: title || "Unknown",
      episode: "1",
      url: `${URLS.ANIME1_BASE}/${episodeId}`,
      date,
    };
  }

  /**
   * 获取总页数
   */
  private getTotalEpisodePages(html: string): number {
    const $ = cheerio.load(html);
    let maxPage = 1;

    $('a[href*="/page/"]').each((_, elem) => {
      const href = $(elem).attr("href") || "";
      const match = href.match(/\/page\/(\d+)/);
      if (match) {
        const pageNum = parseInt(match[1], 10);
        maxPage = Math.max(maxPage, pageNum);
      }
    });

    return maxPage;
  }

  /**
   * 构建分页 URL
   */
  private buildPageUrl(detailUrl: string, page: number): string {
    if (detailUrl.includes("/category/")) {
      const parts = detailUrl.split("/category/");
      return `${parts[0]}/category/${parts[1]}/page/${page}`;
    } else if (detailUrl.includes("?cat=")) {
      return `${detailUrl}&page=${page}`;
    } else {
      return `${detailUrl}?page=${page}`;
    }
  }

  /**
   * 提取视频 URL
   * 对应原项目: src/routes/proxy.py - proxy_episode_api / proxy_video_url
   *
   * 注意：使用原生 fetch API 以支持 cookie 会话保持
   */
  async extractVideoUrl(episodeUrl: string): Promise<{
    url: string;
    cookies?: Record<string, string>;
  }> {
    log.info(`[Anime1] Extracting video URL: ${episodeUrl}`);

    const isPwDomain = episodeUrl.includes(DOMAINS.ANIME1_PW);

    const commonHeaders = {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      Accept: "text/html,*/*",
      "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
      Referer: URLS.ANIME1_BASE,
    };

    const html = await this.fetchPage(episodeUrl);
    const $ = cheerio.load(html);

    // 对于 anime1.pw: 直接从 video 标签提取
    if (isPwDomain) {
      const videoElem = $("video[src]");
      const src = videoElem.attr("src");

      if (!src) {
        throw new Error("未找到视频源");
      }

      const url = src.startsWith("//") ? `https:${src}` : src;
      log.info(`[Anime1] Extracted video URL (pw): ${url.substring(0, 50)}...`);

      return { url };
    }

    // 对于 anime1.me: 提取 API 参数并调用 API
    const videoElem = $("video[data-apireq]");
    const dataApireq = videoElem.attr("data-apireq");

    if (!dataApireq) {
      throw new Error("未找到 video[data-apireq] 元素");
    }

    // 解码并解析 API 参数
    let apiParams: Record<string, string | number>;
    try {
      const decoded = decodeURIComponent(dataApireq);
      apiParams = JSON.parse(decoded);
    } catch (error) {
      log.error("[Anime1] Failed to parse API params:", error);
      throw new Error("解析 API 参数失败");
    }

    const { c, e, t, p, s } = apiParams;

    if (!c || !e || !t || !s) {
      throw new Error("API 参数不完整");
    }

    // 2. 调用视频 API（会自动带上之前设置的 cookies）
    const postData = new URLSearchParams({
      d: JSON.stringify({
        [VIDEO_API.PARAM_C]: c,
        [VIDEO_API.PARAM_E]: e,
        [VIDEO_API.PARAM_T]: t,
        [VIDEO_API.PARAM_P]: p || 0,
        [VIDEO_API.PARAM_S]: s,
      }),
    });

    log.info("[Anime1] Calling video API...");
    const apiResponse = await fetch(VIDEO_API.URL, {
      method: "POST",
      headers: {
        ...commonHeaders,
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        Origin: URLS.ANIME1_BASE,
        Referer: URLS.ANIME1_BASE, // 使用首页作为 Referer（与 Python 一致）
      },
      body: postData.toString(),
      redirect: "manual", // 不跟随重定向（与 Python 的 allow_redirects=False 一致）
    });

    if (!apiResponse.ok) {
      throw new Error(`视频 API 请求失败: ${apiResponse.status}`);
    }

    // 3. 解析响应
    let data: any;
    try {
      data = await apiResponse.json();
    } catch (error) {
      log.error("[Anime1] Failed to parse API response:", error);
      throw new Error("解析视频 API 响应失败");
    }

    // 4. 从响应头中解析 cookies（用于后续视频流代理）
    const cookies: Record<string, string> = {};
    const setCookieHeader = apiResponse.headers.get("set-cookie");
    if (setCookieHeader) {
      // 简单解析 cookie
      setCookieHeader.split(",").forEach((cookieStr) => {
        const [nameValue] = cookieStr.split(";");
        const [name, value] = nameValue.trim().split("=");
        if (name && value) {
          cookies[name.trim()] = value.trim();
        }
      });
    }

    log.debug(`[Anime1] Video API cookies: ${JSON.stringify(cookies)}`);

    // 5. 从响应中提取视频 URL
    // 新格式: {"s": [{"src": "//host/path/file.mp4", "type": "video/mp4"}]}
    const sources = data.s;
    if (Array.isArray(sources) && sources.length > 0) {
      const src = sources[0].src;
      if (src) {
        const url = src.startsWith("//") ? `https:${src}` : src;
        log.info(
          `[Anime1] Extracted video URL (api): ${url.substring(0, 50)}...`,
        );
        return { url, cookies };
      }
    }

    // 旧格式回退
    if (data.l || data.file) {
      const url = data.l || data.file;
      log.info(
        `[Anime1] Extracted video URL (legacy): ${url.substring(0, 50)}...`,
      );
      return { url, cookies };
    }

    throw new Error("未能从 API 响应中提取视频 URL");
  }

  /**
   * 检测是否为成人内容
   */
  private checkIsAdult(title: string, detailUrl: string): boolean {
    // 检查标题中是否包含 🔞 标记
    if (title.includes(ADULT_CONTENT.MARKER)) {
      return true;
    }

    // 检查是否为 anime1.pw 域名
    if (ADULT_CONTENT.DOMAINS.some((domain) => detailUrl.includes(domain))) {
      return true;
    }

    // 检查关键词
    const titleLower = title.toLowerCase();
    if (
      ADULT_CONTENT.KEYWORDS.some((keyword) =>
        titleLower.includes(keyword.toLowerCase()),
      )
    ) {
      return true;
    }

    return false;
  }

  /**
   * 关闭爬虫
   */
  close(): void {
    this.httpClient.close();
    log.info("[Anime1] Crawler closed");
  }
}
