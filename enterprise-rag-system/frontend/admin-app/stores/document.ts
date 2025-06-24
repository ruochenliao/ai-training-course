import { defineStore } from 'pinia'
import axios from 'axios'

interface Document {
  id: string
  name: string
  type: string
  size: number
  status: 'processed' | 'processing' | 'failed' | 'pending'
  knowledge_base_id: string
  knowledge_base_name: string
  chunks_count?: number
  avg_chunk_length?: number
  processing_error?: string
  created_at: string
  updated_at: string
}

interface UploadTask {
  id: string
  fileName: string
  status: 'uploading' | 'completed' | 'failed'
  progress: number
  uploadedSize: number
  totalSize: number
  error?: string
}

export const useDocumentStore = defineStore('document', {
  state: () => ({
    documents: [] as Document[],
    uploadTasks: [] as UploadTask[],
    loading: false,
    error: null as string | null
  }),

  getters: {
    getDocumentById: (state) => (id: string) => {
      return state.documents.find(doc => doc.id === id)
    },
    
    getDocumentsByKnowledgeBase: (state) => (knowledgeBaseId: string) => {
      return state.documents.filter(doc => doc.knowledge_base_id === knowledgeBaseId)
    },
    
    getDocumentsByStatus: (state) => (status: string) => {
      return state.documents.filter(doc => doc.status === status)
    },
    
    getTotalDocuments: (state) => {
      return state.documents.length
    },
    
    getProcessingDocuments: (state) => {
      return state.documents.filter(doc => doc.status === 'processing').length
    }
  },

  actions: {
    // 获取文档列表
    async fetchDocuments() {
      this.loading = true
      this.error = null

      try {
        // 模拟数据，实际应该调用 API
        await new Promise(resolve => setTimeout(resolve, 500))

        this.documents = [
          {
            id: '1',
            name: '产品使用手册.pdf',
            type: 'pdf',
            size: 2048576,
            status: 'processed',
            knowledge_base_id: '1',
            knowledge_base_name: '企业产品手册',
            chunks_count: 45,
            avg_chunk_length: 512,
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-15T10:35:00Z'
          },
          {
            id: '2',
            name: 'API接口文档.docx',
            type: 'docx',
            size: 1024000,
            status: 'processing',
            knowledge_base_id: '2',
            knowledge_base_name: '技术文档库',
            created_at: '2024-01-16T14:20:00Z',
            updated_at: '2024-01-16T14:20:00Z'
          },
          {
            id: '3',
            name: '客服FAQ.txt',
            type: 'txt',
            size: 512000,
            status: 'failed',
            knowledge_base_id: '3',
            knowledge_base_name: '客户服务知识库',
            processing_error: '文档格式不支持',
            created_at: '2024-01-17T09:15:00Z',
            updated_at: '2024-01-17T09:20:00Z'
          },
          {
            id: '4',
            name: '培训材料.pptx',
            type: 'pptx',
            size: 4096000,
            status: 'pending',
            knowledge_base_id: '1',
            knowledge_base_name: '企业产品手册',
            created_at: '2024-01-18T16:45:00Z',
            updated_at: '2024-01-18T16:45:00Z'
          }
        ]

        return this.documents
      } catch (error) {
        this.error = '获取文档列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个文档详情
    async getDocument(id: string) {
      try {
        const response = await axios.get(`/api/v1/documents/${id}`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取文档详情失败'
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
        
        // 添加到本地状态
        const newDocument = response.data
        this.documents.unshift(newDocument)
        
        return newDocument
      } catch (error) {
        this.error = error.response?.data?.message || '文档上传失败'
        throw error
      }
    },

    // 批量上传文档
    async batchUploadDocuments(files: File[], knowledgeBaseId: string, onProgress?: (progress: any) => void) {
      const tasks: UploadTask[] = []
      
      for (const file of files) {
        const taskId = Date.now() + Math.random()
        const task: UploadTask = {
          id: taskId.toString(),
          fileName: file.name,
          status: 'uploading',
          progress: 0,
          uploadedSize: 0,
          totalSize: file.size
        }
        
        tasks.push(task)
        this.uploadTasks.push(task)
        
        try {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('knowledge_base_id', knowledgeBaseId)
          
          await this.uploadDocument(formData, (progressEvent) => {
            task.progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            task.uploadedSize = progressEvent.loaded
            onProgress?.(task)
          })
          
          task.status = 'completed'
          task.progress = 100
        } catch (error) {
          task.status = 'failed'
          task.error = error.message || '上传失败'
        }
      }
      
      return tasks
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

    // 批量删除文档
    async batchDeleteDocuments(ids: string[]) {
      try {
        await axios.post('/api/v1/documents/batch-delete', { ids })
        
        // 从本地状态中移除
        this.documents = this.documents.filter(doc => !ids.includes(doc.id))
      } catch (error) {
        this.error = error.response?.data?.message || '批量删除失败'
        throw error
      }
    },

    // 重新处理文档
    async reprocessDocument(id: string) {
      try {
        const response = await axios.post(`/api/v1/documents/${id}/reprocess`)
        
        // 更新本地状态
        const document = this.documents.find(doc => doc.id === id)
        if (document) {
          document.status = 'processing'
          document.processing_error = undefined
        }
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '重新处理失败'
        throw error
      }
    },

    // 批量重新处理文档
    async batchReprocessDocuments(ids: string[]) {
      try {
        await axios.post('/api/v1/documents/batch-reprocess', { ids })
        
        // 更新本地状态
        this.documents.forEach(doc => {
          if (ids.includes(doc.id)) {
            doc.status = 'processing'
            doc.processing_error = undefined
          }
        })
      } catch (error) {
        this.error = error.response?.data?.message || '批量重新处理失败'
        throw error
      }
    },

    // 下载文档
    async downloadDocument(id: string) {
      try {
        const response = await axios.get(`/api/v1/documents/${id}/download`, {
          responseType: 'blob'
        })
        
        // 创建下载链接
        const document = this.getDocumentById(id)
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', document?.name || 'document')
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '下载文档失败'
        throw error
      }
    },

    // 批量下载文档
    async batchDownloadDocuments(ids: string[]) {
      try {
        const response = await axios.post('/api/v1/documents/batch-download', { ids }, {
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `documents-${Date.now()}.zip`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '批量下载失败'
        throw error
      }
    },

    // 搜索文档
    async searchDocuments(query: string, filters?: any) {
      try {
        const params = { q: query, ...filters }
        const response = await axios.get('/api/v1/documents/search', { params })
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '搜索失败'
        throw error
      }
    },

    // 获取文档处理状态
    async getProcessingStatus(id: string) {
      try {
        const response = await axios.get(`/api/v1/documents/${id}/status`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取处理状态失败'
        throw error
      }
    },

    // 清除上传任务
    clearUploadTasks() {
      this.uploadTasks = []
    },

    // 移除上传任务
    removeUploadTask(taskId: string) {
      this.uploadTasks = this.uploadTasks.filter(task => task.id !== taskId)
    },

    // 清除错误状态
    clearError() {
      this.error = null
    },

    // 重置状态
    reset() {
      this.documents = []
      this.uploadTasks = []
      this.loading = false
      this.error = null
    }
  }
})
