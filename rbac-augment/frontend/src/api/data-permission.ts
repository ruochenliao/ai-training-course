/**
 * 数据权限管理API
 */

import request from '@/utils/request'
import type { 
  DataPermission, 
  DataPermissionCreateRequest, 
  DataPermissionUpdateRequest,
  DataPermissionListResponse,
  DataPermissionSearchParams,
  DataPermissionAssignRequest,
  DataPermissionCheckRequest,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types/data-permission'

/**
 * 获取数据权限列表
 */
export function getDataPermissionList(params: DataPermissionSearchParams & { page: number; page_size: number }) {
  return request.get<DataPermissionListResponse>('/api/v1/data-permissions', { params })
}

/**
 * 获取数据权限详情
 */
export function getDataPermissionDetail(id: number) {
  return request.get<DataPermission>(`/api/v1/data-permissions/${id}`)
}

/**
 * 创建数据权限
 */
export function createDataPermission(data: DataPermissionCreateRequest) {
  return request.post<DataPermission>('/api/v1/data-permissions', data)
}

/**
 * 更新数据权限
 */
export function updateDataPermission(id: number, data: DataPermissionUpdateRequest) {
  return request.put<DataPermission>(`/api/v1/data-permissions/${id}`, data)
}

/**
 * 删除数据权限
 */
export function deleteDataPermission(id: number) {
  return request.delete(`/api/v1/data-permissions/${id}`)
}

/**
 * 批量删除数据权限
 */
export function bulkDeleteDataPermissions(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/data-permissions/bulk-delete', data)
}

/**
 * 获取数据权限选项
 */
export function getDataPermissionOptions() {
  return request.get<DataPermission[]>('/api/v1/data-permissions/options')
}

/**
 * 分配数据权限给用户
 */
export function assignDataPermissionToUsers(id: number, data: DataPermissionAssignRequest) {
  return request.post(`/api/v1/data-permissions/${id}/assign-users`, data)
}

/**
 * 分配数据权限给角色
 */
export function assignDataPermissionToRoles(id: number, data: DataPermissionAssignRequest) {
  return request.post(`/api/v1/data-permissions/${id}/assign-roles`, data)
}

/**
 * 检查数据权限
 */
export function checkDataPermission(data: DataPermissionCheckRequest) {
  return request.post('/api/v1/data-permissions/check', data)
}

/**
 * 分配数据权限（通用函数）
 */
export function assignDataPermission(id: number, data: DataPermissionAssignRequest) {
  return request.post(`/api/v1/data-permissions/${id}/assign`, data)
}
