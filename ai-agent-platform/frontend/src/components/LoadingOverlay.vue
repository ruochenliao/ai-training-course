<template>
  <div v-if="visible" class="loading-overlay" :class="{ fullscreen }">
    <div class="loading-content">
      <el-icon class="loading-icon" :size="size">
        <Loading />
      </el-icon>
      <p v-if="text" class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

interface Props {
  visible: boolean
  text?: string
  fullscreen?: boolean
  size?: number
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
  fullscreen: false,
  size: 40
})
</script>

<style lang="scss" scoped>
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  
  &.fullscreen {
    position: fixed;
    background: rgba(0, 0, 0, 0.5);
  }
  
  .loading-content {
    text-align: center;
    
    .loading-icon {
      color: #409eff;
      animation: rotate 2s linear infinite;
    }
    
    .loading-text {
      margin: 16px 0 0 0;
      color: #606266;
      font-size: 14px;
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
