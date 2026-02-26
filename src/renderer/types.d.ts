/**
 * 全局类型定义
 */

import type { 
  AutoDownloadConfig, 
  DownloadFilter, 
  DownloadRecord, 
  AutoDownloadStatus 
} from '@shared/types'

// 扩展 Window 接口
declare global {
  interface Window {
    api: {
      window: {
        minimize: () => Promise<void>
        maximize: () => Promise<void>
        close: () => Promise<void>;
        toggleFullscreen: () => Promise<void>;
        getState: () => Promise<any>;
      };
      anime: {
        getList: (params: any) => Promise<any>;
        getListWithProgress: (params: any) => Promise<any>;
        getDetail: (params: any) => Promise<any>;
        getEpisodes: (params: any) => Promise<any>;
        search: (params: any) => Promise<any>;
        searchWithProgress: (params: any) => Promise<any>;
        getBangumiInfo: (params: any) => Promise<any>;
        extractVideo: (params: any) => Promise<any>;
        getVideoProxyUrl: (params: any) => Promise<any>;
        getCacheStatus: () => Promise<any>;
        refreshCache: () => Promise<any>;
        parsePwEpisodes: (params: any) => Promise<any>;
      };
      favorite: {
        getList: () => Promise<any>;
        batchStatus: (params: any) => Promise<any>;
        add: (params: any) => Promise<any>;
        remove: (params: any) => Promise<any>;
        check: (params: any) => Promise<any>;
      };
      history: {
        getList: (params?: any) => Promise<any>;
        save: (params: any) => Promise<any>;
        getProgress: (params: any) => Promise<any>;
        clear: () => Promise<any>;
        delete: (params: any) => Promise<any>;
        getByAnime: (params: any) => Promise<any>;
        batchProgress: (params: any) => Promise<any>;
      };
      settings: {
        get: (params: any) => Promise<any>;
        set: (params: any) => Promise<any>;
        getAll: () => Promise<any>;
      };
      download: {
        getList: () => Promise<any>;
        add: (params: any) => Promise<any>;
        pause: (params: any) => Promise<any>;
        resume: (params: any) => Promise<any>;
        cancel: (params: any) => Promise<any>;
        onProgress: (callback: any) => void;
      };
      autoDownload: {
        getConfig: () => Promise<{ success: boolean; data?: AutoDownloadConfig; error?: any }>;
        updateConfig: (params: { config: AutoDownloadConfig }) => Promise<{ success: boolean; error?: any }>;
        getStatus: () => Promise<{ success: boolean; data?: AutoDownloadStatus; error?: any }>;
        getHistory: (params?: { limit?: number; status?: string }) => Promise<{ success: boolean; data?: DownloadRecord[]; error?: any }>;
        previewFilter: (params: { filters?: DownloadFilter }) => Promise<{ success: boolean; data?: any; error?: any }>;
        runCheck: () => Promise<{ success: boolean; data?: any; error?: any }>;
      };
      system: {
        showItemInFolder: (params: { path: string }) => Promise<void>;
        openExternal: (params: { url: string }) => Promise<void>;
      };
      update: {
        check: () => Promise<any>;
        download: () => Promise<any>;
        install: () => Promise<any>;
        onAvailable: (callback: any) => void;
        onProgress: (callback: any) => void;
        onDownloaded: (callback: any) => void;
      };
    };
  }
}

export {};
