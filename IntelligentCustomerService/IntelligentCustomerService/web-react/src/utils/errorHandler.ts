import {message} from 'antd';

/**
 * 错误类型
 */
export enum ErrorType {
  API = 'api',
  NETWORK = 'network',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  BUSINESS = 'business',
  SYSTEM = 'system',
  UNKNOWN = 'unknown',
}

/**
 * 自定义错误类
 */
export class AppError extends Error {
  type: ErrorType;
  code?: string | number;
  data?: any;

  constructor(message: string, type: ErrorType = ErrorType.UNKNOWN, code?: string | number, data?: any) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.code = code;
    this.data = data;
  }
}

/**
 * API错误类
 */
export class ApiError extends AppError {
  constructor(message: string, code: string | number | undefined = undefined, data?: any) {
    super(message, ErrorType.API, code, data);
    this.name = 'ApiError';
  }
}

/**
 * 网络错误类
 */
export class NetworkError extends AppError {
  constructor(message = '网络连接错误，请检查网络设置') {
    super(message, ErrorType.NETWORK);
    this.name = 'NetworkError';
  }
}

/**
 * 验证错误类
 */
export class ValidationError extends AppError {
  constructor(message: string, data?: any) {
    super(message, ErrorType.VALIDATION, undefined, data);
    this.name = 'ValidationError';
  }
}

/**
 * 认证错误类
 */
export class AuthenticationError extends AppError {
  constructor(message = '用户未登录或登录已过期') {
    super(message, ErrorType.AUTHENTICATION);
    this.name = 'AuthenticationError';
  }
}

/**
 * 授权错误类
 */
export class AuthorizationError extends AppError {
  constructor(message = '没有权限执行此操作') {
    super(message, ErrorType.AUTHORIZATION);
    this.name = 'AuthorizationError';
  }
}

/**
 * 错误处理服务
 */
class ErrorHandler {
  private static instance: ErrorHandler;

  // 错误监听器列表
  private listeners: Array<(error: Error) => void> = [];

  // 单例模式
  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * 处理错误
   * @param error 错误对象
   * @param showMessage 是否显示错误消息
   */
  public handleError(error: Error, showMessage = true): void {
    console.error('Error caught:', error);

    // 通知所有监听器
    this.notifyListeners(error);

    // 显示错误消息
    if (showMessage) {
      this.showErrorMessage(error);
    }

    // 根据错误类型处理
    if (error instanceof AppError) {
      this.handleAppError(error);
    } else {
      // 处理未知错误
      this.handleUnknownError(error);
    }

    // 可以在这里添加错误上报逻辑
    this.reportError(error);
  }

  /**
   * 处理应用错误
   * @param error 应用错误对象
   */
  private handleAppError(error: AppError): void {
    switch (error.type) {
      case ErrorType.AUTHENTICATION:
        // 处理认证错误，如跳转到登录页
        this.handleAuthenticationError(error as AuthenticationError);
        break;
      case ErrorType.AUTHORIZATION:
        // 处理授权错误，如跳转到403页面
        this.handleAuthorizationError(error as AuthorizationError);
        break;
      case ErrorType.API:
        // 处理API错误
        this.handleApiError(error as ApiError);
        break;
      case ErrorType.NETWORK:
        // 处理网络错误
        this.handleNetworkError(error as NetworkError);
        break;
      case ErrorType.VALIDATION:
        // 处理验证错误
        this.handleValidationError(error as ValidationError);
        break;
      case ErrorType.BUSINESS:
        // 处理业务错误
        this.handleBusinessError(error);
        break;
      case ErrorType.SYSTEM:
        // 处理系统错误
        this.handleSystemError(error);
        break;
      default:
        // 处理未知错误
        this.handleUnknownError(error);
        break;
    }
  }

  /**
   * 处理认证错误
   * @param error 认证错误对象
   */
  private handleAuthenticationError(error: AuthenticationError): void {
    // 跳转到登录页
    if (window.location.pathname !== '/login') {
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
    }
  }

