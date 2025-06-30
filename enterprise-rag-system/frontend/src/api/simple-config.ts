// 简化的API配置文件

import axios from 'axios'
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
export const simpleHttpClient = axios.create(API_CONFIG)

// 简单的token管理
export const simpleTokenManager = {
  getToken(): string | null {
    return localStorage.getItem('access_token')
  },

  setToken(token: string): void {
    localStorage.setItem('access_token', token)
  },

  removeToken(): void {
    localStorage.removeItem('access_token')
  }
}

// 请求拦截器
simpleHttpClient.interceptors.request.use(
  (config) => {
    // 添加认证头
    const token = simpleTokenManager.getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 开发环境日志
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
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
simpleHttpClient.interceptors.response.use(
  (response) => {
    // 开发环境日志
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ API Response:', {
        status: response.status,
        url: response.config.url,
        data: response.data,
      })
    }

    return response
  },
  error => {
    const { response } = error

    // 错误日志
    console.error('❌ API Error:', {
      status: response?.status,
      message: error.message,
      data: response?.data,
    })

    // 处理 401 未授权错误
    if (response?.status === 401) {
      simpleTokenManager.removeToken()
      message.error('登录已过期，请重新登录')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // 处理其他错误
    const errorMessage = response?.data?.message || error.message || '请求失败'
    message.error(errorMessage)

    return Promise.reject(error)
  }
)

export default simpleHttpClient
