/**
 * 权限相关类型定义
 */

// 权限基础信息
export interface Permission {
  id: number
  name: string
  code: string
  description?: string
  resource: string
  action: string
  parent_id?: number
  sort_order: number
  created_at: string
  updated_at: string
}

// 权限列表项
export interface PermissionListItem extends Permission {
  parent_name?: string
  role_count: number
}

// 权限树节点
export interface PermissionTreeNode extends Permission {
  children: PermissionTreeNode[]
}

// 权限创建请求
export interface PermissionCreateRequest {
  name: string
  code: string
  description?: string
  resource: string
  action: string
  parent_id?: number
  sort_order?: number
}

// 权限更新请求
export interface PermissionUpdateRequest {
  name?: string
  description?: string
  parent_id?: number
  sort_order?: number
}

// 权限选择选项
export interface PermissionSelectOption {
  id: number
  name: string
  code: string
  resource: string
  action: string
}

// 权限分组
export interface PermissionGroup {
  resource: string
  permissions: Permission[]
}
