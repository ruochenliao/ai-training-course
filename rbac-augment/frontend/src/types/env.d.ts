// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 环境变量类型声明
 */

// 扩展ImportMeta接口以包含自定义环境变量
declare interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_BUILD_TIME: string
  readonly VITE_ENABLE_MOCK: string
  readonly VITE_ENABLE_DEVTOOLS: string
  readonly VITE_UPLOAD_URL: string
  readonly VITE_WEBSOCKET_URL: string
  readonly MODE: string
  readonly BASE_URL: string
  readonly PROD: boolean
  readonly DEV: boolean
  readonly SSR: boolean
}

// 扩展ImportMeta接口
declare interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 环境配置类型
export interface EnvConfig {
  apiBaseUrl: string
  appTitle: string
  appVersion: string
  buildTime: string
  enableMock: boolean
  enableDevtools: boolean
  uploadUrl: string
  websocketUrl: string
  isDevelopment: boolean
  isProduction: boolean
}

// 环境变量工具函数类型
export interface EnvUtils {
  getEnvConfig: () => EnvConfig
  isProduction: () => boolean
  isDevelopment: () => boolean
  getApiBaseUrl: () => string
  getUploadUrl: () => string
  getWebSocketUrl: () => string
}
