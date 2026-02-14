<template>
  <div v-if="isMockMode" class="mock-updater-panel">
    <div class="panel-header" @click="isExpanded = !isExpanded">
      <span class="mock-badge">🧪 MOCK</span>
      <span class="title">更新测试控制面板</span>
      <span class="toggle-icon">{{ isExpanded ? '▼' : '▶' }}</span>
    </div>
    
    <div v-show="isExpanded" class="panel-content">
      <!-- 场景选择 -->
      <div class="control-group">
        <label>测试场景:</label>
        <select v-model="currentScenario" @change="changeScenario">
          <option 
            v-for="s in scenarios" 
            :key="s.id" 
            :value="s.id"
          >
            {{ s.name }}
          </option>
        </select>
        <p class="scenario-desc">{{ currentScenarioDesc }}</p>
      </div>
      
      <!-- 状态显示 -->
      <div class="control-group">
        <label>当前状态:</label>
        <div class="status-box">
          <div class="status-item" :class="{ active: status.checking }">
            🔍 检查中
          </div>
          <div class="status-item" :class="{ active: status.available }">
            📦 有更新
          </div>
          <div class="status-item" :class="{ active: status.downloading }">
            ⬇️ 下载中
          </div>
          <div class="status-item" :class="{ active: status.downloaded }">
            ✅ 已下载
          </div>
          <div v-if="status.error" class="status-item error">
            ❌ 错误: {{ status.error }}
          </div>
        </div>
      </div>
      
      <!-- 进度条 -->
      <div v-if="status.downloading || status.downloaded" class="control-group">
        <label>下载进度:</label>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: status.progress?.percent + '%' }">
            {{ status.progress?.percent }}%
          </div>
        </div>
        <div class="progress-info">
          <span>{{ formatBytes(status.progress?.transferred || 0) }} / {{ formatBytes(status.progress?.total || 0) }}</span>
          <span v-if="status.progress?.bytesPerSecond">({{ formatBytes(status.progress.bytesPerSecond) }}/s)</span>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="control-group actions">
        <button @click="checkUpdate" :disabled="status.checking || status.downloading">
          {{ status.checking ? '检查中...' : '检查更新' }}
        </button>
        <button @click="downloadUpdate" :disabled="!status.available || status.downloading || status.downloaded">
          {{ status.downloading ? '下载中...' : '下载更新' }}
        </button>
        <button @click="installUpdate" :disabled="!status.downloaded">
          安装更新
        </button>
        <button @click="resetState" class="secondary">
          重置状态
        </button>
      </div>
      
      <!-- 事件日志 -->
      <div class="control-group">
        <label>
          事件日志:
          <button @click="clearLogs" class="small">清空</button>
        </label>
        <div class="log-box">
          <div 
            v-for="(log, index) in logs" 
            :key="index"
            class="log-item"
            :class="log.type"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-event">[{{ log.event }}]</span>
            <span class="log-data" v-if="log.data">{{ JSON.stringify(log.data) }}</span>
          </div>
          <div v-if="logs.length === 0" class="log-empty">暂无事件</div>
        </div>
      </div>
      
      <!-- 配置信息 -->
      <div class="control-group">
        <label>Mock 配置:</label>
        <pre class="config-box">{{ JSON.stringify(config, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const isMockMode = ref(false);
const isExpanded = ref(true);
const currentScenario = ref('has-update');
const scenarios = ref([]);
const status = ref({});
const config = ref({});
const logs = ref([]);

let statusInterval = null;

// 计算当前场景描述
const currentScenarioDesc = computed(() => {
  const s = scenarios.value.find(s => s.id === currentScenario.value);
  return s?.description || '';
});

// 格式化字节
function formatBytes(bytes) {
  if (bytes === 0 || !bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 添加日志
function addLog(event, data = null, type = 'info') {
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
  logs.value.unshift({ time, event, data, type });
  
  // 限制日志数量
  if (logs.value.length > 50) {
    logs.value = logs.value.slice(0, 50);
  }
}

// 清空日志
function clearLogs() {
  logs.value = [];
}

// 加载配置
async function loadConfig() {
  try {
    const result = await window.electron.ipcRenderer.invoke('mock-updater:get-config');
    if (result.success) {
      config.value = result.data;
    }
  } catch (err) {
    console.error('Failed to load mock config:', err);
  }
}

// 加载场景列表
async function loadScenarios() {
  try {
    const result = await window.electron.ipcRenderer.invoke('mock-updater:get-scenarios');
    if (result.success) {
      scenarios.value = result.data;
    }
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

// 刷新状态
async function refreshStatus() {
  try {
    const result = await window.electron.ipcRenderer.invoke('updater:status');
    if (result.success) {
      status.value = result.data;
    }
  } catch (err) {
    console.error('Failed to get status:', err);
  }
}

// 切换场景
async function changeScenario() {
  try {
    const result = await window.electron.ipcRenderer.invoke('mock-updater:set-scenario', currentScenario.value);
    if (result.success) {
      addLog('set-scenario', { scenario: currentScenario.value }, 'success');
      await refreshStatus();
    }
  } catch (err) {
    addLog('set-scenario-error', { error: err.message }, 'error');
  }
}

// 检查更新
async function checkUpdate() {
  try {
    addLog('check-started');
    const result = await window.electron.ipcRenderer.invoke('updater:check');
    addLog('check-completed', result.data, result.success ? 'success' : 'error');
    await refreshStatus();
  } catch (err) {
    addLog('check-error', { error: err.message }, 'error');
  }
}

// 下载更新
async function downloadUpdate() {
  try {
    addLog('download-started');
    const result = await window.electron.ipcRenderer.invoke('updater:download');
    addLog('download-completed', result, result.success ? 'success' : 'error');
  } catch (err) {
    addLog('download-error', { error: err.message }, 'error');
  }
}

// 安装更新
async function installUpdate() {
  try {
    addLog('install-started');
    const result = await window.electron.ipcRenderer.invoke('updater:install');
    addLog('install-completed', result, result.success ? 'success' : 'error');
  } catch (err) {
    addLog('install-error', { error: err.message }, 'error');
  }
}

// 重置状态
async function resetState() {
  try {
    const result = await window.electron.ipcRenderer.invoke('mock-updater:reset');
    if (result.success) {
      addLog('reset', result.state, 'success');
      await refreshStatus();
    }
  } catch (err) {
    addLog('reset-error', { error: err.message }, 'error');
  }
}

// 设置事件监听
function setupEventListeners() {
  const events = ['checking', 'available', 'not-available', 'progress', 'downloaded', 'error'];
  
  events.forEach(event => {
    window.electron.ipcRenderer.on(`updater:${event}`, (data) => {
      addLog(event, data, event === 'error' ? 'error' : 'info');
      refreshStatus();
    });
  });
}

onMounted(async () => {
  // 检测是否 Mock 模式
  try {
    const result = await window.electron.ipcRenderer.invoke('mock-updater:get-config');
    isMockMode.value = result.success && result.data?.isMock;
    
    if (isMockMode.value) {
      config.value = result.data;
      currentScenario.value = result.data.scenario;
      
      await loadScenarios();
      await refreshStatus();
      setupEventListeners();
      
      // 定期刷新状态
      statusInterval = setInterval(refreshStatus, 1000);
      
      addLog('panel-mounted', { scenario: currentScenario.value }, 'success');
    }
  } catch (err) {
    console.log('Mock updater not available');
  }
});

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval);
  }
});
</script>

<style scoped>
.mock-updater-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 380px;
  background: #1e1e1e;
  border: 2px solid #ff6b6b;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 13px;
  color: #e0e0e0;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  color: white;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
  user-select: none;
}

.mock-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  margin-right: 10px;
}

.title {
  flex: 1;
  font-weight: 600;
}

.toggle-icon {
  font-size: 12px;
}

.panel-content {
  padding: 15px;
  max-height: 500px;
  overflow-y: auto;
}

.control-group {
  margin-bottom: 15px;
}

.control-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #aaa;
}

