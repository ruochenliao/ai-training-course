/**
 * 菜单相关类型定义
 */

// 菜单基础信息
export interface Menu {
  id: number
  name: string
  title: string
  path?: string
  component?: string
  icon?: string
  parent_id?: number
  sort_order: number
  is_visible: boolean
  is_external: boolean
  cache: boolean
  redirect?: string
  created_at: string
  updated_at: string
}

// 菜单列表项
export interface MenuListItem extends Menu {
  parent_name?: string
}

// 菜单树节点
export interface MenuTreeNode extends Menu {
  children: MenuTreeNode[]
}

// 菜单树项（用于表格显示）
export interface MenuTreeItem extends Menu {
  children?: MenuTreeItem[]
  statusLoading?: boolean
}

// 菜单创建请求
export interface MenuCreateRequest {
  name: string
  title: string
  path?: string
  component?: string
  icon?: string
  parent_id?: number
  sort_order?: number
  is_visible?: boolean
  is_external?: boolean
  cache?: boolean
  redirect?: string
}

// 菜单更新请求
export interface MenuUpdateRequest {
  name?: string
  title?: string
  path?: string
  component?: string
  icon?: string
  parent_id?: number
  sort_order?: number
  is_visible?: boolean
  is_external?: boolean
  cache?: boolean
  redirect?: string
}

// 菜单选择选项
export interface MenuSelectOption {
  id: number
  name: string
  title: string
  parent_id?: number
}

// 菜单路由
export interface MenuRoute {
  id: number
  name: string
  path: string
  component?: string
  redirect?: string
  meta: {
    title: string
    icon?: string
    cache: boolean
    hidden: boolean
    external: boolean
  }
  children?: MenuRoute[]
}

// 面包屑项
export interface BreadcrumbItem {
  id: number
  name: string
  title: string
  path?: string
}

// 菜单排序项
export interface MenuSortItem {
  id: number
  sort_order: number
  parent_id?: number
}
