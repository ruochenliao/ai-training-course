import {create} from 'zustand'
import type {RouteObject} from 'react-router-dom'

export interface MenuItem {
  id: string
  title: string
  path?: string
  icon?: string
  children?: MenuItem[]
  type: 'directory' | 'menu'
  hidden?: boolean
  keepAlive?: boolean
  order?: number
  component?: string
  redirect?: string
  permissions?: string[]
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
          id: '1',
          title: '工作台',
          path: '/workbench',
          icon: 'mdi:view-dashboard',
          type: 'menu',
          order: 1,
        },
        {
          id: '2',
          title: '系统管理',
          icon: 'mdi:cog',
          type: 'directory',
          order: 2,
          children: [
            {
              id: '2-1',
              title: '用户管理',
              path: '/system/user',
              icon: 'mdi:account-multiple',
              type: 'menu',
              permissions: ['system:user:list'],
            },
            {
              id: '2-2',
              title: '角色管理',
              path: '/system/role',
              icon: 'mdi:account-key',
              type: 'menu',
              permissions: ['system:role:list'],
            },
            {
              id: '2-3',
              title: '菜单管理',
              path: '/system/menu',
              icon: 'mdi:menu',
              type: 'menu',
              permissions: ['system:menu:list'],
            },
            {
              id: '2-4',
              title: '部门管理',
              path: '/system/dept',
              icon: 'mdi:office-building',
              type: 'menu',
              permissions: ['system:dept:list'],
            },
            {
              id: '2-5',
              title: 'API管理',
              path: '/system/api',
              icon: 'mdi:api',
              type: 'menu',
              permissions: ['system:api:list'],
            },
            {
              id: '2-6',
              title: '审计日志',
              path: '/system/auditlog',
              icon: 'mdi:file-document-outline',
              type: 'menu',
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