.control-group select,
.control-group button {
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #2d2d2d;
  color: #e0e0e0;
  font-size: 13px;
  cursor: pointer;
}

.control-group select {
  width: 100%;
}

.control-group button {
  margin-right: 8px;
  margin-bottom: 5px;
  transition: all 0.2s;
}

.control-group button:hover:not(:disabled) {
  background: #3d3d3d;
  border-color: #666;
}

.control-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-group button.secondary {
  background: #444;
}

.control-group button.small {
  padding: 2px 8px;
  font-size: 11px;
  float: right;
}

.scenario-desc {
  margin: 5px 0 0;
  font-size: 12px;
  color: #888;
}

.status-box {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px;
}

.status-item {
  padding: 6px 10px;
  background: #2d2d2d;
  border-radius: 4px;
  text-align: center;
  font-size: 12px;
  color: #888;
  transition: all 0.3s;
}

.status-item.active {
  background: #4caf50;
  color: white;
  font-weight: 500;
}

.status-item.error {
  background: #f44336;
  color: white;
  grid-column: span 2;
}

.progress-bar {
  height: 24px;
  background: #2d2d2d;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
  color: white;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #888;
}

.actions button {
  font-size: 12px;
}

.log-box {
  max-height: 150px;
  overflow-y: auto;
  background: #151515;
  border-radius: 4px;
  padding: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
}

.log-item {
  padding: 3px 0;
  border-bottom: 1px solid #2d2d2d;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #666;
  margin-right: 8px;
}

.log-event {
  color: #64b5f6;
  font-weight: 500;
}

.log-item.success .log-event {
  color: #81c784;
}

.log-item.error .log-event {
  color: #e57373;
}

.log-data {
  color: #aaa;
  margin-left: 8px;
}

.log-empty {
  color: #555;
  text-align: center;
  padding: 20px;
}

.config-box {
  background: #151515;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  max-height: 100px;
  overflow: auto;
}

/* 滚动条样式 */
.panel-content::-webkit-scrollbar,
.log-box::-webkit-scrollbar,
.config-box::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.panel-content::-webkit-scrollbar-thumb,
.log-box::-webkit-scrollbar-thumb,
.config-box::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-track,
.log-box::-webkit-scrollbar-track,
.config-box::-webkit-scrollbar-track {
  background: transparent;
}
</style>
