// 企业级错误处理机制

import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION', 
  AUTHORIZATION = 'AUTHORIZATION',
  VALIDATION = 'VALIDATION',
  BUSINESS = 'BUSINESS',
  SYSTEM = 'SYSTEM',
  UNKNOWN = 'UNKNOWN'
}

/**
 * 错误级别枚举
 */
export enum ErrorLevel {
  INFO = 'info',
  WARNING = 'warning', 
  ERROR = 'error',
  CRITICAL = 'critical'
}

/**
 * 错误详情接口
 */
export interface ErrorDetail {
  field?: string
  message: string
  code?: string
  value?: any
}

/**
 * 应用错误类
 */
export class AppError extends Error {
  public readonly type: ErrorType
  public readonly level: ErrorLevel
  public readonly code?: string
  public readonly details?: ErrorDetail[]
  public readonly timestamp: number
  public readonly requestId?: string

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    level: ErrorLevel = ErrorLevel.ERROR,
    code?: string,
    details?: ErrorDetail[]
  ) {
    super(message)
    this.name = 'AppError'
    this.type = type
    this.level = level
    this.code = code
    this.details = details
    this.timestamp = Date.now()
  }
}

/**
 * 网络错误类
 */
export class NetworkError extends AppError {
  constructor(message: string = '网络连接失败', code?: string) {
    super(message, ErrorType.NETWORK, ErrorLevel.ERROR, code)
    this.name = 'NetworkError'
  }
}

/**
 * 认证错误类
 */
export class AuthenticationError extends AppError {
  constructor(message: string = '用户未登录或登录已过期', code?: string) {
    super(message, ErrorType.AUTHENTICATION, ErrorLevel.WARNING, code)
    this.name = 'AuthenticationError'
  }
}

/**
 * 授权错误类
 */
export class AuthorizationError extends AppError {
  constructor(message: string = '没有权限执行此操作', code?: string) {
    super(message, ErrorType.AUTHORIZATION, ErrorLevel.WARNING, code)
    this.name = 'AuthorizationError'
  }
}

/**
 * 验证错误类
 */
export class ValidationError extends AppError {
  constructor(message: string = '数据验证失败', details?: ErrorDetail[], code?: string) {
    super(message, ErrorType.VALIDATION, ErrorLevel.WARNING, code, details)
    this.name = 'ValidationError'
  }
}

/**
 * 业务错误类
 */
export class BusinessError extends AppError {
  constructor(message: string, code?: string, details?: ErrorDetail[]) {
    super(message, ErrorType.BUSINESS, ErrorLevel.WARNING, code, details)
    this.name = 'BusinessError'
  }
}

/**
 * 错误处理器配置
 */
export interface ErrorHandlerConfig {
  showMessage: boolean
  showNotification: boolean
  reportError: boolean
  logError: boolean
  retryEnabled: boolean
  maxRetries: number
}

/**
 * 默认错误处理器配置
 */
const defaultConfig: ErrorHandlerConfig = {
  showMessage: true,
  showNotification: false,
  reportError: true,
  logError: true,
  retryEnabled: true,
  maxRetries: 3
}

/**
 * 错误处理器类
 */
export class ErrorHandler {
  private static instance: ErrorHandler
  private config: ErrorHandlerConfig
  private listeners: Array<(error: AppError) => void> = []
  private retryCount = new Map<string, number>()

  private constructor(config: Partial<ErrorHandlerConfig> = {}) {
    this.config = { ...defaultConfig, ...config }
    this.setupGlobalErrorHandlers()
  }

