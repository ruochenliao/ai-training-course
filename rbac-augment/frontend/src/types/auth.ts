/**
 * 认证相关类型定义
 */

// 登录请求类型
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

// 登录响应类型
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

// 刷新Token请求类型
export interface RefreshTokenRequest {
  refresh_token: string
}

// 刷新Token响应类型
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// 用户信息类型
export interface UserInfo {
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

// 用户个人资料类型
export interface UserProfile extends UserInfo {
  roles: string[]
  permissions: string[]
  menus: MenuRoute[]
  department?: {
    id: number
    name: string
    code: string
  }
}

// 修改密码请求类型
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

// 菜单路由类型
export interface MenuRoute {
  id: number
  name: string
  path: string
  component?: string
  redirect?: string
  meta: {
    title: string
    icon?: string
    cache: boolean
    hidden: boolean
    external: boolean
  }
  children?: MenuRoute[]
}
