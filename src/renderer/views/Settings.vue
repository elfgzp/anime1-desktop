<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1>设置</h1>
    </header>

    <main class="main-content">
      <el-form label-width="150px" class="settings-form">
        <!-- 外观设置 -->
        <el-card class="settings-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Brush /></el-icon>
              <span>外观</span>
            </div>
          </template>
          
          <el-form-item label="主题">
            <el-radio-group v-model="settings.theme" @change="handleThemeChange">
              <el-radio-button label="light">
                <el-icon><Sunny /></el-icon> 浅色
              </el-radio-button>
              <el-radio-button label="dark">
                <el-icon><Moon /></el-icon> 深色
              </el-radio-button>
              <el-radio-button label="system">
                <el-icon><Monitor /></el-icon> 跟随系统
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-card>

        <!-- 播放设置 -->
        <el-card class="settings-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><VideoPlay /></el-icon>
              <span>播放</span>
            </div>
          </template>
          
          <el-form-item label="自动播放下一集">
            <el-switch v-model="settings.autoPlayNext" />
          </el-form-item>
          
          <el-form-item label="记住播放进度">
            <el-switch v-model="settings.rememberPosition" />
          </el-form-item>
          
          <el-form-item label="默认音量">
            <el-slider v-model="settings.defaultVolume" :max="1" :step="0.1" show-stops />
          </el-form-item>
        </el-card>

        <!-- 下载设置 -->
        <el-card class="settings-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Download /></el-icon>
              <span>下载</span>
            </div>
          </template>
          
          <el-form-item label="下载路径">
            <el-input v-model="settings.downloadPath" readonly>
              <template #append>
                <el-button @click="selectDownloadPath">选择</el-button>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="同时下载数量">
            <el-input-number v-model="settings.maxConcurrentDownloads" :min="1" :max="5" />
          </el-form-item>
        </el-card>

        <!-- 更新设置 -->
        <el-card class="settings-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Refresh /></el-icon>
              <span>更新</span>
            </div>
          </template>
          
          <el-form-item label="自动检查更新">
            <el-switch v-model="settings.autoCheckUpdates" />
          </el-form-item>
          
          <el-form-item label="更新通道">
            <el-radio-group v-model="settings.updateChannel">
              <el-radio-button label="stable">稳定版</el-radio-button>
              <el-radio-button label="beta">测试版</el-radio-button>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="checkUpdate" :loading="checkingUpdate">
              立即检查更新
            </el-button>
          </el-form-item>
        </el-card>

        <!-- 关于 -->
        <el-card class="settings-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><InfoFilled /></el-icon>
              <span>关于</span>
            </div>
          </template>
          
          <div class="about-content">
            <div class="app-logo">
              <span class="logo-text">Anime1 Desktop</span>
              <span class="version">v{{ appVersion }}</span>
            </div>
            <p class="app-desc">使用 Electron + Vue 3 + TypeScript 构建的 Anime1 桌面客户端</p>
            <div class="app-links">
              <el-link type="primary" @click="openExternal('https://github.com/elfgzp/anime1-desktop')">
                GitHub
              </el-link>
              <el-link type="primary" @click="openExternal('https://anime1.me')">
                Anime1 官网
              </el-link>
            </div>
          </div>
        </el-card>

        <!-- 保存按钮 -->
        <div class="form-actions">
          <el-button type="primary" size="large" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
          <el-button size="large" @click="resetSettings">重置</el-button>
        </div>
      </el-form>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Brush, Sunny, Moon, Monitor, VideoPlay, Download, Refresh, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  autoPlayNext: boolean
  rememberPosition: boolean
  defaultVolume: number
  downloadPath: string
  maxConcurrentDownloads: number
  autoCheckUpdates: boolean
  updateChannel: 'stable' | 'beta'
}

const appVersion = ref('2.0.0')
const saving = ref(false)
const checkingUpdate = ref(false)

