// 简化的认证状态管理

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SimpleAuthState {
  isAuthenticated: boolean
  user: any | null
  token: string | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => boolean
}

export const useSimpleAuthStore = create<SimpleAuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,

      login: async (username: string, password: string) => {
        // 简单的模拟登录
        if (username === 'admin' && password === 'admin123') {
          const mockUser = {
            id: 1,
            username: 'admin',
            full_name: '系统管理员',
            email: 'admin@example.com'
          }
          
          set({
            isAuthenticated: true,
            user: mockUser,
            token: 'mock-token-' + Date.now()
          })
          
          return true
        }
        
        return false
      },

      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          token: null
        })
      },

      checkAuth: () => {
        const { token } = get()
        return !!token
      }
    }),
    {
      name: 'simple-auth-storage'
    }
  )
)
