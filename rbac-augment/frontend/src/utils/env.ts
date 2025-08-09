// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 环境变量工具函数
 */

import type { EnvConfig, EnvUtils } from '@/types/env'

/**
 * 获取环境配置
 */
export function getEnvConfig(): EnvConfig {
  const env = import.meta.env
  
  return {
    apiBaseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000',
    appTitle: env.VITE_APP_TITLE || 'RBAC管理系统',
    appVersion: env.VITE_APP_VERSION || '1.0.0',
    buildTime: env.VITE_BUILD_TIME || new Date().toISOString(),
    enableMock: env.VITE_ENABLE_MOCK === 'true',
    enableDevtools: env.VITE_ENABLE_DEVTOOLS === 'true',
    uploadUrl: env.VITE_UPLOAD_URL || `${env.VITE_API_BASE_URL}/upload`,
    websocketUrl: env.VITE_WEBSOCKET_URL || 'ws://localhost:8000/ws',
    isDevelopment: env.DEV,
    isProduction: env.PROD
  }
}

/**
 * 检查是否为生产环境
 */
export function isProduction(): boolean {
  return import.meta.env.PROD
}

/**
 * 检查是否为开发环境
 */
export function isDevelopment(): boolean {
  return import.meta.env.DEV
}

/**
 * 获取API基础URL
 */
export function getApiBaseUrl(): string {
  return getEnvConfig().apiBaseUrl
}

/**
 * 获取上传URL
 */
export function getUploadUrl(): string {
  return getEnvConfig().uploadUrl
}

/**
 * 获取WebSocket URL
 */
export function getWebSocketUrl(): string {
  return getEnvConfig().websocketUrl
}

/**
 * 环境变量工具对象
 */
export const envUtils: EnvUtils = {
  getEnvConfig,
  isProduction,
  isDevelopment,
  getApiBaseUrl,
  getUploadUrl,
  getWebSocketUrl
}

// 默认导出环境配置
export default getEnvConfig()
