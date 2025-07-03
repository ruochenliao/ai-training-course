/**
 * 部门相关类型定义
 */

// 部门基础信息
export interface DepartmentBase {
  name: string
  code: string
  description?: string
  parent_id?: number
  manager_id?: number
  phone?: string
  email?: string
  address?: string
  sort_order: number
}

// 部门列表项
export interface DepartmentListItem extends DepartmentBase {
  id: number
  parent_name?: string
  manager_name?: string
  user_count: number
  child_count: number
  level: number
  path: string
  created_at: string
  updated_at: string
}

// 部门详情
export interface DepartmentDetail extends DepartmentListItem {
  parent?: DepartmentListItem
  manager?: {
    id: number
    username: string
    full_name: string
    email: string
  }
  children: DepartmentListItem[]
  users: Array<{
    id: number
    username: string
    full_name: string
    email: string
    phone?: string
  }>
}

// 部门树节点
export interface DepartmentTreeNode {
  id: number
  name: string
  code: string
  parent_id?: number
  manager_id?: number
  manager_name?: string
  user_count: number
  child_count: number
  level: number
  path: string
  sort_order: number
  children: DepartmentTreeNode[]
  created_at: string
  updated_at: string
}

// 创建部门请求
export interface DepartmentCreateRequest extends DepartmentBase {}

// 更新部门请求
export interface DepartmentUpdateRequest extends Partial<DepartmentBase> {}

// 移动部门请求
export interface DepartmentMoveRequest {
  target_parent_id?: number
  position?: 'before' | 'after' | 'inside'
  target_id?: number
}

// 部门用户分配请求
export interface DepartmentUserAssignRequest {
  user_ids: number[]
  action: 'assign' | 'remove'
}

// 部门统计信息
export interface DepartmentStatistics {
  total_users: number
  active_users: number
  inactive_users: number
  total_children: number
  direct_children: number
  max_depth: number
  created_this_month: number
  updated_this_month: number
}

// 部门搜索参数
export interface DepartmentSearchParams {
  name?: string
  code?: string
  manager_id?: number
  parent_id?: number
  level?: number
  has_users?: boolean
  created_start?: string
  created_end?: string
}

// 部门批量操作请求
export interface DepartmentBatchOperationRequest {
  department_ids: number[]
  operation: 'delete' | 'move' | 'activate' | 'deactivate'
  target_parent_id?: number
  options?: Record<string, any>
}

// 部门批量操作响应
export interface DepartmentBatchOperationResponse {
  success_count: number
  failed_count: number
  failed_items: Array<{
    id: number
    error: string
  }>
  warnings: string[]
}

// 部门导入数据项
export interface DepartmentImportDataItem {
  name: string
  code: string
  parent_code?: string
  description?: string
  manager_username?: string
  phone?: string
  email?: string
  address?: string
  sort_order?: number
}

// 部门导入请求
export interface DepartmentImportRequest {
  data: DepartmentImportDataItem[]
  options: {
    update_existing: boolean
    skip_errors: boolean
    validate_only: boolean
  }
}

// 部门导入响应
export interface DepartmentImportResponse {
  total_count: number
  success_count: number
  failed_count: number
  skipped_count: number
  created_departments: DepartmentListItem[]
  updated_departments: DepartmentListItem[]
  failed_items: Array<{
    data: DepartmentImportDataItem
    error: string
    line_number: number
  }>
  warnings: string[]
}

// 部门选择选项
export interface DepartmentSelectOption {
  id: number
  name: string
  code: string
  parent_id?: number
  level: number
  path: string
  disabled?: boolean
}
