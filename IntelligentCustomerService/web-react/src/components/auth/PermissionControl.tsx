import React from 'react'
import {Button, Result} from 'antd'
import {useTranslation} from 'react-i18next'
import {useAuthStore} from '@/store/auth.ts'

// 权限类型定义
export type Permission = string | string[]

// 权限检查函数
export const checkPermission = (userPermissions: string[], requiredPermissions: Permission): boolean => {
  if (!requiredPermissions) return true

  const permissions = Array.isArray(requiredPermissions) ? requiredPermissions : [requiredPermissions]

  // 如果用户有超级管理员权限，直接通过
  if (userPermissions.includes('*') || userPermissions.includes('admin')) {
    return true
  }

  // 检查是否有任一权限
  return permissions.some((permission) => userPermissions.includes(permission))
}

// 权限检查Hook
export const usePermission = () => {
  const { user } = useAuthStore()

  const hasPermission = (requiredPermissions: Permission): boolean => {
    if (!user || !user.permissions) return false
    return checkPermission(user.permissions, requiredPermissions)
  }

  const hasRole = (requiredRoles: string | string[]): boolean => {
    if (!user || !user.roles) return false

    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles]
    return roles.some((role) => user.roles.includes(role))
  }

  const hasAnyPermission = (permissionsList: Permission[]): boolean => {
    return permissionsList.some((permissions) => hasPermission(permissions))
  }

  const hasAllPermissions = (permissionsList: Permission[]): boolean => {
    return permissionsList.every((permissions) => hasPermission(permissions))
  }

  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    user,
  }
}

// 权限控制组件Props
export interface PermissionProps {
  permissions?: Permission
  roles?: string | string[]
  fallback?: React.ReactNode
  children: React.ReactNode
  mode?: 'any' | 'all' // any: 满足任一权限即可, all: 需要满足所有权限
}

// 权限控制组件
export const Permission: React.FC<PermissionProps> = ({ permissions, roles, fallback, children, mode = 'any' }) => {
  const { hasPermission, hasRole } = usePermission()

  let hasAccess = true

  if (permissions && roles) {
    // 同时检查权限和角色
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
    return <>{fallback || null}</>
  }

  return <>{children}</>
}

// 无权限访问页面
export interface NoPermissionProps {
  title?: string
  subTitle?: string
  extra?: React.ReactNode
  onBack?: () => void
}

export const NoPermission: React.FC<NoPermissionProps> = ({ title, subTitle, extra, onBack }) => {
  const { t } = useTranslation()

  const defaultExtra = onBack ? (
    <Button type='primary' onClick={onBack}>
      {t('common.back')}
    </Button>
  ) : undefined

  return (
    <Result
      status='403'
      title={title || t('permission.noAccess')}
      subTitle={subTitle || t('permission.noAccessMessage')}
      extra={extra || defaultExtra}
    />
  )
}

// 权限控制高阶组件
export interface WithPermissionOptions {
  permissions?: Permission
  roles?: string | string[]
  fallback?: React.ComponentType
  redirect?: string
  mode?: 'any' | 'all'
}

export const withPermission = <P extends object>(WrappedComponent: React.ComponentType<P>, options: WithPermissionOptions = {}) => {
  const PermissionWrapper: React.FC<P> = (props) => {
    const { hasPermission, hasRole } = usePermission()
    const { permissions, roles, fallback: Fallback, mode = 'any' } = options

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
      if (Fallback) {
        return <Fallback />
      }
      return <NoPermission />
    }

    return <WrappedComponent {...props} />
  }

  PermissionWrapper.displayName = `withPermission(${WrappedComponent.displayName || WrappedComponent.name})`

  return PermissionWrapper
}

// 权限按钮组件
export interface PermissionButtonProps {
  permissions?: Permission
  roles?: string | string[]
  children: React.ReactNode
  mode?: 'any' | 'all'
  [key: string]: any // 其他props传递给Button
}

export const PermissionButton: React.FC<PermissionButtonProps> = ({ permissions, roles, children, mode = 'any', ...buttonProps }) => {
  return (
    <Permission permissions={permissions} roles={roles} mode={mode}>
      <Button {...buttonProps}>{children}</Button>
    </Permission>
  )
}

// 导出所有组件和工具
export default {
  Permission,
  NoPermission,
  PermissionButton,
  withPermission,
  usePermission,
  checkPermission,
}

// 导出类型
export type { PermissionProps, NoPermissionProps, WithPermissionOptions, PermissionButtonProps }
