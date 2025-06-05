export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
  timestamp: number
}

export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface ListParams extends PaginationParams {
  keyword?: string
  status?: string | number
  startTime?: string
  endTime?: string
  [key: string]: any
}

export interface UploadResponse {
  url: string
  filename: string
  size: number
  type: string
}

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
  children?: SelectOption[]
}

export interface TreeNode {
  id: string | number
  title: string
  key: string | number
  children?: TreeNode[]
  disabled?: boolean
  selectable?: boolean
  checkable?: boolean
  [key: string]: any
}