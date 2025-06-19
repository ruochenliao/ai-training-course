import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios'
import {message} from 'antd'
import {useAuthStore} from '@/store/auth'
import type {ApiResponse} from '@/types/api'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:9999',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 添加token（登录接口除外）
    if (!config.url?.includes('/access_token')) {
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response

    // 如果是下载文件等特殊情况，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }

    // 检查业务状态码 - 匹配后端返回格式 {code: 200, msg: "OK", data: {...}}
    if (data.code === 200) {
      return data
    }

    // 处理业务错误
    const errorMessage = data.msg || '请求失败'
    return Promise.reject(new Error(errorMessage))
  },
  (error) => {
    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          message.error('登录已过期，请重新登录')
          useAuthStore.getState().clearAuth()
          window.location.href = '/login'
          break
        case 403:
          message.error('没有权限访问该资源')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data?.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error('请求配置错误')
    }

    return Promise.reject(error)
  },
)

export default request
export { request }
