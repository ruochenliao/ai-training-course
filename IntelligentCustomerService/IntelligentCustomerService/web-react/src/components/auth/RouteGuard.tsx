import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { Permission, usePermission } from './PermissionControl'
import { PageLoading } from '../common/LoadingEmpty'
import { useTranslation } from 'react-i18next'

// 认证守卫Props
export interface AuthGuardProps {
  children: React.ReactNode
  redirectTo?: string
  fallback?: React.ReactNode
}

// 认证守卫组件
export const AuthGuard: React.FC<AuthGuardProps> = ({ children, redirectTo = '/login', fallback }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()
  const location = useLocation()
  const { t } = useTranslation()

  useEffect(() => {
    // 如果未认证且不在加载中，尝试检查认证状态
    if (!isAuthenticated && !isLoading) {
      checkAuth()
    }
  }, [isAuthenticated, isLoading, checkAuth])

  // 正在加载认证状态
  if (isLoading) {
    return fallback || <PageLoading tip={t('auth.checking')} />
  }

  // 未认证，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  return <>{children}</>
}

// 权限守卫Props
export interface PermissionGuardProps {
  permissions?: Permission
  roles?: string | string[]
  children: React.ReactNode
  fallback?: React.ReactNode
  redirectTo?: string
  mode?: 'any' | 'all'
}

// 权限守卫组件
export const PermissionGuard: React.FC<PermissionGuardProps> = ({ permissions, roles, children, fallback, redirectTo = '/403', mode = 'any' }) => {
  const { hasPermission, hasRole } = usePermission()
  const location = useLocation()

  let hasAccess = true

  if (permissions && roles) {
    if (mode === 'all') {
      hasAccess = hasPermission(permissions) && hasRole(roles)
    } else {
      hasAccess = hasPermission(permissions) || hasRole(roles)
    }
  } else if (permissions) {
    hasAccess = hasPermission(permissions)
  } else if (roles) {
    hasAccess = hasRole(roles)
  }

  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>
    }
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  return <>{children}</>
}

// 组合守卫Props
export interface RouteGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  permissions?: Permission
  roles?: string | string[]
  authRedirectTo?: string
  permissionRedirectTo?: string
  authFallback?: React.ReactNode
  permissionFallback?: React.ReactNode
  mode?: 'any' | 'all'
}

// 路由守卫组件（组合认证和权限守卫）
export const RouteGuard: React.FC<RouteGuardProps> = ({
  children,
  requireAuth = true,
  permissions,
  roles,
  authRedirectTo = '/login',
  permissionRedirectTo = '/403',
  authFallback,
  permissionFallback,
  mode = 'any',
}) => {
  // 如果不需要认证，直接返回子组件
  if (!requireAuth && !permissions && !roles) {
    return <>{children}</>
  }

  // 需要认证的情况
  if (requireAuth) {
    return (
      <AuthGuard redirectTo={authRedirectTo} fallback={authFallback}>
        {permissions || roles ? (
          <PermissionGuard permissions={permissions} roles={roles} redirectTo={permissionRedirectTo} fallback={permissionFallback} mode={mode}>
            {children}
          </PermissionGuard>
        ) : (
          children
        )}
      </AuthGuard>
    )
  }

  // 只需要权限检查的情况
  if (permissions || roles) {
    return (
      <PermissionGuard permissions={permissions} roles={roles} redirectTo={permissionRedirectTo} fallback={permissionFallback} mode={mode}>
        {children}
      </PermissionGuard>
    )
  }

  return <>{children}</>
}

// 公开路由守卫（已登录用户不能访问）
export interface PublicGuardProps {
  children: React.ReactNode
  redirectTo?: string
}

export const PublicGuard: React.FC<PublicGuardProps> = ({ children, redirectTo = '/' }) => {
  const { isAuthenticated, isLoading } = useAuthStore()
  const { t } = useTranslation()

  // 正在加载认证状态
  if (isLoading) {
    return <PageLoading tip={t('auth.checking')} />
  }

  // 已认证，重定向到首页
  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  return <>{children}</>
}

// 角色守卫组件
export interface RoleGuardProps {
  roles: string | string[]
  children: React.ReactNode
  fallback?: React.ReactNode
  redirectTo?: string
  mode?: 'any' | 'all'
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ roles, children, fallback, redirectTo = '/403', mode = 'any' }) => {
  const { hasRole } = usePermission()
  const location = useLocation()

  const roleArray = Array.isArray(roles) ? roles : [roles]
  const hasAccess = mode === 'all' ? roleArray.every((role) => hasRole(role)) : roleArray.some((role) => hasRole(role))

  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>
    }
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  return <>{children}</>
}

// 管理员守卫组件
export interface AdminGuardProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  redirectTo?: string
}

export const AdminGuard: React.FC<AdminGuardProps> = ({ children, fallback, redirectTo = '/403' }) => {
  return (
    <RoleGuard roles={['admin', 'super_admin']} fallback={fallback} redirectTo={redirectTo} mode='any'>
      {children}
    </RoleGuard>
  )
}

// 导出所有组件
export default {
  AuthGuard,
  PermissionGuard,
  RouteGuard,
  PublicGuard,
  RoleGuard,
  AdminGuard,
}

// 导出类型
export type { AuthGuardProps, PermissionGuardProps, RouteGuardProps, PublicGuardProps, RoleGuardProps, AdminGuardProps }
