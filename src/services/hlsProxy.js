/**
 * HLS Proxy Service for Electron
 * Handles HLS playlist proxying with URL rewriting for cross-origin support
 */

import axios from 'axios';
import { Parser } from 'm3u8-parser';

const ANIME1_BASE_URL = 'https://anime1.me';
const DOMAIN_ANIME1_ME = 'anime1.me';
const DOMAIN_ANIME1_PW = 'anime1.pw';

const DEFAULT_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': '*/*',
  'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
  'Referer': ANIME1_BASE_URL,
};

/**
 * Check if content is an HLS playlist
 */
function isHlsPlaylist(content) {
  if (typeof content === 'string') {
    return content.includes('#EXTM3U') || content.includes('.m3u8');
  }
  if (Buffer.isBuffer(content)) {
    const str = content.toString('utf-8', 0, Math.min(content.length, 100));
    return str.includes('#EXTM3U');
  }
  return false;
}

/**
 * Rewrite URI to proxy URL
 */
function rewriteUri(uri, baseUrl, cookies = {}) {
  let absoluteUrl;
  
  if (uri.startsWith('http://') || uri.startsWith('https://')) {
    // Absolute URL - proxy it
    absoluteUrl = uri;
  } else if (uri.startsWith('/')) {
    // Absolute path on same domain
    const parsed = new URL(baseUrl);
    absoluteUrl = `${parsed.protocol}//${parsed.host}${uri}`;
  } else {
    // Relative path - convert to absolute using base URL
    const parsed = new URL(baseUrl);
    const baseDir = parsed.pathname.split('/').slice(0, -1).join('/');
    absoluteUrl = `${parsed.protocol}//${parsed.host}${baseDir}/${uri}`;
  }
  
  // Return absolute URL (player will use proxy protocol handler)
  return absoluteUrl;
}

/**
 * Parse and rewrite HLS playlist
 */
function rewritePlaylist(content, playlistUrl, cookies = {}) {
  const parser = new Parser();
  parser.push(content);
  parser.end();
  
  const manifest = parser.manifest;
  let modified = false;
  
  // Rewrite segment URIs
  if (manifest.segments && manifest.segments.length > 0) {
    manifest.segments.forEach(segment => {
      if (segment.uri) {
        segment.uri = rewriteUri(segment.uri, playlistUrl, cookies);
        modified = true;
      }
    });
  }
  
  // Rewrite playlist URIs (variant streams in master playlist)
  if (manifest.playlists && manifest.playlists.length > 0) {
    manifest.playlists.forEach(playlist => {
      if (playlist.uri) {
        playlist.uri = rewriteUri(playlist.uri, playlistUrl, cookies);
        modified = true;
      }
    });
  }
  
  // Serialize back to M3U8 format
  return serializeM3U8(manifest, content);
}

/**
 * Serialize manifest back to M3U8 format
 */
function serializeM3U8(manifest, originalContent) {
  const lines = ['#EXTM3U'];
  
  // Add version if present
  if (manifest.version) {
    lines.push(`#EXT-X-VERSION:${manifest.version}`);
  }
  
  // Add target duration
  if (manifest.targetDuration) {
    lines.push(`#EXT-X-TARGETDURATION:${manifest.targetDuration}`);
  }
  
  // Add media sequence
  if (manifest.mediaSequence !== undefined) {
    lines.push(`#EXT-X-MEDIA-SEQUENCE:${manifest.mediaSequence}`);
  }
  
  // Add playlists (variant streams in master playlist)
  if (manifest.playlists && manifest.playlists.length > 0) {
    manifest.playlists.forEach(playlist => {
      const attrs = [];
      if (playlist.attributes) {
        if (playlist.attributes.BANDWIDTH) {
          attrs.push(`BANDWIDTH=${playlist.attributes.BANDWIDTH}`);
        }
        if (playlist.attributes.RESOLUTION) {
          attrs.push(`RESOLUTION=${playlist.attributes.RESOLUTION.width}x${playlist.attributes.RESOLUTION.height}`);
        }
        if (playlist.attributes.CODECS) {
          attrs.push(`CODECS="${playlist.attributes.CODECS}"`);
        }
      }
      if (attrs.length > 0) {
        lines.push(`#EXT-X-STREAM-INF:${attrs.join(',')}`);
      }
      lines.push(playlist.uri);
    });
  }
  
  // Add segments
  if (manifest.segments && manifest.segments.length > 0) {
    manifest.segments.forEach(segment => {
      // Add discontinuity tag if present
      if (segment.discontinuity) {
        lines.push('#EXT-X-DISCONTINUITY');
      }
      
      // Add key tag if present
      if (segment.key) {
        const keyAttrs = [`METHOD=${segment.key.method}`];
        if (segment.key.uri) {
          keyAttrs.push(`URI="${segment.key.uri}"`);
        }
        if (segment.key.iv) {
          keyAttrs.push(`IV=${segment.key.iv}`);
        }
        lines.push(`#EXT-X-KEY:${keyAttrs.join(',')}`);
      }
      
      // Add map tag if present
      if (segment.map) {
        const mapAttrs = [`URI="${segment.map.uri}"`];
        if (segment.map.byterange) {
          mapAttrs.push(`BYTERANGE=${segment.map.byterange}`);
        }
        lines.push(`#EXT-X-MAP:${mapAttrs.join(',')}`);
      }
      
      // Add segment info
      if (segment.duration !== undefined) {
        const title = segment.title || '';
        lines.push(`#EXTINF:${segment.duration.toFixed(3)},${title}`);
      }
      
      // Add byte range if present
      if (segment.byterange) {
        lines.push(`#EXT-X-BYTERANGE:${segment.byterange}`);
      }
      
      lines.push(segment.uri);
    });
  }
  
  // Add endlist if present
  if (manifest.endList) {
    lines.push('#EXT-X-ENDLIST');
  }
  
  return lines.join('\n') + '\n';
}

