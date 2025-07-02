/**
 * 权限验证工具函数
 */

import { useAuthStore } from '@/stores/auth'

/**
 * 检查用户是否拥有指定权限
 */
export function hasPermission(permission: string | string[]): boolean {
  const authStore = useAuthStore()
  
  // 超级用户拥有所有权限
  if (authStore.userInfo?.is_superuser) {
    return true
  }
  
  const userPermissions = authStore.permissions
  
  if (typeof permission === 'string') {
    return userPermissions.includes(permission)
  }
  
  if (Array.isArray(permission)) {
    return permission.some(p => userPermissions.includes(p))
  }
  
  return false
}

/**
 * 检查用户是否拥有所有指定权限
 */
export function hasAllPermissions(permissions: string[]): boolean {
  const authStore = useAuthStore()
  
  // 超级用户拥有所有权限
  if (authStore.userInfo?.is_superuser) {
    return true
  }
  
  const userPermissions = authStore.permissions
  
  return permissions.every(permission => userPermissions.includes(permission))
}

/**
 * 检查用户是否拥有指定角色
 */
export function hasRole(role: string | string[]): boolean {
  const authStore = useAuthStore()
  
  // 超级用户拥有所有角色
  if (authStore.userInfo?.is_superuser) {
    return true
  }
  
  const userRoles = authStore.roles
  
  if (typeof role === 'string') {
    return userRoles.includes(role)
  }
  
  if (Array.isArray(role)) {
    return role.some(r => userRoles.includes(r))
  }
  
  return false
}

/**
 * 检查用户是否为超级用户
 */
export function isSuperUser(): boolean {
  const authStore = useAuthStore()
  return authStore.userInfo?.is_superuser || false
}

/**
 * 检查路由是否需要权限验证
 */
export function checkRoutePermission(route: any): boolean {
  const { meta } = route
  
  // 没有权限要求的路由直接通过
  if (!meta?.permissions && !meta?.roles) {
    return true
  }
  
  // 检查权限
  if (meta.permissions) {
    if (!hasPermission(meta.permissions)) {
      return false
    }
  }
  
  // 检查角色
  if (meta.roles) {
    if (!hasRole(meta.roles)) {
      return false
    }
  }
  
  return true
}

/**
 * 过滤用户有权限的菜单
 */
export function filterMenusByPermission(menus: any[]): any[] {
  const authStore = useAuthStore()
  
  // 超级用户显示所有菜单
  if (authStore.userInfo?.is_superuser) {
    return menus
  }
  
  return menus.filter(menu => {
    // 检查菜单权限
    if (menu.meta?.permissions && !hasPermission(menu.meta.permissions)) {
      return false
    }
    
    if (menu.meta?.roles && !hasRole(menu.meta.roles)) {
      return false
    }
    
    // 递归过滤子菜单
    if (menu.children && menu.children.length > 0) {
      menu.children = filterMenusByPermission(menu.children)
      // 如果所有子菜单都被过滤掉了，则隐藏父菜单
      return menu.children.length > 0
    }
    
    return true
  })
}

/**
 * 权限验证装饰器
 */
export function requirePermission(permission: string | string[]) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value
    
    descriptor.value = function (...args: any[]) {
      if (!hasPermission(permission)) {
        console.warn(`权限不足，需要权限: ${permission}`)
        return
      }
      
      return originalMethod.apply(this, args)
    }
    
    return descriptor
  }
}
