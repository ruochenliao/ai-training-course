// 用户管理相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 用户相关类型定义
export interface User {
  id: number
  username: string
  email: string
  full_name: string
  avatar_url?: string
  is_superuser: boolean
  is_staff: boolean
  status: string
  created_at: string
  updated_at: string
  last_login_at?: string
  login_count: number
}

export interface UserCreateRequest {
  username: string
  email: string
  password: string
  full_name?: string
  is_staff?: boolean
  is_superuser?: boolean
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
  avatar_url?: string
  is_staff?: boolean
  is_superuser?: boolean
  status?: string
}

export interface UserListParams {
  page?: number
  size?: number
  search?: string
  status?: string
  is_staff?: boolean
  is_superuser?: boolean
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  size: number
  pages: number
}

// 用户管理API接口
export const usersApi = {
  // 获取用户列表
  getUsers: (params?: UserListParams): Promise<ApiResponseData<UserListResponse>> => {
    return httpClient.get('/users', { params })
  },

  // 获取用户详情
  getUser: (userId: number): Promise<ApiResponseData<User>> => {
    return httpClient.get(`/users/${userId}`)
  },

  // 创建用户
  createUser: (data: UserCreateRequest): Promise<ApiResponseData<User>> => {
    return httpClient.post('/users', data)
  },

  // 更新用户信息
  updateUser: (userId: number, data: UserUpdateRequest): Promise<ApiResponseData<User>> => {
    return httpClient.put(`/users/${userId}`, data)
  },

  // 更新当前用户信息
  updateCurrentUser: (data: UserUpdateRequest): Promise<ApiResponseData<User>> => {
    return httpClient.put('/users/me', data)
  },

  // 删除用户
  deleteUser: (userId: number): Promise<ApiResponseData<any>> => {
    return httpClient.delete(`/users/${userId}`)
  },

  // 激活用户
  activateUser: (userId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/users/${userId}/activate`)
  },

  // 禁用用户
  deactivateUser: (userId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/users/${userId}/deactivate`)
  },

  // 重置用户密码
  resetUserPassword: (userId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/users/${userId}/reset-password`)
  },

  // 获取用户统计信息
  getUserStats: (): Promise<ApiResponseData<any>> => {
    return httpClient.get('/users/stats')
  }
}
