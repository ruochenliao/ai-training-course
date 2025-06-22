import {defineStore} from 'pinia'
import axios from 'axios'

interface SystemMetrics {
  system: {
    status: string
    onlineUsers: number
    activeSessions: number
    uptime: string
  }
  cpu: number
  memory: number
  requests: number
  responseTime: number
  services: ServiceStatus[]
  databases: DatabaseStatus[]
}

interface ServiceStatus {
  name: string
  description: string
  status: 'healthy' | 'warning' | 'error'
  responseTime: number
  lastCheck: string
}

interface DatabaseStatus {
  name: string
  status: 'connected' | 'disconnected'
  connections: number
  qps: number
  latency: number
}

interface ErrorLog {
  id: string
  timestamp: string
  level: 'error' | 'warning' | 'info'
  service: string
  message: string
  stack?: string
  metadata?: any
}

interface SystemConfig {
  llm: {
    provider: string
    model: string
    apiKey: string
    maxTokens: number
    temperature: number
  }
  embedding: {
    provider: string
    model: string
    apiKey: string
    dimensions: number
  }
  reranker: {
    provider: string
    model: string
    apiKey: string
  }
  storage: {
    vectorDb: {
      host: string
      port: number
      collection: string
    }
    graphDb: {
      host: string
      port: number
      database: string
    }
    fileStorage: {
      endpoint: string
      bucket: string
    }
  }
}

export const useSystemStore = defineStore('system', {
  state: () => ({
    metrics: null as SystemMetrics | null,
    errors: [] as ErrorLog[],
    config: null as SystemConfig | null,
    loading: false,
    error: null as string | null
  }),

  getters: {
    systemHealth: (state) => {
      if (!state.metrics) return 'unknown'
      
      const { services } = state.metrics
      const healthyServices = services.filter(s => s.status === 'healthy').length
      const totalServices = services.length
      
      if (healthyServices === totalServices) return 'healthy'
      if (healthyServices / totalServices >= 0.8) return 'warning'
      return 'error'
    },

    criticalErrors: (state) => {
      return state.errors.filter(error => error.level === 'error')
    },

    recentErrors: (state) => {
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
      return state.errors.filter(error => new Date(error.timestamp) > oneHourAgo)
    }
  },

  actions: {
    // 获取系统指标
    async getMetrics(): Promise<SystemMetrics> {
      try {
        const response = await axios.get('/api/v1/system/metrics')
        this.metrics = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取系统指标失败'
        throw error
      }
    },

    // 获取错误日志
    async getErrors(params?: { level?: string; service?: string; limit?: number }) {
      try {
        const response = await axios.get('/api/v1/system/errors', { params })
        this.errors = response.data.items || []
        return this.errors
      } catch (error) {
        this.error = error.response?.data?.message || '获取错误日志失败'
        throw error
      }
    },

    // 获取系统配置
    async getConfig() {
      try {
        const response = await axios.get('/api/v1/system/config')
        this.config = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取系统配置失败'
        throw error
      }
    },

    // 更新系统配置
    async updateConfig(config: Partial<SystemConfig>) {
      try {
        const response = await axios.put('/api/v1/system/config', config)
        this.config = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '更新系统配置失败'
        throw error
      }
    },

    // 测试服务连接
    async testService(serviceName: string) {
      try {
        const response = await axios.post(`/api/v1/system/test/${serviceName}`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '测试服务连接失败'
        throw error
      }
    },

    // 重启服务
    async restartService(serviceName: string) {
      try {
        const response = await axios.post(`/api/v1/system/restart/${serviceName}`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '重启服务失败'
        throw error
      }
    },

    // 获取系统日志
    async getLogs(params?: { 
      level?: string
      service?: string
      startTime?: string
      endTime?: string
      limit?: number
    }) {
      try {
        const response = await axios.get('/api/v1/system/logs', { params })
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '获取系统日志失败'
        throw error
      }
    },

    // 导出日志
    async exportLogs(params?: {
      level?: string
      service?: string
      startTime?: string
      endTime?: string
    }) {
      try {
        const response = await axios.get('/api/v1/system/logs/export', {
          params,
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `system-logs-${Date.now()}.zip`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '导出日志失败'
        throw error
      }
    },

    // 清理日志
    async cleanupLogs(olderThan: string) {
      try {
        const response = await axios.post('/api/v1/system/logs/cleanup', { olderThan })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '清理日志失败'
        throw error
      }
    },

    // 获取系统信息
    async getSystemInfo() {
      try {
        const response = await axios.get('/api/v1/system/info')
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取系统信息失败'
        throw error
      }
    },

    // 获取性能统计
    async getPerformanceStats(timeRange: string = '1h') {
      try {
        const response = await axios.get('/api/v1/system/performance', {
          params: { timeRange }
        })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取性能统计失败'
        throw error
      }
    },

    // 获取资源使用情况
    async getResourceUsage() {
      try {
        const response = await axios.get('/api/v1/system/resources')
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取资源使用情况失败'
        throw error
      }
    },

    // 执行系统维护
    async performMaintenance(tasks: string[]) {
      try {
        const response = await axios.post('/api/v1/system/maintenance', { tasks })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '执行系统维护失败'
        throw error
      }
    },

    // 备份系统
    async backupSystem(options?: { includeData?: boolean; includeConfig?: boolean }) {
      try {
        const response = await axios.post('/api/v1/system/backup', options, {
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `system-backup-${Date.now()}.tar.gz`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '系统备份失败'
        throw error
      }
    },

    // 恢复系统
    async restoreSystem(backupFile: File) {
      try {
        const formData = new FormData()
        formData.append('backup', backupFile)
        
        const response = await axios.post('/api/v1/system/restore', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '系统恢复失败'
        throw error
      }
    },

    // 获取告警规则
    async getAlertRules() {
      try {
        const response = await axios.get('/api/v1/system/alerts/rules')
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '获取告警规则失败'
        throw error
      }
    },

    // 创建告警规则
    async createAlertRule(rule: any) {
      try {
        const response = await axios.post('/api/v1/system/alerts/rules', rule)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '创建告警规则失败'
        throw error
      }
    },

    // 更新告警规则
    async updateAlertRule(id: string, rule: any) {
      try {
        const response = await axios.put(`/api/v1/system/alerts/rules/${id}`, rule)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '更新告警规则失败'
        throw error
      }
    },

    // 删除告警规则
    async deleteAlertRule(id: string) {
      try {
        await axios.delete(`/api/v1/system/alerts/rules/${id}`)
      } catch (error) {
        this.error = error.response?.data?.message || '删除告警规则失败'
        throw error
      }
    },

    // 获取活跃告警
    async getActiveAlerts() {
      try {
        const response = await axios.get('/api/v1/system/alerts/active')
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '获取活跃告警失败'
        throw error
      }
    },

    // 确认告警
    async acknowledgeAlert(id: string) {
      try {
        const response = await axios.post(`/api/v1/system/alerts/${id}/acknowledge`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '确认告警失败'
        throw error
      }
    },

    // 清除错误状态
    clearError() {
      this.error = null
    },

    // 重置状态
    reset() {
      this.metrics = null
      this.errors = []
      this.config = null
      this.loading = false
      this.error = null
    }
  }
})
