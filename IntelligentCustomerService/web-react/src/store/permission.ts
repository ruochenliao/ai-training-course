import {create} from 'zustand'
import type {RouteObject} from 'react-router-dom'
import {userMenuApi} from '@/api/menu.ts'
import {Icon} from '@iconify/react'
import React from 'react'

// Ant Design Menu 菜单项接口
export interface MenuItem {
  key: string
  label: React.ReactNode
  icon?: React.ReactNode
  path?: string
  order?: number
  children?: MenuItem[]
}

// 原始菜单数据接口 - 对应后端返回的数据结构
export interface RawMenuItem {
  id: number
  name: string
  path: string
  component: string
  icon?: string
  order: number
  parent_id: number
  redirect?: string
  menu_type: 'catalog' | 'menu'
  is_hidden: boolean
  keepalive: boolean
  created_at: string
  updated_at: string
  remark?: any
  children: RawMenuItem[]
}

interface PermissionState {
  permissions: string[]
  routes: RouteObject[]
  menus: MenuItem[]
  rawMenus: RawMenuItem[]
  menuLoading: boolean
  setPermissions: (permissions: string[]) => void
  setRoutes: (routes: RouteObject[]) => void
  setMenus: (menus: MenuItem[]) => void
  setRawMenus: (menus: RawMenuItem[]) => void
  setMenuLoading: (loading: boolean) => void
  generateRoutes: () => Promise<void>
  hasPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  clearPermissions: () => void
}

// 构建完整路径的辅助函数
const buildFullPath = (menu: RawMenuItem, parentPath = ''): string => {
  // 如果是绝对路径（以/开头），直接使用
  if (menu.path.startsWith('/')) {
    return menu.path
  }

  // 如果是相对路径，需要与父路径组合
  if (parentPath) {
    // 确保父路径以/开头
    const normalizedParentPath = parentPath.startsWith('/') ? parentPath : `/${parentPath}`
    return `${normalizedParentPath}/${menu.path}`.replace(/\/+/g, '/') // 去除多余的斜杠
  }

  return `/${menu.path}`
}

// 菜单数据转换函数 - 将后端数据转换为企业级Ant Design Menu格式
const transformMenuData = (rawMenus: RawMenuItem[], parentPath = ''): MenuItem[] => {
  return rawMenus
    .filter((menu) => !menu.is_hidden) // 过滤隐藏菜单
    .sort((a, b) => a.order - b.order) // 按order排序
    .map((menu) => {
      // 构建完整路径
      const fullPath = buildFullPath(menu, parentPath)

      // 智能路径转换 - 根据不同的路径类型进行处理
      let routePath = fullPath

      if (fullPath.startsWith('/system')) {
        // 系统管理模块路径
        routePath = `/dashboard${fullPath}`
      } else if (fullPath === '/top-menu') {
        // 一级菜单特殊处理
        routePath = `/dashboard/top-menu`
      } else if (fullPath === '/workbench') {
        // 工作台路径
        routePath = `/dashboard/workbench`
      } else if (!fullPath.startsWith('/dashboard') && !fullPath.startsWith('/workbench')) {
        // 其他路径默认添加dashboard前缀
        routePath = `/dashboard${fullPath}`
      }

      // 创建菜单标签，支持更丰富的显示效果
      const menuLabel = React.createElement(
        'div',
        {
          className: 'enterprise-menu-item-content',
          style: {
            display: 'flex',
            alignItems: 'center',
            width: '100%',
            overflow: 'hidden',
          },
        },
        [
          // 菜单文字
          React.createElement(
            'span',
            {
              key: 'text',
              className: 'enterprise-menu-text',
              style: {
                flex: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                fontSize: '14px',
                fontWeight: menu.menu_type === 'catalog' ? 500 : 400,
              },
            },
            menu.name,
          ),
          // 菜单类型标识（可选）
          menu.menu_type === 'catalog' &&
            React.createElement(
              'span',
              {
                key: 'badge',
                className: 'enterprise-menu-badge',
                style: {
                  marginLeft: '8px',
                  fontSize: '10px',
                  color: '#1890ff',
                  opacity: 0.7,
                },
              },
              '📁',
            ),
        ],
      )

      const menuItem: MenuItem = {
        key: routePath,
        label: menuLabel,
        icon: menu.icon
          ? React.createElement(Icon, {
              icon: menu.icon,
              style: {
                fontSize: '16px',
                color: menu.menu_type === 'catalog' ? '#1890ff' : '#666',
                transition: 'color 0.2s ease',
              },
            })
          : React.createElement(Icon, {
              icon: menu.menu_type === 'catalog' ? 'mdi:folder-outline' : 'mdi:circle-small',
              style: {
                fontSize: '16px',
                color: menu.menu_type === 'catalog' ? '#1890ff' : '#999',
                transition: 'color 0.2s ease',
              },
            }),
        path: routePath,
        order: menu.order,
      }

      // 处理子菜单
      if (menu.children && menu.children.length > 0) {
        const visibleChildren = menu.children.filter((child) => !child.is_hidden)
        if (visibleChildren.length > 0) {
          menuItem.children = transformMenuData(visibleChildren, fullPath)
        }
      }

      return menuItem
    })
}

