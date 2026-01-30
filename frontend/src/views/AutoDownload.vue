<template>
  <div class="auto-download-container">
    <el-card shadow="never" class="page-header-card">
      <h1 class="page-title">自动下载</h1>
    </el-card>

    <!-- 开关和状态 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">服务状态</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>自动下载服务</span>
          <div class="settings-desc">
            {{ config.enabled ? '运行中 - 每 ' + config.check_interval_hours + ' 小时检查一次' : '已停止' }}
          </div>
        </div>
        <div class="settings-control">
          <el-switch
            v-model="config.enabled"
            @change="handleEnabledChange"
            :loading="saving"
          />
        </div>
      </div>
      <div class="settings-item" v-if="status.status_counts">
        <div class="settings-label">
          <span>下载统计</span>
          <div class="settings-desc">
            已完成: {{ status.status_counts.completed }} |
            下载中: {{ status.status_counts.downloading }} |
            失败: {{ status.status_counts.failed }}
          </div>
        </div>
        <div class="settings-control">
          <el-button @click="loadStatus" :loading="loading">刷新</el-button>
        </div>
      </div>
    </el-card>

    <!-- 基本设置 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">基本设置</div>
      </template>

      <div class="settings-item">
        <div class="settings-label">
          <span>下载路径</span>
          <div class="settings-desc">{{ config.download_path || '使用默认下载目录' }}</div>
        </div>
        <div class="settings-control">
          <el-input
            v-model="config.download_path"
            placeholder="留空使用默认目录"
            style="width: 300px"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>检查间隔</span>
          <div class="settings-desc">自动检查新番剧的时间间隔</div>
        </div>
        <div class="settings-control">
          <el-slider
            v-model="config.check_interval_hours"
            :min="1"
            :max="168"
            :step="1"
            style="width: 200px"
            @change="handleSaveConfig"
          />
          <span class="slider-value">{{ config.check_interval_hours }} 小时</span>
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>最大并发下载</span>
          <div class="settings-desc">同时下载的剧集数量</div>
        </div>
        <div class="settings-control">
          <el-slider
            v-model="config.max_concurrent_downloads"
            :min="1"
            :max="5"
            :step="1"
            style="width: 200px"
            @change="handleSaveConfig"
          />
          <span class="slider-value">{{ config.max_concurrent_downloads }} 个</span>
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>自动下载新番</span>
          <div class="settings-desc">自动下载符合筛选条件的新番剧</div>
        </div>
        <div class="settings-control">
          <el-switch
            v-model="config.auto_download_new"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>自动下载追番</span>
          <div class="settings-desc">自动下载追番列表中的番剧更新</div>
        </div>
        <div class="settings-control">
          <el-switch
            v-model="config.auto_download_favorites"
            @change="handleSaveConfig"
          />
        </div>
      </div>
    </el-card>

    <!-- 筛选条件 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">筛选条件</div>
      </template>

      <div class="settings-item">
        <div class="settings-label">
          <span>年份范围</span>
          <div class="settings-desc">下载指定年份范围内的番剧</div>
        </div>
        <div class="settings-control">
          <el-input-number
            v-model="config.filters.min_year"
            :min="2000"
            :max="2100"
            placeholder="最小年份"
            style="width: 120px"
            @change="handleSaveConfig"
          />
          <span style="margin: 0 10px">-</span>
          <el-input-number
            v-model="config.filters.max_year"
            :min="2000"
            :max="2100"
            placeholder="最大年份"
            style="width: 120px"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>指定年份</span>
          <div class="settings-desc">只下载特定年份的番剧（可选）</div>
        </div>
        <div class="settings-control">
          <el-select
            v-model="config.filters.specific_years"
            multiple
            filterable
            allow-create
            placeholder="选择或输入年份"
            style="width: 300px"
            @change="handleSaveConfig"
          >
            <el-option
              v-for="year in availableYears"
              :key="year"
              :label="year + '年'"
              :value="year"
            />
          </el-select>
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>指定季度</span>
          <div class="settings-desc">只下载特定季度的番剧</div>
        </div>
        <div class="settings-control">
          <el-checkbox-group v-model="config.filters.seasons" @change="handleSaveConfig">
            <el-checkbox label="冬季">冬季 (1-3月)</el-checkbox>
            <el-checkbox label="春季">春季 (4-6月)</el-checkbox>
            <el-checkbox label="夏季">夏季 (7-9月)</el-checkbox>
            <el-checkbox label="秋季">秋季 (10-12月)</el-checkbox>
          </el-checkbox-group>
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>最少集数</span>
          <div class="settings-desc">只下载集数大于等于此值的番剧</div>
        </div>
        <div class="settings-control">
          <el-input-number
            v-model="config.filters.min_episodes"
            :min="0"
            :max="100"
            placeholder="不限"
            style="width: 120px"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>标题包含</span>
          <div class="settings-desc">正则表达式，匹配标题中包含的关键词</div>
        </div>
        <div class="settings-control">
          <el-select
            v-model="config.filters.include_patterns"
            multiple
            filterable
            allow-create
            placeholder="输入正则表达式"
            style="width: 300px"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>标题排除</span>
          <div class="settings-desc">正则表达式，排除标题中包含的关键词</div>
        </div>
        <div class="settings-control">
          <el-select
            v-model="config.filters.exclude_patterns"
            multiple
            filterable
            allow-create
            placeholder="输入正则表达式"
            style="width: 300px"
            @change="handleSaveConfig"
          />
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>筛选预览</span>
          <div class="settings-desc">查看当前筛选条件会匹配哪些番剧</div>
        </div>
        <div class="settings-control">
          <el-button type="primary" @click="handlePreviewFilter" :loading="previewLoading">
            {{ previewLoading ? '加载中...' : '预览匹配结果' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 手动下载 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">手动下载</div>
      </template>

      <div class="settings-item">
        <div class="settings-label">
          <span>下载单集</span>
          <div class="settings-desc">输入剧集 URL 或 ID 进行下载</div>
        </div>
        <div class="settings-control">
          <el-input
            v-model="manualDownloadUrl"
            placeholder="https://anime1.me/12345 或 12345"
            style="width: 250px"
          />
          <el-button
            type="primary"
            @click="handleManualDownload"
            :loading="manualDownloading"
            :disabled="!manualDownloadUrl"
          >
            {{ manualDownloading ? '下载中...' : '下载' }}
          </el-button>
        </div>
      </div>

      <div class="settings-item">
        <div class="settings-label">
          <span>测试下载</span>
          <div class="settings-desc">测试视频解析是否正常</div>
        </div>
        <div class="settings-control">
          <el-input
            v-model="testUrl"
            placeholder="https://anime1.me/12345"
            style="width: 250px"
          />
          <el-button
            @click="handleTestDownload"
            :loading="testing"
            :disabled="!testUrl"
          >
            {{ testing ? '测试中...' : '测试' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 下载历史 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">下载历史</div>
      </template>

      <el-table :data="history" style="width: 100%" v-loading="historyLoading">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="anime_title" label="番剧" min-width="200" />
        <el-table-column prop="episode_num" label="集数" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_path" label="文件路径" min-width="200">
          <template #default="{ row }">
            <span v-if="row.file_path" class="file-path">{{ row.file_path }}</span>
            <span v-else-if="row.error_message" class="error-message">{{ row.error_message }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-if="history.length > 0">
        <el-button @click="loadHistory" :loading="historyLoading">刷新</el-button>
      </div>
    </el-card>

    <!-- 筛选预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="筛选预览"
      width="800px"
    >
      <div v-if="previewResult">
        <p>共找到 {{ previewResult.matched_count }} 部匹配的番剧</p>
        <el-table :data="previewResult.matched_anime" height="400">
          <el-table-column prop="title" label="番剧名称" min-width="250" />
          <el-table-column prop="year" label="年份" width="80" />
          <el-table-column prop="season" label="季度" width="80" />
          <el-table-column prop="episode" label="集数" width="80" />
        </el-table>
      </div>
    </el-dialog>

    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { autoDownloadAPI } from '../utils/api'
import { ElMessage } from 'element-plus'

// 状态
const loading = ref(false)
const saving = ref(false)
const previewLoading = ref(false)
const manualDownloading = ref(false)
const testing = ref(false)
const historyLoading = ref(false)
const previewDialogVisible = ref(false)

// 表单数据
const manualDownloadUrl = ref('')
const testUrl = ref('')

// 配置
const config = ref({
  enabled: false,
  download_path: '',
  check_interval_hours: 24,
  max_concurrent_downloads: 2,
  auto_download_new: true,
  auto_download_favorites: false,
  filters: {
    min_year: null,
    max_year: null,
    specific_years: [],
    seasons: [],
    min_episodes: null,
    include_patterns: [],
    exclude_patterns: []
  }
})

// 状态
const status = ref({
  enabled: false,
  running: false,
  download_path: '',
  check_interval_hours: 24,
  filters: {},
  recent_downloads: [],
  status_counts: {
    pending: 0,
    downloading: 0,
    completed: 0,
    failed: 0,
    skipped: 0
  }
})

// 历史记录
const history = ref([])

// 预览结果
const previewResult = ref(null)

// 可用年份选项
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= 2020; i--) {
    years.push(i)
  }
  return years
})

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const response = await autoDownloadAPI.getConfig()
    if (response.data?.data) {
      const data = response.data.data
      config.value = {
        ...config.value,
        ...data,
        filters: {
          ...config.value.filters,
          ...(data.filters || {})
        }
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 加载状态
const loadStatus = async () => {
  try {
    const response = await autoDownloadAPI.getStatus()
    if (response.data?.data) {
      status.value = response.data.data
    }
  } catch (error) {
    console.error('加载状态失败:', error)
  }
}

// 加载历史
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await autoDownloadAPI.getHistory({ limit: 50 })
    if (response.data?.data?.history) {
      history.value = response.data.data.history
    }
  } catch (error) {
    console.error('加载历史失败:', error)
    ElMessage.error('加载历史失败')
  } finally {
    historyLoading.value = false
  }
}

// 保存配置
const handleSaveConfig = async () => {
  saving.value = true
  try {
    await autoDownloadAPI.updateConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 启用/禁用切换
const handleEnabledChange = async (value) => {
  await handleSaveConfig()
  if (value) {
    ElMessage.success('自动下载已启用')
  } else {
    ElMessage.info('自动下载已禁用')
  }
}

// 预览筛选
const handlePreviewFilter = async () => {
  previewLoading.value = true
  try {
    const response = await autoDownloadAPI.previewFilter(config.value.filters)
    if (response.data?.data) {
      previewResult.value = response.data.data
      previewDialogVisible.value = true
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

// 手动下载
const handleManualDownload = async () => {
  if (!manualDownloadUrl.value) return

  manualDownloading.value = true
  try {
    // 解析 URL
    let url = manualDownloadUrl.value.trim()
    if (!url.startsWith('http')) {
      url = `https://anime1.me/${url}`
    }

    // 提取 episode ID
    const episodeId = url.split('/').pop().split('?')[0]

    await autoDownloadAPI.startDownload({
      anime_id: episodeId,
      episode_id: episodeId,
      episode_num: '',
      title: '手动下载',
      url: url
    })

    ElMessage.success('下载任务已创建')
    manualDownloadUrl.value = ''
    loadHistory()
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  } finally {
    manualDownloading.value = false
  }
}

// 测试下载
const handleTestDownload = async () => {
  if (!testUrl.value) return

  testing.value = true
  try {
    let url = testUrl.value.trim()
    if (!url.startsWith('http')) {
      url = `https://anime1.me/${url}`
    }

    const response = await autoDownloadAPI.testDownload(url)
    if (response.data?.data?.success) {
      ElMessage.success('测试成功，视频可以正常下载')
    } else {
      ElMessage.error('测试失败，无法获取视频')
    }
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败')
  } finally {
    testing.value = false
  }
}

// 格式化时间
const formatTime = (isoTime) => {
  if (!isoTime) return '-'
  const date = new Date(isoTime)
  return date.toLocaleString('zh-CN')
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    downloading: 'warning',
    completed: 'success',
    failed: 'danger',
    skipped: ''
  }
  return types[status] || ''
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待下载',
    downloading: '下载中',
    completed: '已完成',
    failed: '失败',
    skipped: '已跳过'
  }
  return texts[status] || status
}

onMounted(() => {
  loadConfig()
  loadStatus()
  loadHistory()
})
</script>

<style scoped>
.auto-download-container {
  max-width: 900px;
  margin: 0 auto;
}

.page-header-card {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.settings-section {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--el-border-color);
}

.settings-item:last-child {
  border-bottom: none;
}

.settings-label {
  color: var(--el-text-color-primary);
  font-size: 0.95rem;
}

.settings-desc {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.settings-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.slider-value {
  min-width: 60px;
  text-align: right;
  color: var(--el-text-color-secondary);
}

.file-path {
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}

.error-message {
  color: var(--el-color-danger);
  font-size: 0.85rem;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}

/* 确保在暗色和亮色主题下都有正确的背景色 */
:deep(.el-card) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

:deep(.el-card__header) {
  background-color: var(--el-bg-color);
  border-bottom-color: var(--el-border-color);
}

:deep(.el-card__body) {
  background-color: var(--el-bg-color);
}
</style>
