import {ApiResponse, request} from './index'

// 分页响应接口
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

// 角色接口
export interface Role {
  id: number
  name: string
  desc: string
  created_at: string
  updated_at: string
}

// 角色查询参数
export interface RoleQueryParams {
  page?: number
  page_size?: number
  role_name?: string
}

// 角色创建参数
export interface RoleCreateData {
  name: string
  desc?: string
}

// 角色更新参数
export interface RoleUpdateData {
  id: number
  name?: string
  desc?: string
}

// 角色权限更新参数
export interface RoleUpdateMenusApis {
  id: number
  menu_ids: number[]
  api_infos: Array<{
    method: string
    path: string
  }>
}

// 角色权限信息
export interface RoleAuthorized {
  id: number
  name: string
  desc: string
  menus: any[]
  apis: any[]
}

export const roleApi = {
  // 获取角色列表
  list: (params?: RoleQueryParams): Promise<PaginatedResponse<Role> & { code: number; msg: string }> => {
    return request.get('/api/v1/role/list', { params })
  },

  // 获取角色详情
  get: (role_id: number): Promise<ApiResponse<Role>> => {
    return request.get('/api/v1/role/get', { params: { role_id } })
  },

  // 创建角色
  create: (data: RoleCreateData): Promise<ApiResponse<{ msg: string }>> => {
    return request.post('/api/v1/role/create', data)
  },

  // 更新角色
  update: (data: RoleUpdateData): Promise<ApiResponse<{ msg: string }>> => {
    return request.post('/api/v1/role/update', data)
  },

  // 删除角色
  delete: (role_id: number): Promise<ApiResponse<{ msg: string }>> => {
    return request.delete('/api/v1/role/delete', { params: { role_id } })
  },

  // 查看角色权限
  getAuthorized: (id: number): Promise<ApiResponse<RoleAuthorized>> => {
    return request.get('/api/v1/role/authorized', { params: { id } })
  },

  // 更新角色权限
  updateAuthorized: (data: RoleUpdateMenusApis): Promise<ApiResponse<{ msg: string }>> => {
    return request.post('/api/v1/role/authorized', data)
  },
}

export default roleApi
