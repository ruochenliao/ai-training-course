// API 相关类型定义

import { AxiosRequestConfig, AxiosResponse } from 'axios'

// HTTP 方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

// API 配置类型
export interface ApiConfig {
  baseURL: string
  timeout: number
  headers: Record<string, string>
  withCredentials: boolean
}

// 请求配置类型
export interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean
  skipLoading?: boolean
  skipErrorHandler?: boolean
  retries?: number
  cache?: boolean
  cacheTime?: number
}

// 响应类型
export interface ApiResponseData<T = any> {
  success: boolean
  data: T
  message?: string
  code?: number
  timestamp?: number
}

export interface ApiError {
  code: string
  message: string
  details?: any
  status?: number
  timestamp: number
}

// 分页请求参数
export interface PaginationParams {
  page?: number
  size?: number
  sort?: string
  order?: 'asc' | 'desc'
}

// 分页响应数据
export interface PaginationData<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

// 文件上传相关
export interface UploadConfig {
  url: string
  method?: HttpMethod
  headers?: Record<string, string>
  data?: Record<string, any>
  onProgress?: (progress: number) => void
  onSuccess?: (response: any) => void
  onError?: (error: any) => void
}

export interface UploadResponse {
  success: boolean
  file_id: string
  file_url: string
  file_name: string
  file_size: number
  message?: string
}

// WebSocket 相关
export interface WebSocketConfig {
  url: string
  protocols?: string[]
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

// 流式响应相关
export interface StreamConfig {
  onMessage?: (message: string) => void
  onError?: (error: any) => void
  onComplete?: () => void
  onStart?: () => void
}

export interface StreamResponse {
  id: string
  object: string
  created: number
  model: string
  choices: StreamChoice[]
}

export interface StreamChoice {
  index: number
  delta: {
    content?: string
    role?: string
  }
  finish_reason?: string
}

// 缓存相关
export interface CacheConfig {
  enabled: boolean
  ttl: number // 缓存时间（毫秒）
  maxSize: number // 最大缓存条目数
  storage: 'memory' | 'localStorage' | 'sessionStorage'
}

export interface CacheItem<T = any> {
  key: string
  data: T
  timestamp: number
  ttl: number
}

// 重试配置
export interface RetryConfig {
  retries: number
  retryDelay: number
  retryCondition?: (error: any) => boolean
}

// 请求拦截器类型
export type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>

// 响应拦截器类型
export type ResponseInterceptor = (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>

// 错误拦截器类型
export type ErrorInterceptor = (error: any) => Promise<any>

// API 客户端接口
export interface ApiClient {
  get<T = any>(url: string, config?: RequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T>
  delete<T = any>(url: string, config?: RequestConfig): Promise<T>
  patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T>
  upload<T = any>(url: string, file: File, config?: UploadConfig): Promise<T>
  stream(url: string, config?: StreamConfig): Promise<void>
}

// Token 管理相关
export interface TokenManager {
  getToken(): string | null
  setToken(token: string): void
  removeToken(): void
  refreshToken(): Promise<string>
  isTokenExpired(): boolean
}

// 请求取消相关
export interface CancelTokenManager {
  create(key?: string): AbortController
  cancel(key?: string): void
  cancelAll(): void
}

// 加载状态管理
export interface LoadingManager {
  show(key?: string): void
  hide(key?: string): void
  isLoading(key?: string): boolean
  clear(): void
}

// 错误处理器
export interface ErrorHandler {
  handle(error: ApiError): void
  register(code: string, handler: (error: ApiError) => void): void
  unregister(code: string): void
}

// API 模块接口
export interface ApiModule {
  name: string
  baseURL?: string
  endpoints: Record<string, ApiEndpoint>
}

export interface ApiEndpoint {
  url: string
  method: HttpMethod
  description?: string
  params?: Record<string, any>
  headers?: Record<string, string>
  cache?: boolean
  auth?: boolean
}

// 监控相关
export interface ApiMetrics {
  totalRequests: number
  successRequests: number
  errorRequests: number
  averageResponseTime: number
  slowestRequest: number
  fastestRequest: number
}

export interface RequestMetric {
  url: string
  method: HttpMethod
  status: number
  responseTime: number
  timestamp: number
  error?: string
}

// 健康检查
export interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: number
  services: ServiceStatus[]
}

export interface ServiceStatus {
  name: string
  status: 'up' | 'down' | 'degraded'
  responseTime?: number
  error?: string
  lastCheck: number
}

// 批量操作
export interface BatchRequest<T = any> {
  requests: Array<{
    method: HttpMethod
    url: string
    data?: T
  }>
}

export interface BatchResponse<T = any> {
  results: Array<{
    success: boolean
    data?: T
    error?: ApiError
  }>
}

// 导出类型
export type ApiResponse<T = any> = Promise<ApiResponseData<T>>
export type PaginatedApiResponse<T = any> = Promise<ApiResponseData<PaginationData<T>>>
