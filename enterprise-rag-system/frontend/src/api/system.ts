// 系统管理相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 系统相关类型定义
export interface SystemInfo {
  version: string
  build_time: string
  environment: string
  database_status: string
  redis_status: string
  milvus_status: string
  neo4j_status: string
}

export interface SystemStats {
  total_users: number
  total_knowledge_bases: number
  total_documents: number
  total_conversations: number
  storage_used: number
  api_calls_today: number
  active_users_today: number
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded'
  services: {
    database: boolean
    redis: boolean
    milvus: boolean
    neo4j: boolean
    autogen: boolean
  }
  timestamp: string
}

export interface MonitoringData {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_io: {
    bytes_sent: number
    bytes_recv: number
  }
  api_metrics: {
    requests_per_minute: number
    average_response_time: number
    error_rate: number
  }
  timestamp: string
}

export interface LogEntry {
  id: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  message: string
  module: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface LogQueryParams {
  page?: number
  size?: number
  level?: string
  module?: string
  start_time?: string
  end_time?: string
  search?: string
}

// 系统管理API接口
export const systemApi = {
  // 获取系统信息
  getSystemInfo: (): Promise<ApiResponseData<SystemInfo>> => {
    return httpClient.get('/system/info')
  },

  // 获取系统统计
  getSystemStats: (): Promise<ApiResponseData<SystemStats>> => {
    return httpClient.get('/system/stats')
  },

  // 健康检查
  healthCheck: (): Promise<ApiResponseData<HealthCheck>> => {
    return httpClient.get('/system/health')
  },

  // 获取监控数据
  getMonitoringData: (timeRange?: string): Promise<ApiResponseData<MonitoringData[]>> => {
    return httpClient.get('/monitoring/metrics', {
      params: { time_range: timeRange }
    })
  },

  // 获取实时监控数据
  getRealtimeMonitoring: (): Promise<ApiResponseData<MonitoringData>> => {
    return httpClient.get('/monitoring/realtime')
  },

  // 获取系统日志
  getSystemLogs: (params?: LogQueryParams): Promise<ApiResponseData<LogEntry[]>> => {
    return httpClient.get('/system/logs', { params })
  },

  // 下载系统日志
  downloadLogs: (params?: LogQueryParams): Promise<Blob> => {
    return httpClient.get('/system/logs/download', {
      params,
      responseType: 'blob'
    })
  },

  // 清理系统缓存
  clearCache: (cacheType?: string): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/cache/clear', { cache_type: cacheType })
  },

  // 重建索引
  rebuildIndex: (indexType: string): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/index/rebuild', { index_type: indexType })
  },

  // 数据库优化
  optimizeDatabase: (): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/database/optimize')
  },

  // 备份数据
  backupData: (backupType: 'full' | 'incremental'): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/backup', { backup_type: backupType })
  },

  // 恢复数据
  restoreData: (backupId: string): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/restore', { backup_id: backupId })
  },

  // 获取备份列表
  getBackups: (): Promise<ApiResponseData<any[]>> => {
    return httpClient.get('/system/backups')
  },

  // 系统配置
  getSystemConfig: (): Promise<ApiResponseData<Record<string, any>>> => {
    return httpClient.get('/system/config')
  },

  // 更新系统配置
  updateSystemConfig: (config: Record<string, any>): Promise<ApiResponseData<any>> => {
    return httpClient.put('/system/config', config)
  },

  // 重启服务
  restartService: (serviceName: string): Promise<ApiResponseData<any>> => {
    return httpClient.post('/system/restart', { service: serviceName })
  }
}
