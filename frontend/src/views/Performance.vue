<template>
  <div class="performance-container">
    <div class="page-header">
      <h1>性能分析</h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="danger" @click="clearData" :loading="clearing">
          清空数据
        </el-button>
      </div>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats?.count || 0 }}</div>
          <div class="stat-label">总记录数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" :style="{ color: getColor(stats?.avg_duration) }">
            {{ (stats?.avg_duration || 0).toFixed(0) }}ms
          </div>
          <div class="stat-label">平均耗时</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" style="color: #67c23a">{{ stats?.good_count || 0 }}</div>
          <div class="stat-label">良好</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value" style="color: #ff4949">{{ stats?.poor_count || 0 }}</div>
          <div class="stat-label">需改进</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分位数图表 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>耗时分布 (P50/P90/P99)</span>
          </template>
          <div ref="percentileChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>评分分布</span>
          </template>
          <div ref="ratingChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近追踪列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>最近链路追踪</span>
          <div class="filter-controls">
            <el-input
              v-model="searchTraceId"
              placeholder="搜索 Trace ID"
              clearable
              style="width: 200px"
              @clear="fetchRecentTraces"
              @keyup.enter="fetchRecentTraces"
            />
            <el-input
              v-model="searchOperation"
              placeholder="搜索操作名称"
              clearable
              style="width: 180px"
              @clear="fetchRecentTraces"
              @keyup.enter="fetchRecentTraces"
            />
            <el-select v-model="selectedPage" placeholder="全部页面" clearable style="width: 150px" @change="fetchRecentTraces">
              <el-option label="首页" value="/" />
              <el-option label="详情页" value="/anime/" />
            </el-select>
            <el-select v-model="sortBy" placeholder="排序字段" style="width: 120px" @change="fetchRecentTraces">
              <el-option label="时间" value="created_at" />
              <el-option label="耗时" value="duration" />
            </el-select>
            <el-select v-model="sortOrder" placeholder="排序方向" style="width: 120px" @change="fetchRecentTraces">
              <el-option label="降序" value="desc" />
              <el-option label="升序" value="asc" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="recentTraces" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="160" sortable :sort-orders="['descending', 'ascending']">
          <template #default="{ row }">
            <span>{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Trace ID" width="120">
          <template #default="{ row }">
            <el-tooltip :content="row.trace_id" placement="top">
              <div class="trace-id-cell">
                <code>{{ row.trace_id.substring(0, 8) }}...</code>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="copyToClipboard(row.trace_id)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.operations?.join(' → ') || row.root_name" placement="top">
              <div class="operation-cell">
                <span>{{ row.root_name }}</span>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="copyToClipboard(row.root_name)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="page" label="页面" width="100" />
        <el-table-column prop="duration" label="耗时" width="100" sortable :sort-orders="['descending', 'ascending']">
          <template #default="{ row }">
            <span :style="{ color: getColor(row.duration) }">
              {{ row.duration.toFixed(0) }}ms
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="span_count" label="Span数" width="70" />
        <el-table-column prop="rating" label="评分" width="90">
          <template #default="{ row }">
            <el-tag :type="getRatingType(row.rating)" size="small">
              {{ row.rating }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewTrace(row.trace_id)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalTraces"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRecentTraces"
          @current-change="handlePageChange"
        />
      </div>
      <el-backtop :right="20" :bottom="80" />
    </el-card>

    <!-- 链路详情弹窗 - 时序图 -->
    <el-dialog v-model="showTraceDialog" title="链路追踪详情 (时序图)" width="900px" @closed="handleDialogClose">
      <div v-if="currentTrace" class="trace-detail">
        <div class="trace-info">
          <span class="trace-id">TraceId: {{ currentTrace.trace_id }}</span>
          <span class="trace-time">时间: {{ formatTime(currentTrace.created_at) }}</span>
          <span class="total-duration">总耗时: {{ currentTrace.total_duration.toFixed(0) }}ms</span>
          <span class="span-count">Span数: {{ currentTrace.span_count }}</span>
        </div>

        <!-- 时序图 (Gantt) -->
        <el-card class="timeline-card">
          <template #header>
            <span>时序图 (类似 OpenTelemetry Trace)</span>
          </template>
          <div ref="timelineChart" class="timeline-container"></div>
        </el-card>

        <!-- 树形详情 -->
        <el-card class="trace-tree-card">
          <template #header>
            <span>调用链详情</span>
          </template>
          <div class="trace-tree">
            <div v-for="span in currentTrace.root_spans" :key="span.span_id" class="trace-span">
              <TraceSpanItem :span="span" :totalDuration="currentTrace.total_duration" />
            </div>
          </div>
        </el-card>
      </div>
    </el-dialog>

    <!-- 各功能耗时统计 -->
    <el-card class="list-card">
      <template #header>
        <span>各功能耗时统计</span>
      </template>
      <div ref="barChart" class="chart-container-large"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { Refresh, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import TraceSpanItem from '../components/TraceSpanItem.vue'
import { performanceAPI } from '../utils/api'

const loading = ref(false)
const clearing = ref(false)
const stats = ref(null)
const recentTraces = ref([])
const selectedPage = ref('')
const searchOperation = ref('')
const searchTraceId = ref('')
const sortBy = ref('duration')
const sortOrder = ref('desc')
const showTraceDialog = ref(false)
const currentTrace = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const totalTraces = ref(0)

const percentileChart = ref(null)
const ratingChart = ref(null)
const barChart = ref(null)
const timelineChart = ref(null)

let percentileChartInstance = null
let ratingChartInstance = null
let barChartInstance = null
let timelineChartInstance = null

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await performanceAPI.getStats()
    if (response.data.success) {
      stats.value = response.data.stats
      updateCharts()
    }
  } catch (e) {
    console.error('获取统计失败:', e)
  }
}

// 获取最近追踪
const fetchRecentTraces = async () => {
  loading.value = true
  try {
    const params = {
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    if (selectedPage.value) {
      params.page = selectedPage.value
    }
    if (searchOperation.value) {
      params.operation = searchOperation.value
    }
    if (searchTraceId.value) {
      params.trace_id = searchTraceId.value
    }
    const response = await performanceAPI.getRecentTraces(params)
    if (response.data.success) {
      recentTraces.value = response.data.traces
      totalTraces.value = response.data.total || 0
    }
  } catch (e) {
    console.error('获取追踪列表失败:', e)
  } finally {
    loading.value = false
  }
}

// 处理页码变化
const handlePageChange = (page) => {
  currentPage.value = page
  fetchRecentTraces()
}

// 查看链路详情
const viewTrace = async (traceId) => {
  try {
    const response = await performanceAPI.getTrace(traceId)
    if (response.data.success) {
      currentTrace.value = response.data
      showTraceDialog.value = true
      // 等待 DOM 更新后绘制时序图
      nextTick(() => {
        initTimelineChart()
      })
    }
  } catch (e) {
    console.error('获取链路详情失败:', e)
  }
}

// 清理数据
const clearData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有链路追踪数据吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return // 用户取消
  }

  clearing.value = true
  try {
    await performanceAPI.clearAllData()
    await refreshData()
    ElMessage.success('已清空所有链路追踪数据')
  } catch (e) {
    console.error('清理失败:', e)
    ElMessage.error('清理失败')
  } finally {
    clearing.value = false
  }
}

