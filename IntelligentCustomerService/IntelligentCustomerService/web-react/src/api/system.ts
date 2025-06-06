import {type ApiResponse, type PageResponse, request} from './index'

// 用户管理接口
export interface User {
  id: string
  username: string
  email: string
  phone?: string
  avatar?: string
  status: 'active' | 'inactive'
  roles: Role[]
  deptId?: string
  deptName?: string
  createdAt: string
  updatedAt: string
}

export interface CreateUserParams {
  username: string
  email: string
  password: string
  phone?: string
  roleIds: string[]
  deptId?: string
  status: 'active' | 'inactive'
}

export interface UpdateUserParams {
  id: string
  username?: string
  email?: string
  phone?: string
  roleIds?: string[]
  deptId?: string
  status?: 'active' | 'inactive'
}

export interface UserQueryParams {
  page?: number
  pageSize?: number
  username?: string
  email?: string
  status?: 'active' | 'inactive'
  deptId?: string
}

// 角色管理接口
export interface Role {
  id: string
  name: string
  code: string
  description?: string
  permissions: Permission[]
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreateRoleParams {
  name: string
  code: string
  description?: string
  permissionIds: string[]
  status: 'active' | 'inactive'
}

export interface UpdateRoleParams {
  id: string
  name?: string
  code?: string
  description?: string
  permissionIds?: string[]
  status?: 'active' | 'inactive'
}

export interface RoleQueryParams {
  page?: number
  pageSize?: number
  name?: string
  code?: string
  status?: 'active' | 'inactive'
}

// 权限/菜单管理接口
export interface Permission {
  id: string
  name: string
  code: string
  type: 'directory' | 'menu' | 'button'
  path?: string
  component?: string
  icon?: string
  parentId?: string
  children?: Permission[]
  order: number
  hidden: boolean
  keepAlive: boolean
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreatePermissionParams {
  name: string
  code: string
  type: 'directory' | 'menu' | 'button'
  path?: string
  component?: string
  icon?: string
  parentId?: string
  order: number
  hidden: boolean
  keepAlive: boolean
  status: 'active' | 'inactive'
}

export interface UpdatePermissionParams {
  id: string
  name?: string
  code?: string
  type?: 'directory' | 'menu' | 'button'
  path?: string
  component?: string
  icon?: string
  parentId?: string
  order?: number
  hidden?: boolean
  keepAlive?: boolean
  status?: 'active' | 'inactive'
}

// 部门管理接口
export interface Department {
  id: string
  name: string
  code: string
  parentId?: string
  children?: Department[]
  order: number
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreateDepartmentParams {
  name: string
  code: string
  parentId?: string
  order: number
  status: 'active' | 'inactive'
}

export interface UpdateDepartmentParams {
  id: string
  name?: string
  code?: string
  parentId?: string
  order?: number
  status?: 'active' | 'inactive'
}

// API管理接口
export interface ApiInfo {
  id: string
  name: string
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  description?: string
  group: string
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

export interface CreateApiParams {
  name: string
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  description?: string
  group: string
  status: 'active' | 'inactive'
}

export interface UpdateApiParams {
  id: string
  name?: string
  path?: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  description?: string
  group?: string
  status?: 'active' | 'inactive'
}

export interface ApiQueryParams {
  page?: number
  pageSize?: number
  name?: string
  path?: string
  method?: string
  group?: string
  status?: 'active' | 'inactive'
}

// 审计日志接口
export interface AuditLog {
  id: string
  userId: string
  username: string
  action: string
  resource: string
  resourceId?: string
  ip: string
  userAgent: string
  status: 'success' | 'failed'
  errorMessage?: string
  createdAt: string
}

export interface AuditLogQueryParams {
  page?: number
  pageSize?: number
  userId?: string
  username?: string
  action?: string
  resource?: string
  status?: 'success' | 'failed'
  startDate?: string
  endDate?: string
}

// 用户管理API
export const userApi = {
  // 获取用户列表
  getUsers: (params?: UserQueryParams): Promise<ApiResponse<PageResponse<User>>> => {
    return request.get('/system/users', { params })
  },

  // 获取用户详情
  getUser: (id: string): Promise<ApiResponse<User>> => {
    return request.get(`/system/users/${id}`)
  },

  // 创建用户
  createUser: (params: CreateUserParams): Promise<ApiResponse<User>> => {
    return request.post('/system/users', params)
  },

  // 更新用户
  updateUser: (params: UpdateUserParams): Promise<ApiResponse<User>> => {
    return request.put(`/system/users/${params.id}`, params)
  },

  // 删除用户
  deleteUser: (id: string): Promise<ApiResponse> => {
    return request.delete(`/system/users/${id}`)
  },

  // 批量删除用户
  batchDeleteUsers: (ids: string[]): Promise<ApiResponse> => {
    return request.delete('/system/users/batch', { data: { ids } })
  },

  // 重置用户密码
  resetPassword: (id: string, newPassword: string): Promise<ApiResponse> => {
    return request.post(`/system/users/${id}/reset-password`, { newPassword })
  },
}

// 角色管理API
export const roleApi = {
  // 获取角色列表
  getRoles: (params?: RoleQueryParams): Promise<ApiResponse<PageResponse<Role>>> => {
    return request.get('/system/roles', { params })
  },

  // 获取所有角色（不分页）
  getAllRoles: (): Promise<ApiResponse<Role[]>> => {
    return request.get('/system/roles/all')
  },

  // 获取角色详情
  getRole: (id: string): Promise<ApiResponse<Role>> => {
    return request.get(`/system/roles/${id}`)
  },

  // 创建角色
  createRole: (params: CreateRoleParams): Promise<ApiResponse<Role>> => {
    return request.post('/system/roles', params)
  },

  // 更新角色
  updateRole: (params: UpdateRoleParams): Promise<ApiResponse<Role>> => {
    return request.put(`/system/roles/${params.id}`, params)
  },

  // 删除角色
  deleteRole: (id: string): Promise<ApiResponse> => {
    return request.delete(`/system/roles/${id}`)
  },

  // 批量删除角色
  batchDeleteRoles: (ids: string[]): Promise<ApiResponse> => {
    return request.delete('/system/roles/batch', { data: { ids } })
  },
}

// 权限/菜单管理API
export const permissionApi = {
  // 获取权限树
  getPermissionTree: (): Promise<ApiResponse<Permission[]>> => {
    return request.get('/system/permissions/tree')
  },

  // 获取权限列表
  getPermissions: (): Promise<ApiResponse<Permission[]>> => {
    return request.get('/system/permissions')
  },

  // 获取权限详情
  getPermission: (id: string): Promise<ApiResponse<Permission>> => {
    return request.get(`/system/permissions/${id}`)
  },

  // 创建权限
  createPermission: (params: CreatePermissionParams): Promise<ApiResponse<Permission>> => {
    return request.post('/system/permissions', params)
  },

  // 更新权限
  updatePermission: (params: UpdatePermissionParams): Promise<ApiResponse<Permission>> => {
    return request.put(`/system/permissions/${params.id}`, params)
  },

  // 删除权限
  deletePermission: (id: string): Promise<ApiResponse> => {
    return request.delete(`/system/permissions/${id}`)
  },

  // 获取用户权限
  getUserPermissions: (userId?: string): Promise<ApiResponse<Permission[]>> => {
    return request.get('/system/permissions/user', { params: { userId } })
  },
}

// 部门管理API
export const departmentApi = {
  // 获取部门树
  getDepartmentTree: (): Promise<ApiResponse<Department[]>> => {
    return request.get('/system/departments/tree')
  },

  // 获取部门列表
  getDepartments: (): Promise<ApiResponse<Department[]>> => {
    return request.get('/system/departments')
  },

  // 获取部门详情
  getDepartment: (id: string): Promise<ApiResponse<Department>> => {
    return request.get(`/system/departments/${id}`)
  },

  // 创建部门
  createDepartment: (params: CreateDepartmentParams): Promise<ApiResponse<Department>> => {
    return request.post('/system/departments', params)
  },

  // 更新部门
  updateDepartment: (params: UpdateDepartmentParams): Promise<ApiResponse<Department>> => {
    return request.put(`/system/departments/${params.id}`, params)
  },

  // 删除部门
  deleteDepartment: (id: string): Promise<ApiResponse> => {
    return request.delete(`/system/departments/${id}`)
  },
}

// API管理API
export const apiManagementApi = {
  // 获取API列表
  getApis: (params?: ApiQueryParams): Promise<ApiResponse<PageResponse<ApiInfo>>> => {
    return request.get('/system/apis', { params })
  },

  // 获取API详情
  getApi: (id: string): Promise<ApiResponse<ApiInfo>> => {
    return request.get(`/system/apis/${id}`)
  },

  // 创建API
  createApi: (params: CreateApiParams): Promise<ApiResponse<ApiInfo>> => {
    return request.post('/system/apis', params)
  },

  // 更新API
  updateApi: (params: UpdateApiParams): Promise<ApiResponse<ApiInfo>> => {
    return request.put(`/system/apis/${params.id}`, params)
  },

  // 删除API
  deleteApi: (id: string): Promise<ApiResponse> => {
    return request.delete(`/system/apis/${id}`)
  },

  // 批量删除API
  batchDeleteApis: (ids: string[]): Promise<ApiResponse> => {
    return request.delete('/system/apis/batch', { data: { ids } })
  },

  // 获取API分组
  getApiGroups: (): Promise<ApiResponse<string[]>> => {
    return request.get('/system/apis/groups')
  },
}

// 审计日志API
export const auditLogApi = {
  // 获取审计日志列表
  getAuditLogs: (params?: AuditLogQueryParams): Promise<ApiResponse<PageResponse<AuditLog>>> => {
    return request.get('/system/audit-logs', { params })
  },

  // 获取审计日志详情
  getAuditLog: (id: string): Promise<ApiResponse<AuditLog>> => {
    return request.get(`/system/audit-logs/${id}`)
  },

  // 导出审计日志
  exportAuditLogs: (params?: AuditLogQueryParams): Promise<void> => {
    return request.get('/system/audit-logs/export', {
      params,
      responseType: 'blob',
    }).then(response => {
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    })
  },
}