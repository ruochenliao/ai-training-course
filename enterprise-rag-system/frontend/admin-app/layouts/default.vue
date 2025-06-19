<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <div class="admin-layout">
              <!-- 侧边栏 -->
              <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
                <div class="sidebar-header">
                  <div class="logo">
                    <Icon name="heroicons:cube" class="logo-icon" />
                    <span v-if="!sidebarCollapsed" class="logo-text">RAG管理系统</span>
                  </div>
                </div>
                
                <div class="sidebar-content">
                  <n-menu
                    v-model:value="activeKey"
                    :collapsed="sidebarCollapsed"
                    :collapsed-width="64"
                    :collapsed-icon-size="20"
                    :options="menuOptions"
                    :render-label="renderMenuLabel"
                    :render-icon="renderMenuIcon"
                    @update:value="handleMenuSelect"
                  />
                </div>
              </div>
              
              <!-- 主内容区 -->
              <div class="main-content">
                <!-- 顶部导航栏 -->
                <div class="header">
                  <div class="header-left">
                    <n-button
                      quaternary
                      circle
                      @click="toggleSidebar"
                    >
                      <Icon name="heroicons:bars-3" />
                    </n-button>
                    
                    <n-breadcrumb>
                      <n-breadcrumb-item
                        v-for="item in breadcrumbs"
                        :key="item.path"
                        :clickable="!!item.path"
                        @click="item.path && navigateTo(item.path)"
                      >
                        {{ item.title }}
                      </n-breadcrumb-item>
                    </n-breadcrumb>
                  </div>
                  
                  <div class="header-right">
                    <!-- 主题切换 -->
                    <n-button
                      quaternary
                      circle
                      @click="toggleDark()"
                    >
                      <Icon :name="isDark ? 'heroicons:sun' : 'heroicons:moon'" />
                    </n-button>
                    
                    <!-- 通知 -->
                    <n-badge :value="notificationCount" :max="99">
                      <n-button quaternary circle>
                        <Icon name="heroicons:bell" />
                      </n-button>
                    </n-badge>
                    
                    <!-- 用户菜单 -->
                    <n-dropdown
                      :options="userMenuOptions"
                      @select="handleUserMenuSelect"
                    >
                      <n-button quaternary circle>
                        <n-avatar
                          round
                          size="small"
                          :src="userStore.user?.avatar"
                          fallback-src="/default-avatar.png"
                        />
                      </n-button>
                    </n-dropdown>
                  </div>
                </div>
                
                <!-- 页面内容 -->
                <div class="page-content">
                  <slot />
                </div>
              </div>
            </div>
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { h } from 'vue'
import type { MenuOption } from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'

// 主题
const isDark = useDark()
const toggleDark = useToggle(isDark)
const theme = inject('theme')

// 用户状态
const userStore = useUserStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 当前路由
const route = useRoute()
const activeKey = computed(() => route.path)

// 通知数量
const notificationCount = ref(3)

// 菜单配置
const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: '/admin',
    icon: 'heroicons:home'
  },
  {
    label: '知识库管理',
    key: '/admin/knowledge-bases',
    icon: 'heroicons:book-open'
  },
  {
    label: '文档管理',
    key: '/admin/documents',
    icon: 'heroicons:document-text'
  },
  {
    label: '用户管理',
    key: '/admin/users',
    icon: 'heroicons:users'
  },
  {
    label: '对话管理',
    key: '/admin/conversations',
    icon: 'heroicons:chat-bubble-left-right'
  },
  {
    label: '图谱可视化',
    key: '/admin/graph',
    icon: 'heroicons:share'
  },
  {
    label: '任务监控',
    key: '/admin/tasks',
    icon: 'heroicons:queue-list'
  },
  {
    label: '系统监控',
    key: '/admin/monitoring',
    icon: 'heroicons:chart-bar'
  },
  {
    label: '系统设置',
    key: '/admin/settings',
    icon: 'heroicons:cog-6-tooth'
  }
]

// 用户菜单配置
const userMenuOptions = [
  {
    label: '个人资料',
    key: 'profile',
    icon: 'heroicons:user'
  },
  {
    label: '账户设置',
    key: 'settings',
    icon: 'heroicons:cog-6-tooth'
  },
  {
    type: 'divider'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: 'heroicons:arrow-right-on-rectangle'
  }
]

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathSegments = route.path.split('/').filter(Boolean)
  const breadcrumbs = [{ title: '首页', path: '/admin' }]
  
  let currentPath = ''
  for (const segment of pathSegments.slice(1)) { // 跳过 'admin'
    currentPath += `/${segment}`
    const menuItem = findMenuItemByPath(`/admin${currentPath}`)
    if (menuItem) {
      breadcrumbs.push({
        title: menuItem.label as string,
        path: `/admin${currentPath}`
      })
    }
  }
  
  return breadcrumbs
})

// 查找菜单项
function findMenuItemByPath(path: string): MenuOption | null {
  for (const item of menuOptions) {
    if (item.key === path) {
      return item
    }
  }
  return null
}

// 渲染菜单标签
function renderMenuLabel(option: MenuOption) {
  return option.label
}

// 渲染菜单图标
function renderMenuIcon(option: MenuOption) {
  if (option.icon) {
    return h(Icon, { name: option.icon as string })
  }
  return null
}

// 菜单选择处理
function handleMenuSelect(key: string) {
  navigateTo(key)
}

// 用户菜单选择处理
function handleUserMenuSelect(key: string) {
  switch (key) {
    case 'profile':
      navigateTo('/admin/profile')
      break
    case 'settings':
      navigateTo('/admin/account-settings')
      break
    case 'logout':
      userStore.logout()
      navigateTo('/login')
      break
  }
}

// 页面加载时检查认证状态
onMounted(() => {
  if (!userStore.isAuthenticated) {
    navigateTo('/login')
  }
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: var(--n-color);
}

.sidebar {
  width: 240px;
  background-color: var(--n-card-color);
  border-right: 1px solid var(--n-border-color);
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--n-border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
  color: var(--n-primary-color);
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: var(--n-card-color);
  border-bottom: 1px solid var(--n-border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: var(--n-body-color);
}
</style>
