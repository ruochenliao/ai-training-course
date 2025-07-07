<template>
  <div class="page-container" :class="containerClass">
    <!-- 页面头部 -->
    <div v-if="showHeader" class="page-header">
      <div class="header-content">
        <!-- 标题区域 -->
        <div class="header-title">
          <div class="title-main">
            <el-icon v-if="icon" class="title-icon">
              <component :is="icon" />
            </el-icon>
            <h1 class="title-text">{{ title }}</h1>
            <el-tag v-if="badge" :type="badgeType" size="small" class="title-badge">
              {{ badge }}
            </el-tag>
          </div>
          <p v-if="description" class="title-description">{{ description }}</p>
        </div>

        <!-- 操作区域 -->
        <div v-if="$slots.actions" class="header-actions">
          <slot name="actions" />
        </div>
      </div>

      <!-- 面包屑导航 -->
      <div v-if="showBreadcrumb" class="header-breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="item in breadcrumbItems"
            :key="item.path"
            :to="item.path === $route.path ? undefined : item.path"
          >
            <el-icon v-if="item.icon" class="breadcrumb-icon">
              <component :is="item.icon" />
            </el-icon>
            {{ item.title }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <!-- 标签页 -->
      <div v-if="$slots.tabs" class="header-tabs">
        <slot name="tabs" />
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="page-content" :class="contentClass">
      <div v-if="loading" class="content-loading">
        <el-skeleton :rows="skeletonRows" animated />
      </div>
      <div v-else class="content-wrapper">
        <slot />
      </div>
    </div>

    <!-- 页面底部 -->
    <div v-if="$slots.footer" class="page-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface BreadcrumbItem {
  title: string
  path: string
  icon?: string | object
}

interface Props {
  title?: string
  description?: string
  icon?: string | object
  badge?: string
  badgeType?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  showHeader?: boolean
  showBreadcrumb?: boolean
  breadcrumbItems?: BreadcrumbItem[]
  loading?: boolean
  skeletonRows?: number
  fluid?: boolean
  noPadding?: boolean
  background?: 'default' | 'transparent' | 'white'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  badgeType: 'primary',
  showHeader: true,
  showBreadcrumb: false,
  breadcrumbItems: () => [],
  loading: false,
  skeletonRows: 5,
  fluid: false,
  noPadding: false,
  background: 'default'
})

const route = useRoute()

// 容器样式类
const containerClass = computed(() => ({
  'is-fluid': props.fluid,
  'no-padding': props.noPadding,
  [`bg-${props.background}`]: props.background !== 'default'
}))

// 内容区域样式类
const contentClass = computed(() => ({
  'is-loading': props.loading
}))
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.page-container {
  min-height: 100%;
  background: $bg-color-page;
  
  &.is-fluid {
    .page-content .content-wrapper {
      max-width: none;
    }
  }
  
  &.no-padding {
    .page-content {
      padding: 0;
    }
  }
  
  &.bg-transparent {
    background: transparent;
  }
  
  &.bg-white {
    background: $card-color;
  }
}

// ==================== 页面头部 ====================
.page-header {
  background: $card-color;
  border-bottom: 1px solid $border-color-light;
  margin-bottom: $spacing-lg;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: $spacing-lg $spacing-xl;
    gap: $spacing-lg;
    
    .header-title {
      flex: 1;
      min-width: 0;
      
      .title-main {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
        margin-bottom: $spacing-xs;
        
        .title-icon {
          font-size: 20px;
          color: $primary-color;
          flex-shrink: 0;
        }
        
        .title-text {
          font-size: $font-size-xxl;
          font-weight: $font-weight-semibold;
          color: $text-color-1;
          margin: 0;
          line-height: 1.2;
        }
        
        .title-badge {
          margin-left: $spacing-sm;
        }
      }
      
      .title-description {
        color: $text-color-2;
        font-size: $font-size-base;
        margin: 0;
        line-height: $line-height-base;
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      flex-shrink: 0;
    }
  }
  
  .header-breadcrumb {
    padding: 0 $spacing-xl $spacing-md;
    border-top: 1px solid $border-color-light;
    
    .breadcrumb-icon {
      font-size: 14px;
      margin-right: 4px;
    }
  }
  
  .header-tabs {
    border-top: 1px solid $border-color-light;
  }
}

// ==================== 页面内容 ====================
.page-content {
  padding: 0 $spacing-xl $spacing-xl;
  
  .content-loading {
    background: $card-color;
    border-radius: $border-radius-lg;
    padding: $spacing-xl;
    box-shadow: $box-shadow-sm;
  }
  
  .content-wrapper {
    max-width: $content-max-width;
    margin: 0 auto;
  }
}

// ==================== 页面底部 ====================
.page-footer {
  background: $card-color;
  border-top: 1px solid $border-color-light;
  padding: $spacing-lg $spacing-xl;
  margin-top: auto;
}

// ==================== 响应式设计 ====================
@media (max-width: $breakpoint-lg) {
  .page-header .header-content {
    padding: $spacing-md $spacing-lg;
    flex-direction: column;
    align-items: stretch;
    
    .header-actions {
      justify-content: flex-end;
    }
  }
  
  .page-content {
    padding: 0 $spacing-lg $spacing-lg;
  }
  
  .page-footer {
    padding: $spacing-md $spacing-lg;
  }
}

@media (max-width: $breakpoint-md) {
  .page-header {
    .header-content {
      padding: $spacing-md;
      
      .header-title .title-main {
        flex-wrap: wrap;
        
        .title-text {
          font-size: $font-size-xl;
        }
      }
    }
    
    .header-breadcrumb {
      padding: 0 $spacing-md $spacing-sm;
    }
  }
  
  .page-content {
    padding: 0 $spacing-md $spacing-md;
  }
}

// ==================== 暗色主题 ====================
.dark {
  .page-container {
    background: $dark-bg-color-page;
    
    &.bg-white {
      background: $dark-card-color;
    }
  }
  
  .page-header {
    background: $dark-card-color;
    border-bottom-color: $dark-border-color;
    
    .header-content .header-title {
      .title-main .title-text {
        color: $dark-text-color-1;
      }
      
      .title-description {
        color: $dark-text-color-2;
      }
    }
    
    .header-breadcrumb {
      border-top-color: $dark-border-color;
    }
    
    .header-tabs {
      border-top-color: $dark-border-color;
    }
  }
  
  .page-content .content-loading {
    background: $dark-card-color;
  }
  
  .page-footer {
    background: $dark-card-color;
    border-top-color: $dark-border-color;
  }
}
</style>
