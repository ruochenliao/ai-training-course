import {defineStore} from 'pinia'
import axios from 'axios'

interface KnowledgeBase {
  id: string
  name: string
  description: string
  status: 'active' | 'disabled' | 'processing'
  access_level: 'private' | 'team' | 'public'
  tags: string[]
  document_count: number
  created_at: string
  updated_at: string
}

interface Document {
  id: string
  name: string
  type: string
  size: number
  status: 'processed' | 'processing' | 'failed' | 'pending'
  knowledge_base_id: string
  created_at: string
  updated_at: string
}

interface Task {
  id: string
  type: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  started_at: string
  completed_at?: string
  error_message?: string
}

interface KnowledgeBaseStats {
  documentCount: number
  vectorCount: number
  nodeCount: number
  storageSize: number
}

export const useKnowledgeBaseStore = defineStore('knowledgeBase', {
  state: () => ({
    knowledgeBases: [] as KnowledgeBase[],
    currentKnowledgeBase: null as KnowledgeBase | null,
    documents: [] as Document[],
    tasks: [] as Task[],
    loading: false,
    error: null as string | null
  }),

  getters: {
    getKnowledgeBaseById: (state) => (id: string) => {
      return state.knowledgeBases.find(kb => kb.id === id)
    },
    
    getDocumentsByKnowledgeBase: (state) => (knowledgeBaseId: string) => {
      return state.documents.filter(doc => doc.knowledge_base_id === knowledgeBaseId)
    },
    
    getActiveKnowledgeBases: (state) => {
      return state.knowledgeBases.filter(kb => kb.status === 'active')
    },
    
    getTotalDocuments: (state) => {
      return state.knowledgeBases.reduce((total, kb) => total + kb.document_count, 0)
    }
  },

  actions: {
    // 获取知识库列表
    async fetchKnowledgeBases() {
      this.loading = true
      this.error = null

      try {
        // 模拟数据，实际应该调用 API
        await new Promise(resolve => setTimeout(resolve, 500)) // 模拟网络延迟

        this.knowledgeBases = [
          {
            id: '1',
            name: '企业产品手册',
            description: '包含所有产品的详细说明和使用指南',
            status: 'active',
            access_level: 'team',
            tags: ['产品', '手册', '指南'],
            document_count: 156,
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-20T15:45:00Z'
          },
          {
            id: '2',
            name: '技术文档库',
            description: '技术规范、API文档和开发指南',
            status: 'active',
            access_level: 'private',
            tags: ['技术', 'API', '开发'],
            document_count: 89,
            created_at: '2024-01-10T09:15:00Z',
            updated_at: '2024-01-18T11:20:00Z'
          },
          {
            id: '3',
            name: '客户服务知识库',
            description: '常见问题解答和客户服务流程',
            status: 'processing',
            access_level: 'public',
            tags: ['客服', 'FAQ', '流程'],
            document_count: 234,
            created_at: '2024-01-05T14:20:00Z',
            updated_at: '2024-01-22T16:30:00Z'
          }
        ]

        return this.knowledgeBases
      } catch (error) {
        this.error = '获取知识库列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个知识库详情
    async getKnowledgeBase(id: string) {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${id}`)
        this.currentKnowledgeBase = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取知识库详情失败'
        throw error
      }
    },

    // 创建知识库
    async createKnowledgeBase(data: Partial<KnowledgeBase>) {
      try {
        const response = await axios.post('/api/v1/knowledge-bases', data)
        const newKnowledgeBase = response.data
        this.knowledgeBases.push(newKnowledgeBase)
        return newKnowledgeBase
      } catch (error) {
        this.error = error.response?.data?.message || '创建知识库失败'
        throw error
      }
    },

    // 更新知识库
    async updateKnowledgeBase(id: string, data: Partial<KnowledgeBase>) {
      try {
        const response = await axios.put(`/api/v1/knowledge-bases/${id}`, data)
        const updatedKnowledgeBase = response.data
        
        // 更新本地状态
        const index = this.knowledgeBases.findIndex(kb => kb.id === id)
        if (index > -1) {
          this.knowledgeBases[index] = updatedKnowledgeBase
        }
        
        if (this.currentKnowledgeBase?.id === id) {
          this.currentKnowledgeBase = updatedKnowledgeBase
        }
        
        return updatedKnowledgeBase
      } catch (error) {
        this.error = error.response?.data?.message || '更新知识库失败'
        throw error
      }
    },

    // 删除知识库
    async deleteKnowledgeBase(id: string) {
      try {
        await axios.delete(`/api/v1/knowledge-bases/${id}`)
        
        // 从本地状态中移除
        this.knowledgeBases = this.knowledgeBases.filter(kb => kb.id !== id)
        
        if (this.currentKnowledgeBase?.id === id) {
          this.currentKnowledgeBase = null
        }
      } catch (error) {
        this.error = error.response?.data?.message || '删除知识库失败'
        throw error
      }
    },

    // 批量删除知识库
    async batchDeleteKnowledgeBases(ids: string[]) {
      try {
        await axios.post('/api/v1/knowledge-bases/batch-delete', { ids })
        
        // 从本地状态中移除
        this.knowledgeBases = this.knowledgeBases.filter(kb => !ids.includes(kb.id))
      } catch (error) {
        this.error = error.response?.data?.message || '批量删除失败'
        throw error
      }
    },

    // 批量导出知识库
    async batchExportKnowledgeBases(ids: string[]) {
      try {
        const response = await axios.post('/api/v1/knowledge-bases/batch-export', { ids }, {
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `knowledge-bases-export-${Date.now()}.zip`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '批量导出失败'
        throw error
      }
    },

    // 获取知识库统计信息
    async getKnowledgeBaseStats(id: string): Promise<KnowledgeBaseStats> {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${id}/stats`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取统计信息失败'
        throw error
      }
    },

    // 获取文档列表
    async getDocuments(knowledgeBaseId: string) {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${knowledgeBaseId}/documents`)
        this.documents = response.data.items || []
        return this.documents
      } catch (error) {
        this.error = error.response?.data?.message || '获取文档列表失败'
        throw error
      }
    },

    // 上传文档
    async uploadDocument(formData: FormData, onProgress?: (progressEvent: any) => void) {
      try {
        const response = await axios.post('/api/v1/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: onProgress
        })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '文档上传失败'
        throw error
      }
    },

    // 删除文档
    async deleteDocument(id: string) {
      try {
        await axios.delete(`/api/v1/documents/${id}`)
        
        // 从本地状态中移除
        this.documents = this.documents.filter(doc => doc.id !== id)
      } catch (error) {
        this.error = error.response?.data?.message || '删除文档失败'
        throw error
      }
    },

    // 获取最近上传的文档
    async getRecentUploads(knowledgeBaseId: string) {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${knowledgeBaseId}/recent-uploads`)
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '获取最近上传失败'
        throw error
      }
    },

    // 获取处理任务
    async getTasks(knowledgeBaseId: string) {
      try {
        const response = await axios.get(`/api/v1/knowledge-bases/${knowledgeBaseId}/tasks`)
        this.tasks = response.data.items || []
        return this.tasks
      } catch (error) {
        this.error = error.response?.data?.message || '获取任务列表失败'
        throw error
      }
    },

    // 获取任务详情
    async getTask(taskId: string) {
      try {
        const response = await axios.get(`/api/v1/tasks/${taskId}`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取任务详情失败'
        throw error
      }
    },

    // 取消任务
    async cancelTask(taskId: string) {
      try {
        await axios.post(`/api/v1/tasks/${taskId}/cancel`)
        
        // 更新本地任务状态
        const task = this.tasks.find(t => t.id === taskId)
        if (task) {
          task.status = 'failed'
        }
      } catch (error) {
        this.error = error.response?.data?.message || '取消任务失败'
        throw error
      }
    },

    // 重试任务
    async retryTask(taskId: string) {
      try {
        const response = await axios.post(`/api/v1/tasks/${taskId}/retry`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '重试任务失败'
        throw error
      }
    },

    // 搜索知识库
    async searchKnowledgeBases(query: string, filters?: any) {
      try {
        const params = { q: query, ...filters }
        const response = await axios.get('/api/v1/knowledge-bases/search', { params })
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '搜索失败'
        throw error
      }
    },

    // 清除错误状态
    clearError() {
      this.error = null
    },

    // 重置状态
    reset() {
      this.knowledgeBases = []
      this.currentKnowledgeBase = null
      this.documents = []
      this.tasks = []
      this.loading = false
      this.error = null
    }
  }
})
