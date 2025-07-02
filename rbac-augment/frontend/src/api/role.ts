/**
 * 角色管理API
 */

import { request } from '@/utils/request'
import type {
  PaginationParams,
  PaginationResponse,
  RoleListItem,
  RoleDetail,
  RoleCreateRequest,
  RoleUpdateRequest,
  PermissionAssignRequest,
  MenuAssignRequest,
  RoleSelectOption,
  IDResponse,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types'

/**
 * 获取角色列表
 */
export function getRoleList(params: PaginationParams) {
  return request.get<PaginationResponse<RoleListItem>>('/api/v1/roles', { params })
}

/**
 * 获取角色详情
 */
export function getRoleDetail(id: number) {
  return request.get<RoleDetail>(`/api/v1/roles/${id}`)
}

/**
 * 创建角色
 */
export function createRole(data: RoleCreateRequest) {
  return request.post<IDResponse>('/api/v1/roles', data)
}

/**
 * 更新角色
 */
export function updateRole(id: number, data: RoleUpdateRequest) {
  return request.put(`/api/v1/roles/${id}`, data)
}

/**
 * 删除角色
 */
export function deleteRole(id: number) {
  return request.delete(`/api/v1/roles/${id}`)
}

/**
 * 分配角色权限
 */
export function assignRolePermissions(id: number, data: PermissionAssignRequest) {
  return request.post(`/api/v1/roles/${id}/permissions`, data)
}

/**
 * 分配角色菜单
 */
export function assignRoleMenus(id: number, data: MenuAssignRequest) {
  return request.post(`/api/v1/roles/${id}/menus`, data)
}

/**
 * 获取角色选择选项
 */
export function getRoleOptions() {
  return request.get<RoleSelectOption[]>('/api/v1/roles/options/select')
}

/**
 * 批量删除角色
 */
export function bulkDeleteRoles(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/roles/bulk-delete', data)
}
