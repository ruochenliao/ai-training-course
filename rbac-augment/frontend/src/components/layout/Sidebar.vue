<template>
  <div class="sidebar">
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <router-link to="/" class="logo-link">
        <div v-if="!appStore.sidebarCollapsed" class="logo-full">
          <el-icon class="logo-icon" size="24">
            <OfficeBuilding />
          </el-icon>
          <span class="logo-text">RBAC系统</span>
        </div>
        <div v-else class="logo-mini">
          <el-icon class="logo-icon-mini" size="20">
            <OfficeBuilding />
          </el-icon>
        </div>
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
import { OfficeBuilding } from '@element-plus/icons-vue'
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
        },
        {
          path: '/system/departments',
          name: 'SystemDepartment',
          meta: {
            title: '部门管理',
            icon: 'OfficeBuilding',
            permissions: ['department:read']
          }
        },
        {
          path: '/system/data-permissions',
          name: 'SystemDataPermission',
          meta: {
            title: '数据权限管理',
            icon: 'Key',
            permissions: ['data_permission:read']
          }
        },
        {
          path: '/system/audit-logs',
          name: 'SystemAuditLog',
          meta: {
            title: '审计日志',
            icon: 'Document',
            permissions: ['audit_log:read']
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
/**
 * 侧边栏样式
 * 参考 SuperIntelligentCustomerService 的设计风格
 * 包含响应式设计和暗色主题支持
 */
@import '@/styles/variables.scss';

.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
  border-right: 1px solid $border-color;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);

  // ==================== Logo区域样式 ====================
  .sidebar-logo {
    height: $header-height;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid $border-color;
    background: $card-color;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 20px;
      right: 20px;
      height: 1px;
      background: linear-gradient(90deg, transparent, $primary-color, transparent);
    }

    .logo-link {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: $text-color-1;
      font-weight: 600;
      font-size: 18px;
      transition: all 0.3s ease;
      padding: 8px 16px;
      border-radius: 8px;

      &:hover {
        background: rgba($primary-color, 0.1);
        transform: translateY(-1px);
      }

      .logo-full {
        display: flex;
        align-items: center;
        gap: 12px;

        .logo-icon {
          color: $primary-color;
          font-size: 24px;
          transition: all 0.3s ease;
        }

        .logo-text {
          background: linear-gradient(135deg, $primary-color, $primary-color-hover);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 700;
          letter-spacing: 0.5px;
        }
      }

      .logo-mini {
        display: flex;
        align-items: center;
        justify-content: center;

        .logo-icon-mini {
          color: $primary-color;
          font-size: 20px;
          transition: all 0.3s ease;

          &:hover {
            transform: scale(1.1);
          }
        }
      }
    }
  }

  // ==================== 菜单区域样式 ====================
  .sidebar-menu {
    flex: 1;
    border: none;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 16px 8px;

    // 自定义滚动条样式
    &::-webkit-scrollbar {
      width: 4px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background: rgba($primary-color, 0.3);
      border-radius: 2px;
      transition: background 0.3s ease;

      &:hover {
        background: rgba($primary-color, 0.5);
      }
    }

    // Element Plus 菜单样式覆盖
    :deep(.el-menu) {
      border: none;
      background: transparent;

      .el-menu-item,
      .el-sub-menu__title {
        height: 48px;
        line-height: 48px;
        margin: 4px 0;
        border-radius: 8px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: $text-color-2;

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          width: 0;
          height: 100%;
          background: linear-gradient(90deg, $primary-color, $primary-color-hover);
          transition: width 0.3s ease;
          border-radius: 0 4px 4px 0;
        }

        &:hover {
          background: rgba($primary-color, 0.08);
          transform: translateX(4px);
          color: $text-color-1;

          &::before {
            width: 3px;
          }
        }

        &.is-active {
          background: linear-gradient(135deg, rgba($primary-color, 0.15), rgba($primary-color, 0.08));
          color: $primary-color;
          font-weight: 600;

          &::before {
            width: 3px;
          }

          .el-icon {
            color: $primary-color;
          }
        }

        .el-icon {
          font-size: 18px;
          margin-right: 12px;
          transition: all 0.3s ease;
        }
      }

      // 子菜单样式
      .el-sub-menu {
        .el-sub-menu__title {
          &:hover {
            background: rgba($primary-color, 0.08);
            color: $text-color-1;
          }
        }

        .el-menu {
          background: rgba($primary-color, 0.02);
          border-radius: 8px;
          margin: 4px 0;

          .el-menu-item {
            padding-left: 48px !important;
            margin: 2px 8px;

            &::before {
              left: 20px;
            }

            &:hover {
              background: rgba($primary-color, 0.12);
            }

            &.is-active {
              background: linear-gradient(135deg, rgba($primary-color, 0.2), rgba($primary-color, 0.12));
            }
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

// ==================== 响应式设计 ====================

// 平板设备适配
@media (max-width: 992px) {
  .sidebar {
    .sidebar-logo {
      .logo-link {
        .logo-full {
          .logo-text {
            font-size: 16px;
          }
        }
      }
    }
  }
}

// 手机设备适配
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1100;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.2, 0, 0, 1);
    width: 280px !important;

    &.mobile-open {
      transform: translateX(0);
    }
  }
}

// ==================== 暗色主题支持 ====================
.dark {
  .sidebar {
    background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
    border-right-color: #333;

    .sidebar-logo {
      background: #1a1a1a;
      border-bottom-color: #333;

      .logo-link {
        color: #e5eaf3;

        &:hover {
          background: rgba($primary-color, 0.15);
        }

        .logo-full {
          .logo-text {
            background: linear-gradient(135deg, $primary-color, $primary-color-hover);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
          }
        }
      }
    }

    .sidebar-menu {
      :deep(.el-menu) {
        .el-menu-item,
        .el-sub-menu__title {
          color: #a3a6ad;

          &:hover {
            background: rgba($primary-color, 0.15);
            color: #e5eaf3;
          }

          &.is-active {
            background: linear-gradient(135deg, rgba($primary-color, 0.25), rgba($primary-color, 0.15));
            color: $primary-color;
          }
        }

        .el-sub-menu {
          .el-menu {
            background: rgba(0, 0, 0, 0.2);

            .el-menu-item {
              &:hover {
                background: rgba($primary-color, 0.2);
              }

              &.is-active {
                background: linear-gradient(135deg, rgba($primary-color, 0.3), rgba($primary-color, 0.2));
              }
            }
          }
        }
      }
    }
  }
}
</style>
