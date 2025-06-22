<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">系统监控</h1>
      <p class="text-gray-600">实时监控系统运行状态和性能指标</p>
    </div>

    <!-- 系统状态概览 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <n-card>
        <n-statistic label="系统状态" :value="systemStatus.status">
          <template #prefix>
            <n-icon :color="systemStatus.status === '正常' ? '#18a058' : '#d03050'">
              <CheckmarkCircle v-if="systemStatus.status === '正常'" />
              <CloseCircle v-else />
            </n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="在线用户" :value="systemStatus.onlineUsers">
          <template #prefix>
            <n-icon color="#2080f0"><People /></n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="活跃会话" :value="systemStatus.activeSessions">
          <template #prefix>
            <n-icon color="#f0a020"><ChatbubbleEllipses /></n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="运行时间" :value="systemStatus.uptime">
          <template #prefix>
            <n-icon color="#18a058"><Time /></n-icon>
          </template>
        </n-statistic>
      </n-card>
    </div>

    <!-- 服务状态 -->
    <n-card title="服务状态" class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="service in services"
          :key="service.name"
          class="flex items-center justify-between p-4 border rounded-lg"
        >
          <div class="flex items-center gap-3">
            <n-icon
              :color="service.status === 'healthy' ? '#18a058' : service.status === 'warning' ? '#f0a020' : '#d03050'"
              size="20"
            >
              <CheckmarkCircle v-if="service.status === 'healthy'" />
              <Warning v-else-if="service.status === 'warning'" />
              <CloseCircle v-else />
            </n-icon>
            <div>
              <div class="font-medium">{{ service.name }}</div>
              <div class="text-sm text-gray-500">{{ service.description }}</div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm font-medium">{{ service.responseTime }}ms</div>
            <div class="text-xs text-gray-500">响应时间</div>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 性能指标图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- CPU 使用率 -->
      <n-card title="CPU 使用率">
        <div class="h-64">
          <v-chart :option="cpuChartOption" class="w-full h-full" />
        </div>
      </n-card>

      <!-- 内存使用率 -->
      <n-card title="内存使用率">
        <div class="h-64">
          <v-chart :option="memoryChartOption" class="w-full h-full" />
        </div>
      </n-card>

      <!-- 请求量统计 -->
      <n-card title="API 请求量">
        <div class="h-64">
          <v-chart :option="requestChartOption" class="w-full h-full" />
        </div>
      </n-card>

      <!-- 响应时间 -->
      <n-card title="平均响应时间">
        <div class="h-64">
          <v-chart :option="responseTimeChartOption" class="w-full h-full" />
        </div>
      </n-card>
    </div>

    <!-- 数据库状态 -->
    <n-card title="数据库状态" class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="db in databases"
          :key="db.name"
          class="p-4 border rounded-lg"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="font-medium">{{ db.name }}</div>
            <n-tag :type="db.status === 'connected' ? 'success' : 'error'" size="small">
              {{ db.status === 'connected' ? '已连接' : '断开' }}
            </n-tag>
          </div>
          <div class="space-y-1 text-sm text-gray-600">
            <div>连接数: {{ db.connections }}</div>
            <div>查询/秒: {{ db.qps }}</div>
            <div>延迟: {{ db.latency }}ms</div>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 错误日志 -->
    <n-card title="最近错误">
      <div class="mb-4 flex justify-between items-center">
        <div class="flex gap-4">
          <n-select
            v-model:value="errorLevelFilter"
            placeholder="错误级别"
            :options="errorLevelOptions"
            class="w-32"
          />
          <n-input
            v-model:value="errorSearch"
            placeholder="搜索错误信息"
            class="w-80"
          >
            <template #prefix>
              <n-icon><Search /></n-icon>
            </template>
          </n-input>
        </div>
        <n-button @click="refreshErrors">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </div>

      <n-data-table
        :columns="errorColumns"
        :data="filteredErrors"
        :loading="errorsLoading"
        :pagination="errorPagination"
        max-height="400"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, onUnmounted, reactive, ref} from 'vue'
