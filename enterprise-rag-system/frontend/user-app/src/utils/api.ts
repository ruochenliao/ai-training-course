import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios'

interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

interface ApiError {
  message: string
  code?: string | number
  details?: any
}

class ApiClient {
  private instance: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    this.instance = axios.create({
      baseURL: `${this.baseURL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = this.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        return response
      },
      (error) => {
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || '网络请求失败',
          code: error.response?.status || error.code,
          details: error.response?.data
        }

        // 处理认证错误
        if (error.response?.status === 401) {
          this.clearToken()
          window.location.href = '/login'
        }

        return Promise.reject(apiError)
      }
    )
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth-token')
    }
    return null
  }

  private setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth-token', token)
    }
  }

  private clearToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth-token')
    }
  }

  // 通用请求方法
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.instance.request<ApiResponse<T>>(config)
      return response.data.data
    } catch (error) {
      throw error
    }
  }

  // GET请求
  async get<T = any>(url: string, params?: any): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url,
      params
    })
  }

  // POST请求
  async post<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data
    })
  }

  // PUT请求
  async put<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      method: 'PUT',
      url,
      data
    })
  }

  // DELETE请求
  async delete<T = any>(url: string): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url
    })
  }

  // 文件上传
  async upload<T = any>(url: string, formData: FormData, onProgress?: (progress: number) => void): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }

  // 认证相关
  async login(credentials: { username: string; password: string }) {
    const response = await this.post<{ access_token: string; user: any }>('/auth/login', credentials)
    this.setToken(response.access_token)
    return response
  }

  async logout() {
    try {
      await this.post('/auth/logout')
    } finally {
      this.clearToken()
    }
  }

  async getCurrentUser() {
    return this.get('/auth/me')
  }

  // 知识库相关
  async getKnowledgeBases(params?: any) {
    return this.get('/knowledge-bases', params)
  }

  async getKnowledgeBase(id: string) {
    return this.get(`/knowledge-bases/${id}`)
  }

  // 聊天相关
  async sendChatMessage(data: {
    message: string
    conversation_id?: number
    knowledge_base_ids?: number[]
    stream?: boolean
  }) {
    return this.post('/chat', data)
  }

  async getConversations(params?: any) {
    return this.get('/conversations', params)
  }

  async getConversation(id: string) {
    return this.get(`/conversations/${id}`)
  }

  async deleteConversation(id: string) {
    return this.delete(`/conversations/${id}`)
  }

  // 搜索相关
  async search(data: {
    query: string
    knowledge_base_ids?: number[]
    top_k?: number
    search_type?: string
  }) {
    return this.post('/search', data)
  }

  // 文档相关
  async getDocuments(params?: any) {
    return this.get('/documents', params)
  }

  async uploadDocument(formData: FormData, onProgress?: (progress: number) => void) {
    return this.upload('/documents/upload', formData, onProgress)
  }

  // 系统相关
  async getSystemHealth() {
    return this.get('/health')
  }

  async getSystemStats() {
    return this.get('/system/stats')
  }
}

// 创建API客户端实例
const apiClient = new ApiClient()

export default apiClient

// 导出类型
export type { ApiResponse, ApiError }

// 导出便捷方法
export const {
  get,
  post,
  put,
  delete: del,
  upload,
  login,
  logout,
  getCurrentUser,
  getKnowledgeBases,
  getKnowledgeBase,
  sendChatMessage,
  getConversations,
  getConversation,
  deleteConversation,
  search,
  getDocuments,
  uploadDocument,
  getSystemHealth,
  getSystemStats
} = apiClient
