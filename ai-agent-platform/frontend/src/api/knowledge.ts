import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 知识库信息
export interface Knowledge {
  id: number
  name: string
  description: string
  type: 'public' | 'private'
  status: 'active' | 'inactive'
  file_count: number
  size: number
  created_at: string
  updated_at: string
  user_id: number
}

// 知识库文件
export interface KnowledgeFile {
  id: number
  name: string
  type: string
  size: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  url: string
  created_at: string
  knowledge_id: number
}

// 创建知识库参数
export interface CreateKnowledgeParams {
  name: string
  description: string
  type: 'public' | 'private'
}

// 更新知识库参数
export interface UpdateKnowledgeParams extends Partial<CreateKnowledgeParams> {
  status?: 'active' | 'inactive'
}

// 知识库列表查询参数
export interface KnowledgeListParams {
  page?: number
  size?: number
  search?: string
  type?: string
  status?: string
}

// 知识库列表响应
export interface KnowledgeListResponse {
  items: Knowledge[]
  total: number
  page: number
  size: number
  pages: number
}

// 文件上传参数
export interface UploadFileParams {
  knowledge_id: number
  files: File[]
}

// 知识库API接口
export const knowledgeApi = {
  // 获取知识库列表
  getKnowledgeBases: (params?: any): Promise<ApiResponse<Knowledge[]>> => {
    return request({
      url: '/api/v1/knowledge-bases',
      method: 'get',
      params
    })
  },

  // 获取我的知识库列表
  getMyKnowledgeBases: (params?: any): Promise<ApiResponse<Knowledge[]>> => {
    return request({
      url: '/api/v1/knowledge-bases/my',
      method: 'get',
      params
    })
  },

  // 获取知识库详情
  getKnowledgeBase: (id: number): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: `/api/v1/knowledge-bases/${id}`,
      method: 'get'
    })
  },

  // 创建知识库
  createKnowledgeBase: (data: CreateKnowledgeParams): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: '/api/v1/knowledge-bases',
      method: 'post',
      data
    })
  },

  // 更新知识库
  updateKnowledgeBase: (id: number, data: UpdateKnowledgeParams): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: `/api/v1/knowledge-bases/${id}`,
      method: 'put',
      data
    })
  },

  // 删除知识库
  deleteKnowledgeBase: (id: number): Promise<ApiResponse<null>> => {
    return request({
      url: `/api/v1/knowledge-bases/${id}`,
      method: 'delete'
    })
  },

  // 获取知识库文档列表
  getDocuments: (kbId: number, params?: any): Promise<ApiResponse<any[]>> => {
    return request({
      url: `/api/v1/knowledge-bases/${kbId}/documents`,
      method: 'get',
      params
    })
  },

  // 上传文档到知识库
  uploadDocument: (kbId: number, file: File): Promise<ApiResponse<any>> => {
    const formData = new FormData()
    formData.append('file', file)

    return request({
      url: `/api/v1/knowledge-bases/${kbId}/upload`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除文档
  deleteDocument: (kbId: number, docId: number): Promise<ApiResponse<null>> => {
    return request({
      url: `/api/v1/knowledge-bases/${kbId}/documents/${docId}`,
      method: 'delete'
    })
  },

  // 搜索知识库
  searchKnowledgeBase: (kbId: number, data: any): Promise<ApiResponse<any>> => {
    return request({
      url: `/api/v1/knowledge-bases/${kbId}/search`,
      method: 'post',
      data
    })
  }
}
