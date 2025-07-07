/**
 * 权限管理API
 */

import { request } from '@/utils/request'
import type {
  PaginationParams,
  PaginationResponse,
  PermissionListItem,
  Permission,
  PermissionTreeNode,
  PermissionCreateRequest,
  PermissionUpdateRequest,
  PermissionSelectOption,
  PermissionGroup,
  IDResponse,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types'

/**
 * 获取权限列表
 */
export function getPermissionList(params: PaginationParams) {
  return request.get<PaginationResponse<PermissionListItem>>('/api/v1/permissions', { params })
}

/**
 * 获取权限树
 */
export function getPermissionTree() {
  return request.get<PermissionTreeNode[]>('/api/v1/permissions/tree')
}

/**
 * 获取权限分组
 */
export function getPermissionGroups() {
  return request.get<PermissionGroup[]>('/api/v1/permissions/groups')
}

/**
 * 获取权限详情
 */
export function getPermissionDetail(id: number) {
  return request.get<Permission>(`/api/v1/permissions/${id}`)
}

/**
 * 创建权限
 */
export function createPermission(data: PermissionCreateRequest) {
  return request.post<IDResponse>('/api/v1/permissions', data)
}

/**
 * 更新权限
 */
export function updatePermission(id: number, data: PermissionUpdateRequest) {
  return request.put(`/api/v1/permissions/${id}`, data)
}

/**
 * 更新权限状态
 */
export function updatePermissionStatus(id: number, data: { is_active: boolean }) {
  return request.patch(`/api/v1/permissions/${id}/status`, data)
}

/**
 * 删除权限
 */
export function deletePermission(id: number) {
  return request.delete(`/api/v1/permissions/${id}`)
}

/**
 * 获取子权限
 */
export function getPermissionChildren(id: number) {
  return request.get<Permission[]>(`/api/v1/permissions/${id}/children`)
}

/**
 * 获取权限选择选项
 */
export function getPermissionOptions() {
  return request.get<PermissionSelectOption[]>('/api/v1/permissions/options/select')
}

/**
 * 根据资源获取权限
 */
export function getPermissionsByResource(resource: string) {
  return request.get<Permission[]>(`/api/v1/permissions/resource/${resource}`)
}

/**
 * 批量删除权限
 */
export function bulkDeletePermissions(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/permissions/bulk-delete', data)
}