// 刷新所有数据
const refreshData = async () => {
  await Promise.all([fetchStats(), fetchRecentTraces()])
}

// 更新图表
const updateCharts = () => {
  if (!stats.value) return

  // 更新分位数图表
  if (percentileChartInstance) {
    percentileChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['P50', 'P90', 'P99'] },
      yAxis: { type: 'value', name: 'ms' },
      series: [{
        data: [
          stats.value.p50.toFixed(0),
          stats.value.p90.toFixed(0),
          stats.value.p99.toFixed(0)
        ],
        type: 'bar',
        itemStyle: {
          color: (params) => {
            const colors = ['#67c23a', '#e6a23c', '#ff4949']
            return colors[params.dataIndex]
          }
        }
      }]
    })
  }

  // 更新评分分布图表
  if (ratingChartInstance) {
    ratingChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: stats.value.good_count, name: '良好', itemStyle: { color: '#67c23a' } },
          { value: stats.value.needs_improvement_count, name: '需改进', itemStyle: { color: '#e6a23c' } },
          { value: stats.value.poor_count, name: '慢', itemStyle: { color: '#ff4949' } }
        ]
      }]
    })
  }

  // 更新功能耗时图表
  if (barChartInstance && stats.value.by_name) {
    const names = Object.keys(stats.value.by_name)
    const avgs = names.map(n => stats.value.by_name[n].avg.toFixed(0))
    const p99s = names.map(n => stats.value.by_name[n].p99.toFixed(0))

    barChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['平均', 'P99'] },
      xAxis: { type: 'category', data: names },
      yAxis: { type: 'value', name: 'ms' },
      series: [
        {
          name: '平均',
          type: 'bar',
          data: avgs,
          itemStyle: { color: '#409eff' }
        },
        {
          name: 'P99',
          type: 'bar',
          data: p99s,
          itemStyle: { color: '#f56c6c' }
        }
      ]
    })
  }
}

// 获取颜色
const getColor = (value) => {
  if (value > 2500) return '#ff4949'
  if (value > 1000) return '#e6a23c'
  return '#67c23a'
}

// 格式化时间戳
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now - date

  // 小于1分钟显示刚刚
  if (diff < 60000) return '刚刚'
  // 小于1小时显示n分钟前
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 小于24小时显示 n 小时前
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  // 显示完整时间
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 获取评分类型
const getRatingType = (rating) => {
  switch (rating) {
    case 'good': return 'success'
    case 'needs-improvement': return 'warning'
    case 'poor': return 'danger'
    default: return 'info'
  }
}

