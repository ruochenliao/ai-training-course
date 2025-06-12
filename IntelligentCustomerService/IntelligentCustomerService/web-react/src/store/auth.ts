import {create} from 'zustand'
import {persist} from 'zustand/middleware'
import {authApi} from '@/api/auth'
import type {LoginParams, User} from '@/types/auth'
import {usePermissionStore} from './permission'

interface AuthState {
  user: User | null
  token: string | null
  menus: any[] | null
  apis: string[] | null
  isAuthenticated: boolean
  loading: boolean
  login: (params: LoginParams) => Promise<void>
  logout: () => void
  clearAuth: () => void
  checkAuth: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      menus: null,
      apis: null,
      isAuthenticated: false,
      loading: false,

      login: async (params: LoginParams) => {
        set({ loading: true })
        try {
          // 1. 获取token
          const tokenResponse = await authApi.login(params)
          const { access_token } = tokenResponse.data
          
          // 设置token
          localStorage.setItem('token', access_token)
          set({ token: access_token })
          
          // 2. 获取用户信息
          const userResponse = await authApi.getUserInfo()
          const user = userResponse.data
          
          // 3. 获取用户菜单
          const menuResponse = await authApi.getUserMenu()
          const menus = menuResponse.data
          
          // 4. 获取用户API权限
          const apiResponse = await authApi.getUserApi()
          const apis = apiResponse.data
          
          // 设置认证状态
          set({
            user,
            menus,
            apis,
            isAuthenticated: true,
            loading: false
          })

          // 初始化权限
          const permissionStore = usePermissionStore.getState()
          await permissionStore.generateRoutes(apis || [])

          return
        } catch (error: unknown) {
          // 清除可能已设置的token
          localStorage.removeItem('token')
          set({ loading: false })
          throw error
        }
      },

      logout: () => {
        authApi.logout() // 客户端登出
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          menus: null,
          apis: null,
          isAuthenticated: false,
        })
      },

      clearAuth: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          token: null,
          menus: null,
          apis: null,
          isAuthenticated: false,
          loading: false,
        })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token')
        if (!token) {
          set({ loading: false })
          return false
        }

        set({ loading: true, token })
        try {
          // 1. 获取用户信息
          const userResponse = await authApi.getUserInfo()
          const user = userResponse.data
          
          // 2. 获取用户菜单
          const menuResponse = await authApi.getUserMenu()
          const menus = menuResponse.data
          
          // 3. 获取用户API权限
          const apiResponse = await authApi.getUserApi()
          const apis = apiResponse.data
          
          // 设置认证状态
          set({
            user,
            menus,
            apis,
            isAuthenticated: true,
            loading: false
          })

          // 初始化权限
          const permissionStore = usePermissionStore.getState()
          await permissionStore.generateRoutes(apis || [])

          return true
        } catch (error) {
          localStorage.removeItem('token')
          set({
            user: null,
            token: null,
            menus: null,
            apis: null,
            isAuthenticated: false,
            loading: false,
          })
          return false
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        menus: state.menus,
        apis: state.apis,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)