/**
 * Proxy HLS playlist and rewrite URLs
 */
export async function proxyHlsPlaylist(playlistUrl, cookies = {}) {
  console.log('[HlsProxy] Proxying HLS playlist:', playlistUrl);
  
  if (!playlistUrl) {
    return { success: false, error: 'URL is required' };
  }
  
  // Check domain
  const urlObj = new URL(playlistUrl);
  const isAnime1Me = urlObj.hostname.includes(DOMAIN_ANIME1_ME);
  const isAnime1Pw = urlObj.hostname.includes(DOMAIN_ANIME1_PW);
  
  if (!isAnime1Me && !isAnime1Pw) {
    return { success: false, error: 'Invalid domain' };
  }
  
  try {
    const response = await axios.get(playlistUrl, {
      headers: {
        ...DEFAULT_HEADERS,
        'Accept': 'application/vnd.apple.mpegurl,*/*',
      },
      cookies: cookies,
      timeout: 15000,
      responseType: 'text',
    });
    
    const content = response.data;
    
    // Check if it's an HLS playlist
    if (!isHlsPlaylist(content)) {
      // Not a playlist, return as-is (likely a video segment)
      return {
        success: true,
        isPlaylist: false,
        content: Buffer.from(content),
        contentType: response.headers['content-type'] || 'video/mp2t',
      };
    }
    
    // Parse and rewrite playlist
    const rewrittenContent = rewritePlaylist(content, playlistUrl, cookies);
    
    return {
      success: true,
      isPlaylist: true,
      content: rewrittenContent,
      contentType: 'application/vnd.apple.mpegurl',
    };
    
  } catch (error) {
    console.error('[HlsProxy] Error proxying HLS playlist:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Proxy video stream with range support
 */
export async function proxyVideoStream(videoUrl, options = {}) {
  console.log('[HlsProxy] Proxying video stream:', videoUrl);
  
  if (!videoUrl) {
    return { success: false, error: 'URL is required' };
  }
  
  const { cookies = {}, range, useAxios = false } = options;
  
  try {
    const headers = {
      ...DEFAULT_HEADERS,
      'Accept': '*/*',
    };
    
    // Add range header for seeking support
    if (range) {
      headers['Range'] = range;
    }
    
    const response = await axios.get(videoUrl, {
      headers,
      cookies: Object.keys(cookies).length > 0 ? cookies : undefined,
      timeout: 60000,
      responseType: 'stream',
      validateStatus: (status) => status < 400,
    });
    
    const responseHeaders = {
      'Content-Type': response.headers['content-type'] || 'video/mp4',
      'Accept-Ranges': response.headers['accept-ranges'] || 'bytes',
    };
    
    // Pass through content length and range headers
    if (response.headers['content-length']) {
      responseHeaders['Content-Length'] = response.headers['content-length'];
    }
    if (response.headers['content-range']) {
      responseHeaders['Content-Range'] = response.headers['content-range'];
    }
    
    return {
      success: true,
      stream: response.data,
      headers: responseHeaders,
      statusCode: response.status,
    };
    
  } catch (error) {
    console.error('[HlsProxy] Error proxying video stream:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Get proxy URL for video playback
 * This returns a URL that can be used directly in the player
 */
export function getProxyUrl(originalUrl, type = 'auto') {
  if (!originalUrl) return null;
  
  // For HLS playlists, we need to proxy through our custom protocol
  if (type === 'hls' || originalUrl.includes('.m3u8')) {
    // Use a custom protocol handler that will be registered in main process
    return `anime1-proxy://${Buffer.from(originalUrl).toString('base64')}`;
  }
  
  // For direct MP4, return as-is (CORS headers are handled by webRequest)
  return originalUrl;
}

export default {
  proxyHlsPlaylist,
  proxyVideoStream,
  getProxyUrl,
};
