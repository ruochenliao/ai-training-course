/**
 * 企业级HTTP请求封装
 * 集成错误处理、性能优化、重试机制等功能
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import type { BaseResponse } from '@/types'
import { errorHandler } from './errorHandler'
import { loadingManager, cancelTokenManager, retry, performanceMonitor } from './performance'

// 请求配置接口
export interface RequestConfig extends AxiosRequestConfig {
  loading?: boolean | string  // 是否显示加载状态
  retry?: boolean | number    // 是否重试
  cache?: boolean | number    // 是否缓存
  silent?: boolean           // 是否静默处理错误
}

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config: RequestConfig) => {
    const authStore = useAuthStore()

    // 性能监控
    const requestKey = `${config.method}-${config.url}`
    performanceMonitor.mark(`request-${requestKey}-start`)

    // 添加认证token
    if (authStore.token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${authStore.token}`
      }
    }

    // 添加请求ID用于追踪
    config.headers = {
      ...config.headers,
      'X-Request-ID': `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
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
  (response: AxiosResponse<BaseResponse>) => {
    const config = response.config as RequestConfig
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
    } as BaseResponse
  },
  async (error: AxiosError) => {
    const config = error.config as RequestConfig
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
      if (authStore.refreshToken && !error.config?._retry) {
        error.config!._retry = true
        try {
          await authStore.refreshAccessToken()
          // 重新发送原请求
          return service(error.config!)
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
   * 带重试的请求
   */
  async withRetry<T = any>(
    requestFn: () => Promise<BaseResponse<T>>,
    maxAttempts: number = 3,
    delay: number = 1000
  ): Promise<BaseResponse<T>> {
    return retry(requestFn, maxAttempts, delay)
  },

  /**
   * 批量请求
   */
  async batch<T = any>(
    requests: Array<() => Promise<BaseResponse<T>>>,
    batchSize: number = 5,
    delay: number = 100
  ): Promise<BaseResponse<T>[]> {
    const results: BaseResponse<T>[] = []

    for (let i = 0; i < requests.length; i += batchSize) {
      const batch = requests.slice(i, i + batchSize)
      const batchResults = await Promise.all(batch.map(req => req()))
      results.push(...batchResults)

      if (delay > 0 && i + batchSize < requests.length) {
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    return results
  },

  /**
   * 上传文件
   */
  upload<T = any>(
    url: string,
    file: File,
    config?: RequestConfig & {
      onUploadProgress?: (progressEvent: any) => void
    }
  ): Promise<BaseResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    return service.post(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 下载文件
   */
  async download(
    url: string,
    filename?: string,
    config?: RequestConfig
  ): Promise<void> {
    const response = await service.get(url, {
      ...config,
      responseType: 'blob'
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}

export default service