import {NButton, NCard, NDataTable, NIcon, NInput, NSelect, NStatistic, NTag, useMessage} from 'naive-ui'
import {
  ChatbubbleEllipses,
  CheckmarkCircle,
  CloseCircle,
  People,
  Refresh,
  Search,
  Time,
  Warning
} from '@vicons/ionicons5'
import {use} from 'echarts/core'
import {CanvasRenderer} from 'echarts/renderers'
import {BarChart, LineChart} from 'echarts/charts'
import {GridComponent, LegendComponent, TitleComponent, TooltipComponent} from 'echarts/components'
import VChart from 'vue-echarts'
import {useSystemStore} from '~/stores/system'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const message = useMessage()
const systemStore = useSystemStore()

// 响应式数据
const errorsLoading = ref(false)
const errorSearch = ref('')
const errorLevelFilter = ref(null)

// 系统状态
const systemStatus = reactive({
  status: '正常',
  onlineUsers: 0,
  activeSessions: 0,
  uptime: '0天0小时'
})

// 服务状态
const services = ref([
  { name: 'API Gateway', description: 'FastAPI 网关', status: 'healthy', responseTime: 45 },
  { name: 'LLM Service', description: 'DeepSeek Chat', status: 'healthy', responseTime: 1200 },
  { name: 'Vector DB', description: 'Milvus 向量库', status: 'healthy', responseTime: 80 },
  { name: 'Graph DB', description: 'Neo4j 图数据库', status: 'healthy', responseTime: 120 },
  { name: 'Cache', description: 'Redis 缓存', status: 'healthy', responseTime: 15 },
  { name: 'File Storage', description: 'MinIO 对象存储', status: 'healthy', responseTime: 35 }
])

// 数据库状态
const databases = ref([
  { name: 'MySQL', status: 'connected', connections: 25, qps: 150, latency: 12 },
  { name: 'Milvus', status: 'connected', connections: 8, qps: 45, latency: 80 },
  { name: 'Neo4j', status: 'connected', connections: 5, qps: 20, latency: 120 },
  { name: 'Redis', status: 'connected', connections: 15, qps: 300, latency: 5 }
])

// 错误日志
const errors = ref([])

// 选项数据
const errorLevelOptions = [
  { label: '全部', value: null },
  { label: 'ERROR', value: 'error' },
  { label: 'WARNING', value: 'warning' },
  { label: 'INFO', value: 'info' }
]

// 图表配置
const cpuChartOption = reactive({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{
    name: 'CPU使用率',
    type: 'line',
    data: [],
    smooth: true,
    areaStyle: { opacity: 0.3 },
    lineStyle: { color: '#2080f0' },
    areaStyle: { color: '#2080f0' }
  }]
})

const memoryChartOption = reactive({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{
    name: '内存使用率',
    type: 'line',
    data: [],
    smooth: true,
    areaStyle: { opacity: 0.3 },
    lineStyle: { color: '#18a058' },
    areaStyle: { color: '#18a058' }
  }]
})

const requestChartOption = reactive({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value' },
  series: [{
    name: '请求数',
    type: 'bar',
    data: [],
    itemStyle: { color: '#f0a020' }
  }]
})

const responseTimeChartOption = reactive({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', axisLabel: { formatter: '{value}ms' } },
  series: [{
    name: '响应时间',
    type: 'line',
    data: [],
    smooth: true,
    lineStyle: { color: '#d03050' }
  }]
})

// 错误表格列配置
const errorColumns = [
  {
    title: '时间',
    key: 'timestamp',
    width: 180,
    render: (row) => new Date(row.timestamp).toLocaleString()
  },
  {
    title: '级别',
    key: 'level',
    width: 80,
    render: (row) => {
      const levelMap = {
        error: { color: 'error', text: 'ERROR' },
        warning: { color: 'warning', text: 'WARNING' },
        info: { color: 'info', text: 'INFO' }
      }
      const level = levelMap[row.level] || { color: 'default', text: 'UNKNOWN' }
      return h(NTag, { type: level.color, size: 'small' }, { default: () => level.text })
    }
  },
  {
    title: '服务',
    key: 'service',
    width: 120
  },
  {
    title: '错误信息',
    key: 'message',
    ellipsis: { tooltip: true }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, {
      size: 'small',
      onClick: () => handleViewError(row)
    }, { default: () => '详情' })
  }
]

