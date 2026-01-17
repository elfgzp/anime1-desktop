<template>
  <div class="settings-container">
    <el-card shadow="never" class="page-header-card">
      <h1 class="page-title">设置</h1>
    </el-card>

    <!-- 外观设置 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">外观</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>主题模式</span>
        </div>
        <div class="settings-control">
          <el-select v-model="theme" @change="handleThemeChange" class="theme-select">
            <el-option label="跟随系统" :value="THEME.SYSTEM" />
            <el-option label="暗黑模式" :value="THEME.DARK" />
            <el-option label="普通模式" :value="THEME.LIGHT" />
          </el-select>
        </div>
      </div>
    </el-card>

    <!-- 更新设置 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">更新</div>
      </template>
      <div class="settings-item">
        <div class="settings-label">
          <span>检查更新</span>
        </div>
        <div class="settings-control">
          <el-button
            type="primary"
            :loading="checkingUpdate"
            @click="handleCheckUpdate"
          >
            {{ checkingUpdate ? '检查中...' : '检查更新' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 关于 -->
    <el-card shadow="never" class="settings-section">
      <template #header>
        <div class="section-title">关于</div>
      </template>
      <div class="about-info" v-if="aboutInfo">
        <p><strong>版本:</strong> {{ aboutInfo.version }}</p>
        <p><strong>更新渠道:</strong> {{ aboutInfo.channel }}</p>
        <p>
          <strong>仓库地址:</strong>
          <el-link :href="aboutInfo.repository" target="_blank" type="primary">
            {{ aboutInfo.repository }}
          </el-link>
        </p>
      </div>
      <el-skeleton v-else :rows="3" animated />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsAPI } from '../utils/api'
import { useThemeStore } from '../composables/useTheme'
import { THEME, RESPONSE_FIELDS, REQUEST_PARAMS, ERROR_MESSAGES, UI_TEXT } from '../constants/api'

const SUCCESS_UPDATE_FOUND = '发现新版本'
const SUCCESS_LATEST_VERSION = '已是最新版本'
import { ElMessage } from 'element-plus'

const themeStore = useThemeStore()
const theme = ref(THEME.SYSTEM)
const checkingUpdate = ref(false)
const aboutInfo = ref(null)

const handleThemeChange = async (value) => {
  await themeStore.saveTheme(value)
  ElMessage.success(UI_TEXT.THEME_UPDATED || '主题已更新')
}

const handleCheckUpdate = async () => {
  checkingUpdate.value = true
  try {
    const response = await settingsAPI.checkUpdate()
    if (response.data[RESPONSE_FIELDS.HAS_UPDATE]) {
      ElMessage.success(
        `${SUCCESS_UPDATE_FOUND}: ${response.data[RESPONSE_FIELDS.LATEST_VERSION]}\n当前版本: ${response.data[RESPONSE_FIELDS.CURRENT_VERSION]}`
      )
    } else {
      ElMessage.info(SUCCESS_LATEST_VERSION)
    }
  } catch (error) {
    console.error('检查更新失败:', error)
    ElMessage.error(ERROR_MESSAGES.CHECK_UPDATE_FAILED || '检查更新失败')
  } finally {
    checkingUpdate.value = false
  }
}

const loadTheme = async () => {
  try {
    const response = await settingsAPI.getTheme()
    if (response.data[RESPONSE_FIELDS.SUCCESS] && response.data[RESPONSE_FIELDS.DATA]) {
      theme.value = response.data[RESPONSE_FIELDS.DATA][REQUEST_PARAMS.THEME]
    }
  } catch (error) {
    console.error('加载主题失败:', error)
  }
}

const loadAbout = async () => {
  try {
    const response = await settingsAPI.getAbout()
    if (response.data[RESPONSE_FIELDS.SUCCESS] && response.data[RESPONSE_FIELDS.DATA]) {
      aboutInfo.value = response.data[RESPONSE_FIELDS.DATA]
    }
  } catch (error) {
    console.error('加载关于信息失败:', error)
  }
}

onMounted(() => {
  loadTheme()
  loadAbout()
})
</script>

<style scoped>
.settings-container {
  max-width: 800px;
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

.settings-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.theme-select {
  width: 200px;
}

.about-info {
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
  line-height: 1.6;
}

.about-info p {
  margin: 8px 0;
}

.about-info strong {
  color: var(--el-text-color-primary);
  margin-right: 8px;
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
