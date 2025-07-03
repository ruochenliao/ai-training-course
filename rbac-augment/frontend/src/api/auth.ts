/**
 * 认证相关API
 */

import { request } from '@/utils/request'
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserProfile,
  ChangePasswordRequest,
  MenuRoute
} from '@/types'

/**
 * 用户登录
 */
export function login(data: LoginRequest) {
  return request.post<LoginResponse>('/api/v1/auth/login', data)
}

/**
 * 用户登出
 */
export function logout() {
  return request.post('/api/v1/auth/logout')
}

/**
 * 刷新Token
 */
export function refreshToken(data: RefreshTokenRequest) {
  return request.post<RefreshTokenResponse>('/api/v1/auth/refresh', data)
}

/**
 * 获取用户个人资料
 */
export function getUserProfile() {
  return request.get<UserProfile>('/api/v1/auth/profile')
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest) {
  return request.put('/api/v1/auth/password', data)
}

/**
 * 获取用户权限
 */
export function getUserPermissions() {
  return request.get<string[]>('/api/v1/auth/permissions')
}

/**
 * 获取用户菜单
 */
export function getUserMenus() {
  return request.get<MenuRoute[]>('/api/v1/auth/menus')
}

/**
 * 更新个人资料
 */
export function updateProfile(data: {
  username: string
  full_name: string
  email: string
  phone?: string
}) {
  return request.put('/api/v1/auth/profile', data)
}

/**
 * 上传头像
 */
export function uploadAvatar(formData: FormData) {
  return request.post('/api/v1/auth/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
