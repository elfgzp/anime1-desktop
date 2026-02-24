var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
import { contextBridge, ipcRenderer } from "electron";
var require_index = __commonJS({
  "index.cjs"() {
    const validChannels = [
      // 窗口
      "window:minimize",
      "window:maximize",
      "window:close",
      "window:toggleFullscreen",
      "window:getState",
      // 番剧
      "anime:list",
      "anime:detail",
      "anime:episodes",
      "anime:search",
      "anime:bangumi",
      "anime:video",
      "anime:cache:status",
      "anime:cache:refresh",
      // 收藏
      "favorite:list",
      "favorite:add",
      "favorite:remove",
      "favorite:check",
      // 播放历史
      "history:list",
      "history:save",
      "history:progress",
      "history:clear",
      // 设置
      "settings:get",
      "settings:set",
      "settings:getAll",
      // 下载
      "download:list",
      "download:add",
      "download:pause",
      "download:resume",
      "download:cancel",
      // 系统
      "system:showItemInFolder",
      "system:openExternal",
      // 更新
      "update:check",
      "update:download",
      "update:install"
    ];
    const invoke = async (channel, ...args) => {
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args);
      }
      throw new Error(`Invalid channel: ${channel}`);
    };
    const on = (channel, callback) => {
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (_, ...args) => callback(...args));
      }
    };
    const api = {
      window: {
        minimize: () => invoke("window:minimize"),
        maximize: () => invoke("window:maximize"),
        close: () => invoke("window:close"),
        toggleFullscreen: () => invoke("window:toggleFullscreen"),
        getState: () => invoke("window:getState")
      },
      anime: {
        getList: (params) => invoke("anime:list", params),
        getDetail: (params) => invoke("anime:detail", params),
        getEpisodes: (params) => invoke("anime:episodes", params),
        search: (params) => invoke("anime:search", params),
        getBangumiInfo: (params) => invoke("anime:bangumi", params),
        extractVideo: (params) => invoke("anime:video", params),
        getCacheStatus: () => invoke("anime:cache:status"),
        refreshCache: () => invoke("anime:cache:refresh")
      },
      favorite: {
        getList: () => invoke("favorite:list"),
        add: (params) => invoke("favorite:add", params),
        remove: (params) => invoke("favorite:remove", params),
        check: (params) => invoke("favorite:check", params)
      },
      history: {
        getList: (params) => invoke("history:list", params),
        save: (params) => invoke("history:save", params),
        getProgress: (params) => invoke("history:progress", params),
        clear: () => invoke("history:clear")
      },
      settings: {
        get: (params) => invoke("settings:get", params),
        set: (params) => invoke("settings:set", params),
        getAll: () => invoke("settings:getAll")
      },
      download: {
        getList: () => invoke("download:list"),
        add: (params) => invoke("download:add", params),
        pause: (params) => invoke("download:pause", params),
        resume: (params) => invoke("download:resume", params),
        cancel: (params) => invoke("download:cancel", params),
        onProgress: (callback) => on("download:progress", callback)
      },
      system: {
        showItemInFolder: (params) => invoke("system:showItemInFolder", params),
        openExternal: (params) => invoke("system:openExternal", params)
      },
      update: {
        check: () => invoke("update:check"),
        download: () => invoke("update:download"),
        install: () => invoke("update:install"),
        onAvailable: (callback) => on("update:available", callback),
        onProgress: (callback) => on("update:progress", callback),
        onDownloaded: (callback) => on("update:downloaded", callback)
      }
    };
    console.log("[Preload] Starting to expose API...");
    try {
      contextBridge.exposeInMainWorld("api", api);
      console.log("[Preload] API exposed successfully");
    } catch (error) {
      console.error("[Preload] Failed to expose API:", error);
    }
  }
});
export default require_index();
//# sourceMappingURL=index.cjs.map
