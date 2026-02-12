<template>
  <div class="settings">
    <h2>设置</h2>
    
    <el-card class="setting-card">
      <template #header>
        <span>外观</span>
      </template>
      <el-form label-width="120px">
        <el-form-item label="主题">
          <el-select v-model="theme" placeholder="选择主题">
            <el-option label="跟随系统" value="system" />
            <el-option label="浅色" value="light" />
            <el-option label="深色" value="dark" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="setting-card">
      <template #header>
        <span>关于</span>
      </template>
      <p>Anime1 Desktop v2.0.0 (Electron版)</p>
      <p>使用 Electron + Vue 3 + TypeScript 构建</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const theme = ref('system')
</script>

<style scoped>
.settings {
  padding: 40px;
  max-width: 600px;
  margin: 0 auto;
}

.setting-card {
  margin-bottom: 20px;
}
</style>
