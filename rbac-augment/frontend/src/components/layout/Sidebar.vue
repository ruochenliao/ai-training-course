<template>
  <div class="sidebar">
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <router-link to="/" class="logo-link">
        <img 
          v-if="!appStore.sidebarCollapsed" 
          src="/logo.svg" 
          alt="Logo" 
          class="logo-img"
        >
        <span v-if="!appStore.sidebarCollapsed" class="logo-text">
          RBAC系统
        </span>
        <img 
          v-else 
          src="/logo.svg" 
          alt="Logo" 
          class="logo-img-mini"
        >
      </router-link>
    </div>

    <!-- 菜单区域 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="appStore.sidebarCollapsed"
      :unique-opened="true"
      :collapse-transition="false"
      mode="vertical"
      background-color="#001529"
      text-color="#fff"
      active-text-color="#1890ff"
      class="sidebar-menu"
      @select="handleMenuSelect"
    >
      <sidebar-item
        v-for="route in menuRoutes"
        :key="route.path"
        :item="route"
        :base-path="route.path"
      />
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SidebarItem from './SidebarItem.vue'
import { filterMenusByPermission } from '@/utils/permission'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

// 当前激活的菜单
const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta?.activeMenu) {
    return meta.activeMenu as string
  }
  return path
})

// 菜单路由（基于权限过滤）
const menuRoutes = computed(() => {
  // 基础菜单结构
  const baseRoutes = [
    {
      path: '/dashboard',
      name: 'Dashboard',
      meta: {
        title: '仪表板',
        icon: 'Odometer'
      }
    },
    {
      path: '/system',
      name: 'System',
      meta: {
        title: '系统管理',
        icon: 'Setting'
      },
      children: [
        {
          path: '/system/users',
          name: 'SystemUser',
          meta: {
            title: '用户管理',
            icon: 'User',
            permissions: ['user:read']
          }
        },
        {
          path: '/system/roles',
          name: 'SystemRole',
          meta: {
            title: '角色管理',
            icon: 'UserFilled',
            permissions: ['role:read']
          }
        },
        {
          path: '/system/permissions',
          name: 'SystemPermission',
          meta: {
            title: '权限管理',
            icon: 'Key',
            permissions: ['permission:read']
          }
        },
        {
          path: '/system/menus',
          name: 'SystemMenu',
          meta: {
            title: '菜单管理',
            icon: 'Menu',
            permissions: ['menu:read']
          }
        }
      ]
    }
  ]

  // 根据用户权限过滤菜单
  return filterMenusByPermission(baseRoutes)
})

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  if (index !== route.path) {
    router.push(index)
  }
}

// 监听路由变化，自动展开对应的菜单
watch(
  () => route.path,
  () => {
    // 这里可以添加自动展开父菜单的逻辑
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;

  .sidebar-logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid #1f2937;
    background-color: #000c17;

    .logo-link {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: #fff;
      font-weight: 600;
      font-size: 18px;

      .logo-img {
        width: 32px;
        height: 32px;
        margin-right: 12px;
      }

      .logo-img-mini {
        width: 32px;
        height: 32px;
      }

      .logo-text {
        transition: all 0.3s ease;
      }
    }
  }

  .sidebar-menu {
    flex: 1;
    border: none;
    overflow-y: auto;
    overflow-x: hidden;

    // 自定义滚动条
    &::-webkit-scrollbar {
      width: 4px;
    }

    &::-webkit-scrollbar-track {
      background: #001529;
    }

    &::-webkit-scrollbar-thumb {
      background: #1890ff;
      border-radius: 2px;
    }

    // 菜单项样式
    :deep(.el-menu-item) {
      height: 50px;
      line-height: 50px;
      color: rgba(255, 255, 255, 0.85);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);

      &:hover {
        background-color: #1890ff !important;
        color: #fff;
      }

      &.is-active {
        background-color: #1890ff !important;
        color: #fff;
        position: relative;

        &::after {
          content: '';
          position: absolute;
          right: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background-color: #fff;
        }
      }

      .el-icon {
        margin-right: 8px;
        font-size: 16px;
      }
    }

    // 子菜单样式
    :deep(.el-sub-menu) {
      .el-sub-menu__title {
        height: 50px;
        line-height: 50px;
        color: rgba(255, 255, 255, 0.85);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);

        &:hover {
          background-color: #1890ff !important;
          color: #fff;
        }

        .el-icon {
          margin-right: 8px;
          font-size: 16px;
        }
      }

      .el-menu {
        background-color: #000c17;

        .el-menu-item {
          height: 45px;
          line-height: 45px;
          padding-left: 60px !important;
          background-color: transparent;

          &:hover {
            background-color: rgba(24, 144, 255, 0.8) !important;
          }

          &.is-active {
            background-color: #1890ff !important;
          }
        }
      }
    }

    // 折叠状态样式
    &.el-menu--collapse {
      .el-sub-menu {
        .el-sub-menu__title {
          padding: 0 20px;
        }
      }

      .el-menu-item {
        padding: 0 20px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    width: 240px;
  }
}
</style>
