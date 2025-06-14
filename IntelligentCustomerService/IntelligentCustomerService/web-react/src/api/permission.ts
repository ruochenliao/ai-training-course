import { request } from '../utils/request'

// 权限接口
export interface Permission {
  id: string
  name: string
  displayName: string
  description?: string
  type: 'menu' | 'button' | 'api'
  path?: string
  method?: string
  icon?: string
  sort: number
  status: 'active' | 'inactive'
  parentId?: string
  children?: Permission[]
  level: number
  isSystem: boolean
  createdAt: string
  updatedAt: string
}

// 权限查询参数
export interface PermissionQueryParams {
  page?: number
  pageSize?: number
  keyword?: string
  type?: 'menu' | 'button' | 'api'
  status?: 'active' | 'inactive'
  parentId?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 权限创建/更新参数
export interface PermissionFormData {
  name: string
  displayName: string
  description?: string
  type: 'menu' | 'button' | 'api'
  path?: string
  method?: string
  icon?: string
  sort: number
  status: 'active' | 'inactive'
  parentId?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  list: T[]
  pagination: {
    current: number
    pageSize: number
    total: number
  }
}

export const permissionApi = {
  // 获取权限列表（分页）
  getPermissions: (params?: PermissionQueryParams): Promise<PaginatedResponse<Permission>> => {
    return request.get('/api/permissions', { params })
  },

  // 获取权限树
  getPermissionTree: (): Promise<Permission[]> => {
    return request.get('/api/permissions/tree')
  },

  // 获取权限详情
  getPermissionById: (id: string): Promise<Permission> => {
    return request.get(`/api/permissions/${id}`)
  },

  // 创建权限
  createPermission: (data: PermissionFormData): Promise<Permission> => {
    return request.post('/api/permissions', data)
  },

  // 更新权限
  updatePermission: (id: string, data: Partial<PermissionFormData>): Promise<Permission> => {
    return request.put(`/api/permissions/${id}`, data)
  },

  // 删除权限
  deletePermission: (id: string): Promise<void> => {
    return request.delete(`/api/permissions/${id}`)
  },

  // 批量删除权限
  batchDeletePermissions: (ids: string[]): Promise<void> => {
    return request.delete('/api/permissions/batch', { data: { ids } })
  },

  // 切换权限状态
  togglePermissionStatus: (id: string, status: 'active' | 'inactive'): Promise<Permission> => {
    return request.patch(`/api/permissions/${id}/status`, { status })
  },

  // 复制权限
  copyPermission: (id: string): Promise<Permission> => {
    return request.post(`/api/permissions/${id}/copy`)
  },

  // 移动权限
  movePermission: (id: string, targetParentId?: string, targetIndex?: number): Promise<void> => {
    return request.patch(`/api/permissions/${id}/move`, {
      targetParentId,
      targetIndex,
    })
  },

  // 获取权限的子权限
  getChildPermissions: (parentId: string): Promise<Permission[]> => {
    return request.get(`/api/permissions/${parentId}/children`)
  },

  // 获取权限路径（从根到当前权限的路径）
  getPermissionPath: (id: string): Promise<Permission[]> => {
    return request.get(`/api/permissions/${id}/path`)
  },

  // 检查权限名称是否可用
  checkPermissionName: (name: string, excludeId?: string): Promise<{ available: boolean }> => {
    return request.get('/api/permissions/check-name', {
      params: { name, excludeId },
    })
  },

  // 检查权限路径是否可用
  checkPermissionPath: (path: string, method?: string, excludeId?: string): Promise<{ available: boolean }> => {
    return request.get('/api/permissions/check-path', {
      params: { path, method, excludeId },
    })
  },

  // 获取权限统计信息
  getPermissionStats: (): Promise<{
    totalPermissions: number
    menuPermissions: number
    buttonPermissions: number
    apiPermissions: number
    activePermissions: number
    inactivePermissions: number
  }> => {
    return request.get('/api/permissions/stats')
  },

  // 获取用户权限
  getUserPermissions: (userId?: string): Promise<Permission[]> => {
    return request.get('/api/permissions/user', {
      params: { userId },
    })
  },

  // 获取角色权限
  getRolePermissions: (roleId: string): Promise<Permission[]> => {
    return request.get('/api/permissions/role', {
      params: { roleId },
    })
  },

  // 同步权限（从代码中扫描并同步权限）
  syncPermissions: (): Promise<{
    added: number
    updated: number
    removed: number
    errors: string[]
  }> => {
    return request.post('/api/permissions/sync')
  },

  // 重建权限树
  rebuildPermissionTree: (): Promise<void> => {
    return request.post('/api/permissions/rebuild-tree')
  },

  // 导出权限
  exportPermissions: (params?: PermissionQueryParams): Promise<Blob> => {
    return request.get('/api/permissions/export', {
      params,
      responseType: 'blob',
    })
  },

  // 导入权限
  importPermissions: (
    file: File,
  ): Promise<{
    success: number
    failed: number
    errors: string[]
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/api/permissions/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 获取权限使用情况
  getPermissionUsage: (
    id: string,
  ): Promise<{
    roles: Array<{ id: string; name: string; displayName: string }>
    users: Array<{ id: string; username: string; displayName: string }>
  }> => {
    return request.get(`/api/permissions/${id}/usage`)
  },

  // 批量更新权限状态
  batchUpdatePermissionStatus: (ids: string[], status: 'active' | 'inactive'): Promise<void> => {
    return request.patch('/api/permissions/batch-status', { ids, status })
  },

  // 批量移动权限
  batchMovePermissions: (ids: string[], targetParentId?: string): Promise<void> => {
    return request.patch('/api/permissions/batch-move', {
      ids,
      targetParentId,
    })
  },

  // 获取权限依赖关系
  getPermissionDependencies: (
    id: string,
  ): Promise<{
    dependencies: Permission[] // 依赖的权限
    dependents: Permission[] // 依赖此权限的权限
  }> => {
    return request.get(`/api/permissions/${id}/dependencies`)
  },

  // 验证权限
  validatePermission: (permission: string, resource?: string): Promise<{ valid: boolean; message?: string }> => {
    return request.post('/api/permissions/validate', {
      permission,
      resource,
    })
  },
}
