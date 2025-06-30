// 文档管理相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 文档相关类型定义
export interface Document {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  knowledge_base_id: number
  knowledge_base_name?: string
  upload_user_id: number
  upload_user_name?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  processing_progress: number
  chunk_count: number
  vector_count: number
  error_message?: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  processed_at?: string
}

export interface DocumentUploadRequest {
  knowledge_base_id: number
  files: File[]
  auto_process?: boolean
}

export interface DocumentListParams {
  page?: number
  size?: number
  search?: string
  knowledge_base_id?: number
  status?: string
  file_type?: string
}

export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DocumentProcessingStatus {
  document_id: number
  status: string
  progress: number
  current_step: string
  error_message?: string
  estimated_time_remaining?: number
}

export interface DocumentChunk {
  id: number
  document_id: number
  content: string
  chunk_index: number
  token_count: number
  metadata: Record<string, any>
  created_at: string
}

// 文档管理API接口
export const documentsApi = {
  // 获取文档列表
  getDocuments: (params?: DocumentListParams): Promise<ApiResponseData<DocumentListResponse>> => {
    return httpClient.get('/documents', { params })
  },

  // 获取文档详情
  getDocument: (docId: number): Promise<ApiResponseData<Document>> => {
    return httpClient.get(`/documents/${docId}`)
  },

  // 上传文档
  uploadDocuments: (data: DocumentUploadRequest): Promise<ApiResponseData<Document[]>> => {
    const formData = new FormData()
    formData.append('knowledge_base_id', data.knowledge_base_id.toString())
    data.files.forEach(file => {
      formData.append('files', file)
    })
    if (data.auto_process !== undefined) {
      formData.append('auto_process', data.auto_process.toString())
    }

    return httpClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 批量上传文档
  batchUpload: (files: File[], knowledgeBaseId: number): Promise<ApiResponseData<Document[]>> => {
    const formData = new FormData()
    formData.append('knowledge_base_id', knowledgeBaseId.toString())
    files.forEach(file => {
      formData.append('files', file)
    })

    return httpClient.post('/documents/batch-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除文档
  deleteDocument: (docId: number): Promise<ApiResponseData<any>> => {
    return httpClient.delete(`/documents/${docId}`)
  },

  // 批量删除文档
  batchDeleteDocuments: (docIds: number[]): Promise<ApiResponseData<any>> => {
    return httpClient.post('/documents/batch-delete', { document_ids: docIds })
  },

  // 处理文档
  processDocument: (docId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/documents/${docId}/process`)
  },

  // 重新处理文档
  reprocessDocument: (docId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/documents/${docId}/reprocess`)
  },

  // 获取文档处理状态
  getProcessingStatus: (docId: number): Promise<ApiResponseData<DocumentProcessingStatus>> => {
    return httpClient.get(`/documents/${docId}/status`)
  },

  // 获取文档分块
  getDocumentChunks: (docId: number, page?: number, size?: number): Promise<ApiResponseData<DocumentChunk[]>> => {
    return httpClient.get(`/documents/${docId}/chunks`, {
      params: { page, size }
    })
  },

  // 下载文档
  downloadDocument: (docId: number): Promise<Blob> => {
    return httpClient.get(`/documents/${docId}/download`, {
      responseType: 'blob'
    })
  },

  // 预览文档
  previewDocument: (docId: number): Promise<ApiResponseData<any>> => {
    return httpClient.get(`/documents/${docId}/preview`)
  },

  // 获取文档统计信息
  getDocumentStats: (): Promise<ApiResponseData<any>> => {
    return httpClient.get('/documents/stats')
  }
}
