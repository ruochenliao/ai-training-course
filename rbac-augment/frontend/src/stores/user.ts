/**
 * 用户管理状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as userApi from '@/api/user'
import type { UserListItem, UserDetail, PaginationParams } from '@/types'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userList = ref<UserListItem[]>([])
  const userDetail = ref<UserDetail | null>(null)
  const loading = ref(false)
  const total = ref(0)

  /**
   * 获取用户列表
   */
  async function fetchUserList(params: PaginationParams) {
    try {
      loading.value = true
      const response = await userApi.getUserList(params)
      userList.value = response.data.items
      total.value = response.data.total
      return response
    } catch (error) {
      console.error('Failed to fetch user list:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取用户详情
   */
  async function fetchUserDetail(id: number) {
    try {
      loading.value = true
      const response = await userApi.getUserDetail(id)
      userDetail.value = response.data
      return response
    } catch (error) {
      console.error('Failed to fetch user detail:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建用户
   */
  async function createUser(userData: any) {
    try {
      const response = await userApi.createUser(userData)
      return response
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    }
  }

  /**
   * 更新用户
   */
  async function updateUser(id: number, userData: any) {
    try {
      const response = await userApi.updateUser(id, userData)
      return response
    } catch (error) {
      console.error('Failed to update user:', error)
      throw error
    }
  }

  /**
   * 删除用户
   */
  async function deleteUser(id: number) {
    try {
      const response = await userApi.deleteUser(id)
      return response
    } catch (error) {
      console.error('Failed to delete user:', error)
      throw error
    }
  }

  /**
   * 批量删除用户
   */
  async function batchDeleteUsers(ids: number[]) {
    try {
      const response = await userApi.bulkDeleteUsers({ ids, action: 'delete' })
      return response
    } catch (error) {
      console.error('Failed to batch delete users:', error)
      throw error
    }
  }

  /**
   * 重置用户密码
   */
  async function resetUserPassword(id: number, newPassword: string) {
    try {
      const response = await userApi.resetUserPassword(id, { new_password: newPassword })
      return response
    } catch (error) {
      console.error('Failed to reset user password:', error)
      throw error
    }
  }

  /**
   * 分配用户角色
   */
  async function assignUserRoles(id: number, roleIds: number[]) {
    try {
      const response = await userApi.assignUserRoles(id, { role_ids: roleIds })
      return response
    } catch (error) {
      console.error('Failed to assign user roles:', error)
      throw error
    }
  }

  /**
   * 切换用户状态
   */
  async function toggleUserStatus(id: number) {
    try {
      const response = await userApi.toggleUserStatus(id)
      return response
    } catch (error) {
      console.error('Failed to toggle user status:', error)
      throw error
    }
  }

  /**
   * 清空状态
   */
  function clearState() {
    userList.value = []
    userDetail.value = null
    total.value = 0
  }

  return {
    // 状态
    userList,
    userDetail,
    loading,
    total,
    
    // 方法
    fetchUserList,
    fetchUserDetail,
    createUser,
    updateUser,
    deleteUser,
    batchDeleteUsers,
    resetUserPassword,
    assignUserRoles,
    toggleUserStatus,
    clearState
  }
})
