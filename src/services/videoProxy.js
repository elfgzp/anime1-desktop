/**
 * Video Proxy Service for Electron
 * Handles video URL extraction and streaming from anime1.me/anime1.pw
 */

import axios from 'axios';
import * as cheerio from 'cheerio';

const ANIME1_BASE_URL = 'https://anime1.me';
const ANIME1_API_URL = 'https://v.anime1.me/api';
const DOMAIN_ANIME1_ME = 'anime1.me';
const DOMAIN_ANIME1_PW = 'anime1.pw';

// Video API parameters
const VIDEO_API_PARAM_C = 'c';
const VIDEO_API_PARAM_E = 'e';
const VIDEO_API_PARAM_T = 't';
const VIDEO_API_PARAM_P = 'p';
const VIDEO_API_PARAM_S = 's';

const DEFAULT_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'text/html,*/*',
  'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
  'Referer': ANIME1_BASE_URL,
  'Origin': ANIME1_BASE_URL,
};

/**
 * Extract API parameters from episode page HTML
 */
function extractApiParams(html) {
  try {
    const $ = cheerio.load(html);
    const videoElem = $('video[data-apireq]');
    
    if (!videoElem.length) {
      console.log('[VideoProxy] No video[data-apireq] element found');
      return null;
    }
    
    const dataApireq = decodeURIComponent(videoElem.attr('data-apireq') || '{}');
    return JSON.parse(dataApireq);
  } catch (error) {
    console.error('[VideoProxy] Failed to extract API params:', error);
    return null;
  }
}

/**
 * Call anime1.me video API
 */
async function callVideoApi(params) {
  const postData = new URLSearchParams();
  postData.append('d', JSON.stringify({
    [VIDEO_API_PARAM_C]: params[VIDEO_API_PARAM_C],
    [VIDEO_API_PARAM_E]: params[VIDEO_API_PARAM_E],
    [VIDEO_API_PARAM_T]: params[VIDEO_API_PARAM_T],
    [VIDEO_API_PARAM_P]: params[VIDEO_API_PARAM_P] || 0,
    [VIDEO_API_PARAM_S]: params[VIDEO_API_PARAM_S],
  }));

  const response = await axios.post(ANIME1_API_URL, postData, {
    headers: {
      ...DEFAULT_HEADERS,
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
    },
    timeout: 10000,
    maxRedirects: 0,
    validateStatus: (status) => status < 400,
  });

  // Parse cookies from response
  const cookies = {};
  const setCookieHeader = response.headers['set-cookie'];
  if (setCookieHeader) {
    setCookieHeader.forEach(cookie => {
      const [nameValue] = cookie.split(';');
      const [name, value] = nameValue.split('=').map(s => s.trim());
      if (name && value) {
        cookies[name] = value;
      }
    });
  }

  return { data: response.data, cookies };
}

/**
 * Extract video URL from API response
 */
function extractVideoUrl(data) {
  // New format: {"s": [{"src": "//host/path/file.mp4", "type": "video/mp4"}]}
  const videoSources = data.s;
  if (videoSources && videoSources.length > 0) {
    const src = videoSources[0].src;
    if (src) {
      return src.startsWith('//') ? `https:${src}` : src;
    }
  }

  // Old format fallback
  if (data.success && data.file) {
    return data.file;
  }
  if (data.success && data.stream) {
    return data.stream;
  }

  return null;
}

/**
 * Extract video URL from anime1.pw page
 */
function extractPwVideoUrl(html) {
  try {
    const $ = cheerio.load(html);
    const videoElem = $('video[src]');
    
    if (videoElem.length && videoElem.attr('src')) {
      let videoUrl = videoElem.attr('src');
      if (videoUrl.startsWith('//')) {
        videoUrl = `https:${videoUrl}`;
      }
      return videoUrl;
    }
    
    return null;
  } catch (error) {
    console.error('[VideoProxy] Failed to extract PW video URL:', error);
    return null;
  }
}

/**
 * Get video info from episode URL
 */
export async function getVideoInfo(targetUrl) {
  console.log('[VideoProxy] Getting video info for:', targetUrl);
  
  if (!targetUrl) {
    return { success: false, error: 'URL is required' };
  }

  // Check domain
  const urlObj = new URL(targetUrl);
  const isAnime1Me = urlObj.hostname.includes(DOMAIN_ANIME1_ME);
  const isAnime1Pw = urlObj.hostname.includes(DOMAIN_ANIME1_PW);
  
  if (!isAnime1Me && !isAnime1Pw) {
    return { success: false, error: 'Invalid domain' };
  }

  try {
    // Fetch episode page
    const response = await axios.get(targetUrl, {
      headers: DEFAULT_HEADERS,
      timeout: 10000,
    });

    // Handle anime1.pw
    if (isAnime1Pw) {
      const videoUrl = extractPwVideoUrl(response.data);
      if (videoUrl) {
        return { success: true, url: videoUrl, cookies: {} };
      }
      return { success: false, error: 'Player not found' };
    }

    // Handle anime1.me
    const apiParams = extractApiParams(response.data);
    if (!apiParams) {
      console.log('[VideoProxy] API params not found in HTML');
      return { success: false, error: 'Player not found on page' };
    }

    const params = {
      [VIDEO_API_PARAM_C]: apiParams[VIDEO_API_PARAM_C] || '',
      [VIDEO_API_PARAM_E]: apiParams[VIDEO_API_PARAM_E] || '',
      [VIDEO_API_PARAM_T]: apiParams[VIDEO_API_PARAM_T] || '',
      [VIDEO_API_PARAM_P]: apiParams[VIDEO_API_PARAM_P] || 0,
      [VIDEO_API_PARAM_S]: apiParams[VIDEO_API_PARAM_S] || '',
    };

    if (!params[VIDEO_API_PARAM_C] || !params[VIDEO_API_PARAM_E] || 
        !params[VIDEO_API_PARAM_T] || !params[VIDEO_API_PARAM_S]) {
      console.log('[VideoProxy] Incomplete API params:', params);
      return { success: false, error: 'Incomplete API parameters' };
    }

    // Call video API
    const { data, cookies } = await callVideoApi(params);
    const videoUrl = extractVideoUrl(data);
    
    if (!videoUrl) {
      console.log('[VideoProxy] No video URL in API response:', data);
      return { success: false, error: 'No video sources found' };
    }

    return { success: true, url: videoUrl, cookies };

  } catch (error) {
    console.error('[VideoProxy] Error getting video info:', error.message);
    return { success: false, error: error.message || 'Network error' };
  }
}

/**
 * Stream video content (for direct proxy)
 */
export async function streamVideo(videoUrl, cookies = {}) {
  console.log('[VideoProxy] Streaming video:', videoUrl);
  
  try {
    const cookieHeader = Object.entries(cookies)
      .map(([name, value]) => `${name}=${value}`)
      .join('; ');

    const response = await axios.get(videoUrl, {
      headers: {
        ...DEFAULT_HEADERS,
        'Cookie': cookieHeader,
        'Range': 'bytes=0-',
      },
      timeout: 30000,
      responseType: 'stream',
      maxRedirects: 5,
    });

    return {
      success: true,
      data: response.data,
      headers: response.headers,
    };

  } catch (error) {
    console.error('[VideoProxy] Error streaming video:', error.message);
    return { success: false, error: error.message };
  }
}

export default {
  getVideoInfo,
  streamVideo,
};