const defaultSettings: AppSettings = {
  theme: 'system',
  autoPlayNext: true,
  rememberPosition: true,
  defaultVolume: 0.8,
  downloadPath: '',
  maxConcurrentDownloads: 3,
  autoCheckUpdates: true,
  updateChannel: 'stable'
}

const settings = ref<AppSettings>({ ...defaultSettings })

// 加载设置
const loadSettings = async () => {
  try {
    const result = await window.api.settings.getAll()
    if (result.success && result.data) {
      // 解析 JSON 格式的设置值
      const parsedSettings: Partial<AppSettings> = {}
      for (const [key, value] of Object.entries(result.data)) {
        try {
          parsedSettings[key as keyof AppSettings] = JSON.parse(value as string)
        } catch {
          parsedSettings[key as keyof AppSettings] = value as any
        }
      }
      settings.value = { ...defaultSettings, ...parsedSettings }
      // 立即应用主题
      applyTheme(settings.value.theme)
    }
  } catch (err) {
    console.error('[Settings] 加载设置失败:', err)
    // 使用默认设置
    settings.value = { ...defaultSettings }
    applyTheme(settings.value.theme)
  }
}

// 保存设置
const saveSettings = async () => {
  saving.value = true
  try {
    // 保存每个设置项
    const promises = Object.entries(settings.value).map(([key, value]) =>
      window.api.settings.set({ key, value: JSON.stringify(value) })
    )
    await Promise.all(promises)
    
    // 应用主题
    applyTheme(settings.value.theme)
    
    ElMessage.success('设置已保存')
  } catch (err: any) {
    ElMessage.error(err.message || '保存设置失败')
  } finally {
    saving.value = false
  }
}

// 重置设置
const resetSettings = () => {
  settings.value = { ...defaultSettings }
  // 应用重置后的主题
  applyTheme(settings.value.theme)
  ElMessage.info('设置已重置为默认值')
}

// 处理主题变更（立即应用）
const handleThemeChange = (theme: string) => {
  applyTheme(theme)
}

// 应用主题
const applyTheme = (theme: string) => {
  const html = document.documentElement
  html.classList.remove('light', 'dark')
  
  if (theme === 'dark') {
    html.classList.add('dark')
  } else if (theme === 'light') {
    html.classList.add('light')
  } else {
    // 跟随系统
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    html.classList.add(prefersDark ? 'dark' : 'light')
  }
}

// 选择下载路径
const selectDownloadPath = async () => {
  // TODO: 实现选择文件夹对话框
  ElMessage.info('功能开发中...')
}

// 检查更新
const checkUpdate = async () => {
  checkingUpdate.value = true
  try {
    const result = await window.api.update.check()
    if (result.success && result.data) {
      const { hasUpdate, latestVersion } = result.data
      if (hasUpdate) {
        ElMessage.success(`发现新版本: ${latestVersion}`)
      } else {
        ElMessage.success('当前已是最新版本')
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '检查更新失败')
  } finally {
    checkingUpdate.value = false
  }
}

// 打开外部链接
const openExternal = async (url: string) => {
  try {
    await window.api.system.openExternal({ url })
  } catch (err) {
    console.error('[Settings] 打开链接失败:', err)
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  min-height: 100%;
  background: var(--el-bg-color-page);
}

.page-header {
  padding: 20px 40px;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.main-content {
  padding: 24px 40px;
  max-width: 800px;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-section {
  border-radius: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.about-content {
  text-align: center;
  padding: 24px;
}

.app-logo {
  margin-bottom: 16px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #ff6b9d 0%, #7c5cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-right: 12px;
}

.version {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 2px 8px;
  border-radius: 4px;
}

.app-desc {
  color: var(--el-text-color-secondary);
  margin: 0 0 16px;
}

.app-links {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 24px 0;
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .main-content {
    padding: 16px 20px;
  }
  
  .settings-form :deep(.el-form-item__label) {
    float: none;
    display: block;
    text-align: left;
    margin-bottom: 8px;
  }
  
  .settings-form :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }
}
</style>
