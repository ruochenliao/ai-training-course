import {request} from './index'
import type {ApiResponse, PageResponse} from './index'

// 菜单项接口类型定义 - 对应后端Menu模型
export interface Menu {
  id: number
  name: string
  path: string
  component: string
  icon?: string
  order: number
  parent_id: number
  redirect?: string
  menu_type?: 'catalog' | 'menu'
  is_hidden?: boolean
  keepalive?: boolean
  created_at?: string
  updated_at?: string
  remark?: any
  children?: Menu[]
}

// 用户菜单接口类型 - 对应API返回的数据结构
export interface UserMenu {
  id: number
  name: string
  path: string
  component: string
  icon?: string
  order: number
  parent_id: number
  redirect?: string
  menu_type: 'catalog' | 'menu'
  is_hidden: boolean
  keepalive: boolean
  created_at: string
  updated_at: string
  remark?: any
  children: UserMenu[]
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

// 用户菜单API - 获取当前用户的动态菜单
export const userMenuApi = {
  // 获取当前用户的菜单
  getUserMenu: (): Promise<ApiResponse<UserMenu[]>> => {
    return request.get('/api/v1/base/usermenu')
  },

  // 获取当前用户的API权限
  getUserApi: (): Promise<ApiResponse<string[]>> => {
    return request.get('/api/v1/base/userapi')
  },
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