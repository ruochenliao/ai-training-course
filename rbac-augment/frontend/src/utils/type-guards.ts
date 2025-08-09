// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 类型守卫和验证工具
 */

import type { 
  User, 
  UserProfile, 
  LoginResponse, 
  ChangePasswordRequest,
  MenuRoute,
  BaseResponse 
} from '@/types'

/**
 * 检查是否为有效的用户对象
 */
export function isValidUser(obj: any): obj is User {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'number' &&
    typeof obj.username === 'string' &&
    typeof obj.email === 'string' &&
    typeof obj.is_active === 'boolean' &&
    typeof obj.is_superuser === 'boolean' &&
    typeof obj.created_at === 'string' &&
    typeof obj.updated_at === 'string'
  )
}

/**
 * 检查是否为有效的用户资料对象
 */
export function isValidUserProfile(obj: any): obj is UserProfile {
  return (
    isValidUser(obj) &&
    Array.isArray(obj.roles) &&
    Array.isArray(obj.permissions) &&
    Array.isArray(obj.menus)
  )
}

/**
 * 检查是否为有效的登录响应
 */
export function isValidLoginResponse(obj: any): obj is LoginResponse {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.access_token === 'string' &&
    typeof obj.refresh_token === 'string' &&
    typeof obj.token_type === 'string' &&
    typeof obj.expires_in === 'number' &&
    isValidUser(obj.user)
  )
}

/**
 * 检查是否为有效的修改密码请求
 */
export function isValidChangePasswordRequest(obj: any): obj is ChangePasswordRequest {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.old_password === 'string' &&
    typeof obj.new_password === 'string' &&
    typeof obj.confirm_password === 'string' &&
    obj.old_password.length > 0 &&
    obj.new_password.length >= 6 &&
    obj.new_password === obj.confirm_password
  )
}

/**
 * 检查是否为有效的菜单路由
 */
export function isValidMenuRoute(obj: any): obj is MenuRoute {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'number' &&
    typeof obj.name === 'string' &&
    typeof obj.path === 'string' &&
    obj.meta &&
    typeof obj.meta.title === 'string'
  )
}

/**
 * 检查是否为有效的API响应
 */
export function isValidApiResponse<T>(obj: any, dataValidator?: (data: any) => data is T): obj is BaseResponse<T> {
  const isValidBase = (
    obj &&
    typeof obj === 'object' &&
    typeof obj.code === 'number' &&
    typeof obj.message === 'string' &&
    typeof obj.timestamp === 'string' &&
    typeof obj.request_id === 'string'
  )
  
  if (!isValidBase) return false
  
  if (dataValidator) {
    return dataValidator(obj.data)
  }
  
  return true
}

/**
 * 类型断言工具
 */
export class TypeAssertionError extends Error {
  constructor(message: string, public readonly received: any) {
    super(`Type assertion failed: ${message}`)
    this.name = 'TypeAssertionError'
  }
}

/**
 * 断言函数
 */
export function assertType<T>(
  value: any, 
  guard: (value: any) => value is T, 
  errorMessage: string
): asserts value is T {
  if (!guard(value)) {
    throw new TypeAssertionError(errorMessage, value)
  }
}

/**
 * 安全类型转换
 */
export function safeTypeConvert<T>(
  value: any,
  guard: (value: any) => value is T,
  fallback: T
): T {
  return guard(value) ? value : fallback
}
