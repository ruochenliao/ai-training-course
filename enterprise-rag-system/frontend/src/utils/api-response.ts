/**
 * API响应处理工具
 * 统一处理后端 {code, msg, data} 格式的响应
 */

import type { ApiResponseData, ApiError, PaginationData } from '@/types/api'

/**
 * 检查API响应是否成功
 */
export function isApiSuccess<T>(response: ApiResponseData<T>): boolean {
  return response.code === 200
}

/**
 * 提取API响应数据
 */
export function extractApiData<T>(response: ApiResponseData<T>): T {
  if (!isApiSuccess(response)) {
    throw new Error(response.msg || '请求失败')
  }
  return response.data
}

/**
 * 创建API错误对象
 */
export function createApiError(response: ApiResponseData<any>): ApiError {
  return {
    code: response.code,
    msg: response.msg,
    data: response.data,
  }
}

/**
 * 处理分页响应
 */
export function handlePaginationResponse<T>(response: ApiResponseData<PaginationData<T>>): PaginationData<T> {
  return extractApiData(response)
}

/**
 * 统一的API响应处理器
 */
export class ApiResponseHandler {
  /**
   * 处理成功响应
   */
  static success<T>(response: ApiResponseData<T>): T {
    return extractApiData(response)
  }

  /**
   * 处理错误响应
   */
  static error(response: ApiResponseData<any>): never {
    const error = createApiError(response)
    throw error
  }

  /**
   * 处理分页响应
   */
  static pagination<T>(response: ApiResponseData<PaginationData<T>>): PaginationData<T> {
    return handlePaginationResponse(response)
  }

  /**
   * 安全处理响应（不抛出异常）
   */
  static safe<T>(response: ApiResponseData<T>): { success: boolean; data?: T; error?: ApiError } {
    if (isApiSuccess(response)) {
      return { success: true, data: response.data }
    } else {
      return { success: false, error: createApiError(response) }
    }
  }
}

/**
 * 响应状态码常量
 */
export const API_CODES = {
  SUCCESS: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
} as const

/**
 * 检查特定状态码
 */
export function isApiCode(response: ApiResponseData<any>, code: number): boolean {
  return response.code === code
}

/**
 * 响应消息处理
 */
export function getApiMessage(response: ApiResponseData<any>, defaultMsg = '操作完成'): string {
  return response.msg || defaultMsg
}

/**
 * 批量处理API响应
 */
export function handleBatchResponse<T>(responses: ApiResponseData<T>[]): { successes: T[]; errors: ApiError[] } {
  const successes: T[] = []
  const errors: ApiError[] = []

  responses.forEach(response => {
    if (isApiSuccess(response)) {
      successes.push(response.data)
    } else {
      errors.push(createApiError(response))
    }
  })

  return { successes, errors }
}

/**
 * 创建标准化的API请求包装器
 */
export function createApiWrapper<T>(apiCall: () => Promise<ApiResponseData<T>>): Promise<T> {
  return apiCall().then(response => {
    if (isApiSuccess(response)) {
      return response.data
    } else {
      throw createApiError(response)
    }
  })
}

/**
 * 重试机制包装器
 */
export async function withRetry<T>(
  apiCall: () => Promise<ApiResponseData<T>>,
  maxRetries = 3,
  delay = 1000
): Promise<T> {
  let lastError: any

  for (let i = 0; i <= maxRetries; i++) {
    try {
      const response = await apiCall()
      return extractApiData(response)
    } catch (error) {
      lastError = error
      if (i < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
      }
    }
  }

  throw lastError
}

/**
 * 缓存包装器
 */
export class ApiCache {
  private static cache = new Map<string, { data: any; timestamp: number; ttl: number }>()

  static get<T>(key: string): T | null {
    const item = this.cache.get(key)
    if (!item) return null

    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key)
      return null
    }

    return item.data
  }

  static set<T>(key: string, data: T, ttl = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  static clear(): void {
    this.cache.clear()
  }

  static delete(key: string): void {
    this.cache.delete(key)
  }
}

/**
 * 带缓存的API调用
 */
export async function withCache<T>(
  key: string,
  apiCall: () => Promise<ApiResponseData<T>>,
  ttl = 5 * 60 * 1000
): Promise<T> {
  // 尝试从缓存获取
  const cached = ApiCache.get<T>(key)
  if (cached) {
    return cached
  }

  // 调用API并缓存结果
  const response = await apiCall()
  const data = extractApiData(response)
  ApiCache.set(key, data, ttl)

  return data
}

export default ApiResponseHandler