// 复制到剪贴板
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

// 初始化图表
const initCharts = () => {
  if (percentileChart.value) {
    percentileChartInstance = echarts.init(percentileChart.value)
  }
  if (ratingChart.value) {
    ratingChartInstance = echarts.init(ratingChart.value)
  }
  if (barChart.value) {
    barChartInstance = echarts.init(barChart.value)
  }
}

// 初始化时序图 (Gantt)
const initTimelineChart = () => {
  if (!timelineChart.value || !currentTrace.value) return

  // 销毁旧实例
  if (timelineChartInstance) {
    timelineChartInstance.dispose()
  }

  timelineChartInstance = echarts.init(timelineChart.value)

  // 收集所有 span 用于绘制 Gantt
  const allSpans = []
  const collectSpans = (spans, depth = 0) => {
    for (const span of spans) {
      allSpans.push({
        name: span.name,
        spanId: span.span_id,
        duration: span.duration,
        startTime: span.start_time,
        endTime: span.end_time,
        depth: depth,
        rating: span.rating,
        parentSpanId: span.parent_span_id
      })
      if (span.children?.length) {
        collectSpans(span.children, depth + 1)
      }
    }
  }
  collectSpans(currentTrace.value.root_spans)

  // 转换为 Gantt 数据格式
  // 排序：按 start_time 从大到小（上面显示最新的）
  allSpans.sort((a, b) => b.startTime - a.startTime)

  const categories = allSpans.map(s => s.name.substring(0, 30))
  const startTimes = allSpans.map(s => s.startTime * 1000)
  const durations = allSpans.map(s => s.duration)
  const colors = allSpans.map(s => {
    switch (s.rating) {
      case 'good': return '#67c23a'
      case 'needs-improvement': return '#e6a23c'
      case 'poor': return '#ff4949'
      default: return '#409eff'
    }
  })

  // 计算时间范围
  const minTime = Math.min(...startTimes)
  const maxTime = Math.max(...startTimes.map((t, i) => t + durations[i]))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const idx = params[0].dataIndex
        const span = allSpans[idx]
        return `
          <div style="font-weight: bold; margin-bottom: 4px;">${span.name}</div>
          <div>Span ID: ${span.spanId.substring(0, 12)}...</div>
          <div>耗时: ${span.duration.toFixed(2)}ms</div>
          <div>评分: ${span.rating}</div>
        `
      }
    },
    grid: {
      left: '180px',
      right: '20px',
      top: '20px',
      bottom: '40px'
    },
    xAxis: {
      type: 'value',
      min: minTime,
      max: maxTime,
      axisLabel: {
        formatter: (value) => `${(value - minTime).toFixed(0)}ms`
      },
      name: '相对时间',
      nameLocation: 'middle',
      nameGap: 25
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        width: 170,
        overflow: 'truncate'
      }
    },
    series: [{
      type: 'bar',
      stack: 'timeline',
      label: {
        show: true,
        position: 'inside',
        formatter: (params) => `${params.value.toFixed(0)}ms`
      },
      itemStyle: {
        color: (params) => colors[params.dataIndex],
        borderRadius: 4
      },
      data: allSpans.map((s, idx) => ({
        value: [s.startTime - minTime, s.duration],
        itemStyle: { color: colors[idx] }
      }))
    }]
  }

  timelineChartInstance.setOption(option)
}

// 关闭弹窗时销毁时序图实例
const handleDialogClose = () => {
  if (timelineChartInstance) {
    timelineChartInstance.dispose()
    timelineChartInstance = null
  }
  currentTrace.value = null
}

// 窗口大小变化时更新图表
const handleResize = () => {
  percentileChartInstance?.resize()
  ratingChartInstance?.resize()
  barChartInstance?.resize()
  timelineChartInstance?.resize()
}

onMounted(() => {
  nextTick(() => {
    initCharts()
    refreshData()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  percentileChartInstance?.dispose()
  ratingChartInstance?.dispose()
  barChartInstance?.dispose()
  timelineChartInstance?.dispose()
})
</script>

<style scoped>
.performance-container {
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

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 250px;
}

.chart-container-large {
  height: 300px;
}

.timeline-container {
  height: 300px;
}

.timeline-card {
  margin-bottom: 20px;
}

.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-controls {
  display: flex;
  gap: 10px;
}

.operation-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-id-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.trace-id-cell code {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.trace-detail {
  padding: 10px 0;
}

.trace-info {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 10px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.trace-id {
  font-family: monospace;
  color: var(--el-text-color-secondary);
}

.trace-time {
  color: var(--el-text-color-secondary);
}

.total-duration {
  font-weight: bold;
  color: var(--el-color-primary);
}

.span-count {
  color: var(--el-text-color-secondary);
}

.trace-tree {
  max-height: 400px;
  overflow-y: auto;
}

.trace-span {
  margin-bottom: 8px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
