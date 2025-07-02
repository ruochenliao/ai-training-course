/**
 * 用户相关类型定义
 */

// 用户基础信息
export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar?: string
  phone?: string
  is_active: boolean
  is_superuser: boolean
  last_login_at?: string
  created_at: string
  updated_at: string
}

// 用户列表项
export interface UserListItem extends User {
  role_names: string[]
}

// 用户详情
export interface UserDetail extends User {
  roles: Role[]
  permissions: string[]
}

// 用户创建请求
export interface UserCreateRequest {
  username: string
  email: string
  password: string
  full_name?: string
  phone?: string
  is_active?: boolean
  role_ids?: number[]
}

// 用户更新请求
export interface UserUpdateRequest {
  email?: string
  full_name?: string
  phone?: string
  avatar?: string
  is_active?: boolean
  role_ids?: number[]
}

// 密码重置请求
export interface PasswordResetRequest {
  new_password: string
}

// 角色分配请求
export interface RoleAssignRequest {
  role_ids: number[]
}

// 角色信息
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
