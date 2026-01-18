<template>
  <div class="span-item">
    <div class="span-header" :style="{ marginLeft: depth * 20 + 'px' }">
      <span class="expand-icon" @click="expanded = !expanded">
        <el-icon v-if="span.children?.length">
          <component :is="expanded ? 'ArrowDown' : 'ArrowRight'" />
        </el-icon>
        <el-icon v-else><Document /></el-icon>
      </span>
      <span class="span-name">{{ displayName }}</span>
      <span class="span-duration" :style="{ color: getColor(span.duration) }">
        {{ span.duration.toFixed(0) }}ms
      </span>
      <span class="span-percent" v-if="totalDuration">
        ({{ ((span.duration / totalDuration) * 100).toFixed(1) }}%)
      </span>
      <el-tag :type="getRatingType(span.rating)" size="small" class="span-tag">
        {{ span.rating }}
      </el-tag>
    </div>

    <div v-if="expanded && span.children?.length" class="span-children">
      <TraceSpanItem
        v-for="child in span.children"
        :key="child.span_id"
        :span="child"
        :totalDuration="totalDuration"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowDown, ArrowRight, Document } from '@element-plus/icons-vue'

const props = defineProps({
  span: {
    type: Object,
    required: true
  },
  totalDuration: {
    type: Number,
    default: 0
  },
  depth: {
    type: Number,
    default: 0
  }
})

const expanded = ref(false)

const displayName = computed(() => {
  let name = props.span.name
  // 简化名称显示
  if (name.startsWith('web-vital_')) return name.replace('web-vital_', 'WebVitals: ')
  if (name.startsWith('custom_')) return name.replace('custom_', '')
  if (name.startsWith('trace_')) return name.replace('trace_', '')
  if (name.startsWith('api_')) return name.replace('api_', 'API: ')
  return name
})

const getColor = (value) => {
  if (value > 2500) return '#ff4949'
  if (value > 1000) return '#e6a23c'
  return '#67c23a'
}

const getRatingType = (rating) => {
  switch (rating) {
    case 'good': return 'success'
    case 'needs-improvement': return 'warning'
    case 'poor': return 'danger'
    default: return 'info'
  }
}
</script>

<style scoped>
.span-item {
  margin-bottom: 4px;
}

.span-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.span-header:hover {
  background: var(--el-fill-color);
}

.expand-icon {
  display: flex;
  align-items: center;
  color: var(--el-text-color-secondary);
}

.span-name {
  flex: 1;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.span-duration {
  font-weight: bold;
  font-family: monospace;
}

.span-percent {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.span-tag {
  margin-left: 8px;
}

.span-children {
  margin-top: 4px;
}
</style>
