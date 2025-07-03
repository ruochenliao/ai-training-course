/**
 * API接口入口文件
 */

export * from './auth'
export * from './user'
export * from './role'
export * from './permission'
export * from './menu'
export * from './department'

// API基础配置
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
export const API_VERSION = '/api/v1'
