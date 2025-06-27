<template>
  <div id="app">
    <n-config-provider :theme="theme">
      <n-loading-bar-provider>
        <n-dialog-provider>
          <n-notification-provider>
            <n-message-provider>
              <NuxtLayout>
                <NuxtPage />
              </NuxtLayout>
            </n-message-provider>
          </n-notification-provider>
        </n-dialog-provider>
      </n-loading-bar-provider>
    </n-config-provider>
  </div>
</template>

<script setup lang="ts">
import {
  darkTheme,
  NConfigProvider,
  NDialogProvider,
  NLoadingBarProvider,
  NMessageProvider,
  NNotificationProvider
} from 'naive-ui'

// 应用元数据
useHead({
  title: '企业级RAG知识库管理系统',
  meta: [
    { name: 'description', content: '基于多智能体协作的企业级知识库管理系统' }
  ]
})

// 主题配置
const isDark = useDark()
const theme = computed(() => isDark.value ? darkTheme : null)

// 提供主题给子组件
provide('theme', theme)
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条样式 */
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

/* 暗色主题滚动条 */
.dark ::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.dark ::-webkit-scrollbar-thumb {
  background: #5a5a5a;
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: #6a6a6a;
}
</style>
