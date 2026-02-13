/**
 * Anime scraper service using Anime1.me JSON API
 * Reference: ~/Github/anime1-desktop/src/parser/anime1_parser.py
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { getCoverUrl, getBatchCovers } from './bangumi.js';
import { initCoverCache, getCachedCovers } from './coverCache.js';

const BASE_URL = 'https://anime1.me';
const API_URL = 'https://anime1.me/animelist.json';

// Create axios instance with browser-like headers
const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Referer': BASE_URL,
  }
});

// Cache for anime list
let animeCache = [];
let cacheTimestamp = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Parse anime list from JSON API
 * Data format: [id, title, episode_status, year, season, subtitle_group]
 * Example: [1805,"蘑菇魔女","連載中(07)","2026","冬",""]
 */
function parseAnimeListJSON(jsonData) {
  try {
    const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
    
    if (!Array.isArray(data)) {
      console.log('[Scraper] Invalid JSON data format');
      return [];
    }

    const animeList = [];
    const seenIds = new Set();

    for (const item of data) {
      if (!Array.isArray(item) || item.length < 2) continue;

      const catId = String(item[0]);
      const titleRaw = String(item[1]);
      
      // Extract clean title (remove HTML tags)
      const title = titleRaw.replace(/<[^>]*>/g, '').trim();
      
      if (!title) continue;

      // Extract episode from format like "連載中(07)" or "(37)"
      const episodeStr = item[2] ? String(item[2]) : '0';
      const episodeMatch = episodeStr.match(/\((\d+)\)/);
      const episode = episodeMatch ? parseInt(episodeMatch[1]) : 0;

      // Extract year, season, subtitle group
      const year = item[3] ? String(item[3]) : '';
      const season = item[4] ? String(item[4]) : '';
      const subtitleGroup = item[5] ? String(item[5]) : '';

      // Build detail URL
      let detailUrl;
      let uniqueId;
      
      if (catId === '0' || !catId) {
        // External link - extract from href
        const linkMatch = titleRaw.match(/href="([^"]+)"/);
        if (linkMatch) {
          detailUrl = linkMatch[1];
          uniqueId = String(Math.abs(title.split('').reduce((a, b) => ((a << 5) - a) + b.charCodeAt(0), 0)) % 1000000);
        } else {
          continue;
        }
      } else {
        detailUrl = `${BASE_URL}/?cat=${catId}`;
        uniqueId = catId;
      }

      // Skip duplicates
      if (seenIds.has(uniqueId)) continue;
      seenIds.add(uniqueId);

      animeList.push({
        id: uniqueId,
        title,
        episode,
        year,
        season,
        subtitle_group: subtitleGroup,
        detail_url: detailUrl,
        cover_url: '',
      });
    }

    return animeList;
  } catch (error) {
    console.error('[Scraper] Error parsing JSON:', error.message);
    return [];
  }
}

/**
 * Parse anime detail from HTML
 * Reference: parse_anime_detail in Python parser
 */
function parseAnimeDetail(html, id) {
  const $ = cheerio.load(html);
  
  // Get title from entry-title
  const titleElem = $('h1.entry-title, h2.entry-title').first();
  const title = titleElem.text().trim() || $('h1').first().text().trim() || `番剧 ${id}`;
  
  // Get description from entry-content
  const description = $('.entry-content p').first().text().trim() || '';
  
  // Extract metadata from page text
  const pageText = $.text();
  
  // Extract year (2020-2029)
  const yearMatch = pageText.match(/(202[0-9])/);
  const year = yearMatch ? yearMatch[1] : '';
  
  // Extract season
  const seasons = ['冬季', '春季', '夏季', '秋季'];
  const season = seasons.find(s => pageText.includes(s)) || '';
  
  // Extract subtitle group keywords
  const subtitleKeywords = ['MCE', 'Bilibili', '巴哈姆特', '木棉花', 'Ani-One', 'Viu', 'Netflix', 'Disney'];
  const subtitleGroup = subtitleKeywords.find(kw => pageText.includes(kw)) || '';
  
  return {
    id,
    title,
    description,
    cover_url: '',
    year,
    season,
    subtitle_group: subtitleGroup,
  };
}

/**
 * Parse episodes from HTML
 * Reference: _extract_episodes in Python parser
 */
function parseEpisodes(html) {
  const $ = cheerio.load(html);
  const episodes = [];
  
  // Pattern 1: Standard category listing - h2.entry-title a
  $('h2.entry-title a[href*="/"]').each((i, elem) => {
    const $elem = $(elem);
    const href = $elem.attr('href') || '';
    const titleText = $elem.text().trim();
    
    // Skip category links
    if (href.includes('/?cat=') || href.includes('/category/')) return;
    
    // Extract episode ID from URL like https://anime1.me/27788
    const match = href.match(/\/(\d+)$/);
    if (!match) return;
    
    const episodeId = match[1];
    
    // Extract episode number from title like "Princession Orchestra [37]"
    const epMatch = titleText.match(/\[(\d+(?:\.\d+)?)\]$/);
    if (!epMatch) return;
    
    const episodeNum = epMatch[1];
    const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, '').trim();
    
    // Find date in same article
    const article = $elem.closest('article');
    const date = article.find('time.entry-date').text().trim() || '';
    
    episodes.push({
      id: episodeId,
      title: `${title} [${episodeNum}]`,
      episode: episodeNum,
      url: href,
      date,
    });
  });
  
  // If no episodes found, check for single episode page (movie/standalone)
  if (episodes.length === 0) {
    const singleEpisode = parseSingleEpisode($);
    if (singleEpisode) {
      episodes.push(singleEpisode);
    }
  }
  
  return episodes;
}

