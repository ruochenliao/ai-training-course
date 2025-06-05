import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/api/auth'
import type { User, LoginParams } from '@/types/auth'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  login: (params: LoginParams) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  clearAuth: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,

      login: async (params: LoginParams) => {
        set({ loading: true })
        try {
          const response = await authApi.login(params)
          const { user, token } = response.data
          
          set({
            user,
            token,
            isAuthenticated: true,
            loading: false,
          })
          
          // 设置axios默认header
          if (token) {
            localStorage.setItem('token', token)
          }
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      logout: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      setUser: (user: User) => {
        set({ user })
      },

      clearAuth: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          loading: false,
        })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token')
        if (!token) {
          set({ loading: false })
          return
        }

        set({ loading: true })
        try {
          const response = await authApi.verifyToken()
          const { data: user } = response
          set({
            user,
            token,
            isAuthenticated: true,
            loading: false,
          })
        } catch (error) {
          localStorage.removeItem('token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)