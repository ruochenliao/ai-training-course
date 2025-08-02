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
  getList: (params?: KnowledgeListParams): Promise<ApiResponse<KnowledgeListResponse>> => {
    return request({
      url: API_PATHS.KNOWLEDGE.LIST,
      method: 'get',
      params
    })
  },

  // 获取知识库详情
  getDetail: (id: number): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: `${API_PATHS.KNOWLEDGE.DETAIL}/${id}`,
      method: 'get'
    })
  },

  // 创建知识库
  create: (data: CreateKnowledgeParams): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: API_PATHS.KNOWLEDGE.CREATE,
      method: 'post',
      data
    })
  },

  // 更新知识库
  update: (id: number, data: UpdateKnowledgeParams): Promise<ApiResponse<Knowledge>> => {
    return request({
      url: `${API_PATHS.KNOWLEDGE.UPDATE}/${id}`,
      method: 'put',
      data
    })
  },

  // 删除知识库
  delete: (id: number): Promise<ApiResponse<null>> => {
    return request({
      url: `${API_PATHS.KNOWLEDGE.DELETE}/${id}`,
      method: 'delete'
    })
  },

  // 获取知识库文件列表
  getFiles: (knowledgeId: number, params?: { page?: number; size?: number }): Promise<ApiResponse<{ items: KnowledgeFile[]; total: number }>> => {
    return request({
      url: `${API_PATHS.KNOWLEDGE.DETAIL}/${knowledgeId}/files`,
      method: 'get',
      params
    })
  },

  // 上传文件到知识库
  uploadFiles: (data: UploadFileParams): Promise<ApiResponse<KnowledgeFile[]>> => {
    const formData = new FormData()
    formData.append('knowledge_id', data.knowledge_id.toString())
    data.files.forEach(file => {
      formData.append('files', file)
    })

    return request({
      url: API_PATHS.KNOWLEDGE.UPLOAD,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除知识库文件
  deleteFile: (knowledgeId: number, fileId: number): Promise<ApiResponse<null>> => {
    return request({
      url: `${API_PATHS.KNOWLEDGE.DETAIL}/${knowledgeId}/files/${fileId}`,
      method: 'delete'
    })
  }
}