export const usePermissionStore = create<PermissionState>()((set, get) => ({
  permissions: [],
  routes: [],
  menus: [],
  rawMenus: [],
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

  setRawMenus: (menus: RawMenuItem[]) => {
    set({ rawMenus: menus })
  },

  setMenuLoading: (loading: boolean) => {
    set({ menuLoading: loading })
  },

  generateRoutes: async () => {
    set({ menuLoading: true })
    try {
      // 调用API获取用户菜单和权限
      const [menuResponse, apiResponse] = await Promise.all([userMenuApi.getUserMenu(), userMenuApi.getUserApi()])

      const rawMenus = menuResponse.data as RawMenuItem[]
      const userApis = apiResponse.data

      // 数据验证和预处理
      if (!Array.isArray(rawMenus)) {
        throw new Error('菜单数据格式错误')
      }

      // 转换菜单数据为Ant Design Menu格式
      const transformedMenus = transformMenuData(rawMenus)

      // 添加默认工作台菜单（如果不存在）
      const hasWorkbench = transformedMenus.some((menu) => menu.key === '/workbench')
      if (!hasWorkbench) {
        const workbenchMenu: MenuItem = {
          key: '/workbench',
          label: React.createElement('div', { className: 'enterprise-menu-item-content' }, [
            React.createElement('span', { key: 'text', className: 'enterprise-menu-text' }, '工作台'),
            React.createElement('span', { key: 'badge', className: 'enterprise-menu-badge' }, '🏠'),
          ]),
          icon: React.createElement(Icon, {
            icon: 'mdi:view-dashboard',
            style: { fontSize: '16px', color: '#1890ff' },
          }),
          path: '/workbench',
          order: 0,
        }
        transformedMenus.unshift(workbenchMenu)
      }

      // 按order排序
      transformedMenus.sort((a, b) => (a.order || 0) - (b.order || 0))

      set({
        permissions: userApis,
        menus: transformedMenus,
        rawMenus: rawMenus,
        menuLoading: false,
      })

      console.log('🎉 动态菜单加载成功:', {
        menuCount: transformedMenus.length,
        permissionCount: userApis.length,
        rawMenus,
        transformedMenus,
      })

      // 存储到localStorage作为缓存
      localStorage.setItem(
        'user_menus_cache',
        JSON.stringify({
          menus: transformedMenus,
          rawMenus: rawMenus,
          permissions: userApis,
          timestamp: Date.now(),
        }),
      )
    } catch (error) {
      console.error('❌ 获取用户菜单失败:', error)

      // 尝试从缓存恢复
      try {
        const cache = localStorage.getItem('user_menus_cache')
        if (cache) {
          const cacheData = JSON.parse(cache)
          const isExpired = Date.now() - cacheData.timestamp > 24 * 60 * 60 * 1000 // 24小时过期

          if (!isExpired) {
            set({
              menus: cacheData.menus || [],
              rawMenus: cacheData.rawMenus || [],
              permissions: cacheData.permissions || [],
              menuLoading: false,
            })
            console.log('📦 从缓存恢复菜单数据')
            return
          }
        }
      } catch (cacheError) {
        console.warn('缓存恢复失败:', cacheError)
      }

      // 使用默认菜单
      const defaultMenus: MenuItem[] = [
        {
          key: '/workbench',
          label: React.createElement('div', { className: 'enterprise-menu-item-content' }, [
            React.createElement('span', { key: 'text', className: 'enterprise-menu-text' }, '工作台'),
            React.createElement('span', { key: 'badge', className: 'enterprise-menu-badge' }, '🏠'),
          ]),
          icon: React.createElement(Icon, {
            icon: 'mdi:view-dashboard',
            style: { fontSize: '16px', color: '#1890ff' },
          }),
          path: '/workbench',
          order: 1,
        },
      ]

      set({
        menus: defaultMenus,
        rawMenus: [],
        permissions: [],
        menuLoading: false,
      })
    }
  },

  hasPermission: (permission: string) => {
    const { permissions } = get()
    return permissions.includes(permission)
  },

  hasAnyPermission: (permissions: string[]) => {
    const { permissions: userPermissions } = get()
    return permissions.some((permission) => userPermissions.includes(permission))
  },

  clearPermissions: () => {
    set({
      permissions: [],
      routes: [],
      menus: [],
      menuLoading: false,
    })
  },
}))
