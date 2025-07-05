<template>
  <div class="loading-state" :class="loadingClass">
    <!-- 骨架屏模式 -->
    <template v-if="type === 'skeleton'">
      <div class="skeleton-container">
        <div v-for="i in skeletonRows" :key="i" class="skeleton-row">
          <div class="skeleton-avatar" v-if="showAvatar"></div>
          <div class="skeleton-content">
            <div class="skeleton-line" :style="{ width: getLineWidth(i) }"></div>
            <div class="skeleton-line short" v-if="i % 2 === 0"></div>
          </div>
        </div>
      </div>
    </template>
    
    <!-- 加载指示器模式 -->
    <template v-else-if="type === 'spinner'">
      <div class="spinner-container">
        <div class="spinner" :class="spinnerSize">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <div v-if="text" class="spinner-text">{{ text }}</div>
      </div>
    </template>
    
    <!-- 进度条模式 -->
    <template v-else-if="type === 'progress'">
      <div class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <div v-if="text" class="progress-text">{{ text }} {{ progress }}%</div>
      </div>
    </template>
    
    <!-- 点状加载器 -->
    <template v-else-if="type === 'dots'">
      <div class="dots-container">
        <div class="dots">
          <div class="dot" v-for="i in 3" :key="i"></div>
        </div>
        <div v-if="text" class="dots-text">{{ text }}</div>
      </div>
    </template>
    
    <!-- 脉冲加载器 -->
    <template v-else-if="type === 'pulse'">
      <div class="pulse-container">
        <div class="pulse-circle"></div>
        <div v-if="text" class="pulse-text">{{ text }}</div>
      </div>
    </template>
    
    <!-- 默认加载器 -->
    <template v-else>
      <div class="default-container">
        <el-icon class="loading-icon" :size="iconSize">
          <Loading />
        </el-icon>
        <div v-if="text" class="loading-text">{{ text }}</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

// 组件属性
interface Props {
  type?: 'default' | 'skeleton' | 'spinner' | 'progress' | 'dots' | 'pulse'
  text?: string
  size?: 'small' | 'medium' | 'large'
  progress?: number
  skeletonRows?: number
  showAvatar?: boolean
  overlay?: boolean
  fullscreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  text: '',
  size: 'medium',
  progress: 0,
  skeletonRows: 3,
  showAvatar: false,
  overlay: false,
  fullscreen: false
})

// 计算属性
const loadingClass = computed(() => ({
  [`loading-${props.size}`]: true,
  'loading-overlay': props.overlay,
  'loading-fullscreen': props.fullscreen
}))

const spinnerSize = computed(() => `spinner-${props.size}`)

const iconSize = computed(() => {
  switch (props.size) {
    case 'small': return 16
    case 'large': return 32
    default: return 24
  }
})

// 方法
const getLineWidth = (index: number): string => {
  const widths = ['100%', '80%', '60%', '90%', '70%']
  return widths[index % widths.length]
}
</script>

<style lang="scss" scoped>
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  
  &.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    z-index: 1000;
    backdrop-filter: blur(2px);
  }
  
  &.loading-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    z-index: 9999;
  }
}

// 默认加载器
.default-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .loading-icon {
    color: var(--el-color-primary);
    animation: rotate 1s linear infinite;
  }
  
  .loading-text {
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

// 骨架屏
.skeleton-container {
  width: 100%;
  max-width: 400px;
  
  .skeleton-row {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    
    .skeleton-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
      margin-right: 12px;
      flex-shrink: 0;
    }
    
    .skeleton-content {
      flex: 1;
      
      .skeleton-line {
        height: 16px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;
        border-radius: 4px;
        margin-bottom: 8px;
        
        &.short {
          width: 60%;
        }
      }
    }
  }
}

// 旋转加载器
.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .spinner {
    position: relative;
    
    &.spinner-small {
      width: 24px;
      height: 24px;
    }
    
    &.spinner-medium {
      width: 32px;
      height: 32px;
    }
    
    &.spinner-large {
      width: 48px;
      height: 48px;
    }
    
    .spinner-ring {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border: 2px solid transparent;
      border-top-color: var(--el-color-primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      
      &:nth-child(2) {
        animation-delay: 0.1s;
        border-top-color: var(--el-color-primary-light-3);
      }
      
      &:nth-child(3) {
        animation-delay: 0.2s;
        border-top-color: var(--el-color-primary-light-5);
      }
    }
  }
  
  .spinner-text {
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

// 进度条
.progress-container {
  width: 100%;
  max-width: 300px;
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--el-color-info-light-8);
    border-radius: 4px;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--el-color-primary), var(--el-color-primary-light-3));
      border-radius: 4px;
      transition: width 0.3s ease;
      animation: progress-shine 2s infinite;
    }
  }
  
  .progress-text {
    text-align: center;
    margin-top: 8px;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

// 点状加载器
.dots-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .dots {
    display: flex;
    gap: 8px;
    
    .dot {
      width: 8px;
      height: 8px;
      background: var(--el-color-primary);
      border-radius: 50%;
      animation: dot-bounce 1.4s infinite ease-in-out;
      
      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
      &:nth-child(3) { animation-delay: 0s; }
    }
  }
  
  .dots-text {
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

// 脉冲加载器
.pulse-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .pulse-circle {
    width: 40px;
    height: 40px;
    background: var(--el-color-primary);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  
  .pulse-text {
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

// 动画定义
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes skeleton-loading {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes progress-shine {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

// 尺寸变体
.loading-small {
  min-height: 60px;
  
  .skeleton-row .skeleton-avatar {
    width: 32px;
    height: 32px;
  }
  
  .pulse-circle {
    width: 32px;
    height: 32px;
  }
}

.loading-large {
  min-height: 150px;
  
  .skeleton-row .skeleton-avatar {
    width: 48px;
    height: 48px;
  }
  
  .pulse-circle {
    width: 56px;
    height: 56px;
  }
}

// 暗色主题适配
.dark .loading-state {
  &.loading-overlay {
    background: rgba(0, 0, 0, 0.8);
  }
  
  &.loading-fullscreen {
    background: rgba(0, 0, 0, 0.9);
  }
  
  .skeleton-avatar,
  .skeleton-line {
    background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
    background-size: 200% 100%;
  }
  
  .progress-bar {
    background: var(--el-color-info-dark-2);
  }
}
</style>
