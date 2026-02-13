<template>
  <div class="logs-container">
    <div class="page-header">
      <h1>日志查看</h1>
      <div class="header-actions">
        <el-button @click="refreshLogs" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="exportLogs" :loading="exporting">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button type="danger" @click="clearLogs" :loading="clearing">
          清空日志
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats?.totalLines || 0 }}</div>
          <div class="stat-label">总行数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" style="color: #67c23a">{{ stats?.byLevel?.INFO || 0 }}</div>
          <div class="stat-label">INFO</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" style="color: #e6a23c">{{ stats?.byLevel?.WARN || 0 }}</div>
          <div class="stat-label">WARN</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" style="color: #ff4949">{{ stats?.byLevel?.ERROR || 0 }}</div>
          <div class="stat-label">ERROR</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选器 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索日志内容"
          clearable
          style="width: 300px"
          @keyup.enter="refreshLogs"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="levelFilter" placeholder="日志级别" clearable style="width: 150px">
          <el-option label="DEBUG" value="DEBUG" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARN" value="WARN" />
          <el-option label="ERROR" value="ERROR" />
        </el-select>

        <el-select v-model="linesCount" placeholder="显示行数" style="width: 120px">
          <el-option label="50 行" :value="50" />
          <el-option label="100 行" :value="100" />
          <el-option label="200 行" :value="200" />
          <el-option label="500 行" :value="500" />
        </el-select>

        <el-button type="primary" @click="refreshLogs">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </div>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="logs-card" v-loading="loading">
      <el-table :data="logs" stripe style="width: 100%" height="600">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="内容" min-width="400">
          <template #default="{ row }">
            <div class="log-message">{{ row.message }}</div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="logs.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无日志" />
      </div>
    </el-card>

    <!-- 文件信息 -->
    <el-card class="file-info-card" v-if="fileInfo">
      <template #header>
        <span>文件信息</span>
      </template>
      <div class="file-info">
        <div class="info-item">
          <span class="label">路径:</span>
          <span class="value">{{ fileInfo.path }}</span>
        </div>
        <div class="info-item">
          <span class="label">大小:</span>
          <span class="value">{{ formatFileSize(fileInfo.size) }}</span>
        </div>
        <div class="info-item">
          <span class="label">修改时间:</span>
          <span class="value">{{ fileInfo.modified ? new Date(fileInfo.modified).toLocaleString() : '-' }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, Download, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logsAPI } from '../utils/api'

const loading = ref(false)
const clearing = ref(false)
const exporting = ref(false)

const logs = ref([])
const stats = ref(null)
const fileInfo = ref(null)

const searchKeyword = ref('')
const levelFilter = ref('')
const linesCount = ref(100)

// 获取日志级别对应的 tag 类型
const getLevelType = (level) => {
  switch (level) {
    case 'DEBUG':
      return 'info'
    case 'INFO':
      return 'success'
    case 'WARN':
      return 'warning'
    case 'ERROR':
      return 'danger'
    default:
      return 'info'
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 刷新日志
const refreshLogs = async () => {
  loading.value = true
  try {
    const [logsResponse, statsResponse, fileResponse] = await Promise.all([
      logsAPI.getLogs({
        lines: linesCount.value,
        level: levelFilter.value,
        search: searchKeyword.value,
      }),
      logsAPI.getLogStats(),
      logsAPI.getLogFileInfo(),
    ])

    if (logsResponse.success) {
      logs.value = logsResponse.logs || []
    }

    if (statsResponse.success) {
      stats.value = statsResponse.stats
    }

    if (fileResponse.success) {
      fileInfo.value = fileResponse.info
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

// 清空日志
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  clearing.value = true
  try {
    const response = await logsAPI.clearLogs()
    if (response.success) {
      ElMessage.success('日志已清空')
      await refreshLogs()
    } else {
      ElMessage.error(response.error || '清空失败')
    }
  } catch (error) {
    console.error('清空日志失败:', error)
    ElMessage.error('清空失败')
  } finally {
    clearing.value = false
  }
}

// 导出日志
const exportLogs = async () => {
  exporting.value = true
  try {
    // 使用 electron 的 dialog API 选择保存路径
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const defaultPath = `anime1-logs-${timestamp}.log`
    
    // 调用后端导出
    const response = await logsAPI.exportLogs(defaultPath)
    if (response.success) {
      ElMessage.success('日志已导出')
    } else {
      ElMessage.error(response.error || '导出失败')
    }
  } catch (error) {
    console.error('导出日志失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.logs-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.logs-card {
  margin-bottom: 20px;
}

.log-message {
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
}

.empty-state {
  padding: 40px 0;
}

.file-info-card {
  margin-bottom: 20px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
}

.info-item .label {
  width: 80px;
  color: var(--el-text-color-secondary);
}

.info-item .value {
  flex: 1;
  color: var(--el-text-color-primary);
  font-family: monospace;
  font-size: 13px;
}
</style>
