/**
 * 企业级HTTP请求封装
 * 集成错误处理、性能优化、重试机制等功能
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
// @ts-ignore - 忽略类型检查
import { useAuthStore } from '@/stores/auth'
// @ts-ignore - 忽略类型检查
import router from '@/router'
// @ts-ignore - 忽略类型检查
import type { BaseResponse } from '@/types'
import { errorHandler } from './errorHandler'
import { loadingManager, cancelTokenManager, retry, performanceMonitor, cacheManager } from './performance'

// 导入环境变量工具
import { getApiBaseUrl } from './env'

// 扩展Axios类型定义
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean
    loading?: boolean | string
    retry?: boolean | number
    cache?: boolean | number
    silent?: boolean
  }
}

// 请求配置接口
export interface RequestConfig extends AxiosRequestConfig {
  loading?: boolean | string  // 是否显示加载状态
  retry?: boolean | number    // 是否重试
  cache?: boolean | number    // 是否缓存
  silent?: boolean           // 是否静默处理错误
  _retry?: boolean           // 是否已重试
}

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()

    // 性能监控
    const requestKey = `${config.method}-${config.url}`
    performanceMonitor.mark(`request-${requestKey}-start`)

    // 添加认证token
    if (authStore.token) {
      if (typeof config.headers?.set === 'function') {
        config.headers.set('Authorization', `Bearer ${authStore.token}`)
      } else {
        config.headers = {
          ...config.headers,
          Authorization: `Bearer ${authStore.token}`
        } as any
      }
    }

    // 添加请求ID用于追踪
    if (typeof config.headers?.set === 'function') {
      config.headers.set('X-Request-ID', `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
    } else {
      config.headers = {
        ...config.headers,
        'X-Request-ID': `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      } as any
    }

    // 处理取消令牌
    if (!config.signal) {
      const controller = cancelTokenManager.create(requestKey)
      config.signal = controller.signal
    }

    // 显示加载状态
    if (config.loading !== false) {
      const loadingKey = typeof config.loading === 'string' ? config.loading : requestKey
      loadingManager.show(loadingKey)
    }

    return config
  },
  (error) => {
    console.error('Request error:', error)
    errorHandler.handleError(error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<any>) => {
    const config = response.config as any as RequestConfig
    const requestKey = `${config.method}-${config.url}`

    // 性能监控
    performanceMonitor.measure(`request-${requestKey}`, `request-${requestKey}-start`)

    // 隐藏加载状态
    if (config.loading !== false) {
      const loadingKey = typeof config.loading === 'string' ? config.loading : requestKey
      loadingManager.hide(loadingKey)
    }

    const { data } = response

    // 后端返回的是BaseResponse格式，直接返回data
    // 如果有code字段，检查是否成功
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 200) {
        return data
      } else {
        // 业务错误 - 使用新的错误处理机制
        if (!config.silent) {
          const error = errorHandler.handleApiError({
            response,
            config,
            message: data.message || '请求失败'
          } as AxiosError)
          return Promise.reject(error)
        }
        return Promise.reject(new Error(data.message || '请求失败'))
      }
    }

    // 如果没有code字段，说明是直接的数据响应，包装成BaseResponse格式
    return {
      code: 200,
      message: 'success',
      data: data,
      timestamp: new Date().toISOString(),
      request_id: response.headers['x-request-id'] || ''
    }
  },
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig
    const requestKey = `${config?.method}-${config?.url}`
    const authStore = useAuthStore()

    // 性能监控
    if (config) {
      performanceMonitor.measure(`request-${requestKey}-error`, `request-${requestKey}-start`)

      // 隐藏加载状态
      if (config.loading !== false) {
        const loadingKey = typeof config.loading === 'string' ? config.loading : requestKey
        loadingManager.hide(loadingKey)
      }
    }

    // 处理401认证错误的特殊逻辑
    if (error.response?.status === 401) {
      // 未授权，尝试刷新token
      if (authStore.refreshToken && !config?._retry) {
        config._retry = true
        try {
          await authStore.refreshAccessToken()
          // 重新发送原请求
          return service(config)
        } catch (refreshError) {
          // 刷新失败，跳转到登录页
          authStore.logout()
          router.push('/login')
          if (!config?.silent) {
            ElMessage.error('登录已过期，请重新登录')
          }
          return Promise.reject(error)
        }
      } else {
        authStore.logout()
        router.push('/login')
        if (!config?.silent) {
          ElMessage.error('登录已过期，请重新登录')
        }
        return Promise.reject(error)
      }
    }

    // 使用新的错误处理机制
    if (!config?.silent) {
      const appError = errorHandler.handleApiError(error)
      return Promise.reject(appError)
    }

    return Promise.reject(error)
  }
)

// 增强的请求方法封装
export const request = {
  /**
   * GET请求
   */
  get<T = any>(url: string, config?: RequestConfig): Promise<BaseResponse<T>> {
    return service.get(url, config)
  },

  /**
   * POST请求
   */
  post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<BaseResponse<T>> {
    return service.post(url, data, config)
  },

  /**
   * PUT请求
   */
  put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<BaseResponse<T>> {
    return service.put(url, data, config)
  },

  /**
   * DELETE请求
   */
  delete<T = any>(url: string, config?: RequestConfig): Promise<BaseResponse<T>> {
    return service.delete(url, config)
  },

  /**
   * PATCH请求
   */
  patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<BaseResponse<T>> {
    return service.patch(url, data, config)
  },

  /**
   * 上传文件
   */
  upload<T = any>(url: string, file: File | FormData, config?: RequestConfig): Promise<BaseResponse<T>> {
    const formData = file instanceof FormData ? file : new FormData()
    
    if (file instanceof File) {
      formData.append('file', file)
    }
    
    return service.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      ...config
    })
  },

  /**
   * 下载文件
   */
  download(url: string, filename?: string, config?: RequestConfig): Promise<void> {
    return service.get(url, {
      responseType: 'blob',
      ...config
    }).then(response => {
      const blob = new Blob([response.data])
      const downloadUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || url.substring(url.lastIndexOf('/') + 1) || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(downloadUrl)
    })
  },

  /**
   * 带重试的请求
   */
  async withRetry<T = any>(
    method: 'get' | 'post' | 'put' | 'delete' | 'patch',
    url: string,
    data?: any,
    config?: RequestConfig & { maxRetries?: number, retryDelay?: number }
  ): Promise<BaseResponse<T>> {
    const maxRetries = config?.maxRetries || 3
    const retryDelay = config?.retryDelay || 1000
    
    return retry(
      async () => {
        switch (method) {
          case 'get':
            return await request.get<T>(url, config)
          case 'post':
            return await request.post<T>(url, data, config)
          case 'put':
            return await request.put<T>(url, data, config)
          case 'delete':
            return await request.delete<T>(url, config)
          case 'patch':
            return await request.patch<T>(url, data, config)
          default:
            throw new Error(`Unsupported method: ${method}`)
        }
      },
      maxRetries,
      retryDelay
    )
  },

  /**
   * 带缓存的GET请求
   */
  async cachedGet<T = any>(
    url: string,
    config?: RequestConfig & { ttl?: number }
  ): Promise<BaseResponse<T>> {
    const ttl = config?.ttl || 5 * 60 * 1000 // 默认5分钟
    const cacheKey = `${url}${config ? JSON.stringify(config) : ''}`
    
    // 尝试从缓存获取
    const cachedData = cacheManager.get(cacheKey)
    if (cachedData) {
      return cachedData
    }
    
    // 发起请求
    const response = await request.get<T>(url, config)
    
    // 缓存结果
    cacheManager.set(cacheKey, response, ttl)
    
    return response
  }
}

export default service
