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
 * 更新角色状态
 */
export function updateRoleStatus(id: number, data: { is_active: boolean }) {
  return request.patch(`/api/v1/roles/${id}/status`, data)
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
  return request.get<RoleSelectOption[]>('/api/v1/roles/options')
}

/**
 * 批量删除角色
 */
export function bulkDeleteRoles(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/roles/bulk-delete', data)
}

/**
 * 获取角色权限
 */
export function getRolePermissions(id: number) {
  return request.get<{ permission_ids: number[] }>(`/api/v1/roles/${id}/permissions`)
}

/**
 * 获取角色菜单
 */
export function getRoleMenus(id: number) {
  return request.get<{ menu_ids: number[] }>(`/api/v1/roles/${id}/menus`)
}

/**
 * 获取角色关联的用户列表
 */
export function getRoleUsers(id: number) {
  return request.get<{ data: any[] }>(`/api/v1/roles/${id}/users`)
}
