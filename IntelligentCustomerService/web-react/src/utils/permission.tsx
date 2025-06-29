import React from 'react'
import {usePermissionStore} from '@/store/permission.ts'
import {useAuthStore} from '@/store/auth.ts'

/**
 * 检查是否有指定权限
 */
export function hasPermission(permission: string): boolean {
  const { hasPermission } = usePermissionStore.getState()
  return hasPermission(permission)
}

/**
 * 检查是否有任意一个权限
 */
export function hasAnyPermission(permissions: string[]): boolean {
  const { hasAnyPermission } = usePermissionStore.getState()
  return hasAnyPermission(permissions)
}

/**
 * 检查是否有所有权限
 */
export function hasAllPermissions(permissions: string[]): boolean {
  const { permissions: userPermissions } = usePermissionStore.getState()
  return permissions.every((permission) => userPermissions.includes(permission))
}

/**
 * 检查是否是管理员
 */
export function isAdmin(): boolean {
  const { user } = useAuthStore.getState()
  return user?.roles?.includes('admin') || false
}

/**
 * 检查是否是超级管理员
 */
export function isSuperAdmin(): boolean {
  const { user } = useAuthStore.getState()
  return user?.roles?.includes('super_admin') || false
}

/**
 * 检查用户角色
 */
export function hasRole(role: string): boolean {
  const { user } = useAuthStore.getState()
  return user?.roles?.includes(role) || false
}

/**
 * 检查是否有任意一个角色
 */
export function hasAnyRole(roles: string[]): boolean {
  const { user } = useAuthStore.getState()
  if (!user?.roles) return false
  return roles.some((role) => user.roles.includes(role))
}

/**
 * 权限指令 Hook
 * 用于在 React 组件中进行权限控制
 */
export function usePermission() {
  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
    isSuperAdmin,
    hasRole,
    hasAnyRole,
  }
}

/**
 * 权限高阶组件
 * 用于包装需要权限控制的组件
 */
export function withPermission<P extends object>(Component: React.ComponentType<P>, permission: string | string[], fallback?: React.ReactNode) {
  return function PermissionWrapper(props: P): React.ReactNode {
    const hasAccess = Array.isArray(permission) ? hasAnyPermission(permission) : hasPermission(permission)

    if (!hasAccess) {
      return fallback || null
    }

    return <Component {...props} />
  }
}

/**
 * Role higher-order component
 * Used to wrap components that require role control
 */
export function withRole<P extends object>(Component: React.ComponentType<P>, role: string | string[], fallback?: React.ReactNode) {
  return function RoleWrapper(props: P): React.ReactNode {
    const hasAccess = Array.isArray(role) ? hasAnyRole(role) : hasRole(role)

    if (!hasAccess) {
      return fallback || null
    }

    return <Component {...props} />
  }
}

/**
 * 权限检查组件
 * 用于在 JSX 中进行权限控制
 */
interface PermissionProps {
  permission?: string | string[]
  role?: string | string[]
  fallback?: React.ReactNode
  children: React.ReactNode
}

export function Permission({ permission, role, fallback, children }: PermissionProps): React.ReactNode {
  let hasAccess = true

  // 检查权限
  if (permission) {
    hasAccess = Array.isArray(permission) ? hasAnyPermission(permission) : hasPermission(permission)
  }

  // 检查角色
  if (hasAccess && role) {
    hasAccess = Array.isArray(role) ? hasAnyRole(role) : hasRole(role)
  }

  if (!hasAccess) {
    return fallback || null
  }

  return <>{children}</>
}

/**
 * 权限按钮组件
 * 用于控制按钮的显示和禁用状态
 */
interface PermissionButtonProps {
  permission?: string | string[]
  role?: string | string[]
  hideWhenNoAccess?: boolean
  disableWhenNoAccess?: boolean
  children: React.ReactElement
}

export function PermissionButton({ permission, role, hideWhenNoAccess = false, disableWhenNoAccess = true, children }: PermissionButtonProps) {
  let hasAccess = true

  // 检查权限
  if (permission) {
    hasAccess = Array.isArray(permission) ? hasAnyPermission(permission) : hasPermission(permission)
  }

  // 检查角色
  if (hasAccess && role) {
    hasAccess = Array.isArray(role) ? hasAnyRole(role) : hasRole(role)
  }

  // 没有权限时隐藏
  if (!hasAccess && hideWhenNoAccess) {
    return null
  }

  // 没有权限时禁用
  if (!hasAccess && disableWhenNoAccess) {
    return React.cloneElement(children, {
      ...children.props,
      disabled: true,
    })
  }

  return children
}

/**
 * 获取用户可访问的菜单
 */
export function getAccessibleMenus(menus: any[]): any[] {
  const { permissions } = usePermissionStore.getState()

  function filterMenus(menuList: any[]): any[] {
    return menuList.filter((menu) => {
      // 检查菜单权限
      if (menu.permissions && menu.permissions.length > 0) {
        const hasMenuPermission = menu.permissions.some((permission: string) => permissions.includes(permission))
        if (!hasMenuPermission) {
          return false
        }
      }

      // 递归过滤子菜单
      if (menu.children && menu.children.length > 0) {
        menu.children = filterMenus(menu.children)
        // 如果是目录类型且没有可访问的子菜单，则隐藏
        if (menu.type === 'directory' && menu.children.length === 0) {
          return false
        }
      }

      return true
    })
  }

  return filterMenus(menus)
}

/**
 * 权限常量
 */
export const PERMISSIONS = {
  // 系统管理
  SYSTEM_USER_LIST: 'system:user:list',
  SYSTEM_USER_CREATE: 'system:user:create',
  SYSTEM_USER_UPDATE: 'system:user:update',
  SYSTEM_USER_DELETE: 'system:user:delete',
  SYSTEM_USER_RESET_PASSWORD: 'system:user:reset_password',

  SYSTEM_ROLE_LIST: 'system:role:list',
  SYSTEM_ROLE_CREATE: 'system:role:create',
  SYSTEM_ROLE_UPDATE: 'system:role:update',
  SYSTEM_ROLE_DELETE: 'system:role:delete',

  SYSTEM_MENU_LIST: 'system:menu:list',
  SYSTEM_MENU_CREATE: 'system:menu:create',
  SYSTEM_MENU_UPDATE: 'system:menu:update',
  SYSTEM_MENU_DELETE: 'system:menu:delete',

  SYSTEM_DEPT_LIST: 'system:dept:list',
  SYSTEM_DEPT_CREATE: 'system:dept:create',
  SYSTEM_DEPT_UPDATE: 'system:dept:update',
  SYSTEM_DEPT_DELETE: 'system:dept:delete',

  SYSTEM_API_LIST: 'system:api:list',
  SYSTEM_API_CREATE: 'system:api:create',
  SYSTEM_API_UPDATE: 'system:api:update',
  SYSTEM_API_DELETE: 'system:api:delete',

  SYSTEM_AUDITLOG_LIST: 'system:auditlog:list',
  SYSTEM_AUDITLOG_EXPORT: 'system:auditlog:export',
} as const

/**
 * 角色常量
 */
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  USER: 'user',
} as const
