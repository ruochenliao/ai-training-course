import {create} from 'zustand'
import type {RouteObject} from 'react-router-dom'

export interface MenuItem {
  id?: string
  name: string
  title?: string
  path?: string
  icon?: string
  children?: MenuItem[]
  type?: 'directory' | 'menu'
  hidden?: boolean
  isHidden?: boolean
  keepAlive?: boolean
  order?: number
  component?: string
  redirect?: string
  permissions?: string[]
  meta?: {
    title?: string
    icon?: string
    customIcon?: string
    order?: number
    keepAlive?: boolean
    activeMenu?: string
  }
}

interface PermissionState {
  permissions: string[]
  routes: RouteObject[]
  menus: MenuItem[]
  menuLoading: boolean
  setPermissions: (permissions: string[]) => void
  setRoutes: (routes: RouteObject[]) => void
  setMenus: (menus: MenuItem[]) => void
  setMenuLoading: (loading: boolean) => void
  generateRoutes: (userPermissions: string[]) => Promise<void>
  hasPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  clearPermissions: () => void
}

export const usePermissionStore = create<PermissionState>()((set, get) => ({
  permissions: [],
  routes: [],
  menus: [],
  menuLoading: false,

  setPermissions: (permissions: string[]) => {
    set({ permissions })
  },

  setRoutes: (routes: RouteObject[]) => {
    set({ routes })
  },

  setMenus: (menus: MenuItem[]) => {
    set({ menus })
  },

  setMenuLoading: (loading: boolean) => {
    set({ menuLoading: loading })
  },

  generateRoutes: async (userPermissions: string[]) => {
    set({ menuLoading: true })
    try {
      // 这里应该调用API获取用户的菜单和路由
      // 暂时使用静态数据
      const staticMenus: MenuItem[] = [
        {
          name: 'workbench',
          path: '/workbench',
          meta: {
            title: '工作台',
            icon: 'mdi:view-dashboard',
            order: 1,
          },
        },
        {
          name: 'system',
          path: '/system',
          meta: {
            title: '系统管理',
            icon: 'mdi:cog',
            order: 2,
          },
          children: [
            {
              name: 'system-user',
              path: '/system/user',
              meta: {
                title: '用户管理',
                icon: 'mdi:account-multiple',
              },
              permissions: ['system:user:list'],
            },
            {
              name: 'system-role',
              path: '/system/role',
              meta: {
                title: '角色管理',
                icon: 'mdi:account-key',
              },
              permissions: ['system:role:list'],
            },
            {
              name: 'system-menu',
              path: '/system/menu',
              meta: {
                title: '菜单管理',
                icon: 'mdi:menu',
              },
              permissions: ['system:menu:list'],
            },
            {
              name: 'system-dept',
              path: '/system/dept',
              meta: {
                title: '部门管理',
                icon: 'mdi:office-building',
              },
              permissions: ['system:dept:list'],
            },
            {
              name: 'system-api',
              path: '/system/api',
              meta: {
                title: 'API管理',
                icon: 'mdi:api',
              },
              permissions: ['system:api:list'],
            },
            {
              name: 'system-auditlog',
              path: '/system/auditlog',
              meta: {
                title: '审计日志',
                icon: 'mdi:file-document-outline',
              },
              permissions: ['system:auditlog:list'],
            },
          ],
        },
      ]

      // 根据权限过滤菜单
      const filterMenusByPermissions = (menus: MenuItem[]): MenuItem[] => {
        return menus.filter(menu => {
          if (menu.permissions && menu.permissions.length > 0) {
            const hasPermission = menu.permissions.some(permission => 
              userPermissions.includes(permission)
            )
            if (!hasPermission) return false
          }

          if (menu.children) {
            menu.children = filterMenusByPermissions(menu.children)
            // 如果目录下没有可访问的子菜单，则隐藏该目录
            if (menu.type === 'directory' && menu.children.length === 0) {
              return false
            }
          }

          return true
        })
      }

      const filteredMenus = filterMenusByPermissions(staticMenus)
      
      set({ 
        permissions: userPermissions,
        menus: filteredMenus,
        menuLoading: false 
      })
    } catch (error) {
      console.error('生成路由失败:', error)
      set({ menuLoading: false })
    }
  },

  hasPermission: (permission: string) => {
    const { permissions } = get()
    return permissions.includes(permission)
  },

  hasAnyPermission: (permissions: string[]) => {
    const { permissions: userPermissions } = get()
    return permissions.some(permission => userPermissions.includes(permission))
  },

  clearPermissions: () => {
    set({ 
      permissions: [],
      routes: [],
      menus: [],
      menuLoading: false 
    })
  },
}))