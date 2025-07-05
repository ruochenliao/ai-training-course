/**
 * 审计日志API
 */

import { request } from '@/utils/request'
import type { ApiResponse, PaginationParams, PaginationResponse } from '@/types/api'

// 审计日志相关类型定义
export interface AuditLogItem {
  id: number
  action: string
  resource_type: string
  resource_id?: string
  resource_name?: string
  description: string
  status: 'success' | 'failed' | 'pending'
  level: 'low' | 'medium' | 'high' | 'critical'
  user_id?: number
  username?: string
  user_ip?: string
  user_agent?: string
  request_method?: string
  request_url?: string
  request_params?: Record<string, any>
  response_status?: number
  response_time?: number
  old_values?: Record<string, any>
  new_values?: Record<string, any>
  created_at: string
}

export interface AuditLogSearchParams extends PaginationParams {
  action?: string
  resource?: string
  user_id?: number
  level?: string
  result?: string
  start_time?: string
  end_time?: string
  ip_address?: string
}

export interface AuditLogStats {
  total_logs: number
  level_stats: {
    low: number
    medium: number
    high: number
    critical: number
  }
  result_stats: {
    success: number
    failure: number
  }
  action_stats: Array<{
    action: string
    count: number
  }>
  user_stats: Array<{
    user_id: number
    username: string
    count: number
  }>
  high_risk_count: number
  time_range: {
    start_time: string
    end_time: string
    days: number
  }
}

/**
 * 获取审计日志列表
 */
export function getAuditLogList(params: AuditLogSearchParams): Promise<ApiResponse<PaginationResponse<AuditLogItem>>> {
  return request.get('/api/v1/audit-logs', { params })
}

/**
 * 获取审计日志详情
 */
export function getAuditLogDetail(id: number): Promise<ApiResponse<AuditLogItem>> {
  return request.get(`/api/v1/audit-logs/${id}`)
}

/**
 * 获取审计日志统计信息
 */
export function getAuditLogStats(days: number = 7): Promise<ApiResponse<AuditLogStats>> {
  return request.get('/api/v1/audit-logs/stats', { params: { days } })
}

/**
 * 清理过期审计日志
 */
export function cleanupAuditLogs(days: number = 90): Promise<ApiResponse<{ deleted_count: number; cleanup_time: string }>> {
  return request.delete('/api/v1/audit-logs/cleanup', { params: { days } })
}

/**
 * 导出审计日志为CSV
 */
export function exportAuditLogsCSV(params: {
  start_time?: string
  end_time?: string
}): Promise<Blob> {
  return request.get('/api/v1/audit-logs/export/csv', {
    params,
    responseType: 'blob'
  })
}

// 审计级别选项
export const AUDIT_LEVEL_OPTIONS = [
  { label: '低', value: 'low', color: '#67C23A' },
  { label: '中', value: 'medium', color: '#E6A23C' },
  { label: '高', value: 'high', color: '#F56C6C' },
  { label: '严重', value: 'critical', color: '#F56C6C' }
]

// 操作结果选项
export const AUDIT_RESULT_OPTIONS = [
  { label: '成功', value: 'success', color: '#67C23A' },
  { label: '失败', value: 'failed', color: '#F56C6C' }
]

// 常见操作类型
export const AUDIT_ACTION_OPTIONS = [
  { label: '用户登录', value: 'user:login' },
  { label: '用户登出', value: 'user:logout' },
  { label: '创建用户', value: 'user:create' },
  { label: '更新用户', value: 'user:update' },
  { label: '删除用户', value: 'user:delete' },
  { label: '创建角色', value: 'role:create' },
  { label: '更新角色', value: 'role:update' },
  { label: '删除角色', value: 'role:delete' },
  { label: '分配权限', value: 'permission:assign' },
  { label: '撤销权限', value: 'permission:revoke' },
  { label: '创建部门', value: 'department:create' },
  { label: '更新部门', value: 'department:update' },
  { label: '删除部门', value: 'department:delete' }
]

// 资源类型选项
export const AUDIT_RESOURCE_OPTIONS = [
  { label: '用户', value: 'user' },
  { label: '角色', value: 'role' },
  { label: '权限', value: 'permission' },
  { label: '菜单', value: 'menu' },
  { label: '部门', value: 'department' },
  { label: '数据权限', value: 'data_permission' }
]

/**
 * 获取审计级别颜色
 */
export function getAuditLevelColor(level: string): string {
  const option = AUDIT_LEVEL_OPTIONS.find(opt => opt.value === level)
  return option?.color || '#909399'
}

/**
 * 获取审计级别文本
 */
export function getAuditLevelText(level: string): string {
  const option = AUDIT_LEVEL_OPTIONS.find(opt => opt.value === level)
  return option?.label || level
}

/**
 * 获取操作结果颜色
 */
export function getAuditResultColor(result: string): string {
  const option = AUDIT_RESULT_OPTIONS.find(opt => opt.value === result)
  return option?.color || '#909399'
}

/**
 * 获取操作结果文本
 */
export function getAuditResultText(result: string): string {
  const option = AUDIT_RESULT_OPTIONS.find(opt => opt.value === result)
  return option?.label || result
}

/**
 * 格式化操作描述
 */
export function formatActionDescription(action: string): string {
  const option = AUDIT_ACTION_OPTIONS.find(opt => opt.value === action)
  return option?.label || action
}

/**
 * 格式化资源类型
 */
export function formatResourceType(resourceType: string): string {
  const option = AUDIT_RESOURCE_OPTIONS.find(opt => opt.value === resourceType)
  return option?.label || resourceType
}