/**
 * Parse single episode/movie page
 * Reference: _extract_single_episode in Python parser
 */
function parseSingleEpisode($) {
  // Check if this is a single post page
  const article = $('article').first();
  if (!article.length) return null;
  
  const articleClasses = article.attr('class') || '';
  if (!articleClasses.includes('post')) return null;
  
  // Check for video tag
  const video = $('video');
  if (!video.length) return null;
  
  // Get episode ID from article class (e.g., "post-27546")
  const postMatch = articleClasses.match(/post-(\d+)/);
  const episodeId = postMatch ? postMatch[1] : '';
  
  if (!episodeId) return null;
  
  // Extract title
  const titleElem = $('h1.entry-title, h2.entry-title').first();
  const titleText = titleElem.text().trim();
  const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, '').trim() || 'Unknown';
  
  // Extract date
  const date = $('time.entry-date').text().trim() || '';
  
  return {
    id: episodeId,
    title,
    episode: '1',
    url: `${BASE_URL}/${episodeId}`,
    date,
  };
}

/**
 * Fetch anime list with caching
 */
async function fetchAnimeList() {
  const now = Date.now();
  if (animeCache.length > 0 && (now - cacheTimestamp) < CACHE_TTL) {
    console.log('[Scraper] Using cached anime list');
    return animeCache;
  }
  
  try {
    console.log('[Scraper] Fetching anime list from', API_URL);
    const response = await http.get(API_URL);
    const animeList = parseAnimeListJSON(response.data);
    
    if (animeList.length === 0) {
      console.log('[Scraper] No anime found from API, using mock data');
      return getMockAnimeList();
    }
    
    animeCache = animeList;
    cacheTimestamp = now;
    
    console.log(`[Scraper] Fetched ${animeList.length} anime from API`);
    return animeList;
  } catch (error) {
    console.error('[Scraper] Error fetching anime list:', error.message);
    return getMockAnimeList();
  }
}

/**
 * Get mock anime list as fallback
 */
function getMockAnimeList() {
  return [
    { id: '1', title: '鬼灭之刃 柱训练篇', episode: 8, cover_url: '', year: '2024', season: '春季', subtitle_group: 'MCE', description: '鬼灭之刃最新篇章' },
    { id: '2', title: '咒术回战 第二季', episode: 23, cover_url: '', year: '2023', season: '夏季', subtitle_group: 'Bilibili', description: '涩谷事变篇' },
    { id: '3', title: '我推的孩子', episode: 11, cover_url: '', year: '2023', season: '春季', subtitle_group: 'MCE', description: '偶像与转生的故事' },
    { id: '4', title: '无职转生 第二季', episode: 12, cover_url: '', year: '2023', season: '夏季', subtitle_group: 'Bilibili', description: '异世界转生经典' },
    { id: '5', title: '葬送的芙莉莲', episode: 28, cover_url: '', year: '2023', season: '秋季', subtitle_group: 'MCE', description: '勇者死后的世界' },
    { id: '6', title: '进击的巨人 最终季', episode: 32, cover_url: '', year: '2023', season: '秋季', subtitle_group: 'Bilibili', description: '完结篇' },
    { id: '7', title: '间谍过家家 第二季', episode: 12, cover_url: '', year: '2023', season: '秋季', subtitle_group: 'MCE', description: '家庭喜剧' },
    { id: '8', title: '电锯人', episode: 12, cover_url: '', year: '2022', season: '秋季', subtitle_group: 'MCE', description: '藤本树原作' },
    { id: '9', title: '孤独摇滚', episode: 12, cover_url: '', year: '2022', season: '秋季', subtitle_group: 'Bilibili', description: '音乐番' },
    { id: '10', title: '灵能百分百 第三季', episode: 12, cover_url: '', year: '2022', season: '秋季', subtitle_group: 'Bilibili', description: 'ONE原作' },
    { id: '11', title: '文豪野犬 第四季', episode: 13, cover_url: '', year: '2023', season: '冬季', subtitle_group: 'MCE', description: '异能战斗' },
    { id: '12', title: '蓝色监狱', episode: 24, cover_url: '', year: '2022', season: '秋季', subtitle_group: 'Bilibili', description: '足球竞技' },
  ];
}

// Helper to format anime data for list view
const formatAnimeList = (animeList) => {
  return animeList.map(a => ({
    id: a.id,
    title: a.title,
    episode: a.episode,
    cover_url: a.cover_url || '',
    year: a.year || '',
    season: a.season || '',
    subtitle_group: a.subtitle_group || '',
    detail_url: a.detail_url || `${BASE_URL}/?cat=${a.id}`
  }));
};

