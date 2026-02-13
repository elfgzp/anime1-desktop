import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios');

describe('HLS Proxy Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('isHlsPlaylist', () => {
    it('should return true for M3U8 content', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const mockResponse = {
        data: '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nvideo.m3u8',
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/test/playlist.m3u8');
      
      expect(result.success).toBe(true);
      expect(result.isPlaylist).toBe(true);
      expect(result.content).toContain('#EXTM3U');
    });

    it('should return false for non-M3U8 content', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const mockResponse = {
        data: Buffer.from('binary video data'),
        headers: { 'content-type': 'video/mp2t' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/test/segment.ts');
      
      expect(result.success).toBe(true);
      expect(result.isPlaylist).toBe(false);
    });
  });

  describe('proxyHlsPlaylist', () => {
    it('should require URL parameter', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const result = await proxyHlsPlaylist('');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('URL is required');
    });

    it('should reject invalid domains', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const result = await proxyHlsPlaylist('https://example.com/video.m3u8');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid domain');
    });

    it('should accept anime1.me domain', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const mockResponse = {
        data: '#EXTM3U\n#EXT-X-VERSION:3\n',
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/1779/2/playlist.m3u8');
      
      expect(result.success).toBe(true);
    });

    it('should accept anime1.pw domain', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const mockResponse = {
        data: '#EXTM3U\n#EXT-X-VERSION:3\n',
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://v.anime1.pw/video.m3u8');
      
      expect(result.success).toBe(true);
    });
  });

  describe('proxyVideoStream', () => {
    it('should require URL parameter', async () => {
      const { proxyVideoStream } = await import('../../src/services/hlsProxy.js');
      
      const result = await proxyVideoStream('');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('URL is required');
    });

    it('should handle range requests', async () => {
      const { proxyVideoStream } = await import('../../src/services/hlsProxy.js');
      
      const mockStream = {
        pipe: vi.fn(),
        on: vi.fn(),
      };
      
      const mockResponse = {
        data: mockStream,
        status: 206,
        headers: {
          'content-type': 'video/mp4',
          'content-range': 'bytes 0-1023/1024000',
          'accept-ranges': 'bytes',
        },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyVideoStream('https://suisei.v.anime1.me/video.mp4', {
        range: 'bytes=0-1023',
      });
      
      expect(result.success).toBe(true);
      expect(result.statusCode).toBe(206);
      expect(result.headers['Content-Range']).toBe('bytes 0-1023/1024000');
    });

    it('should pass cookies to request', async () => {
      const { proxyVideoStream } = await import('../../src/services/hlsProxy.js');
      
      const mockStream = {
        pipe: vi.fn(),
        on: vi.fn(),
      };
      
      const mockResponse = {
        data: mockStream,
        status: 200,
        headers: { 'content-type': 'video/mp4' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const cookies = { 'auth': 'token123', 'session': 'abc' };
      await proxyVideoStream('https://suisei.v.anime1.me/video.mp4', { cookies });
      
      expect(axios.get).toHaveBeenCalledWith(
        'https://suisei.v.anime1.me/video.mp4',
        expect.objectContaining({
          cookies: cookies,
        })
      );
    });
  });

  describe('URL rewriting', () => {
    it('should rewrite relative segment URLs to absolute', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const playlistContent = `#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:9.009,
segment1.ts
#EXTINF:8.008,
segment2.ts
#EXT-X-ENDLIST
`;
      
      const mockResponse = {
        data: playlistContent,
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/1779/2/720p.m3u8');
      
      expect(result.success).toBe(true);
      expect(result.isPlaylist).toBe(true);
      // The content should have rewritten URLs
      expect(result.content).toContain('https://suisei.v.anime1.me/1779/2/segment1.ts');
      expect(result.content).toContain('https://suisei.v.anime1.me/1779/2/segment2.ts');
    });

    it('should rewrite absolute URLs in playlists', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const playlistContent = `#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=1920x1080
https://other.cdn.com/1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=1280x720
https://other.cdn.com/720p.m3u8
`;
      
      const mockResponse = {
        data: playlistContent,
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/1779/2/master.m3u8');
      
      expect(result.success).toBe(true);
      // URLs should be preserved as absolute
      expect(result.content).toContain('https://other.cdn.com/1080p.m3u8');
    });

    it('should preserve EXTINF tags', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      const playlistContent = `#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:9.009,
segment1.ts
#EXTINF:8.008,
segment2.ts
#EXT-X-ENDLIST
`;
      
      const mockResponse = {
        data: playlistContent,
        headers: { 'content-type': 'application/vnd.apple.mpegurl' },
      };
      axios.get.mockResolvedValue(mockResponse);

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/1779/2/playlist.m3u8');
      
      expect(result.success).toBe(true);
      expect(result.content).toContain('#EXTINF:9.009,');
      expect(result.content).toContain('#EXTINF:8.008,');
      expect(result.content).toContain('#EXT-X-ENDLIST');
    });
  });

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      const { proxyHlsPlaylist } = await import('../../src/services/hlsProxy.js');
      
      axios.get.mockRejectedValue(new Error('Network Error'));

      const result = await proxyHlsPlaylist('https://suisei.v.anime1.me/test.m3u8');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Network Error');
    });

    it('should handle 403 errors', async () => {
      const { proxyVideoStream } = await import('../../src/services/hlsProxy.js');
      
      axios.get.mockRejectedValue(new Error('Request failed with status code 403'));

      const result = await proxyVideoStream('https://suisei.v.anime1.me/video.mp4');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('403');
    });
  });
});

describe('getProxyUrl', () => {
  it('should return null for empty URL', async () => {
    const { getProxyUrl } = await import('../../src/services/hlsProxy.js');
    
    expect(getProxyUrl('')).toBeNull();
    expect(getProxyUrl(null)).toBeNull();
    expect(getProxyUrl(undefined)).toBeNull();
  });

  it('should return original URL for MP4 videos', async () => {
    const { getProxyUrl } = await import('../../src/services/hlsProxy.js');
    
    const url = 'https://example.com/video.mp4';
    expect(getProxyUrl(url)).toBe(url);
  });

  it('should detect HLS by URL pattern', async () => {
    const { getProxyUrl } = await import('../../src/services/hlsProxy.js');
    
    const hlsUrl = 'https://example.com/playlist.m3u8';
    const result = getProxyUrl(hlsUrl);
    
    // Should return a proxied URL
    expect(result).not.toBe(hlsUrl);
    expect(result).toContain('anime1-proxy://');
  });

  it('should detect HLS by type parameter', async () => {
    const { getProxyUrl } = await import('../../src/services/hlsProxy.js');
    
    const url = 'https://example.com/video';
    const result = getProxyUrl(url, 'hls');
    
    expect(result).not.toBe(url);
    expect(result).toContain('anime1-proxy://');
  });
});
