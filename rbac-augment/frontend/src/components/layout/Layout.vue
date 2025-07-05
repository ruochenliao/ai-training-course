<template>
  <div class="enterprise-layout">
    <!-- 侧边栏 -->
    <aside
      class="layout-sidebar"
      :class="{
        'is-collapsed': appStore.sidebarCollapsed,
        'is-mobile': isMobile
      }"
    >
      <Sidebar />
    </aside>

    <!-- 主内容区域 -->
    <main class="layout-main">
      <!-- 顶部导航栏 -->
      <header class="layout-header">
        <Header />
      </header>

      <!-- 页面内容区域 -->
      <section class="layout-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component, route }">
            <transition name="page-transition" mode="out-in" appear>
              <keep-alive :include="cachedViews">
                <component :is="Component" :key="route.path" />
              </keep-alive>
            </transition>
          </router-view>
        </div>
      </section>
    </main>

    <!-- 移动端遮罩层 -->
    <div
      v-if="isMobile && !appStore.sidebarCollapsed"
      class="mobile-overlay"
      @click="appStore.toggleSidebar"
      aria-label="关闭侧边栏"
    />

    <!-- 全局加载指示器 -->
    <transition name="loading-fade">
      <div v-if="appStore.loading" class="global-loading">
        <div class="loading-spinner">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span class="loading-text">加载中...</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const appStore = useAppStore()

// 响应式断点检测
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)
const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)

// 缓存的视图组件
const cachedViews = computed(() => {
  // 根据路由配置决定需要缓存的页面组件
  return [
    'Dashboard',
    'SystemUser',
    'SystemRole',
    'SystemPermission',
    'SystemMenu',
    'SystemDepartment',
    'SystemAuditLog',
    'SystemDataPermission'
  ]
})

// 响应式处理函数
const handleResize = () => {
  windowWidth.value = window.innerWidth

  // 移动端自动折叠侧边栏
  if (isMobile.value && !appStore.sidebarCollapsed) {
    appStore.toggleSidebar()
  }

  // 平板端适配处理
  if (isTablet.value) {
    // 可以在这里添加平板端特殊处理逻辑
  }
}

// 防抖处理
let resizeTimer: number | null = null
const debouncedResize = () => {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
  resizeTimer = setTimeout(handleResize, 150)
}

onMounted(() => {
  window.addEventListener('resize', debouncedResize, { passive: true })
  handleResize() // 初始化检查
})

onUnmounted(() => {
  window.removeEventListener('resize', debouncedResize)
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.enterprise-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: $bg-color;
  font-family: $font-family;

  // ==================== 侧边栏样式 ====================
  .layout-sidebar {
    width: $sidebar-width;
    background: linear-gradient(180deg, #001529 0%, #002140 100%);
    transition: all $transition-duration cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    z-index: $z-index-sidebar;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
    position: relative;

    &.is-collapsed {
      width: $sidebar-collapsed-width;
    }

    &.is-mobile {
      position: fixed;
      left: 0;
      top: 0;
      height: 100vh;
      transform: translateX(-100%);
      transition: transform $transition-duration ease;

      &:not(.is-collapsed) {
        transform: translateX(0);
      }
    }

    // 侧边栏边框装饰
    &::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 1px;
      height: 100%;
      background: linear-gradient(180deg,
        rgba(255, 255, 255, 0.1) 0%,
        rgba(255, 255, 255, 0.05) 50%,
        rgba(255, 255, 255, 0.1) 100%
      );
    }
  }

  // ==================== 主内容区域样式 ====================
  .layout-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0;
    position: relative;

    .layout-header {
      height: $header-height;
      background: $card-color;
      border-bottom: 1px solid $border-color;
      display: flex;
      align-items: center;
      box-shadow: $box-shadow-light;
      z-index: $z-index-header;
      position: relative;
      backdrop-filter: blur(8px);
    }

    .layout-content {
      flex: 1;
      overflow: hidden;
      background: $bg-color-page;
      position: relative;

      .content-wrapper {
        height: 100%;
        overflow: auto;
        padding: $content-padding;

        // 自定义滚动条
        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-track {
          background: transparent;
        }

        &::-webkit-scrollbar-thumb {
          background: rgba($text-color-3, 0.3);
          border-radius: 3px;

          &:hover {
            background: rgba($text-color-3, 0.5);
          }
        }
      }
    }
  }

  // ==================== 移动端遮罩层 ====================
  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: $z-index-overlay;
    backdrop-filter: blur(2px);
    cursor: pointer;

    @media (min-width: 769px) {
      display: none;
    }
  }

  // ==================== 全局加载指示器 ====================
  .global-loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: $z-index-loading;
    backdrop-filter: blur(4px);

    .loading-spinner {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      padding: 32px;
      background: $card-color;
      border-radius: $border-radius-lg;
      box-shadow: $box-shadow-base;

      .el-icon {
        font-size: 32px;
        color: $primary-color;
      }

      .loading-text {
        font-size: 14px;
        color: $text-color-2;
        font-weight: 500;
      }
    }
  }
}

// ==================== 页面切换动画 ====================
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all $transition-duration ease;
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

// ==================== 加载动画 ====================
.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: all 0.3s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

// ==================== 响应式设计 ====================
@media (max-width: 1200px) {
  .enterprise-layout {
    .layout-main .layout-content .content-wrapper {
      padding: 16px;
    }
  }
}

@media (max-width: 768px) {
  .enterprise-layout {
    .layout-main .layout-content .content-wrapper {
      padding: 12px;
    }
  }
}

@media (max-width: 480px) {
  .enterprise-layout {
    .layout-main .layout-content .content-wrapper {
      padding: 8px;
    }
  }
}

// ==================== 暗色主题支持 ====================
.dark {
  .enterprise-layout {
    background-color: $dark-bg-color;

    .layout-sidebar {
      background: linear-gradient(180deg, #0f1419 0%, #1a1f29 100%);

      &::after {
        background: linear-gradient(180deg,
          rgba(255, 255, 255, 0.05) 0%,
          rgba(255, 255, 255, 0.02) 50%,
          rgba(255, 255, 255, 0.05) 100%
        );
      }
    }

    .layout-main {
      .layout-header {
        background: $dark-card-color;
        border-bottom-color: $dark-border-color;
      }

      .layout-content {
        background: $dark-bg-color-page;

        .content-wrapper {
          &::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);

            &:hover {
              background: rgba(255, 255, 255, 0.3);
            }
          }
        }
      }
    }

    .global-loading {
      background: rgba(0, 0, 0, 0.8);

      .loading-spinner {
        background: $dark-card-color;

        .loading-text {
          color: $dark-text-color-2;
        }
      }
    }

    .mobile-overlay {
      background: rgba(0, 0, 0, 0.7);
    }
  }
}

// ==================== 高对比度模式支持 ====================
@media (prefers-contrast: high) {
  .enterprise-layout {
    .layout-sidebar {
      border-right: 2px solid $border-color;
    }

    .layout-main .layout-header {
      border-bottom-width: 2px;
    }
  }
}

// ==================== 减少动画模式支持 ====================
@media (prefers-reduced-motion: reduce) {
  .enterprise-layout {
    .layout-sidebar {
      transition: none;
    }

    .page-transition-enter-active,
    .page-transition-leave-active,
    .loading-fade-enter-active,
    .loading-fade-leave-active {
      transition: none;
    }
  }
}
</style>
