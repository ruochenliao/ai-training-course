import { useCallback } from 'react'
import { usePermissionStore } from '@/store/permission'

/**
 * 权限验证Hook
 */
function usePermission() {
  const { permissions, hasPermission, hasAnyPermission } = usePermissionStore()

  /**
   * 检查是否拥有指定权限
   * @param permission 权限标识
   * @returns 是否拥有权限
   */
  const checkPermission = useCallback(
    (permission: string): boolean => {
      return hasPermission(permission)
    },
    [hasPermission],
  )

  /**
   * 检查是否拥有指定权限中的任意一个
   * @param permissionList 权限标识列表
   * @returns 是否拥有权限
   */
  const checkAnyPermission = useCallback(
    (permissionList: string[]): boolean => {
      return hasAnyPermission(permissionList)
    },
    [hasAnyPermission],
  )

  /**
   * 检查是否拥有指定权限中的所有权限
   * @param permissionList 权限标识列表
   * @returns 是否拥有权限
   */
  const checkAllPermissions = useCallback(
    (permissionList: string[]): boolean => {
      return permissionList.every((permission) => hasPermission(permission))
    },
    [hasPermission],
  )

  /**
   * 过滤出有权限的项目
   * @param items 项目列表
   * @param getPermission 获取项目权限的函数
   * @returns 有权限的项目列表
   */
  const filterByPermission = useCallback(
    <T>(items: T[], getPermission: (item: T) => string | string[] | undefined): T[] => {
      return items.filter((item) => {
        const permission = getPermission(item)
        if (!permission) return true

        if (Array.isArray(permission)) {
          return hasAnyPermission(permission)
        }

        return hasPermission(permission)
      })
    },
    [hasPermission, hasAnyPermission],
  )

  return {
    permissions,
    checkPermission,
    checkAnyPermission,
    checkAllPermissions,
    filterByPermission,
  }
}

export default usePermission
