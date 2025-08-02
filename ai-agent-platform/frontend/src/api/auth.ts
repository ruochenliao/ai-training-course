import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 登录请求参数
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

// 注册请求参数
export interface RegisterParams {
  username: string
  email: string
  password: string
  confirmPassword: string
}

// 登录响应数据
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

// 用户信息
export interface UserInfo {
  id: number
  username: string
  email: string
  avatar?: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 认证API接口
export const authApi = {
  // 登录
  login: (data: LoginParams): Promise<ApiResponse<LoginResponse>> => {
    return request({
      url: API_PATHS.AUTH.LOGIN,
      method: 'post',
      data
    })
  },

  // 注册
  register: (data: RegisterParams): Promise<ApiResponse<UserInfo>> => {
    return request({
      url: API_PATHS.AUTH.REGISTER,
      method: 'post',
      data
    })
  },

  // 获取用户信息
  getUserInfo: (): Promise<ApiResponse<UserInfo>> => {
    return request({
      url: API_PATHS.AUTH.PROFILE,
      method: 'get'
    })
  },

  // 登出
  logout: (): Promise<ApiResponse<null>> => {
    return request({
      url: API_PATHS.AUTH.LOGOUT,
      method: 'post'
    })
  },

  // 刷新token
  refreshToken: (refreshToken: string): Promise<ApiResponse<LoginResponse>> => {
    return request({
      url: API_PATHS.AUTH.REFRESH,
      method: 'post',
      data: { refresh_token: refreshToken }
    })
  }
}
