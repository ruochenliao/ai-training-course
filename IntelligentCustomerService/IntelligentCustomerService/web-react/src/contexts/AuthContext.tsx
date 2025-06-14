import React, { createContext, ReactNode, useContext, useEffect } from 'react'
import { useAuthStore } from '../store/auth'
import { usePermissionStore } from '../store/permission'
import { User } from '../types/auth'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { user, token, loading, login, logout, checkAuth } = useAuthStore()

  const { generateRoutes, clearPermissions } = usePermissionStore()

  const isAuthenticated = !!token && !!user

  useEffect(() => {
    // 检查本地存储中的认证信息
    checkAuth()
  }, [checkAuth])

  // 当用户认证状态改变时，处理菜单权限
  useEffect(() => {
    if (isAuthenticated) {
      // 用户已认证，获取动态菜单
      generateRoutes().catch((error) => {
        console.error('获取用户菜单失败:', error)
      })
    } else {
      // 用户未认证，清除权限信息
      clearPermissions()
    }
  }, [isAuthenticated, generateRoutes, clearPermissions])

  const value: AuthContextType = {
    user,
    isAuthenticated,
    login,
    logout,
    loading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
