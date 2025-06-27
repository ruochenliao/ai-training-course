import type {Ref} from 'vue'
import {computed, ref} from 'vue'

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

interface UseApiOptions {
  immediate?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: ApiError) => void
}

export function useApi<T = any>(
  url: string | Ref<string>,
  options: UseApiOptions = {}
) {
  const config = useRuntimeConfig()
  const { $fetch } = useNuxtApp()
  
  const data = ref<T | null>(null)
  const error = ref<ApiError | null>(null)
  const loading = ref(false)
  
  const apiUrl = computed(() => {
    const baseUrl = config.public.apiBase
    const endpoint = unref(url)
    return `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
  })
  
  const execute = async (requestOptions: any = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<ApiResponse<T>>(apiUrl.value, {
        ...requestOptions,
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          ...requestOptions.headers
        }
      })
      
      if (response.success) {
        data.value = response.data
        options.onSuccess?.(response.data)
      } else {
        throw new Error(response.message || '请求失败')
      }
      
      return response.data
    } catch (err: any) {
      const apiError: ApiError = {
        message: err.message || '网络请求失败',
        code: err.statusCode || err.code,
        details: err.data
      }
      
      error.value = apiError
      options.onError?.(apiError)
      throw apiError
    } finally {
      loading.value = false
    }
  }
  
  const get = (params?: Record<string, any>) => {
    return execute({
      method: 'GET',
      params
    })
  }
  
  const post = (body?: any) => {
    return execute({
      method: 'POST',
      body
    })
  }
  
  const put = (body?: any) => {
    return execute({
      method: 'PUT',
      body
    })
  }
  
  const del = () => {
    return execute({
      method: 'DELETE'
    })
  }
  
  const patch = (body?: any) => {
    return execute({
      method: 'PATCH',
      body
    })
  }
  
  // 如果设置了immediate，立即执行GET请求
  if (options.immediate) {
    get()
  }
  
  return {
    data: readonly(data),
    error: readonly(error),
    loading: readonly(loading),
    execute,
    get,
    post,
    put,
    delete: del,
    patch,
    refresh: () => get()
  }
}

// 获取认证头
function getAuthHeaders() {
  const token = useCookie('auth-token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// 专用的API组合式函数
export function useKnowledgeBaseApi() {
  return {
    // 获取知识库列表
    getList: (params?: any) => useApi('/knowledge-bases', { immediate: false }).get(params),
    
    // 获取知识库详情
    getDetail: (id: string) => useApi(`/knowledge-bases/${id}`, { immediate: false }).get(),
    
    // 创建知识库
    create: (data: any) => useApi('/knowledge-bases', { immediate: false }).post(data),
    
    // 更新知识库
    update: (id: string, data: any) => useApi(`/knowledge-bases/${id}`, { immediate: false }).put(data),
    
    // 删除知识库
    delete: (id: string) => useApi(`/knowledge-bases/${id}`, { immediate: false }).delete()
  }
}

export function useDocumentApi() {
  return {
    // 获取文档列表
    getList: (params?: any) => useApi('/documents', { immediate: false }).get(params),
    
    // 获取文档详情
    getDetail: (id: string) => useApi(`/documents/${id}`, { immediate: false }).get(),
    
    // 上传文档
    upload: async (formData: FormData) => {
      const config = useRuntimeConfig()
      const { $fetch } = useNuxtApp()
      
      return await $fetch(`${config.public.apiBase}/documents/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          ...getAuthHeaders()
        }
      })
    },
    
    // 删除文档
    delete: (id: string) => useApi(`/documents/${id}`, { immediate: false }).delete(),
    
    // 批量删除文档
    batchDelete: (ids: string[]) => useApi('/documents/batch-delete', { immediate: false }).post({ ids }),
    
    // 重新处理文档
    reprocess: (id: string) => useApi(`/documents/${id}/reprocess`, { immediate: false }).post()
  }
}

export function useUserApi() {
  return {
    // 获取用户列表
    getList: (params?: any) => useApi('/users', { immediate: false }).get(params),
    
    // 获取用户详情
    getDetail: (id: string) => useApi(`/users/${id}`, { immediate: false }).get(),
    
    // 创建用户
    create: (data: any) => useApi('/users', { immediate: false }).post(data),
    
    // 更新用户
    update: (id: string, data: any) => useApi(`/users/${id}`, { immediate: false }).put(data),
    
    // 删除用户
    delete: (id: string) => useApi(`/users/${id}`, { immediate: false }).delete(),
    
    // 重置密码
    resetPassword: (id: string, password: string) => 
      useApi(`/users/${id}/reset-password`, { immediate: false }).post({ password })
  }
}

export function useChatApi() {
  return {
    // 发送聊天消息
    sendMessage: (data: any) => useApi('/chat', { immediate: false }).post(data),
    
    // 获取对话历史
    getConversations: (params?: any) => useApi('/conversations', { immediate: false }).get(params),
    
    // 获取对话详情
    getConversation: (id: string) => useApi(`/conversations/${id}`, { immediate: false }).get(),
    
    // 删除对话
    deleteConversation: (id: string) => useApi(`/conversations/${id}`, { immediate: false }).delete()
  }
}

export function useSearchApi() {
  return {
    // 搜索
    search: (data: any) => useApi('/search', { immediate: false }).post(data),
    
    // 高级搜索
    advancedSearch: (data: any) => useApi('/search/advanced', { immediate: false }).post(data)
  }
}

export function useSystemApi() {
  return {
    // 获取系统状态
    getHealth: () => useApi('/health', { immediate: false }).get(),
    
    // 获取系统统计
    getStats: () => useApi('/system/stats', { immediate: false }).get(),
    
    // 获取系统配置
    getConfig: () => useApi('/system/config', { immediate: false }).get(),
    
    // 更新系统配置
    updateConfig: (data: any) => useApi('/system/config', { immediate: false }).put(data)
  }
}
