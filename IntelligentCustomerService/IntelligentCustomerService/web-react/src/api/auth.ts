import type {ApiResponse} from './index'
import {request} from './index'
import type {
    ChangePasswordParams,
    LoginParams,
    LoginResponse,
    RegisterParams,
    ResetPasswordParams,
    User,
} from '@/types/auth'

export const authApi = {
  // 登录获取token
  login: (params: LoginParams): Promise<ApiResponse<LoginResponse>> => {
    return request.post('/v1/base/access_token', params)
  },

  // 获取用户信息
  getUserInfo: (): Promise<ApiResponse<User>> => {
    return request.get('/v1/base/userinfo')
  },

  // 获取用户菜单
  getUserMenu: (): Promise<ApiResponse<any[]>> => {
    return request.get('/v1/base/usermenu')
  },

  // 获取用户API权限
  getUserApi: (): Promise<ApiResponse<string[]>> => {
    return request.get('/v1/base/userapi')
  },

  // 修改密码
  changePassword: (params: ChangePasswordParams): Promise<ApiResponse> => {
    return request.post('/v1/base/update_password', params)
  },

  // 登出 (客户端清除状态)
  logout: (): Promise<ApiResponse> => {
    return Promise.resolve({ code: 200, message: 'OK', data: null, success: true })
  },

  // 注册
  register: (params: RegisterParams): Promise<ApiResponse<User>> => {
    return request.post('/auth/register', params)
  },

  // 刷新token
  refreshToken: (refreshToken: string): Promise<ApiResponse<{ token: string; refreshToken: string }>> => {
    return request.post('/auth/refresh-token', { refreshToken })
  },

  // 重置密码
  resetPassword: (params: ResetPasswordParams): Promise<ApiResponse> => {
    return request.post('/auth/reset-password', params)
  },

  // 发送重置密码邮件
  sendResetEmail: (email: string): Promise<ApiResponse> => {
    return request.post('/auth/send-reset-email', { email })
  },

  // 验证token
  verifyToken: (): Promise<ApiResponse<User>> => {
    return request.get('/auth/verify-token')
  },
}