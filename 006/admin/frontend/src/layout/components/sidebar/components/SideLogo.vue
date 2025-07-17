<template>
  <div class="logo-container">
    <router-link class="logo-link" to="/">
      <div class="logo-icon">
        <icon-custom-logo text-36 color-primary></icon-custom-logo>
      </div>
      <div v-show="!appStore.collapsed" class="logo-text">
        <h2>{{ title }}</h2>
        <div class="logo-subtitle">AI 智能体平台</div>
      </div>
    </router-link>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store'
const title = import.meta.env.VITE_TITLE

const appStore = useAppStore()
</script>

<style lang="scss" scoped>
.logo-container {
  height: 64px;
  padding: 10px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid #eee; /* 浅色分隔线 */
}

.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  padding: 0 15px;
  width: 100%;
}

.logo-icon {
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo-text {
  margin-left: 12px;
  display: flex;
  flex-direction: column;

  h2 {
    font-size: 18px;
    font-weight: bold;
    color: #333333; /* 深色文字 */
    margin: 0;
  }

  .logo-subtitle {
    font-size: 12px;
    color: #666666; /* 深色副标题 */
    margin-top: 2px;
  }
}

/* 暗色模式样式 */
html.dark {
  .logo-container {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .logo-text {
    h2 {
      color: #ffffff;
    }

    .logo-subtitle {
      color: rgba(255, 255, 255, 0.7);
    }
  }
}
</style>
