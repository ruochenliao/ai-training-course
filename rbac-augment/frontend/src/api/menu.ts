/**
 * 菜单管理API
 */

import { request } from '@/utils/request'
import type {
  PaginationParams,
  PaginationResponse,
  MenuListItem,
  Menu,
  MenuTreeNode,
  MenuCreateRequest,
  MenuUpdateRequest,
  MenuSelectOption,
  MenuRoute,
  BreadcrumbItem,
  MenuSortItem,
  IDResponse,
  BulkOperationRequest,
  BulkOperationResponse
} from '@/types'

/**
 * 获取菜单列表
 */
export function getMenuList(params: PaginationParams) {
  return request.get<PaginationResponse<MenuListItem>>('/api/v1/menus', { params })
}

/**
 * 获取菜单树
 */
export function getMenuTree() {
  return request.get<MenuTreeNode[]>('/api/v1/menus/tree')
}

/**
 * 获取菜单路由
 */
export function getMenuRoutes() {
  return request.get<MenuRoute[]>('/api/v1/menus/routes')
}

/**
 * 获取菜单详情
 */
export function getMenuDetail(id: number) {
  return request.get<Menu>(`/api/v1/menus/${id}`)
}

/**
 * 创建菜单
 */
export function createMenu(data: MenuCreateRequest) {
  return request.post<IDResponse>('/api/v1/menus', data)
}

/**
 * 更新菜单
 */
export function updateMenu(id: number, data: MenuUpdateRequest) {
  return request.put(`/api/v1/menus/${id}`, data)
}

/**
 * 更新菜单状态
 */
export function updateMenuStatus(id: number, data: { is_active: boolean }) {
  return request.patch(`/api/v1/menus/${id}/status`, data)
}

/**
 * 删除菜单
 */
export function deleteMenu(id: number) {
  return request.delete(`/api/v1/menus/${id}`)
}

/**
 * 获取子菜单
 */
export function getMenuChildren(id: number) {
  return request.get<Menu[]>(`/api/v1/menus/${id}/children`)
}

/**
 * 获取面包屑导航
 */
export function getMenuBreadcrumb(id: number) {
  return request.get<{ items: BreadcrumbItem[] }>(`/api/v1/menus/${id}/breadcrumb`)
}

/**
 * 获取菜单选择选项
 */
export function getMenuOptions() {
  return request.get<MenuSelectOption[]>('/api/v1/menus/options/select')
}

/**
 * 更新菜单排序
 */
export function updateMenuSort(data: MenuSortItem[]) {
  return request.put('/api/v1/menus/sort', data)
}

/**
 * 批量删除菜单
 */
export function bulkDeleteMenus(data: BulkOperationRequest) {
  return request.post<BulkOperationResponse>('/api/v1/menus/bulk-delete', data)
}