  /**
   * 获取单例实例
   */
  public static getInstance(config?: Partial<ErrorHandlerConfig>): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler(config)
    }
    return ErrorHandler.instance
  }

  /**
   * 设置全局错误处理器
   */
  private setupGlobalErrorHandlers(): void {
    // 处理未捕获的Promise错误
    window.addEventListener('unhandledrejection', (event) => {
      const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
      this.handleError(this.convertToAppError(error))
      event.preventDefault()
    })

    // 处理未捕获的JS错误
    window.addEventListener('error', (event) => {
      const error = event.error || new Error(event.message)
      this.handleError(this.convertToAppError(error))
    })
  }

  /**
   * 处理错误
   */
  public handleError(error: Error | AppError, showMessage: boolean = true): void {
    const appError = error instanceof AppError ? error : this.convertToAppError(error)

    // 记录错误日志
    if (this.config.logError) {
      this.logError(appError)
    }

    // 通知监听器
    this.notifyListeners(appError)

    // 显示错误消息
    if (showMessage && this.config.showMessage) {
      this.showErrorMessage(appError)
    }

    // 显示通知
    if (this.config.showNotification) {
      this.showErrorNotification(appError)
    }

    // 上报错误
    if (this.config.reportError) {
      this.reportError(appError)
    }
  }

  /**
   * 处理API错误
   */
  public handleApiError(error: AxiosError): AppError {
    const response = error.response
    const request = error.request
    const config = error.config

    let appError: AppError

    if (response) {
      // 服务器响应错误
      const { status, data } = response
      const message = (data as any)?.message || (data as any)?.msg || error.message
      const code = (data as any)?.code || status.toString()
      const details = (data as any)?.errors || (data as any)?.details

      switch (status) {
        case 400:
          appError = new ValidationError(message, details, code)
          break
        case 401:
          appError = new AuthenticationError(message, code)
          break
        case 403:
          appError = new AuthorizationError(message, code)
          break
        case 404:
          appError = new BusinessError('请求的资源不存在', code)
          break
        case 500:
          appError = new AppError('服务器内部错误', ErrorType.SYSTEM, ErrorLevel.ERROR, code)
          break
        default:
          appError = new BusinessError(message, code, details)
      }
    } else if (request) {
      // 网络错误
      appError = new NetworkError('网络连接失败，请检查网络设置')
    } else {
      // 请求配置错误
      appError = new AppError('请求配置错误', ErrorType.SYSTEM, ErrorLevel.ERROR)
    }

    // 检查是否需要重试
    if (this.shouldRetry(appError, config)) {
      return appError
    }

    this.handleError(appError)
    return appError
  }

  /**
   * 转换为应用错误
   */
  private convertToAppError(error: Error): AppError {
    if (error instanceof AppError) {
      return error
    }

    // 根据错误消息判断错误类型
    const message = error.message.toLowerCase()
    
    if (message.includes('network') || message.includes('fetch')) {
      return new NetworkError(error.message)
    }
    
    if (message.includes('unauthorized') || message.includes('401')) {
      return new AuthenticationError(error.message)
    }
    
    if (message.includes('forbidden') || message.includes('403')) {
      return new AuthorizationError(error.message)
    }
    
    return new AppError(error.message, ErrorType.UNKNOWN, ErrorLevel.ERROR)
  }

  /**
   * 显示错误消息
   */
  private showErrorMessage(error: AppError): void {
    const messageType = this.getMessageType(error.level)
    
    switch (error.type) {
      case ErrorType.VALIDATION:
        ElMessage({
          type: 'warning',
          message: error.message,
          duration: 4000,
          showClose: true
        })
        break
      case ErrorType.NETWORK:
        ElMessage({
          type: 'error',
          message: '网络连接失败，请检查网络设置',
          duration: 5000,
          showClose: true
        })
        break
      case ErrorType.AUTHENTICATION:
        ElMessage({
          type: 'warning',
          message: '登录已过期，请重新登录',
          duration: 4000,
          showClose: true
        })
        break
      case ErrorType.AUTHORIZATION:
        ElMessage({
          type: 'warning',
          message: '没有权限执行此操作',
          duration: 4000,
          showClose: true
        })
        break
      default:
        ElMessage({
          type: messageType,
          message: error.message,
          duration: 4000,
          showClose: true
        })
    }
  }

  /**
   * 显示错误通知
   */
  private showErrorNotification(error: AppError): void {
    ElNotification({
      type: this.getMessageType(error.level),
      title: this.getErrorTitle(error.type),
      message: error.message,
      duration: 6000,
      position: 'top-right'
    })
  }

  /**
   * 记录错误日志
   */
  private logError(error: AppError): void {
    const logData = {
      timestamp: new Date(error.timestamp).toISOString(),
      type: error.type,
      level: error.level,
      message: error.message,
      code: error.code,
      details: error.details,
      stack: error.stack,
      userAgent: navigator.userAgent,
      url: window.location.href
    }

    console.group(`🚨 ${error.level.toUpperCase()} - ${error.type}`)
    console.error('Error:', error.message)
    console.error('Details:', logData)
    console.groupEnd()
  }

  /**
   * 上报错误
   */
  private reportError(error: AppError): void {
    // 这里可以集成第三方错误监控服务，如 Sentry
    // 或者发送到自己的错误收集接口
    console.log('Error reported:', error)
  }

  /**
   * 判断是否需要重试
   */
  private shouldRetry(error: AppError, config?: any): boolean {
    if (!this.config.retryEnabled || !config) {
      return false
    }

    const key = `${config.method}-${config.url}`
    const currentRetries = this.retryCount.get(key) || 0

    if (currentRetries >= this.config.maxRetries) {
      this.retryCount.delete(key)
      return false
    }

    // 只对网络错误和5xx错误进行重试
    if (error.type === ErrorType.NETWORK || (error.code && error.code.startsWith('5'))) {
      this.retryCount.set(key, currentRetries + 1)
      return true
    }

    return false
  }

  /**
   * 获取消息类型
   */
  private getMessageType(level: ErrorLevel): 'success' | 'warning' | 'info' | 'error' {
    switch (level) {
      case ErrorLevel.INFO:
        return 'info'
      case ErrorLevel.WARNING:
        return 'warning'
      case ErrorLevel.ERROR:
      case ErrorLevel.CRITICAL:
        return 'error'
      default:
        return 'error'
    }
  }

  /**
   * 获取错误标题
   */
  private getErrorTitle(type: ErrorType): string {
    switch (type) {
      case ErrorType.NETWORK:
        return '网络错误'
      case ErrorType.AUTHENTICATION:
        return '认证错误'
      case ErrorType.AUTHORIZATION:
        return '权限错误'
      case ErrorType.VALIDATION:
        return '验证错误'
      case ErrorType.BUSINESS:
        return '业务错误'
      case ErrorType.SYSTEM:
        return '系统错误'
      default:
        return '未知错误'
    }
  }

  /**
   * 添加错误监听器
   */
  public addListener(listener: (error: AppError) => void): void {
    this.listeners.push(listener)
  }

  /**
   * 移除错误监听器
   */
  public removeListener(listener: (error: AppError) => void): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  /**
   * 通知所有监听器
   */
  private notifyListeners(error: AppError): void {
    this.listeners.forEach(listener => {
      try {
        listener(error)
      } catch (err) {
        console.error('Error in error listener:', err)
      }
    })
  }

  /**
   * 更新配置
   */
  public updateConfig(config: Partial<ErrorHandlerConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * 清除重试计数
   */
  public clearRetryCount(): void {
    this.retryCount.clear()
  }
}

// 创建全局错误处理器实例
export const errorHandler = ErrorHandler.getInstance()


