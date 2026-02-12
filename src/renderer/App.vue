<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

onMounted(() => {
  console.log('[Renderer] App mounted')
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

html {
  overflow-x: hidden;
  overflow-y: auto;
}

#app {
  min-height: 100vh;
}

/* 主题变量 */
:root {
  --anime-primary: #7c5cff;
  --anime-primary-hover: #6a4fd6;
  --anime-secondary: #ff6b9d;
}
</style>
