// 认证状态管理

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, type UserInfo, type LoginRequest } from '@/api/auth'
import { message } from 'antd'

export interface AuthState {
  // 状态
  isAuthenticated: boolean
  user: UserInfo | null
  token: string | null
  loading: boolean
  
  // 操作
  login: (credentials: LoginRequest) => Promise<boolean>
  logout: () => void
  refreshToken: () => Promise<boolean>
  updateUser: (user: Partial<UserInfo>) => void
  checkAuth: () => Promise<boolean>
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,

      // 登录
      login: async (credentials: LoginRequest) => {
        try {
          set({ loading: true })
          
          const response = await authApi.login(credentials)
          
          if (response.data) {
            const { access_token, user } = response.data
            
            set({
              isAuthenticated: true,
              user,
              token: access_token,
              loading: false
            })
            
            // 存储token到localStorage
            localStorage.setItem('token', access_token)
            
            message.success('登录成功')
            return true
          }
          
          set({ loading: false })
          return false
        } catch (error: any) {
          set({ loading: false })
          message.error(error.response?.data?.message || '登录失败')
          return false
        }
      },

      // 登出
      logout: () => {
        try {
          authApi.logout().catch(() => {
            // 忽略登出API错误
          })
        } finally {
          set({
            isAuthenticated: false,
            user: null,
            token: null
          })
          
          // 清除本地存储
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          
          message.success('已退出登录')
        }
      },

      // 刷新令牌
      refreshToken: async () => {
        try {
          const refreshToken = localStorage.getItem('refresh_token')
          if (!refreshToken) {
            return false
          }

          const response = await authApi.refreshToken({ refresh_token: refreshToken })
          
          if (response.data) {
            const { access_token, user } = response.data
            
            set({
              isAuthenticated: true,
              user,
              token: access_token
            })
            
            localStorage.setItem('token', access_token)
            return true
          }
          
          return false
        } catch (error) {
          // 刷新失败，清除认证状态
          get().logout()
          return false
        }
      },

      // 更新用户信息
      updateUser: (userData: Partial<UserInfo>) => {
        const currentUser = get().user
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          })
        }
      },

      // 检查认证状态
      checkAuth: async () => {
        try {
          const token = localStorage.getItem('token')
          if (!token) {
            return false
          }

          const response = await authApi.getCurrentUser()
          
          if (response.data) {
            set({
              isAuthenticated: true,
              user: response.data,
              token
            })
            return true
          }
          
          return false
        } catch (error) {
          // 验证失败，尝试刷新令牌
          return await get().refreshToken()
        }
      },

      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ loading })
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token
      })
    }
  )
)
