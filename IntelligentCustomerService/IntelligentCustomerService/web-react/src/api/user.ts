import { request } from './index'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

// 用户接口类型定义
export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  is_active: boolean
  is_superuser: boolean
  last_login?: string
  created_at: string
  updated_at: string
  dept_id?: number
  dept?: {
    id: number
    name: string
  }
  roles: Role[]
}

export interface Role {
  id: number
  name: string
  remark?: string
  created_at: string
  updated_at: string
}

export interface CreateUserParams {
  username: string
  email: string
  password: string
  dept_id?: number
  role_ids: number[]
}

export interface UpdateUserParams {
  id: number
  username?: string
  email?: string
  dept_id?: number
  role_ids?: number[]
  is_active?: boolean
}

export interface UserQueryParams {
  page?: number
  page_size?: number
  username?: string
  email?: string
  dept_id?: number
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export interface ResetPasswordParams {
  user_id: number
}

// 用户管理API
export const userApi = {
  // 获取用户列表
  getUsers: (params?: UserQueryParams): Promise<ApiResponse<PaginatedResponse<User>>> => {
    return request.get('/api/v1/user/list', { params })
  },

  // 获取用户详情
  getUserById: (id: number): Promise<ApiResponse<User>> => {
    return request.get('/api/v1/user/get', { params: { user_id: id } })
  },

  // 创建用户
  createUser: (params: CreateUserParams): Promise<ApiResponse> => {
    return request.post('/api/v1/user/create', params)
  },

  // 更新用户
  updateUser: (params: UpdateUserParams): Promise<ApiResponse> => {
    return request.post('/api/v1/user/update', params)
  },

  // 删除用户
  deleteUser: (id: number): Promise<ApiResponse> => {
    return request.delete('/api/v1/user/delete', { params: { user_id: id } })
  },

  // 切换用户状态
  toggleUserStatus: (id: number, isActive: boolean): Promise<ApiResponse> => {
    return request.post('/api/v1/user/update', {
      id,
      is_active: isActive,
    })
  },

  // 重置用户密码
  resetPassword: (params: ResetPasswordParams): Promise<ApiResponse> => {
    return request.post('/api/v1/user/reset_password', params)
  },

  // 修改用户密码
  changePassword: (params: ChangePasswordParams): Promise<ApiResponse> => {
    return request.post('/api/v1/base/update_password', { req_in: params })
  },
}
