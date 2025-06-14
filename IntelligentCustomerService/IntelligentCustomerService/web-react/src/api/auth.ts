import type {ApiResponse} from './index'
import {request} from './index'
import type {ChangePasswordParams, LoginParams, LoginResponse, User} from '@/types/auth'

export const authApi = {
  // 登录获取token - 正确的API路径
  login: (params: LoginParams): Promise<ApiResponse<LoginResponse>> => {
    return request.post('/api/v1/base/access_token', params)
  },

  // 获取用户信息
  getUserInfo: (): Promise<ApiResponse<User>> => {
    return request.get('/api/v1/base/userinfo')
  },

  // 获取用户菜单
  getUserMenu: (): Promise<ApiResponse<any[]>> => {
    return request.get('/api/v1/base/usermenu')
  },

  // 获取用户API权限
  getUserApi: (): Promise<ApiResponse<string[]>> => {
    return request.get('/api/v1/base/userapi')
  },

  // 修改密码
  changePassword: (params: ChangePasswordParams): Promise<ApiResponse> => {
    return request.post('/api/v1/base/update_password', params)
  },

  // 登出 (客户端清除状态)
  logout: (): Promise<ApiResponse> => {
    return Promise.resolve({ code: 200, message: 'OK', data: null, success: true })
  },
}
