<template>
  <div class="home">
    <h1>Anime1 Desktop (Electron重构版)</h1>
    <p>欢迎使用 Electron + TypeScript 重构版本</p>
    
    <div class="status">
      <el-card>
        <template #header>
          <span>开发状态</span>
        </template>
        <el-timeline>
          <el-timeline-item type="success">
            项目架构搭建
          </el-timeline-item>
          <el-timeline-item type="success">
            TypeScript 配置
          </el-timeline-item>
          <el-timeline-item type="primary">
            服务层开发 (进行中)
          </el-timeline-item>
          <el-timeline-item>
            UI 组件迁移
          </el-timeline-item>
          <el-timeline-item>
            功能测试
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
    
    <div class="actions">
      <el-button type="primary" @click="testIPC">
        测试 IPC 通信
      </el-button>
      <el-button @click="openSettings">
        打开设置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const testIPC = async () => {
  try {
    // 测试 IPC 调用
    const result = await window.api.anime.getCacheStatus()
    console.log('IPC Test Result:', result)
  } catch (error) {
    console.error('IPC Test Error:', error)
  }
}

const openSettings = () => {
  router.push('/settings')
}
</script>

<style scoped>
.home {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  color: var(--anime-primary);
  margin-bottom: 16px;
}

.status {
  margin: 32px 0;
}

.actions {
  margin-top: 24px;
}
</style>
