import {request} from './index'
import type {ApiResponse, PaginatedResponse} from '@/types/api'

// 审计日志接口类型定义
export interface AuditLog {
  id: number
  user_id: number
  username: string
  module: string
  method: string
  summary: string
  path: string
  request_args: any
  status: number
  response_body: any
  response_time: number
  created_at: string
  updated_at: string
}

export interface AuditLogQueryParams {
  page?: number
  page_size?: number
  username?: string
  module?: string
  method?: string
  summary?: string
  status?: number
  start_time?: string
  end_time?: string
}

// 审计日志管理API
export const auditLogApi = {
  // 获取审计日志列表
  list: (params?: AuditLogQueryParams): Promise<ApiResponse<PaginatedResponse<AuditLog>>> => {
    return request.get('/api/v1/auditlog/list', { params })
  },
}