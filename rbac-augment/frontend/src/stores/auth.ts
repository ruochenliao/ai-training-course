/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as authApi from '@/api/auth'
import {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
  removeRefreshToken,
  getUserInfo,
  setUserInfo,
  removeUserInfo,
  clearAuth
} from '@/utils/auth'
import type {
  LoginRequest,
  User,
  UserInfo,
  UserProfile,
  ChangePasswordRequest,
  MenuRoute
} from '@/types'
import type { AuthStoreType } from '@/types/store-types'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>(getToken() || '')
  const refreshToken = ref<string>(getRefreshToken() || '')
  const userInfo = ref<User | null>(getUserInfo())
  const permissions = ref<string[]>([])
  const roles = ref<string[]>([])
  const menus = ref<MenuRoute[]>([])

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isSuperUser = computed(() => userInfo.value?.is_superuser || false)

  /**
   * 登录
   */
  async function login(loginData: LoginRequest) {
    try {
      const response = await authApi.login(loginData)
      const { access_token, refresh_token, user } = response.data

      // 保存token和用户信息
      token.value = access_token
      refreshToken.value = refresh_token
      userInfo.value = user

      setToken(access_token)
      setRefreshToken(refresh_token)
      setUserInfo(user)

      ElMessage.success('登录成功')
      return response
    } catch (error) {
      ElMessage.error('登录失败')
      throw error
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除本地状态
      token.value = ''
      refreshToken.value = ''
      userInfo.value = null
      permissions.value = []
      roles.value = []
      menus.value = []

      clearAuth()
      ElMessage.success('已退出登录')
    }
  }

  /**
   * 刷新访问令牌
   */
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await authApi.refreshToken({
        refresh_token: refreshToken.value
      })

      const { access_token } = response.data
      token.value = access_token
      setToken(access_token)

      return response
    } catch (error) {
      // 刷新失败，清除所有认证信息
      await logout()
      throw error
    }
  }

  /**
   * 获取用户个人资料
   */
  async function fetchUserProfile() {
    try {
      const response = await authApi.getUserProfile()
      const profile: UserProfile = response.data

      userInfo.value = {
        id: profile.id,
        username: profile.username,
        email: profile.email,
        full_name: profile.full_name,
        avatar: profile.avatar,
        phone: profile.phone,
        is_active: profile.is_active,
        is_superuser: profile.is_superuser,
        last_login_at: profile.last_login_at,
        created_at: profile.created_at,
        updated_at: profile.updated_at
      }

      permissions.value = profile.permissions
      roles.value = profile.roles
      menus.value = profile.menus

      setUserInfo(userInfo.value)
      return response
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      throw error
    }
  }

  /**
   * 修改密码
   */
  async function changePassword(passwordData: ChangePasswordRequest) {
    try {
      const response = await authApi.changePassword(passwordData)
      ElMessage.success('密码修改成功')
      return response
    } catch (error) {
      ElMessage.error('密码修改失败')
      throw error
    }
  }

  /**
   * 检查权限
   */
  function hasPermission(permission: string | string[]): boolean {
    if (isSuperUser.value) {
      return true
    }

    if (typeof permission === 'string') {
      return permissions.value.includes(permission)
    }

    if (Array.isArray(permission)) {
      return permission.some(p => permissions.value.includes(p))
    }

    return false
  }

  /**
   * 检查角色
   */
  function hasRole(role: string | string[]): boolean {
    if (isSuperUser.value) {
      return true
    }

    if (typeof role === 'string') {
      return roles.value.includes(role)
    }

    if (Array.isArray(role)) {
      return role.some(r => roles.value.includes(r))
    }

    return false
  }

  /**
   * 初始化认证状态
   */
  async function initAuth() {
    if (token.value && userInfo.value) {
      try {
        await fetchUserProfile()
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        await logout()
      }
    }
  }

  return {
    // 状态
    token,
    refreshToken,
    userInfo,
    permissions,
    roles,
    menus,

    // 计算属性
    isLoggedIn,
    isSuperUser,

    // 方法
    login,
    logout,
    refreshAccessToken,
    fetchUserProfile,
    changePassword,
    hasPermission,
    hasRole,
    initAuth
  } as AuthStoreType
})
