import request from '@/utils/request'
import type {
  LoginParams,
  LoginResponse,
  RegisterParams,
  ResetPasswordParams,
  ChangePasswordParams,
  User,
} from '@/types/auth'
import type { ApiResponse } from '@/types/api'

export const authApi = {
  // 登录
  login: (params: LoginParams): Promise<ApiResponse<LoginResponse>> => {
    return request.post('/auth/login', params)
  },

  // 注册
  register: (params: RegisterParams): Promise<ApiResponse<User>> => {
    return request.post('/auth/register', params)
  },

  // 登出
  logout: (): Promise<ApiResponse> => {
    return request.post('/auth/logout')
  },

  // 获取用户信息
  getUserInfo: (): Promise<ApiResponse<User>> => {
    return request.get('/auth/user-info')
  },

  // 刷新token
  refreshToken: (refreshToken: string): Promise<ApiResponse<{ token: string; refreshToken: string }>> => {
    return request.post('/auth/refresh-token', { refreshToken })
  },

  // 修改密码
  changePassword: (params: ChangePasswordParams): Promise<ApiResponse> => {
    return request.post('/auth/change-password', params)
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