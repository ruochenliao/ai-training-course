/**
 * 数据权限相关类型定义
 */

export enum DataPermissionType {
  ALL = 'all',
  SELF = 'self', 
  DEPARTMENT = 'department',
  DEPARTMENT_AND_SUB = 'department_and_sub',
  CUSTOM = 'custom'
}

export enum DataPermissionScope {
  USER = 'user',
  DEPARTMENT = 'department', 
  ROLE = 'role',
  CUSTOM = 'custom'
}

export interface DataPermission {
  id: number
  name: string
  code: string
  description?: string
  permission_type: DataPermissionType
  scope: DataPermissionScope
  resource_type: string
  custom_conditions?: Record<string, any>
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface DataPermissionCreateRequest {
  name: string
  code: string
  description?: string
  permission_type: DataPermissionType
  scope: DataPermissionScope
  resource_type: string
  custom_conditions?: Record<string, any>
  is_active?: boolean
  sort_order?: number
}

export interface DataPermissionUpdateRequest {
  name?: string
  code?: string
  description?: string
  permission_type?: DataPermissionType
  scope?: DataPermissionScope
  resource_type?: string
  custom_conditions?: Record<string, any>
  is_active?: boolean
  sort_order?: number
}

export interface DataPermissionListItem {
  id: number
  name: string
  code: string
  permission_type: DataPermissionType
  scope: DataPermissionScope
  resource_type: string
  is_active: boolean
  sort_order: number
  created_at: string
}

export interface DataPermissionListResponse {
  items: DataPermissionListItem[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DataPermissionSearchParams {
  keyword?: string
  permission_type?: DataPermissionType
  scope?: DataPermissionScope
  resource_type?: string
  is_active?: boolean
}

export interface DataPermissionAssignRequest {
  user_ids?: number[]
  role_ids?: number[]
}

export interface DataPermissionCheckRequest {
  user_id: number
  resource_type: string
  resource_id?: number
  action: string
  extra_params?: Record<string, any>
}

export interface DataPermissionCheckResponse {
  has_permission: boolean
  permission_type?: DataPermissionType
  reason?: string
}

export interface BulkOperationRequest {
  ids: number[]
  action: string
}

export interface BulkOperationResponse {
  success_count: number
  failed_count: number
  errors: string[]
}

// 数据权限类型选项
export const DATA_PERMISSION_TYPE_OPTIONS = [
  { label: '全部数据', value: DataPermissionType.ALL },
  { label: '仅本人数据', value: DataPermissionType.SELF },
  { label: '本部门数据', value: DataPermissionType.DEPARTMENT },
  { label: '本部门及子部门数据', value: DataPermissionType.DEPARTMENT_AND_SUB },
  { label: '自定义数据范围', value: DataPermissionType.CUSTOM }
]

// 数据权限范围选项
export const DATA_PERMISSION_SCOPE_OPTIONS = [
  { label: '用户数据', value: DataPermissionScope.USER },
  { label: '部门数据', value: DataPermissionScope.DEPARTMENT },
  { label: '角色数据', value: DataPermissionScope.ROLE },
  { label: '自定义数据', value: DataPermissionScope.CUSTOM }
]

// 资源类型选项
export const RESOURCE_TYPE_OPTIONS = [
  { label: '用户', value: 'user' },
  { label: '部门', value: 'department' },
  { label: '角色', value: 'role' },
  { label: '权限', value: 'permission' },
  { label: '菜单', value: 'menu' },
  { label: '文档', value: 'document' },
  { label: '报表', value: 'report' },
  { label: '自定义', value: 'custom' }
]
