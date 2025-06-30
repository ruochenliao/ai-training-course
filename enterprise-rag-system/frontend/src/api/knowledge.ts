// 知识库管理相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 知识库相关类型定义
export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  visibility: 'public' | 'private'
  knowledge_type: string
  owner_id: number
  owner_name?: string
  document_count: number
  vector_count: number
  created_at: string
  updated_at: string
  is_deleted: boolean
}

export interface KnowledgeBaseCreateRequest {
  name: string
  description?: string
  is_public?: boolean
  knowledge_type?: string
}

export interface KnowledgeBaseUpdateRequest {
  name?: string
  description?: string
  visibility?: 'public' | 'private'
}

export interface KnowledgeBaseListParams {
  page?: number
  size?: number
  search?: string
  knowledge_type?: string
  visibility?: string
}

export interface KnowledgeBaseListResponse {
  items: KnowledgeBase[]
  total: number
  page: number
  size: number
  pages: number
}

export interface KnowledgeBaseStats {
  total_knowledge_bases: number
  total_documents: number
  total_vectors: number
  storage_used: number
  recent_activity: any[]
}

// 知识库管理API接口
export const knowledgeApi = {
  // 获取知识库列表
  getKnowledgeBases: (params?: KnowledgeBaseListParams): Promise<ApiResponseData<KnowledgeBaseListResponse>> => {
    return httpClient.get('/knowledge-bases', { params })
  },

  // 获取知识库详情
  getKnowledgeBase: (kbId: number): Promise<ApiResponseData<KnowledgeBase>> => {
    return httpClient.get(`/knowledge-bases/${kbId}`)
  },

  // 创建知识库
  createKnowledgeBase: (data: KnowledgeBaseCreateRequest): Promise<ApiResponseData<KnowledgeBase>> => {
    return httpClient.post('/knowledge-bases', data)
  },

  // 更新知识库
  updateKnowledgeBase: (kbId: number, data: KnowledgeBaseUpdateRequest): Promise<ApiResponseData<KnowledgeBase>> => {
    return httpClient.put(`/knowledge-bases/${kbId}`, data)
  },

  // 删除知识库
  deleteKnowledgeBase: (kbId: number): Promise<ApiResponseData<any>> => {
    return httpClient.delete(`/knowledge-bases/${kbId}`)
  },

  // 获取知识库统计信息
  getKnowledgeBaseStats: (kbId?: number): Promise<ApiResponseData<KnowledgeBaseStats>> => {
    const url = kbId ? `/knowledge-bases/${kbId}/stats` : '/knowledge-bases/stats'
    return httpClient.get(url)
  },

  // 导出知识库
  exportKnowledgeBase: (kbId: number): Promise<Blob> => {
    return httpClient.get(`/knowledge-bases/${kbId}/export`, {
      responseType: 'blob'
    })
  },

  // 导入知识库
  importKnowledgeBase: (file: File): Promise<ApiResponseData<KnowledgeBase>> => {
    const formData = new FormData()
    formData.append('file', file)
    return httpClient.post('/knowledge-bases/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}
