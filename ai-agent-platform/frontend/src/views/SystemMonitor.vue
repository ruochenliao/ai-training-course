<template>
  <div class="system-monitor">
    <div class="page-header">
      <h1>系统监控</h1>
      <p>实时监控系统性能和运行状态</p>
      
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 系统状态概览 -->
    <div class="status-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <div class="status-icon healthy">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="status-info">
                <h3>系统状态</h3>
                <p class="status-value">{{ systemStatus.overall }}</p>
                <p class="status-desc">运行时间: {{ systemStatus.uptime }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <div class="status-icon performance">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="status-info">
                <h3>系统性能</h3>
                <p class="status-value">{{ systemStatus.performance }}%</p>
                <p class="status-desc">CPU: {{ systemStatus.cpu }}% | 内存: {{ systemStatus.memory }}%</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <div class="status-icon active">
                <el-icon><User /></el-icon>
              </div>
              <div class="status-info">
                <h3>活跃用户</h3>
                <p class="status-value">{{ systemStatus.activeUsers }}</p>
                <p class="status-desc">在线: {{ systemStatus.onlineUsers }} | 今日: {{ systemStatus.todayUsers }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <div class="status-icon requests">
                <el-icon><DataLine /></el-icon>
              </div>
              <div class="status-info">
                <h3>请求处理</h3>
                <p class="status-value">{{ systemStatus.requestsPerSecond }}/s</p>
                <p class="status-desc">成功率: {{ systemStatus.successRate }}%</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 监控图表 -->
    <div class="monitor-charts">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card title="系统性能趋势">
            <div ref="performanceChart" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card title="请求量统计">
            <div ref="requestChart" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card title="错误率分析">
            <div ref="errorChart" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card title="响应时间分布">
            <div ref="responseTimeChart" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 服务状态 -->
    <el-card class="services-status">
      <template #header>
        <div class="card-header">
          <span>服务状态</span>
          <el-button size="small" @click="refreshServices">
            <el-icon><Refresh /></el-icon>
            刷新服务状态
          </el-button>
        </div>
      </template>
      
      <el-table :data="services" stripe>
        <el-table-column prop="name" label="服务名称" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getServiceStatusType(row.status)">
              {{ getServiceStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="uptime" label="运行时间" width="150" />
        <el-table-column prop="cpu" label="CPU使用率" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.cpu" :status="row.cpu > 80 ? 'exception' : ''" />
          </template>
        </el-table-column>
        <el-table-column prop="memory" label="内存使用率" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.memory" :status="row.memory > 80 ? 'exception' : ''" />
          </template>
        </el-table-column>
        <el-table-column prop="requests" label="请求数/分钟" width="120" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewServiceLogs(row)">
              日志
            </el-button>
            <el-button 
              size="small" 
              :type="row.status === 'running' ? 'warning' : 'success'"
              @click="toggleService(row)"
            >
              {{ row.status === 'running' ? '停止' : '启动' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 系统日志 -->
    <el-card class="system-logs">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="log-controls">
            <el-select v-model="logLevel" size="small" style="width: 120px;">
              <el-option label="全部" value="all" />
              <el-option label="错误" value="error" />
              <el-option label="警告" value="warning" />
              <el-option label="信息" value="info" />
            </el-select>
            <el-button size="small" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="log-container">
        <div 
          v-for="log in filteredLogs" 
          :key="log.id"
          class="log-entry"
          :class="`log-${log.level}`"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">{{ log.level.toUpperCase() }}</span>
          <span class="log-service">{{ log.service }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-card>

    <!-- 服务日志对话框 -->
    <el-dialog v-model="showServiceLogs" :title="`${selectedService?.name} 服务日志`" width="80%">
      <ServiceLogs v-if="selectedService" :service="selectedService" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Download, CircleCheckFilled, TrendCharts, User, DataLine, Delete 
} from '@element-plus/icons-vue'
import ServiceLogs from '@/components/Monitor/ServiceLogs.vue'
import { useSystemMonitor } from '@/composables/useSystemMonitor'

// 响应式数据
const loading = ref(false)
const logLevel = ref('all')
const showServiceLogs = ref(false)
const selectedService = ref(null)

const performanceChart = ref<HTMLElement>()
const requestChart = ref<HTMLElement>()
const errorChart = ref<HTMLElement>()
const responseTimeChart = ref<HTMLElement>()

// 使用系统监控组合式函数
const {
  systemStatus,
  services,
  logs,
  refreshSystemStatus,
  refreshServices: refreshServicesData,
  toggleServiceStatus,
  clearSystemLogs
} = useSystemMonitor()

// 计算属性
const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return logs.value
  }
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      refreshSystemStatus(),
      refreshServicesData()
    ])
    
    // 刷新图表
    await nextTick()
    initCharts()
    
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const refreshServices = async () => {
  try {
    await refreshServicesData()
    ElMessage.success('服务状态已刷新')
  } catch (error) {
    ElMessage.error('刷新服务状态失败')
  }
}

const exportReport = () => {
  // 导出系统监控报告
  const report = {
    timestamp: new Date().toISOString(),
    systemStatus: systemStatus.value,
    services: services.value,
    logs: logs.value.slice(-100) // 最近100条日志
  }
  
  const dataStr = JSON.stringify(report, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  
  const link = document.createElement('a')
  link.href = URL.createObjectURL(dataBlob)
  link.download = `system-monitor-report-${Date.now()}.json`
  link.click()
  
  ElMessage.success('报告已导出')
}

const viewServiceLogs = (service: any) => {
  selectedService.value = service
  showServiceLogs.value = true
}

const toggleService = async (service: any) => {
  try {
    const action = service.status === 'running' ? '停止' : '启动'
    await ElMessageBox.confirm(
      `确定要${action}服务 "${service.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await toggleServiceStatus(service.id)
    ElMessage.success(`服务已${action}`)
  } catch (error) {
    // 用户取消操作
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空系统日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await clearSystemLogs()
    ElMessage.success('日志已清空')
  } catch (error) {
    // 用户取消操作
  }
}

const getServiceStatusType = (status: string) => {
  const types = {
    running: 'success',
    stopped: 'danger',
    starting: 'warning',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getServiceStatusText = (status: string) => {
  const texts = {
    running: '运行中',
    stopped: '已停止',
    starting: '启动中',
    error: '错误'
  }
  return texts[status] || '未知'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const initCharts = () => {
  // 这里应该使用图表库（如ECharts）初始化图表
  // 暂时用占位符
  if (performanceChart.value) {
    performanceChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #909399;">系统性能趋势图表</div>'
  }
  
  if (requestChart.value) {
    requestChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #909399;">请求量统计图表</div>'
  }
  
  if (errorChart.value) {
    errorChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #909399;">错误率分析图表</div>'
  }
  
  if (responseTimeChart.value) {
    responseTimeChart.value.innerHTML = '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #909399;">响应时间分布图表</div>'
  }
}

// 定时刷新
let refreshInterval: number

// 生命周期
onMounted(async () => {
  await refreshData()
  
  // 设置定时刷新（每30秒）
  refreshInterval = window.setInterval(() => {
    refreshSystemStatus()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.system-monitor {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.status-overview {
  margin-bottom: 24px;
}

.status-card {
  height: 120px;
}

.status-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.status-icon.healthy {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.status-icon.performance {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.status-icon.active {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.status-icon.requests {
  background: linear-gradient(135deg, #909399, #a6a9ad);
}

.status-info h3 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #606266;
}

.status-value {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.status-desc {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.monitor-charts {
  margin-bottom: 24px;
}

.chart-container {
  height: 300px;
  background: #fafafa;
  border-radius: 4px;
}

.services-status,
.system-logs {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.log-container {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-entry {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.log-time {
  color: #888;
  min-width: 160px;
}

.log-level {
  min-width: 60px;
  font-weight: bold;
}

.log-service {
  min-width: 100px;
  color: #66b1ff;
}

.log-message {
  flex: 1;
  color: #e4e7ed;
}

.log-error .log-level {
  color: #f56c6c;
}

.log-warning .log-level {
  color: #e6a23c;
}

.log-info .log-level {
  color: #67c23a;
}
</style>
