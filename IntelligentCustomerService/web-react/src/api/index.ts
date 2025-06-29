import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios'
import {message} from 'antd'
import {useAuthStore} from '@/store/auth.ts'

// API响应接口
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

// 分页响应接口
export interface PageResponse<T = any> {
  data: T[]
  total: number
  page: number
  page_size: number
}

// 创建axios实例
const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: '/',
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 添加token
      const { token } = useAuthStore.getState()
      if (token) {
        // 将token放在header.token中，而不是Authorization
        config.headers.token = token
      }

      // 添加时间戳防止缓存
      if (config.method === 'get') {
        config.params = {
          ...config.params,
          _t: Date.now(),
        }
      }

      return config
    },
    (error) => {
      return Promise.reject(error)
    },
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse<ApiResponse>) => {
      const { data } = response

      // 检查业务状态码
      if (data.code === 200) {
        return response
      }

      // 处理业务错误
      if (data.code === 401) {
        // token过期，清除认证信息并跳转到登录页
        const { clearAuth } = useAuthStore.getState()
        clearAuth()
        window.location.href = '/login'
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }

      if (data.code === 403) {
        message.error('没有权限访问该资源')
        return Promise.reject(new Error('没有权限访问该资源'))
      }

      // 其他业务错误
      const errorMessage = data.msg || '请求失败'
      message.error(errorMessage)
      return Promise.reject(new Error(errorMessage))
    },
    (error) => {
      // 网络错误处理
      if (error.response) {
        const { status, data } = error.response

        switch (status) {
          case 400:
            message.error(data?.msg || '请求参数错误')
            break
          case 401: {
            const { clearAuth } = useAuthStore.getState()
            clearAuth()
            window.location.href = '/login'
            break
          }
          case 403:
            message.error('没有权限访问该资源')
            window.location.href = '/403'
            break
          case 404:
            message.error('请求的资源不存在')
            break
          case 500:
            message.error('服务器内部错误')
            window.location.href = '/500'
            break
          default:
            message.error(data?.msg || `请求失败 (${status})`)
        }
      } else if (error.request) {
        message.error('网络连接失败，请检查网络设置')
      } else {
        message.error(error.message || '请求失败')
      }

      return Promise.reject(error)
    },
  )

  return instance
}

// 创建API实例
export const api = createAxiosInstance()

// 通用请求方法
export const request = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return api.get(url, config).then((res) => res.data)
  },

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return api.post(url, data, config).then((res) => res.data)
  },

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return api.put(url, data, config).then((res) => res.data)
  },

  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return api.delete(url, config).then((res) => res.data)
  },

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return api.patch(url, data, config).then((res) => res.data)
  },
}

// 文件上传
export const uploadFile = (url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  return api
    .post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    .then((res) => res.data)
}

// 文件下载
export const downloadFile = (url: string, filename?: string): Promise<void> => {
  return api
    .get(url, {
      responseType: 'blob',
    })
    .then((response) => {
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
}

export default api
