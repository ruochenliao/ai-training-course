/**
 * 部门管理API
 */

import { request } from '@/utils/request'
import type {
  PaginationParams,
  PaginationResponse,
  DepartmentListItem,
  DepartmentDetail,
  DepartmentCreateRequest,
  DepartmentUpdateRequest,
  DepartmentTreeNode,
  DepartmentMoveRequest,
  DepartmentUserAssignRequest,
  DepartmentStatistics,
  DepartmentBatchOperationRequest,
  DepartmentBatchOperationResponse,
  DepartmentImportRequest,
  DepartmentImportResponse,
  IDResponse,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types'

/**
 * 获取部门树结构
 */
export function getDepartmentTree() {
  return request.get<DepartmentTreeNode[]>('/api/v1/departments/tree')
}

/**
 * 获取部门列表
 */
export function getDepartmentList(params: PaginationParams) {
  return request.get<PaginationResponse<DepartmentListItem>>('/api/v1/departments', { params })
}

/**
 * 获取部门详情
 */
export function getDepartmentDetail(id: number) {
  return request.get<DepartmentDetail>(`/api/v1/departments/${id}`)
}

/**
 * 创建部门
 */
export function createDepartment(data: DepartmentCreateRequest) {
  return request.post<IDResponse>('/api/v1/departments', data)
}

/**
 * 更新部门
 */
export function updateDepartment(id: number, data: DepartmentUpdateRequest) {
  return request.put(`/api/v1/departments/${id}`, data)
}

/**
 * 更新部门状态
 */
export function updateDepartmentStatus(id: number, data: { is_active: boolean }) {
  return request.patch(`/api/v1/departments/${id}/status`, data)
}

/**
 * 删除部门
 */
export function deleteDepartment(id: number) {
  return request.delete(`/api/v1/departments/${id}`)
}

/**
 * 移动部门
 */
export function moveDepartment(id: number, data: DepartmentMoveRequest) {
  return request.put(`/api/v1/departments/${id}/move`, data)
}

/**
 * 获取部门用户列表
 */
export function getDepartmentUsers(id: number, params?: PaginationParams) {
  return request.get<PaginationResponse<any>>(`/api/v1/departments/${id}/users`, { params })
}

/**
 * 分配用户到部门
 */
export function assignUsersToDepartment(id: number, data: DepartmentUserAssignRequest) {
  return request.post(`/api/v1/departments/${id}/users`, data)
}

/**
 * 从部门移除用户
 */
export function removeUsersFromDepartment(id: number, data: { user_ids: number[] }) {
  return request.delete(`/api/v1/departments/${id}/users`, { data })
}

/**
 * 获取部门统计信息
 */
export function getDepartmentStatistics(id: number) {
  return request.get<DepartmentStatistics>(`/api/v1/departments/${id}/statistics`)
}

/**
 * 批量操作部门
 */
export function batchOperateDepartments(data: DepartmentBatchOperationRequest) {
  return request.post<DepartmentBatchOperationResponse>('/api/v1/departments/batch', data)
}

/**
 * 导入部门数据
 */
export function importDepartments(data: DepartmentImportRequest) {
  return request.post<DepartmentImportResponse>('/api/v1/departments/import', data)
}

/**
 * 导出部门数据
 */
export function exportDepartments(params?: any) {
  return request.get('/api/v1/departments/export', { 
    params,
    responseType: 'blob'
  })
}

/**
 * 获取部门选择选项
 */
export function getDepartmentOptions() {
  return request.get<Array<{ id: number; name: string; parent_id?: number }>>('/api/v1/departments/options')
}

/**
 * 批量删除部门
 */
export function bulkDeleteDepartments(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/departments/bulk-delete', data)
}

/**
 * 获取部门员工列表（别名函数）
 */
export function getDepartmentEmployees(id: number, params?: PaginationParams) {
  return getDepartmentUsers(id, params)
}
