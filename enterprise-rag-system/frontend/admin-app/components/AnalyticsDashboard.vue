<template>
  <div class="analytics-dashboard">
    <!-- 概览卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div
        v-for="metric in overviewMetrics"
        :key="metric.key"
        class="bg-white rounded-lg shadow-sm p-6 border border-gray-200"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">{{ metric.label }}</p>
            <p class="text-2xl font-bold text-gray-900">{{ metric.value }}</p>
            <p class="text-sm text-gray-500 mt-1">
              <span :class="metric.trend > 0 ? 'text-green-600' : 'text-red-600'">
                {{ metric.trend > 0 ? '+' : '' }}{{ metric.trend }}%
              </span>
              vs 上期
            </p>
          </div>
          <div :class="metric.iconBg" class="p-3 rounded-full">
            <component :is="metric.icon" class="h-6 w-6 text-white" />
          </div>
        </div>
      </div>
    </div>

    <!-- 时间范围选择器 -->
    <div class="bg-white rounded-lg shadow-sm p-6 mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 class="text-lg font-semibold text-gray-900">数据分析</h2>
        <div class="flex items-center gap-4">
          <select
            v-model="selectedTimeRange"
            @change="handleTimeRangeChange"
            class="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="7">最近7天</option>
            <option value="30">最近30天</option>
            <option value="90">最近90天</option>
            <option value="365">最近一年</option>
          </select>
          <button
            @click="refreshData"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            刷新
          </button>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
      <!-- 用户趋势图 -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">用户增长趋势</h3>
        <div ref="userTrendChart" class="h-80"></div>
      </div>

      <!-- 文档处理统计 -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">文档处理统计</h3>
        <div ref="documentChart" class="h-80"></div>
      </div>

      <!-- 对话分析 -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">对话分析</h3>
        <div ref="conversationChart" class="h-80"></div>
      </div>

      <!-- 系统性能 -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">系统性能指标</h3>
        <div ref="performanceChart" class="h-80"></div>
      </div>
    </div>

    <!-- 详细数据表格 -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">详细数据</h3>
        <div class="flex gap-2">
          <button
            v-for="tab in dataTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'px-4 py-2 text-sm font-medium rounded-md',
              activeTab === tab.key
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- 用户数据表格 -->
      <div v-if="activeTab === 'users'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                用户ID
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                用户名
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                注册时间
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                最后活动
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                活跃度
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in userData" :key="user.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ user.id }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ user.username }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(user.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(user.last_activity) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getActivityBadgeClass(user.activity_score)" class="px-2 py-1 text-xs font-medium rounded-full">
                  {{ getActivityLabel(user.activity_score) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 文档数据表格 -->
      <div v-if="activeTab === 'documents'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                文档名称
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                类型
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                大小
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                上传时间
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="doc in documentData" :key="doc.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ doc.name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ doc.type }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatFileSize(doc.size) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getStatusBadgeClass(doc.status)" class="px-2 py-1 text-xs font-medium rounded-full">
                  {{ doc.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(doc.created_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 对话数据表格 -->
      <div v-if="activeTab === 'conversations'" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                对话ID
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                用户
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                消息数
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                满意度
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                开始时间
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="conv in conversationData" :key="conv.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ conv.id }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ conv.user_name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ conv.message_count }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex text-yellow-400">
                    <svg
                      v-for="i in 5"
                      :key="i"
                      :class="i <= conv.satisfaction ? 'text-yellow-400' : 'text-gray-300'"
                      class="h-4 w-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                  </div>
                  <span class="ml-2 text-sm text-gray-600">{{ conv.satisfaction }}/5</span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(conv.created_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import {nextTick, onMounted, ref} from 'vue'
import * as echarts from 'echarts'
import {useToast} from 'vue-toastification'

const toast = useToast()

// 响应式数据
const loading = ref(false)
const selectedTimeRange = ref('30')
const activeTab = ref('users')

// 图表引用
const userTrendChart = ref(null)
const documentChart = ref(null)
const conversationChart = ref(null)
const performanceChart = ref(null)

// 概览指标
const overviewMetrics = ref([
  {
    key: 'users',
    label: '总用户数',
    value: '2,543',
    trend: 12.5,
    icon: 'UserGroupIcon',
    iconBg: 'bg-blue-500'
  },
  {
    key: 'documents',
    label: '文档总数',
    value: '18,429',
    trend: 8.2,
    icon: 'DocumentTextIcon',
    iconBg: 'bg-green-500'
  },
  {
    key: 'conversations',
    label: '对话总数',
    value: '45,678',
    trend: 15.3,
    icon: 'ChatBubbleLeftRightIcon',
    iconBg: 'bg-purple-500'
  },
  {
    key: 'satisfaction',
    label: '平均满意度',
    value: '4.2/5',
    trend: 3.1,
    icon: 'StarIcon',
    iconBg: 'bg-yellow-500'
  }
])

// 数据标签页
const dataTabs = [
  { key: 'users', label: '用户数据' },
  { key: 'documents', label: '文档数据' },
  { key: 'conversations', label: '对话数据' }
]

// 表格数据
const userData = ref([])
const documentData = ref([])
const conversationData = ref([])

// 方法
const handleTimeRangeChange = async () => {
  await refreshData()
}

const refreshData = async () => {
  loading.value = true
  try {
    // 并行加载所有数据
    await Promise.all([
      loadOverviewData(),
      loadChartData(),
      loadTableData()
    ])
    
    // 重新渲染图表
    await nextTick()
    renderCharts()
    
  } catch (error) {
    console.error('刷新数据失败:', error)
    toast.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const loadOverviewData = async () => {
  try {
    const response = await $fetch(`/api/v1/analytics/overview?days=${selectedTimeRange.value}`)
    
    // 更新概览指标
    if (response.success && response.data) {
      const data = response.data
      overviewMetrics.value[0].value = data.users?.total?.toLocaleString() || '0'
      overviewMetrics.value[1].value = data.documents?.total?.toLocaleString() || '0'
      overviewMetrics.value[2].value = data.conversations?.total?.toLocaleString() || '0'
      
      // 更新增长率
      overviewMetrics.value[0].trend = data.users?.growth_rate || 0
      overviewMetrics.value[1].trend = data.documents?.growth_rate || 0
      overviewMetrics.value[2].trend = data.conversations?.growth_rate || 0
    }
  } catch (error) {
    console.error('加载概览数据失败:', error)
  }
}

const loadChartData = async () => {
  // 这里应该从API加载图表数据
  // 目前使用模拟数据
}

const loadTableData = async () => {
  // 模拟表格数据
  userData.value = [
    {
      id: 1,
      username: 'admin',
      created_at: '2024-01-15T10:30:00Z',
      last_activity: '2024-01-20T15:45:00Z',
      activity_score: 85
    },
    {
      id: 2,
      username: 'user1',
      created_at: '2024-01-16T09:20:00Z',
      last_activity: '2024-01-20T14:30:00Z',
      activity_score: 72
    }
  ]
  
  documentData.value = [
    {
      id: 1,
      name: '用户手册.pdf',
      type: 'PDF',
      size: 2048576,
      status: 'processed',
      created_at: '2024-01-20T10:00:00Z'
    },
    {
      id: 2,
      name: '技术文档.docx',
      type: 'DOCX',
      size: 1024000,
      status: 'processing',
      created_at: '2024-01-20T11:00:00Z'
    }
  ]
  
  conversationData.value = [
    {
      id: 1,
      user_name: 'user1',
      message_count: 15,
      satisfaction: 4,
      created_at: '2024-01-20T09:00:00Z'
    },
    {
      id: 2,
      user_name: 'user2',
      message_count: 8,
      satisfaction: 5,
      created_at: '2024-01-20T10:30:00Z'
    }
  ]
}

const renderCharts = () => {
  // 渲染用户趋势图
  if (userTrendChart.value) {
    const chart = echarts.init(userTrendChart.value)
    chart.setOption({
      title: { text: '' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
      },
      yAxis: { type: 'value' },
      series: [{
        data: [120, 200, 150, 80, 70, 110],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#3B82F6' }
      }]
    })
  }
  
  // 渲染其他图表...
}

// 工具函数
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes) => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const getActivityBadgeClass = (score) => {
  if (score >= 80) return 'bg-green-100 text-green-800'
  if (score >= 60) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const getActivityLabel = (score) => {
  if (score >= 80) return '高活跃'
  if (score >= 60) return '中活跃'
  return '低活跃'
}

const getStatusBadgeClass = (status) => {
  const classes = {
    'processed': 'bg-green-100 text-green-800',
    'processing': 'bg-yellow-100 text-yellow-800',
    'failed': 'bg-red-100 text-red-800',
    'pending': 'bg-gray-100 text-gray-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

// 生命周期
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.analytics-dashboard {
  max-width: 100%;
  margin: 0 auto;
}
</style>
