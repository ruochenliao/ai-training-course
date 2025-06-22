<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold text-gray-900">
              企业级RAG知识库管理系统
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">管理端</span>
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span class="text-white text-sm font-medium">A</span>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主要内容 -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <!-- 欢迎区域 -->
      <div class="px-4 py-6 sm:px-0">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <div class="text-center">
              <h2 class="text-3xl font-bold text-gray-900 mb-4">
                欢迎使用企业级RAG知识库管理系统
              </h2>
              <p class="text-lg text-gray-600 mb-8">
                基于多智能体协作的企业级知识库管理平台
              </p>
              
              <!-- 快速操作卡片 -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                <!-- 知识库管理 -->
                <div class="bg-blue-50 rounded-lg p-6 hover:bg-blue-100 transition-colors cursor-pointer"
                     @click="navigateTo('/knowledge-bases')">
                  <div class="text-blue-600 mb-4">
                    <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                    </svg>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">知识库管理</h3>
                  <p class="text-gray-600">创建、编辑和管理企业知识库</p>
                </div>

                <!-- 系统监控 -->
                <div class="bg-green-50 rounded-lg p-6 hover:bg-green-100 transition-colors cursor-pointer"
                     @click="navigateTo('/system/monitor')">
                  <div class="text-green-600 mb-4">
                    <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                    </svg>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">系统监控</h3>
                  <p class="text-gray-600">监控系统状态和性能指标</p>
                </div>

                <!-- 用户管理 -->
                <div class="bg-purple-50 rounded-lg p-6 hover:bg-purple-100 transition-colors cursor-pointer"
                     @click="navigateTo('/users')">
                  <div class="text-purple-600 mb-4">
                    <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                    </svg>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">用户管理</h3>
                  <p class="text-gray-600">管理用户账户和权限设置</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统状态概览 -->
      <div class="px-4 py-6 sm:px-0">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">系统状态概览</h3>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">{{ stats.knowledgeBases }}</div>
                <div class="text-sm text-gray-500">知识库数量</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-green-600">{{ stats.documents }}</div>
                <div class="text-sm text-gray-500">文档总数</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">{{ stats.queries }}</div>
                <div class="text-sm text-gray-500">今日查询</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-orange-600">{{ stats.users }}</div>
                <div class="text-sm text-gray-500">活跃用户</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
// 页面元数据
definePageMeta({
  title: '企业级RAG知识库管理系统',
  description: '基于多智能体协作的企业级知识库管理平台'
})

// 响应式数据
const stats = ref({
  knowledgeBases: 12,
  documents: 1248,
  queries: 156,
  users: 24
})

// 页面加载时获取统计数据
onMounted(async () => {
  try {
    // 这里可以调用 API 获取真实的统计数据
    // const response = await $fetch('/api/stats')
    // stats.value = response
    console.log('页面加载完成，统计数据已初始化')
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
})
</script>

<style scoped>
/* 自定义样式 */
.transition-colors {
  transition: background-color 0.2s ease-in-out;
}
</style>
