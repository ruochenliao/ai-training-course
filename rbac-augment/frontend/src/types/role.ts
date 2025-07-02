/**
 * 角色相关类型定义
 */

// 角色基础信息
export interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

// 角色列表项
export interface RoleListItem extends Role {
  user_count: number
  permission_count: number
}

// 角色详情
export interface RoleDetail extends Role {
  permissions: Permission[]
  menus: Menu[]
  user_count: number
}

// 角色创建请求
export interface RoleCreateRequest {
  name: string
  code: string
  description?: string
  is_active?: boolean
  sort_order?: number
  permission_ids?: number[]
  menu_ids?: number[]
}

// 角色更新请求
export interface RoleUpdateRequest {
  name?: string
  description?: string
  is_active?: boolean
  sort_order?: number
  permission_ids?: number[]
  menu_ids?: number[]
}

// 权限分配请求
export interface PermissionAssignRequest {
  permission_ids: number[]
}

// 菜单分配请求
export interface MenuAssignRequest {
  menu_ids: number[]
}

// 角色选择选项
export interface RoleSelectOption {
  id: number
  name: string
  code: string
  is_active: boolean
}

// 权限信息
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

// 菜单信息
export interface Menu {
  id: number
  name: string
  title: string
  path?: string
  component?: string
  icon?: string
  parent_id?: number
  sort_order: number
  is_visible: boolean
  is_external: boolean
  cache: boolean
  redirect?: string
  created_at: string
  updated_at: string
}
