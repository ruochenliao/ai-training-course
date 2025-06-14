import { request } from './index'
import type { ApiResponse } from '@/types/api'

// API接口类型定义
export interface ApiItem {
  id: number
  path: string
  method: string
  summary: string
  tags: string
  created_at?: string
  updated_at?: string
}

export interface CreateApiParams {
  path: string
  method: string
  summary: string
  tags: string
}

export interface UpdateApiParams {
  id: number
  path?: string
  method?: string
  summary?: string
  tags?: string
}

export interface ApiQueryParams {
  page?: number
  page_size?: number
  path?: string
  summary?: string
  tags?: string
}

// API接口响应类型
export interface ApiListResponse {
  code: number
  msg: string | null
  data: ApiItem[]
  total: number
  page: number
  page_size: number
}

// API接口定义
export const apiApi = {
  // 获取API列表
  getApis: (params?: ApiQueryParams): Promise<ApiListResponse> => {
    return request.get('/api/v1/api/list', { params })
  },

  // 获取API详情
  getApiById: (id: number): Promise<ApiResponse<ApiItem>> => {
    return request.get('/api/v1/api/get', { params: { id } })
  },

  // 创建API
  createApi: (params: CreateApiParams): Promise<ApiResponse> => {
    return request.post('/api/v1/api/create', params)
  },

  // 更新API
  updateApi: (params: UpdateApiParams): Promise<ApiResponse> => {
    return request.post('/api/v1/api/update', params)
  },

  // 删除API
  deleteApi: (id: number): Promise<ApiResponse> => {
    return request.delete('/api/v1/api/delete', { params: { api_id: id } })
  },

  // 刷新API
  refreshApi: (): Promise<ApiResponse> => {
    return request.post('/api/v1/api/refresh')
  },
}