  /**
   * 处理授权错误
   * @param error 授权错误对象
   */
  private handleAuthorizationError(error: AuthorizationError): void {
    // 跳转到403页面
    if (window.location.pathname !== '/403') {
      window.location.href = '/403';
    }
  }

  /**
   * 处理API错误
   * @param error API错误对象
   */
  private handleApiError(error: ApiError): void {
    // 根据错误码处理
    if (error.code === 401) {
      this.handleAuthenticationError(new AuthenticationError());
    } else if (error.code === 403) {
      this.handleAuthorizationError(new AuthorizationError());
    }
  }

  /**
   * 处理网络错误
   * @param error 网络错误对象
   */
  private handleNetworkError(error: NetworkError): void {
    // 可以在这里添加网络错误处理逻辑
    console.log('Network error:', error);
  }

  /**
   * 处理验证错误
   * @param error 验证错误对象
   */
  private handleValidationError(error: ValidationError): void {
    // 可以在这里添加验证错误处理逻辑
    console.log('Validation error:', error);
  }

  /**
   * 处理业务错误
   * @param error 业务错误对象
   */
  private handleBusinessError(error: AppError): void {
    // 可以在这里添加业务错误处理逻辑
    console.log('Business error:', error);
  }

  /**
   * 处理系统错误
   * @param error 系统错误对象
   */
  private handleSystemError(error: AppError): void {
    // 可以在这里添加系统错误处理逻辑
    console.log('System error:', error);
  }

  /**
   * 处理未知错误
   * @param error 未知错误对象
   */
  private handleUnknownError(error: Error): void {
    // 可以在这里添加未知错误处理逻辑
    console.log('Unknown error:', error);
  }

  /**
   * 显示错误消息
   * @param error 错误对象
   */
  private showErrorMessage(error: Error): void {
    const errorMessage = error.message || '发生了未知错误';
    
    // 根据错误类型显示不同的消息
    if (error instanceof AppError) {
      switch (error.type) {
        case ErrorType.NETWORK:
          message.error('网络连接错误，请检查网络设置');
          break;
        case ErrorType.AUTHENTICATION:
          message.error('用户未登录或登录已过期');
          break;
        case ErrorType.AUTHORIZATION:
          message.error('没有权限执行此操作');
          break;
        default:
          message.error(errorMessage);
          break;
      }
    } else {
      message.error(errorMessage);
    }
  }

  /**
   * 上报错误
   * @param error 错误对象
   */
  private reportError(error: Error): void {
    // 可以在这里添加错误上报逻辑，如发送到服务器
    // 例如使用Sentry等工具
    console.log('Error reported:', error);
  }

  /**
   * 添加错误监听器
   * @param listener 错误监听器
   */
  public addListener(listener: (error: Error) => void): void {
    this.listeners.push(listener);
  }

  /**
   * 移除错误监听器
   * @param listener 错误监听器
   */
  public removeListener(listener: (error: Error) => void): void {
    const index = this.listeners.indexOf(listener);
    if (index !== -1) {
      this.listeners.splice(index, 1);
    }
  }

  /**
   * 通知所有监听器
   * @param error 错误对象
   */
  private notifyListeners(error: Error): void {
    this.listeners.forEach(listener => {
      try {
        listener(error);
      } catch (e) {
        console.error('Error in error listener:', e);
      }
    });
  }
}

// 创建全局错误处理器实例
const errorHandler = ErrorHandler.getInstance();

// 设置全局错误处理
if (typeof window !== 'undefined') {
  // 处理未捕获的Promise错误
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error 
      ? event.reason 
      : new Error(String(event.reason));
    errorHandler.handleError(error);
  });

  // 处理未捕获的JS错误
  window.addEventListener('error', (event) => {
    errorHandler.handleError(event.error || new Error(event.message));
  });
}

export default errorHandler; 