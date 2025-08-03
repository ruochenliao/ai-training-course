<template>
  <div class="service-logs">
    <div class="log-controls">
      <div class="control-group">
        <el-select v-model="logLevel" size="small" style="width: 120px;">
          <el-option label="全部" value="all" />
          <el-option label="错误" value="error" />
          <el-option label="警告" value="warning" />
          <el-option label="信息" value="info" />
          <el-option label="调试" value="debug" />
        </el-select>
        
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索日志内容"
          size="small"
          style="width: 200px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="control-group">
        <el-switch 
          v-model="autoRefresh" 
          active-text="自动刷新"
          @change="toggleAutoRefresh"
        />
        
        <el-button size="small" @click="refreshLogs" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-button size="small" @click="downloadLogs">
          <el-icon><Download /></el-icon>
          下载
        </el-button>
        
        <el-button size="small" @click="clearLogs">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div class="log-stats">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-item">
            <span class="stat-label">总计:</span>
            <span class="stat-value">{{ totalLogs }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item error">
            <span class="stat-label">错误:</span>
            <span class="stat-value">{{ errorLogs }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item warning">
            <span class="stat-label">警告:</span>
            <span class="stat-value">{{ warningLogs }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item info">
            <span class="stat-label">信息:</span>
            <span class="stat-value">{{ infoLogs }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="log-container" ref="logContainer">
      <div 
        v-for="log in filteredLogs" 
        :key="log.id"
        class="log-entry"
        :class="`log-${log.level}`"
        @click="selectLog(log)"
      >
        <div class="log-main">
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">{{ log.level.toUpperCase() }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        
        <div v-if="log.details && selectedLogId === log.id" class="log-details">
          <pre>{{ JSON.stringify(log.details, null, 2) }}</pre>
        </div>
        
        <div v-if="log.userId || log.ip" class="log-meta">
          <span v-if="log.userId" class="meta-item">用户: {{ log.userId }}</span>
          <span v-if="log.ip" class="meta-item">IP: {{ log.ip }}</span>
        </div>
      </div>
      
      <div v-if="filteredLogs.length === 0" class="empty-logs">
        <el-empty description="暂无日志数据" />
      </div>
    </div>

    <div class="log-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[50, 100, 200, 500]"
        :total="filteredLogs.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Download, Delete } from '@element-plus/icons-vue'
import { useSystemMonitor } from '@/composables/useSystemMonitor'
import type { Service, SystemLog } from '@/composables/useSystemMonitor'

// Props
interface Props {
  service: Service
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(false)
const autoRefresh = ref(false)
const logLevel = ref('all')
const searchKeyword = ref('')
const selectedLogId = ref('')
const currentPage = ref(1)
const pageSize = ref(100)

const logContainer = ref<HTMLElement>()
const logs = ref<SystemLog[]>([])
let refreshInterval: number | null = null

// 使用系统监控组合式函数
const { getServiceLogs, addSystemLog } = useSystemMonitor()

// 计算属性
const filteredLogs = computed(() => {
  let result = logs.value

  // 按日志级别过滤
  if (logLevel.value !== 'all') {
    result = result.filter(log => log.level === logLevel.value)
  }

  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(keyword) ||
      (log.details && JSON.stringify(log.details).toLowerCase().includes(keyword))
    )
  }

  return result
})

const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredLogs.value.slice(start, end)
})

const totalLogs = computed(() => logs.value.length)
const errorLogs = computed(() => logs.value.filter(log => log.level === 'error').length)
const warningLogs = computed(() => logs.value.filter(log => log.level === 'warning').length)
const infoLogs = computed(() => logs.value.filter(log => log.level === 'info').length)

// 方法
const refreshLogs = async () => {
  loading.value = true
  try {
    const serviceLogs = await getServiceLogs(props.service.id, 1000)
    logs.value = serviceLogs
    
    // 滚动到底部显示最新日志
    await nextTick()
    scrollToBottom()
    
  } catch (error) {
    ElMessage.error('刷新日志失败')
  } finally {
    loading.value = false
  }
}

const toggleAutoRefresh = (enabled: boolean) => {
  if (enabled) {
    refreshInterval = window.setInterval(refreshLogs, 5000) // 每5秒刷新
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
}

const selectLog = (log: SystemLog) => {
  selectedLogId.value = selectedLogId.value === log.id ? '' : log.id
}

const downloadLogs = () => {
  const logData = filteredLogs.value.map(log => ({
    timestamp: log.timestamp,
    level: log.level,
    message: log.message,
    details: log.details,
    userId: log.userId,
    ip: log.ip
  }))
  
  const dataStr = JSON.stringify(logData, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  
  const link = document.createElement('a')
  link.href = URL.createObjectURL(dataBlob)
  link.download = `${props.service.name}-logs-${Date.now()}.json`
  link.click()
  
  ElMessage.success('日志已下载')
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清空服务 "${props.service.name}" 的日志吗？此操作不可恢复。`,
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    logs.value = []
    
    addSystemLog({
      level: 'info',
      service: props.service.name,
      message: '服务日志已清空'
    })
    
    ElMessage.success('日志已清空')
  } catch (error) {
    // 用户取消操作
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })
}

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

// 生命周期
onMounted(async () => {
  await refreshLogs()
  
  // 模拟生成一些服务日志
  generateSampleLogs()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

// 生成示例日志数据
const generateSampleLogs = () => {
  const sampleLogs: SystemLog[] = [
    {
      id: 'log_1',
      timestamp: new Date(Date.now() - 1000 * 60 * 1).toISOString(),
      level: 'info',
      service: props.service.name,
      message: '服务启动完成',
      details: { port: props.service.port, version: props.service.version }
    },
    {
      id: 'log_2',
      timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
      level: 'info',
      service: props.service.name,
      message: '处理HTTP请求',
      details: { method: 'GET', path: '/api/users', responseTime: 125 },
      ip: '192.168.1.100'
    },
    {
      id: 'log_3',
      timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
      level: 'warning',
      service: props.service.name,
      message: '响应时间较长',
      details: { responseTime: 2500, threshold: 2000 }
    },
    {
      id: 'log_4',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      level: 'error',
      service: props.service.name,
      message: '数据库连接失败',
      details: { error: 'Connection timeout', retryCount: 3 }
    },
    {
      id: 'log_5',
      timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      level: 'info',
      service: props.service.name,
      message: '缓存更新完成',
      details: { cacheKey: 'user_sessions', size: 1024 }
    }
  ]
  
  logs.value = [...sampleLogs, ...logs.value]
}
</script>

<style scoped>
.service-logs {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.log-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.control-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.log-stats {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  background: white;
}

.stat-item.error {
  border-left: 3px solid #f56c6c;
}

.stat-item.warning {
  border-left: 3px solid #e6a23c;
}

.stat-item.info {
  border-left: 3px solid #409eff;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.stat-value {
  font-weight: bold;
  color: #303133;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  margin-bottom: 16px;
}

.log-entry {
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.log-entry:hover {
  background: rgba(255, 255, 255, 0.05);
}

.log-main {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.log-time {
  color: #888;
  min-width: 180px;
  font-size: 11px;
}

.log-level {
  min-width: 60px;
  font-weight: bold;
  font-size: 11px;
}

.log-message {
  flex: 1;
  color: #e4e7ed;
  line-height: 1.4;
}

.log-details {
  margin-top: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.log-details pre {
  margin: 0;
  color: #66b1ff;
  font-size: 11px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-meta {
  margin-top: 4px;
  display: flex;
  gap: 16px;
}

.meta-item {
  font-size: 10px;
  color: #909399;
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

.log-debug .log-level {
  color: #909399;
}

.empty-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #909399;
}

.log-pagination {
  display: flex;
  justify-content: center;
}
</style>
