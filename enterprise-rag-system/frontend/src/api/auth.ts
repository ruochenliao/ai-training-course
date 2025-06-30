// 认证相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 认证相关类型定义
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string
  avatar_url?: string
  is_superuser: boolean
  is_staff: boolean
  status: string
  created_at?: string
  last_login_at?: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

// 认证API接口
export const authApi = {
  // 用户登录
  login: (data: LoginRequest): Promise<ApiResponseData<LoginResponse>> => {
    return httpClient.post('/auth/login/json', data)
  },

  // 用户注册
  register: (data: RegisterRequest): Promise<ApiResponseData<UserInfo>> => {
    return httpClient.post('/auth/register', data)
  },

  // 刷新令牌
  refreshToken: (data: RefreshTokenRequest): Promise<ApiResponseData<LoginResponse>> => {
    return httpClient.post('/auth/refresh', data)
  },

  // 用户登出
  logout: (): Promise<ApiResponseData<any>> => {
    return httpClient.post('/auth/logout')
  },

  // 获取当前用户信息
  getCurrentUser: (): Promise<ApiResponseData<UserInfo>> => {
    return httpClient.get('/users/me')
  },

  // 修改密码
  changePassword: (data: { old_password: string; new_password: string }): Promise<ApiResponseData<any>> => {
    return httpClient.post('/auth/change-password', data)
  },

  // 重置密码
  resetPassword: (data: { email: string }): Promise<ApiResponseData<any>> => {
    return httpClient.post('/auth/reset-password', data)
  },

  // 验证令牌
  verifyToken: (): Promise<ApiResponseData<UserInfo>> => {
    return httpClient.get('/auth/verify-token')
  }
}
