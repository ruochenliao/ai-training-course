// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 认证相关类型定义
 */

import type { User } from './user'
import type { MenuRoute } from './menu'

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
  user: User
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

// 用户信息类型（继承自User，保持向后兼容）
export interface UserInfo extends User {}

// 用户个人资料类型
export interface UserProfile extends User {
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

// Token信息类型
export interface TokenInfo {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  expires_at: number
}

// 认证状态类型
export interface AuthState {
  isAuthenticated: boolean
  token: string | null
  refreshToken: string | null
  user: User | null
  permissions: string[]
  roles: string[]
  menus: MenuRoute[]
}
