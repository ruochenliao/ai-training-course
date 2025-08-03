/**
 * 系统监控组合式函数
 */

import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '@/api/system'

export interface SystemStatus {
  overall: string
  uptime: string
  performance: number
  cpu: number
  memory: number
  disk: number
  activeUsers: number
  onlineUsers: number
  todayUsers: number
  requestsPerSecond: number
  successRate: number
  errorRate: number
  avgResponseTime: number
}

export interface Service {
  id: string
  name: string
  status: 'running' | 'stopped' | 'starting' | 'error'
  version: string
  uptime: string
  cpu: number
  memory: number
  requests: number
  errors: number
  lastRestart: string
  description?: string
  port?: number
  endpoint?: string
}

export interface SystemLog {
  id: string
  timestamp: string
  level: 'error' | 'warning' | 'info' | 'debug'
  service: string
  message: string
  details?: any
  userId?: string
  ip?: string
}

export interface PerformanceMetric {
  timestamp: string
  cpu: number
  memory: number
  disk: number
  network: number
  requests: number
  errors: number
  responseTime: number
}

export function useSystemMonitor() {
  // 响应式数据
  const systemStatus = ref<SystemStatus>({
    overall: '正常',
    uptime: '0天0小时0分钟',
    performance: 85,
    cpu: 45,
    memory: 62,
    disk: 38,
    activeUsers: 156,
    onlineUsers: 23,
    todayUsers: 89,
    requestsPerSecond: 125,
    successRate: 99.2,
    errorRate: 0.8,
    avgResponseTime: 245
  })

  const services = ref<Service[]>([
    {
      id: 'api-server',
      name: 'API服务器',
      status: 'running',
      version: '1.0.0',
      uptime: '5天12小时',
      cpu: 35,
      memory: 58,
      requests: 1250,
      errors: 2,
      lastRestart: '2024-01-15 10:30:00',
      description: '主要API服务',
      port: 8000,
      endpoint: '/api/v1'
    },
    {
      id: 'websocket-server',
      name: 'WebSocket服务',
      status: 'running',
      version: '1.0.0',
      uptime: '5天12小时',
      cpu: 15,
      memory: 32,
      requests: 890,
      errors: 0,
      lastRestart: '2024-01-15 10:30:00',
      description: '实时通信服务',
      port: 8001
    },
    {
      id: 'database',
      name: '数据库服务',
      status: 'running',
      version: '14.5',
      uptime: '15天8小时',
      cpu: 25,
      memory: 75,
      requests: 2340,
      errors: 1,
      lastRestart: '2024-01-05 14:20:00',
      description: 'PostgreSQL数据库',
      port: 5432
    },
    {
      id: 'redis',
      name: 'Redis缓存',
      status: 'running',
      version: '7.0',
      uptime: '15天8小时',
      cpu: 8,
      memory: 28,
      requests: 5670,
      errors: 0,
      lastRestart: '2024-01-05 14:20:00',
      description: 'Redis缓存服务',
      port: 6379
    },
    {
      id: 'ai-service',
      name: 'AI推理服务',
      status: 'running',
      version: '2.1.0',
      uptime: '2天6小时',
      cpu: 65,
      memory: 85,
      requests: 456,
      errors: 3,
      lastRestart: '2024-01-18 08:15:00',
      description: 'AI模型推理服务',
      port: 8002
    }
  ])

  const logs = ref<SystemLog[]>([
    {
      id: 'log_1',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      level: 'info',
      service: 'api-server',
      message: '用户登录成功',
      userId: 'user_123',
      ip: '192.168.1.100'
    },
    {
      id: 'log_2',
      timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
      level: 'warning',
      service: 'ai-service',
      message: 'AI推理响应时间较长: 3.2秒',
      details: { responseTime: 3200, model: 'gpt-4' }
    },
    {
      id: 'log_3',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      level: 'error',
      service: 'database',
      message: '数据库连接超时',
      details: { timeout: 30000, query: 'SELECT * FROM users' }
    },
    {
      id: 'log_4',
      timestamp: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
      level: 'info',
      service: 'websocket-server',
      message: 'WebSocket连接建立',
      userId: 'user_456'
    }
  ])

  const performanceMetrics = ref<PerformanceMetric[]>([])

  // 实时监控状态
  const isMonitoring = ref(false)
  const monitoringInterval = ref<number | null>(null)

  // 方法
  const refreshSystemStatus = async () => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 更新系统状态（模拟数据）
      systemStatus.value = {
        ...systemStatus.value,
        cpu: Math.floor(Math.random() * 30) + 30,
        memory: Math.floor(Math.random() * 20) + 50,
        requestsPerSecond: Math.floor(Math.random() * 50) + 100,
        performance: Math.floor(Math.random() * 20) + 80
      }
      
      // 添加新的性能指标
      const newMetric: PerformanceMetric = {
        timestamp: new Date().toISOString(),
        cpu: systemStatus.value.cpu,
        memory: systemStatus.value.memory,
        disk: systemStatus.value.disk,
        network: Math.floor(Math.random() * 100),
        requests: systemStatus.value.requestsPerSecond,
        errors: Math.floor(Math.random() * 5),
        responseTime: Math.floor(Math.random() * 200) + 200
      }
      
      performanceMetrics.value.push(newMetric)
      
      // 保持最近100个数据点
      if (performanceMetrics.value.length > 100) {
        performanceMetrics.value.shift()
      }
      
    } catch (error) {
      console.error('刷新系统状态失败:', error)
      throw error
    }
  }

  const refreshServices = async () => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 更新服务状态（模拟数据）
      services.value.forEach(service => {
        service.cpu = Math.floor(Math.random() * 30) + 10
        service.memory = Math.floor(Math.random() * 40) + 20
        service.requests = Math.floor(Math.random() * 1000) + 500
      })
      
    } catch (error) {
      console.error('刷新服务状态失败:', error)
      throw error
    }
  }

  const toggleServiceStatus = async (serviceId: string) => {
    try {
      const service = services.value.find(s => s.id === serviceId)
      if (!service) throw new Error('服务不存在')
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 切换服务状态
      if (service.status === 'running') {
        service.status = 'stopped'
        service.cpu = 0
        service.memory = 0
        service.requests = 0
      } else {
        service.status = 'starting'
        
        // 模拟启动过程
        setTimeout(() => {
          service.status = 'running'
          service.lastRestart = new Date().toLocaleString('zh-CN')
        }, 2000)
      }
      
      // 添加日志
      addSystemLog({
        level: 'info',
        service: service.name,
        message: `服务${service.status === 'running' ? '启动' : '停止'}`,
        details: { serviceId, action: service.status }
      })
      
    } catch (error) {
      console.error('切换服务状态失败:', error)
      throw error
    }
  }

  const getServiceLogs = async (serviceId: string, limit: number = 100) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 200))
      
      // 返回指定服务的日志
      return logs.value
        .filter(log => log.service === serviceId || log.service === services.value.find(s => s.id === serviceId)?.name)
        .slice(-limit)
        .reverse()
      
    } catch (error) {
      console.error('获取服务日志失败:', error)
      throw error
    }
  }

  const clearSystemLogs = async () => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 200))
      
      logs.value = []
      
      addSystemLog({
        level: 'info',
        service: 'system',
        message: '系统日志已清空'
      })
      
    } catch (error) {
      console.error('清空系统日志失败:', error)
      throw error
    }
  }

  const addSystemLog = (logData: Partial<SystemLog>) => {
    const log: SystemLog = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      level: logData.level || 'info',
      service: logData.service || 'system',
      message: logData.message || '',
      details: logData.details,
      userId: logData.userId,
      ip: logData.ip
    }
    
    logs.value.unshift(log)
    
    // 保持最近1000条日志
    if (logs.value.length > 1000) {
      logs.value = logs.value.slice(0, 1000)
    }
  }

  const startRealTimeMonitoring = () => {
    if (isMonitoring.value) return
    
    isMonitoring.value = true
    monitoringInterval.value = window.setInterval(async () => {
      try {
        await refreshSystemStatus()
        
        // 随机生成一些日志
        if (Math.random() < 0.3) {
          const levels = ['info', 'warning', 'error'] as const
          const serviceNames = services.value.map(s => s.name)
          const messages = [
            '请求处理完成',
            '缓存命中',
            '数据库查询执行',
            '用户认证成功',
            '文件上传完成',
            '任务队列处理',
            '内存使用率较高',
            '响应时间超过阈值'
          ]
          
          addSystemLog({
            level: levels[Math.floor(Math.random() * levels.length)],
            service: serviceNames[Math.floor(Math.random() * serviceNames.length)],
            message: messages[Math.floor(Math.random() * messages.length)]
          })
        }
        
      } catch (error) {
        console.error('实时监控更新失败:', error)
      }
    }, 5000) // 每5秒更新一次
  }

  const stopRealTimeMonitoring = () => {
    if (!isMonitoring.value) return
    
    isMonitoring.value = false
    if (monitoringInterval.value) {
      clearInterval(monitoringInterval.value)
      monitoringInterval.value = null
    }
  }

  const exportSystemReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      systemStatus: systemStatus.value,
      services: services.value,
      performanceMetrics: performanceMetrics.value.slice(-100),
      recentLogs: logs.value.slice(0, 100)
    }
    
    return report
  }

  const getSystemHealth = () => {
    const healthScore = (
      (100 - systemStatus.value.cpu) * 0.3 +
      (100 - systemStatus.value.memory) * 0.3 +
      systemStatus.value.successRate * 0.4
    )
    
    let status = 'healthy'
    if (healthScore < 60) status = 'critical'
    else if (healthScore < 80) status = 'warning'
    
    return {
      score: Math.round(healthScore),
      status,
      issues: []
    }
  }

  return {
    // 状态
    systemStatus,
    services,
    logs,
    performanceMetrics,
    isMonitoring,

    // 方法
    refreshSystemStatus,
    refreshServices,
    toggleServiceStatus,
    getServiceLogs,
    clearSystemLogs,
    addSystemLog,
    startRealTimeMonitoring,
    stopRealTimeMonitoring,
    exportSystemReport,
    getSystemHealth
  }
}
