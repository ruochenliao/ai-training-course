/**
 * 权限管理状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as permissionApi from '@/api/permission'
import type { 
  PermissionListItem, 
  Permission, 
  PermissionTreeNode,
  PermissionGroup,
  PaginationParams 
} from '@/types'

export const usePermissionStore = defineStore('permission', () => {
  // 状态
  const permissionList = ref<PermissionListItem[]>([])
  const permissionTree = ref<PermissionTreeNode[]>([])
  const permissionGroups = ref<PermissionGroup[]>([])
  const permissionDetail = ref<Permission | null>(null)
  const loading = ref(false)
  const total = ref(0)

  /**
   * 获取权限列表
   */
  async function fetchPermissionList(params: PaginationParams) {
    try {
      loading.value = true
      const response = await permissionApi.getPermissionList(params)
      permissionList.value = response.data.items
      total.value = response.data.total
      return response
    } catch (error) {
      console.error('Failed to fetch permission list:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取权限树
   */
  async function fetchPermissionTree() {
    try {
      loading.value = true
      const response = await permissionApi.getPermissionTree()
      permissionTree.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch permission tree:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取权限分组
   */
  async function fetchPermissionGroups() {
    try {
      loading.value = true
      const response = await permissionApi.getPermissionGroups()
      permissionGroups.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch permission groups:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取权限详情
   */
  async function fetchPermissionDetail(id: number) {
    try {
      loading.value = true
      const response = await permissionApi.getPermissionDetail(id)
      permissionDetail.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch permission detail:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建权限
   */
  async function createPermission(permissionData: any) {
    try {
      const response = await permissionApi.createPermission(permissionData)
      return response
    } catch (error) {
      console.error('Failed to create permission:', error)
      throw error
    }
  }

  /**
   * 更新权限
   */
  async function updatePermission(id: number, permissionData: any) {
    try {
      const response = await permissionApi.updatePermission(id, permissionData)
      return response
    } catch (error) {
      console.error('Failed to update permission:', error)
      throw error
    }
  }

  /**
   * 删除权限
   */
  async function deletePermission(id: number) {
    try {
      const response = await permissionApi.deletePermission(id)
      return response
    } catch (error) {
      console.error('Failed to delete permission:', error)
      throw error
    }
  }

  /**
   * 批量删除权限
   */
  async function batchDeletePermissions(ids: number[]) {
    try {
      const response = await permissionApi.bulkDeletePermissions({ ids, action: 'delete' })
      return response
    } catch (error) {
      console.error('Failed to batch delete permissions:', error)
      throw error
    }
  }

  /**
   * 获取子权限
   */
  async function fetchPermissionChildren(id: number) {
    try {
      const response = await permissionApi.getPermissionChildren(id)
      return response
    } catch (error) {
      console.error('Failed to fetch permission children:', error)
      throw error
    }
  }

  /**
   * 根据资源获取权限
   */
  async function fetchPermissionsByResource(resource: string) {
    try {
      const response = await permissionApi.getPermissionsByResource(resource)
      return response
    } catch (error) {
      console.error('Failed to fetch permissions by resource:', error)
      throw error
    }
  }

  /**
   * 获取权限选择选项
   */
  async function fetchPermissionOptions() {
    try {
      const response = await permissionApi.getPermissionOptions()
      return response
    } catch (error) {
      console.error('Failed to fetch permission options:', error)
      throw error
    }
  }

  /**
   * 清空状态
   */
  function clearState() {
    permissionList.value = []
    permissionTree.value = []
    permissionGroups.value = []
    permissionDetail.value = null
    total.value = 0
  }

  return {
    // 状态
    permissionList,
    permissionTree,
    permissionGroups,
    permissionDetail,
    loading,
    total,
    
    // 方法
    fetchPermissionList,
    fetchPermissionTree,
    fetchPermissionGroups,
    fetchPermissionDetail,
    createPermission,
    updatePermission,
    deletePermission,
    batchDeletePermissions,
    fetchPermissionChildren,
    fetchPermissionsByResource,
    fetchPermissionOptions,
    clearState
  }
})
