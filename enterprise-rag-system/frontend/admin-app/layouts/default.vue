<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 侧边栏 -->
    <div class="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
      <!-- Logo -->
      <div class="flex items-center justify-center h-16 px-4 border-b">
        <h1 class="text-xl font-bold text-gray-900">RAG管理系统</h1>
      </div>

      <!-- 导航菜单 -->
      <nav class="mt-8">
        <div class="px-4 space-y-2">
          <NuxtLink
            to="/"
            class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            active-class="bg-blue-100 text-blue-700"
          >
            <n-icon class="mr-3" size="20">
              <Home />
            </n-icon>
            首页
          </NuxtLink>

          <NuxtLink
            to="/knowledge-bases"
            class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            active-class="bg-blue-100 text-blue-700"
          >
            <n-icon class="mr-3" size="20">
              <Library />
            </n-icon>
            知识库管理
          </NuxtLink>

          <NuxtLink
            to="/documents"
            class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            active-class="bg-blue-100 text-blue-700"
          >
            <n-icon class="mr-3" size="20">
              <Document />
            </n-icon>
            文档管理
          </NuxtLink>

          <NuxtLink
            to="/system/monitor"
            class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            active-class="bg-blue-100 text-blue-700"
          >
            <n-icon class="mr-3" size="20">
              <Analytics />
            </n-icon>
            系统监控
          </NuxtLink>

          <NuxtLink
            to="/users"
            class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            active-class="bg-blue-100 text-blue-700"
          >
            <n-icon class="mr-3" size="20">
              <People />
            </n-icon>
            用户管理
          </NuxtLink>
        </div>
      </nav>
    </div>

    <!-- 主内容区域 -->
    <div class="pl-64">
      <!-- 顶部导航栏 -->
      <header class="bg-white shadow-sm border-b h-16 flex items-center justify-between px-6">
        <div class="flex items-center">
          <h2 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h2>
        </div>

        <div class="flex items-center space-x-4">
          <!-- 通知 -->
          <n-button text>
            <n-icon size="20">
              <Notifications />
            </n-icon>
          </n-button>

          <!-- 用户菜单 -->
          <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
            <div class="flex items-center space-x-2 cursor-pointer">
              <n-avatar size="small">
                <n-icon>
                  <Person />
                </n-icon>
              </n-avatar>
              <span class="text-sm font-medium">管理员</span>
            </div>
          </n-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="flex-1">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {NAvatar, NButton, NDropdown, NIcon} from 'naive-ui'
import {Analytics, Document, Home, Library, Notifications, People, Person} from '@vicons/ionicons5'

// 页面标题
const route = useRoute()
const pageTitle = computed(() => {
  const titleMap = {
    '/': '首页',
    '/knowledge-bases': '知识库管理',
    '/documents': '文档管理',
    '/system/monitor': '系统监控',
    '/users': '用户管理'
  }
  return titleMap[route.path] || '管理系统'
})

// 用户菜单选项
const userMenuOptions = [
  {
    label: '个人设置',
    key: 'profile'
  },
  {
    label: '系统设置',
    key: 'settings'
  },
  {
    type: 'divider'
  },
  {
    label: '退出登录',
    key: 'logout'
  }
]

// 用户菜单处理
const handleUserMenuSelect = (key: string) => {
  switch (key) {
    case 'profile':
      navigateTo('/profile')
      break
    case 'settings':
      navigateTo('/settings')
      break
    case 'logout':
      // 处理登出逻辑
      localStorage.removeItem('token')
      navigateTo('/login')
      break
  }
}
</script>


