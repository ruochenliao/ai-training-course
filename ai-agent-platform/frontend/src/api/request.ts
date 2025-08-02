import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { NProgressStart, NProgressDone } from '@/utils/nprogress'
import { getToken, removeToken } from '@/utils/auth'
import router from '@/router'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应数据接口
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp?: number
}

// 请求计数器，用于控制loading
let requestCount = 0

// 显示loading
const showLoading = () => {
  if (requestCount === 0) {
    NProgressStart()
  }
  requestCount++
}

// 隐藏loading
const hideLoading = () => {
  requestCount--
  if (requestCount <= 0) {
    requestCount = 0
    NProgressDone()
  }
}

// 请求拦截器
request.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 显示loading
    showLoading()

    // 添加token
    const token = getToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加时间戳防止缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }

    return config
  },
  (error) => {
    hideLoading()
    console.error('Request error:', error)
    ElMessage.error('请求配置错误')
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    hideLoading()

    // 如果响应状态码是2xx，直接返回数据
    if (response.status >= 200 && response.status < 300) {
      // 包装响应数据为统一格式
      return {
        code: 200,
        message: 'success',
        data: response.data
      }
    }

    // 业务错误
    ElMessage.error('请求失败')
    return Promise.reject(new Error('请求失败'))
  },
  (error) => {
    hideLoading()

    console.error('Response error:', error)

    // 网络错误
    if (!error.response) {
      ElMessage.error('网络连接异常，请检查网络设置')
      return Promise.reject(error)
    }

    const { status, data } = error.response

    switch (status) {
      case 401:
        ElMessageBox.confirm('登录状态已过期，请重新登录', '系统提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          removeToken()
          router.push('/login')
        }).catch(() => {
          // 用户取消
        })
        break
      case 403:
        ElMessage.error('没有权限访问该资源')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 422:
        ElMessage.error(data?.message || '请求参数验证失败')
        break
      case 500:
        ElMessage.error('服务器内部错误')
        break
      case 502:
        ElMessage.error('网关错误')
        break
      case 503:
        ElMessage.error('服务暂时不可用')
        break
      case 504:
        ElMessage.error('网关超时')
        break
      default:
        ElMessage.error(data?.message || `请求失败 (${status})`)
    }

    return Promise.reject(error)
  }
)

export default request
