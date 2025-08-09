<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import enUs from 'element-plus/dist/locale/en.mjs'
import { useGlobalConfig } from 'element-plus'
import type { AuthStoreType, AppStoreType } from '@/types/store-types'

const authStore = useAuthStore() as AuthStoreType
const appStore = useAppStore() as AppStoreType
const { locale } = useI18n()
const globalConfig = useGlobalConfig()

// 监听语言变化，同步更新 Element Plus 的语言包
watch(() => appStore.language, (newLang) => {
  // 更新 i18n 的 locale
  locale.value = newLang
  
  try {
    // 更新 Element Plus 的语言包
    // 使用类型断言处理 Element Plus 的全局配置
    const config = globalConfig as any
    if (config.locale) {
      config.locale.value = newLang === 'zh-CN' ? zhCn : enUs
    }
  } catch (error) {
    console.error('更新 Element Plus 语言包失败:', error)
  }
}, { immediate: true })

onMounted(async () => {
  // 初始化应用设置
  appStore.initApp()
  
  // 初始化认证状态
  await authStore.initAuth()
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  overflow: hidden;
}

// 全局样式重置
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

// 滚动条样式
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

// Element Plus 样式覆盖
.el-message {
  min-width: 300px;
}

.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
}

// 暗色主题
.dark {
  ::-webkit-scrollbar-track {
    background: #2d2d2d;
  }

  ::-webkit-scrollbar-thumb {
    background: #5a5a5a;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #6a6a6a;
  }

  .el-loading-mask {
    background-color: rgba(0, 0, 0, 0.8);
  }
}
</style>
