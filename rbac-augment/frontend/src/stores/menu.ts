/**
 * 菜单管理状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as menuApi from '@/api/menu'
import type { 
  MenuListItem, 
  Menu, 
  MenuTreeNode,
  MenuRoute,
  MenuSortItem,
  PaginationParams 
} from '@/types'

export const useMenuStore = defineStore('menu', () => {
  // 状态
  const menuList = ref<MenuListItem[]>([])
  const menuTree = ref<MenuTreeNode[]>([])
  const menuRoutes = ref<MenuRoute[]>([])
  const menuDetail = ref<Menu | null>(null)
  const loading = ref(false)
  const total = ref(0)

  /**
   * 获取菜单列表
   */
  async function fetchMenuList(params: PaginationParams) {
    try {
      loading.value = true
      const response = await menuApi.getMenuList(params)
      menuList.value = response.data.items
      total.value = response.data.total
      return response
    } catch (error) {
      console.error('Failed to fetch menu list:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取菜单树
   */
  async function fetchMenuTree() {
    try {
      loading.value = true
      const response = await menuApi.getMenuTree()
      menuTree.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch menu tree:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取菜单路由
   */
  async function fetchMenuRoutes() {
    try {
      loading.value = true
      const response = await menuApi.getMenuRoutes()
      menuRoutes.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch menu routes:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取菜单详情
   */
  async function fetchMenuDetail(id: number) {
    try {
      loading.value = true
      const response = await menuApi.getMenuDetail(id)
      menuDetail.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch menu detail:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建菜单
   */
  async function createMenu(menuData: any) {
    try {
      const response = await menuApi.createMenu(menuData)
      return response
    } catch (error) {
      console.error('Failed to create menu:', error)
      throw error
    }
  }

  /**
   * 更新菜单
   */
  async function updateMenu(id: number, menuData: any) {
    try {
      const response = await menuApi.updateMenu(id, menuData)
      return response
    } catch (error) {
      console.error('Failed to update menu:', error)
      throw error
    }
  }

  /**
   * 删除菜单
   */
  async function deleteMenu(id: number) {
    try {
      const response = await menuApi.deleteMenu(id)
      return response
    } catch (error) {
      console.error('Failed to delete menu:', error)
      throw error
    }
  }

  /**
   * 批量删除菜单
   */
  async function batchDeleteMenus(ids: number[]) {
    try {
      const response = await menuApi.bulkDeleteMenus({ ids, action: 'delete' })
      return response
    } catch (error) {
      console.error('Failed to batch delete menus:', error)
      throw error
    }
  }

  /**
   * 获取子菜单
   */
  async function fetchMenuChildren(id: number) {
    try {
      const response = await menuApi.getMenuChildren(id)
      return response
    } catch (error) {
      console.error('Failed to fetch menu children:', error)
      throw error
    }
  }

  /**
   * 获取面包屑导航
   */
  async function fetchMenuBreadcrumb(id: number) {
    try {
      const response = await menuApi.getMenuBreadcrumb(id)
      return response
    } catch (error) {
      console.error('Failed to fetch menu breadcrumb:', error)
      throw error
    }
  }

  /**
   * 获取菜单选择选项
   */
  async function fetchMenuOptions() {
    try {
      const response = await menuApi.getMenuOptions()
      return response
    } catch (error) {
      console.error('Failed to fetch menu options:', error)
      throw error
    }
  }

  /**
   * 更新菜单排序
   */
  async function updateMenuSort(sortData: MenuSortItem[]) {
    try {
      const response = await menuApi.updateMenuSort(sortData)
      return response
    } catch (error) {
      console.error('Failed to update menu sort:', error)
      throw error
    }
  }

  /**
   * 清空状态
   */
  function clearState() {
    menuList.value = []
    menuTree.value = []
    menuRoutes.value = []
    menuDetail.value = null
    total.value = 0
  }

  return {
    // 状态
    menuList,
    menuTree,
    menuRoutes,
    menuDetail,
    loading,
    total,
    
    // 方法
    fetchMenuList,
    fetchMenuTree,
    fetchMenuRoutes,
    fetchMenuDetail,
    createMenu,
    updateMenu,
    deleteMenu,
    batchDeleteMenus,
    fetchMenuChildren,
    fetchMenuBreadcrumb,
    fetchMenuOptions,
    updateMenuSort,
    clearState
  }
})