// 分页配置
const errorPagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 计算属性
const filteredErrors = computed(() => {
  let result = errors.value
  
  if (errorSearch.value) {
    result = result.filter(error => 
      error.message.toLowerCase().includes(errorSearch.value.toLowerCase()) ||
      error.service.toLowerCase().includes(errorSearch.value.toLowerCase())
    )
  }
  
  if (errorLevelFilter.value) {
    result = result.filter(error => error.level === errorLevelFilter.value)
  }
  
  return result
})

// 事件处理函数
const handleViewError = (error) => {
  // 显示错误详情
  window.$dialog.info({
    title: '错误详情',
    content: () => h('div', { class: 'space-y-2' }, [
      h('div', [h('strong', '时间: '), new Date(error.timestamp).toLocaleString()]),
      h('div', [h('strong', '服务: '), error.service]),
      h('div', [h('strong', '级别: '), error.level.toUpperCase()]),
      h('div', [h('strong', '消息: '), error.message]),
      error.stack && h('div', [h('strong', '堆栈: '), h('pre', { class: 'text-xs mt-2 p-2 bg-gray-100 rounded' }, error.stack)])
    ]),
    style: { width: '600px' }
  })
}

const refreshErrors = async () => {
  errorsLoading.value = true
  try {
    errors.value = await systemStore.getErrors()
  } catch (error) {
    message.error('加载错误日志失败')
  } finally {
    errorsLoading.value = false
  }
}

// 数据更新函数
const updateMetrics = async () => {
  try {
    const metrics = await systemStore.getMetrics()
    
    // 更新系统状态
    Object.assign(systemStatus, metrics.system)
    
    // 更新服务状态
    services.value = metrics.services
    
    // 更新数据库状态
    databases.value = metrics.databases
    
    // 更新图表数据
    const now = new Date()
    const timeLabel = now.toLocaleTimeString()
    
    // CPU 图表
    cpuChartOption.xAxis.data.push(timeLabel)
    cpuChartOption.series[0].data.push(metrics.cpu)
    if (cpuChartOption.xAxis.data.length > 20) {
      cpuChartOption.xAxis.data.shift()
      cpuChartOption.series[0].data.shift()
    }
    
    // 内存图表
    memoryChartOption.xAxis.data.push(timeLabel)
    memoryChartOption.series[0].data.push(metrics.memory)
    if (memoryChartOption.xAxis.data.length > 20) {
      memoryChartOption.xAxis.data.shift()
      memoryChartOption.series[0].data.shift()
    }
    
    // 请求量图表
    requestChartOption.xAxis.data.push(timeLabel)
    requestChartOption.series[0].data.push(metrics.requests)
    if (requestChartOption.xAxis.data.length > 20) {
      requestChartOption.xAxis.data.shift()
      requestChartOption.series[0].data.shift()
    }
    
    // 响应时间图表
    responseTimeChartOption.xAxis.data.push(timeLabel)
    responseTimeChartOption.series[0].data.push(metrics.responseTime)
    if (responseTimeChartOption.xAxis.data.length > 20) {
      responseTimeChartOption.xAxis.data.shift()
      responseTimeChartOption.series[0].data.shift()
    }
    
  } catch (error) {
    console.error('更新监控数据失败:', error)
  }
}

// 生命周期
let metricsInterval
let errorsInterval

onMounted(async () => {
  // 初始加载
  await Promise.all([
    updateMetrics(),
    refreshErrors()
  ])
  
  // 定期更新
  metricsInterval = setInterval(updateMetrics, 5000) // 每5秒更新一次
  errorsInterval = setInterval(refreshErrors, 30000) // 每30秒更新错误日志
})

onUnmounted(() => {
  if (metricsInterval) clearInterval(metricsInterval)
  if (errorsInterval) clearInterval(errorsInterval)
})
</script>

<style scoped>
.n-statistic {
  text-align: center;
}
</style>
