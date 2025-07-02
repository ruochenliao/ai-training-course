<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div 
      class="layout-sidebar"
      :class="{ collapsed: appStore.sidebarCollapsed }"
    >
      <Sidebar />
    </div>

    <!-- 主内容区 -->
    <div class="layout-main">
      <!-- 头部 -->
      <div class="layout-header">
        <Header />
      </div>

      <!-- 内容区 -->
      <div class="layout-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </div>
    </div>

    <!-- 移动端遮罩 -->
    <div 
      v-if="isMobile && !appStore.sidebarCollapsed"
      class="mobile-mask"
      @click="appStore.toggleSidebar"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const appStore = useAppStore()

// 移动端检测
const isMobile = computed(() => window.innerWidth < 768)

// 缓存的视图
const cachedViews = computed(() => {
  // 这里可以根据路由配置来决定哪些页面需要缓存
  return ['Dashboard', 'SystemUser', 'SystemRole', 'SystemPermission', 'SystemMenu']
})

// 监听窗口大小变化
const handleResize = () => {
  if (window.innerWidth < 768) {
    // 移动端自动折叠侧边栏
    if (!appStore.sidebarCollapsed) {
      appStore.toggleSidebar()
    }
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize() // 初始化检查
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.layout-container {
  display: flex;
  height: 100vh;
  overflow: hidden;

  .layout-sidebar {
    width: 240px;
    background-color: #001529;
    transition: width 0.3s ease;
    overflow: hidden;
    z-index: 1001;

    &.collapsed {
      width: 64px;
    }

    @media (max-width: 768px) {
      position: fixed;
      left: 0;
      top: 0;
      height: 100vh;
      transform: translateX(-100%);
      transition: transform 0.3s ease;

      &:not(.collapsed) {
        transform: translateX(0);
      }
    }
  }

  .layout-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0; // 防止flex子元素溢出

    .layout-header {
      height: 60px;
      background-color: #fff;
      border-bottom: 1px solid #e8e8e8;
      display: flex;
      align-items: center;
      box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
      z-index: 1000;
    }

    .layout-content {
      flex: 1;
      overflow: auto;
      background-color: #f5f7fa;
      position: relative;
    }
  }

  .mobile-mask {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.3);
    z-index: 1000;

    @media (min-width: 769px) {
      display: none;
    }
  }
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 暗色主题
.dark {
  .layout-container {
    .layout-main {
      .layout-header {
        background-color: #1d1e1f;
        border-bottom-color: #4c4d4f;
        color: #e5eaf3;
      }

      .layout-content {
        background-color: #141414;
      }
    }
  }
}
</style>