// Anime scraper service
export const animeScraper = {
  // Get anime list
  async getList(page = 1) {
    console.log('[Scraper] Fetching anime list, page:', page);
    
    // Initialize cover cache
    initCoverCache();
    
    const animeList = await fetchAnimeList();
    
    // Simulate pagination
    const perPage = 20;
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const paginatedList = animeList.slice(start, end);
    
    // Check persistent cache first
    const ids = paginatedList.map(a => a.id);
    const cachedCovers = getCachedCovers(ids);
    
    // Apply cached covers
    const uncachedList = [];
    paginatedList.forEach(anime => {
      const cached = cachedCovers[anime.id];
      if (cached && cached.cover_url) {
        anime.cover_url = cached.cover_url;
        console.log(`[Scraper] Cache hit for ${anime.title}`);
      } else {
        anime.cover_url = '';
        uncachedList.push(anime);
      }
    });
    
    // Fetch covers from Bangumi for uncached anime
    if (uncachedList.length > 0) {
      console.log(`[Scraper] Fetching ${uncachedList.length} covers from Bangumi...`);
      const covers = await getBatchCovers(uncachedList);
      const coverMap = new Map(covers.map(c => [c.id, c.cover_url]));
      
      uncachedList.forEach(anime => {
        anime.cover_url = coverMap.get(anime.id) || '';
      });
    }
    
    const formattedList = formatAnimeList(paginatedList);
    
    return {
      success: true,
      data: {
        anime_list: formattedList,
        current_page: page,
        total_pages: Math.ceil(animeList.length / perPage)
      }
    };
  },
  
  // Search anime
  async search(keyword, page = 1) {
    console.log('[Scraper] Searching:', keyword);
    
    const animeList = await fetchAnimeList();
    
    const filtered = animeList.filter(a => 
      a.title.toLowerCase().includes(keyword.toLowerCase())
    );
    
    const perPage = 20;
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const paginatedList = filtered.slice(start, end);
    
    return {
      success: true,
      data: {
        anime_list: formatAnimeList(paginatedList),
        current_page: page,
        total_pages: Math.ceil(filtered.length / perPage)
      }
    };
  },
  
  // Get anime detail and episodes
  async getDetail(id) {
    console.log('[Scraper] Getting detail for id:', id);
    
    try {
      // Try to fetch real detail page
      const response = await http.get(`/?cat=${id}`);
      const detail = parseAnimeDetail(response.data, id);
      const episodes = parseEpisodes(response.data);
      
      // Fetch cover from Bangumi
      let coverUrl = '';
      try {
        coverUrl = await getCoverUrl(detail.title);
        console.log(`[Scraper] Got cover for ${detail.title}: ${coverUrl ? '✓' : '✗'}`);
      } catch (coverError) {
        console.log(`[Scraper] Failed to get cover for ${detail.title}:`, coverError.message);
      }
      
      return {
        success: true,
        data: {
          anime: {
            id: detail.id,
            title: detail.title,
            description: detail.description || '暂无描述',
            cover_url: coverUrl || detail.cover_url || '',
            year: detail.year || '',
            season: detail.season || '',
            subtitle_group: detail.subtitle_group || ''
          },
          episodes: episodes.length > 0 ? episodes : generateMockEpisodes(12),
          requires_frontend_fetch: false
        }
      };
    } catch (error) {
      console.error('[Scraper] Error fetching detail:', error.message);
      
      // Fallback to mock data
      const animeList = await fetchAnimeList();
      const anime = animeList.find(a => a.id === id) || {
        id,
        title: `番剧 ${id}`,
        episode: 12,
        description: '暂无描述',
        cover_url: '',
        year: '',
        season: '',
        subtitle_group: ''
      };
      
      // Fetch cover for fallback too
      let coverUrl = anime.cover_url || '';
      if (!coverUrl && anime.title) {
        try {
          coverUrl = await getCoverUrl(anime.title);
        } catch (e) {
          // Ignore error
        }
      }
      
      return {
        success: true,
        data: {
          anime: {
            id: anime.id,
            title: anime.title,
            description: anime.description || '暂无描述',
            cover_url: coverUrl,
            year: anime.year || '',
            season: anime.season || '',
            subtitle_group: anime.subtitle_group || ''
          },
          episodes: generateMockEpisodes(anime.episode || 12),
          requires_frontend_fetch: false
        }
      };
    }
  },
  
  // Get episodes (alias for getDetail)
  async getEpisodes(id) {
    const result = await this.getDetail(id);
    if (result.success) {
      return {
        success: true,
        data: {
          anime: result.data.anime,
          episodes: result.data.episodes
        }
      };
    }
    return result;
  }
};

// Generate mock episodes for fallback
function generateMockEpisodes(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: `ep${i + 1}`,
    title: `第${i + 1}集`,
    episode: String(i + 1),
    url: '',
    date: ''
  }));
}

export default animeScraper;
