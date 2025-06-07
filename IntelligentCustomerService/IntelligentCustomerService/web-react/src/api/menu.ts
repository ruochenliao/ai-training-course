import {request} from './index'
import type {ApiResponse, PaginatedResponse} from '@/types/api'

// 菜单项接口类型定义
export interface Menu {
  id: number
  name: string
  path: string
  component: string
  icon?: string
  order: number
  parent_id: number
  perms?: string
  redirect?: string
  menu_type?: 'catalog' | 'menu'
  is_hidden?: boolean
  keepalive?: boolean
  created_at?: string
  updated_at?: string
  remark?: string
  children?: Menu[]
}

// 菜单创建参数接口
export interface CreateMenuParams {
  name: string
  path: string
  component: string
  icon?: string
  order: number
  is_hidden?: boolean
  parent_id: number
  perms?: string
  redirect?: string
  menu_type?: 'catalog' | 'menu'
  keepalive?: boolean
  remark?: string
}

// 菜单更新参数接口
export interface UpdateMenuParams {
  id: number
  name?: string
  path?: string
  component?: string
  icon?: string
  order?: number
  is_hidden?: boolean
  parent_id?: number
  perms?: string
  redirect?: string
  menu_type?: 'catalog' | 'menu'
  keepalive?: boolean
  remark?: string
}

// 菜单查询参数接口
export interface MenuQueryParams {
  page?: number
  page_size?: number
  name?: string
  menu_type?: 'catalog' | 'menu'
  parent_id?: number
}

// 菜单管理API
export const menuApi = {
  // 获取菜单列表
  getMenuList: (params?: MenuQueryParams): Promise<ApiResponse<PaginatedResponse<Menu>>> => {
    return request.get('/api/v1/menu/list', { params })
  },

  // 获取菜单详情
  getMenuById: (id: number): Promise<ApiResponse<Menu>> => {
    return request.get('/api/v1/menu/get', { params: { menu_id: id } })
  },

  // 创建菜单
  createMenu: (params: CreateMenuParams): Promise<ApiResponse> => {
    return request.post('/api/v1/menu/create', params)
  },

  // 更新菜单
  updateMenu: (params: UpdateMenuParams): Promise<ApiResponse> => {
    return request.post('/api/v1/menu/update', params)
  },

  // 删除菜单
  deleteMenu: (id: number): Promise<ApiResponse> => {
    return request.delete('/api/v1/menu/delete', { params: { menu_id: id } })
  },

  // 获取菜单树
  getMenuTree: (): Promise<ApiResponse<Menu[]>> => {
    return request.get('/api/v1/menu/tree')
  },

  // 切换菜单可见状态
  toggleMenuVisibility: (id: number, isHidden: boolean): Promise<ApiResponse> => {
    return request.post('/api/v1/menu/update', { 
      id, is_hidden: isHidden 
    })
  },
};

export default menuApi;