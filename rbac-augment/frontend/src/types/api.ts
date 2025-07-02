/**
 * API相关类型定义
 */

// 基础响应类型
export interface BaseResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
  request_id: string
}

// 错误响应类型
export interface ErrorResponse extends BaseResponse {
  errors?: Array<{
    field: string
    message: string
    type: string
  }>
}

// 分页参数类型
export interface PaginationParams {
  page: number
  page_size: number
  search?: string
  sort_field?: string
  sort_order?: 'asc' | 'desc'
}

// 分页响应类型
export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

// ID响应类型
export interface IDResponse {
  id: number
}

// 批量操作请求类型
export interface BulkOperationRequest {
  ids: number[]
  action: string
}

// 批量操作响应类型
export interface BulkOperationResponse {
  success_count: number
  failed_count: number
  failed_ids: number[]
  errors: string[]
}
