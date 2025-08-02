import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 系统统计数据
export interface SystemStats {
  agentCount: number
  knowledgeCount: number
  todayChats: number
  onlineUsers: number
  systemStatus: {
    api: 'healthy' | 'error'
    database: 'healthy' | 'error'
    redis: 'healthy' | 'error'
    vector_db: 'healthy' | 'error'
  }
}

// 系统信息
export interface SystemInfo {
  version: string
  environment: string
  uptime: number
  timestamp: number
}

// 系统API接口
export const systemApi = {
  // 获取系统健康状态
  getHealth: (): Promise<ApiResponse<SystemInfo>> => {
    return request({
      url: API_PATHS.SYSTEM.HEALTH,
      method: 'get'
    })
  },

  // 获取系统统计数据
  getStats: (): Promise<ApiResponse<SystemStats>> => {
    return request({
      url: API_PATHS.SYSTEM.STATS,
      method: 'get'
    })
  },

  // 获取系统信息
  getInfo: (): Promise<ApiResponse<SystemInfo>> => {
    return request({
      url: API_PATHS.SYSTEM.INFO,
      method: 'get'
    })
  }
}
