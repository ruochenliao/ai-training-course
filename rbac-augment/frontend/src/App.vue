<template>
  <div id="app">
    <router-view />
    <StagewiseToolbar v-if="isDev" :config="{ plugins: [VuePlugin] }" />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { StagewiseToolbar } from '@stagewise/toolbar-vue'
import VuePlugin from '@stagewise-plugins/vue'
import { ref } from 'vue'

const authStore = useAuthStore()
const appStore = useAppStore()

const isDev = ref(import.meta.env.DEV)

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
