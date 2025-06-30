// API 配置文件

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// API 基础配置
export const API_CONFIG = {
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: false,
}

// 创建 axios 实例
export const httpClient: AxiosInstance = axios.create(API_CONFIG)

// Token 管理
export const tokenManager = {
  getToken(): string | null {
    return localStorage.getItem('access_token')
  },

  setToken(token: string): void {
    localStorage.setItem('access_token', token)
  },

  removeToken(): void {
    localStorage.removeItem('access_token')
  },

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  },

  setRefreshToken(token: string): void {
    localStorage.setItem('refresh_token', token)
  },

  removeRefreshToken(): void {
    localStorage.removeItem('refresh_token')
  },

  isTokenExpired(): boolean {
    const token = this.getToken()
    if (!token) return true

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return Date.now() >= payload.exp * 1000
    } catch {
      return true
    }
  },

  async refreshToken(): Promise<string | null> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) return null

    try {
      const response = await axios.post(`${API_CONFIG.baseURL}/auth/refresh`, {
        refresh_token: refreshToken,
      })

      const { access_token, refresh_token: newRefreshToken } = response.data.data
      this.setToken(access_token)
      if (newRefreshToken) {
        this.setRefreshToken(newRefreshToken)
      }

      return access_token
    } catch (error) {
      this.removeToken()
      this.removeRefreshToken()
      return null
    }
  },
}

// 请求拦截器
httpClient.interceptors.request.use(
  (config: any) => {
    // 添加认证头
    const token = tokenManager.getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求时间戳
    if (config.params) {
      config.params._t = Date.now()
    } else {
      config.params = { _t: Date.now() }
    }

    // 打印请求日志（开发环境）
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        params: config.params,
        data: config.data,
      })
    }

    return config
  },
  error => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
httpClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 打印响应日志（开发环境）
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ API Response:', {
        status: response.status,
        url: response.config.url,
        data: response.data,
      })
    }

    // 统一处理响应数据
    const { data } = response
    if (data.success === false) {
      const errorMessage = data.message || '请求失败'
      message.error(errorMessage)
      return Promise.reject(new Error(errorMessage))
    }

    return response
  },
  async error => {
    const { response, config } = error

    // 打印错误日志
    console.error('❌ API Error:', {
      status: response?.status,
      url: config?.url,
      message: error.message,
      data: response?.data,
    })

    // 处理 401 未授权错误
    if (response?.status === 401) {
      const isRefreshing = config._retry
      if (!isRefreshing) {
        config._retry = true

        const newToken = await tokenManager.refreshToken()
        if (newToken) {
          config.headers.Authorization = `Bearer ${newToken}`
          return httpClient(config)
        } else {
          // 刷新失败，跳转到登录页
          tokenManager.removeToken()
          tokenManager.removeRefreshToken()
          window.location.href = '/login'
          return Promise.reject(error)
        }
      }
    }

    // 处理网络错误
    if (!response) {
      message.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }

    // 处理服务器错误
    const errorMessage = response.data?.message || getErrorMessage(response.status)
    message.error(errorMessage)

    return Promise.reject(error)
  }
)

// 错误状态码映射
function getErrorMessage(status: number): string {
  const errorMessages: Record<number, string> = {
    400: '请求参数错误',
    401: '未授权，请重新登录',
    403: '拒绝访问',
    404: '请求的资源不存在',
    405: '请求方法不允许',
    408: '请求超时',
    409: '请求冲突',
    422: '请求参数验证失败',
    429: '请求过于频繁，请稍后再试',
    500: '服务器内部错误',
    502: '网关错误',
    503: '服务不可用',
    504: '网关超时',
  }

  return errorMessages[status] || `请求失败 (${status})`
}

// 请求取消管理
export class CancelTokenManager {
  private cancelTokens = new Map<string, AbortController>()

  create(key?: string): AbortController {
    const controller = new AbortController()
    if (key) {
      this.cancelTokens.set(key, controller)
    }
    return controller
  }

  cancel(key?: string): void {
    if (key) {
      const controller = this.cancelTokens.get(key)
      if (controller) {
        controller.abort()
        this.cancelTokens.delete(key)
      }
    }
  }

  cancelAll(): void {
    this.cancelTokens.forEach(controller => controller.abort())
    this.cancelTokens.clear()
  }
}

export const cancelTokenManager = new CancelTokenManager()

// 加载状态管理
export class LoadingManager {
  private loadingStates = new Map<string, boolean>()
  private globalLoading = false

  show(key?: string): void {
    if (key) {
      this.loadingStates.set(key, true)
    } else {
      this.globalLoading = true
    }
  }

  hide(key?: string): void {
    if (key) {
      this.loadingStates.set(key, false)
    } else {
      this.globalLoading = false
    }
  }

  isLoading(key?: string): boolean {
    if (key) {
      return this.loadingStates.get(key) || false
    }
    return this.globalLoading
  }

  clear(): void {
    this.loadingStates.clear()
    this.globalLoading = false
  }
}

export const loadingManager = new LoadingManager()

// 错误处理器
export class ErrorHandler {
  private handlers = new Map<string, (error: any) => void>()

  handle(error: any): void {
    const code = error.code || error.response?.status?.toString() || 'unknown'
    const handler = this.handlers.get(code)

    if (handler) {
      handler(error)
    } else {
      // 默认错误处理
      console.error('Unhandled error:', error)
      message.error(error.message || '发生未知错误')
    }
  }

  register(code: string, handler: (error: any) => void): void {
    this.handlers.set(code, handler)
  }

  unregister(code: string): void {
    this.handlers.delete(code)
  }
}

export const errorHandler = new ErrorHandler()

// 注册常用错误处理器
errorHandler.register('NETWORK_ERROR', () => {
  message.error('网络连接失败，请检查网络设置')
})

errorHandler.register('TIMEOUT', () => {
  message.error('请求超时，请稍后重试')
})

errorHandler.register('401', () => {
  message.error('登录已过期，请重新登录')
  // 可以在这里添加跳转到登录页的逻辑
})

errorHandler.register('403', () => {
  message.error('没有权限访问该资源')
})

errorHandler.register('500', () => {
  message.error('服务器内部错误，请联系管理员')
})

// 导出配置
export default {
  httpClient,
  tokenManager,
  cancelTokenManager,
  loadingManager,
  errorHandler,
  API_CONFIG,
}
