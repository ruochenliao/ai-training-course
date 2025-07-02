/**
 * HTTP请求封装
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import type { BaseResponse } from '@/types'

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
  (config: AxiosRequestConfig) => {
    const authStore = useAuthStore()
    
    // 添加认证token
    if (authStore.token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${authStore.token}`
      }
    }
    
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<BaseResponse>) => {
    const { data } = response
    
    // 检查业务状态码
    if (data.code === 200) {
      return data
    } else {
      // 业务错误
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
  },
  async (error) => {
    const { response } = error
    const authStore = useAuthStore()
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，尝试刷新token
          if (authStore.refreshToken && !error.config._retry) {
            error.config._retry = true
            try {
              await authStore.refreshAccessToken()
              // 重新发送原请求
              return service(error.config)
            } catch (refreshError) {
              // 刷新失败，跳转到登录页
              authStore.logout()
              router.push('/login')
              ElMessage.error('登录已过期，请重新登录')
            }
          } else {
            authStore.logout()
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
          }
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络设置')
    }
    
    return Promise.reject(error)
  }
)

// 请求方法封装
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<BaseResponse<T>> {
    return service.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<BaseResponse<T>> {
    return service.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<BaseResponse<T>> {
    return service.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<BaseResponse<T>> {
    return service.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<BaseResponse<T>> {
    return service.patch(url, data, config)
  }
}

export default service
