/**
 * 用户管理API
 */

import { request } from '@/utils/request'
import type {
  PaginationParams,
  PaginationResponse,
  UserListItem,
  UserDetail,
  UserCreateRequest,
  UserUpdateRequest,
  PasswordResetRequest,
  RoleAssignRequest,
  IDResponse,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types'

/**
 * 获取用户列表
 */
export function getUserList(params: PaginationParams) {
  return request.get<PaginationResponse<UserListItem>>('/api/v1/users', { params })
}

/**
 * 获取用户详情
 */
export function getUserDetail(id: number) {
  return request.get<UserDetail>(`/api/v1/users/${id}`)
}

/**
 * 创建用户
 */
export function createUser(data: UserCreateRequest) {
  return request.post<IDResponse>('/api/v1/users', data)
}

/**
 * 更新用户
 */
export function updateUser(id: number, data: UserUpdateRequest) {
  return request.put(`/api/v1/users/${id}`, data)
}

/**
 * 删除用户
 */
export function deleteUser(id: number) {
  return request.delete(`/api/v1/users/${id}`)
}

/**
 * 重置用户密码
 */
export function resetUserPassword(id: number, data: PasswordResetRequest) {
  return request.put(`/api/v1/users/${id}/password`, data)
}

/**
 * 分配用户角色
 */
export function assignUserRoles(id: number, data: RoleAssignRequest) {
  return request.post(`/api/v1/users/${id}/roles`, data)
}

/**
 * 切换用户状态
 */
export function toggleUserStatus(id: number) {
  return request.put(`/api/v1/users/${id}/status`)
}

/**
 * 批量删除用户
 */
export function bulkDeleteUsers(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/users/bulk-delete', data)
}

/**
 * 获取用户选项列表（用于下拉选择）
 */
export function getUserOptions() {
  return request.get<UserListItem[]>('/api/v1/users/options')
}
