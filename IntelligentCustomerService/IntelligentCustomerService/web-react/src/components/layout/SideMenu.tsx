import React, { useMemo } from 'react'
import { Menu } from 'antd'
import type { MenuProps } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { Icon } from '@iconify/react'
import { usePermissionStore } from '../../store/permission'
import { useAppStore } from '../../store/app'
import { isExternal } from '../../utils'

type MenuItem = Required<MenuProps>['items'][number]

/**
 * 侧边栏菜单组件 - 对应Vue版本的SideMenu.vue
 * 
 * 功能特性：
 * 1. 基于权限的动态菜单生成
 * 2. 支持多级菜单嵌套
 * 3. 手风琴模式展开
 * 4. 菜单图标支持（Iconify图标）
 * 5. 外链菜单支持
 * 6. 当前路由高亮
 * 7. 菜单排序支持
 */
const SideMenu: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { menus } = usePermissionStore()
  const { reloading, setReloading } = useAppStore()

  // 当前激活的菜单key - 对应Vue版本的 activeKey
  const activeKey = useMemo(() => {
    // 对应Vue版本的 curRoute.meta?.activeMenu || curRoute.name
    return location.pathname
  }, [location.pathname])

  // 路径解析函数 - 对应Vue版本的 resolvePath
  const resolvePath = (basePath: string, path: string): string => {
    if (isExternal(path)) return path
    return (
      '/' +
      [basePath, path]
        .filter((path) => !!path && path !== '/')
        .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
        .join('/')
    )
  }

  // 获取菜单图标 - 对应Vue版本的 getIcon
  const getIcon = (meta: any) => {
    if (meta?.customIcon) {
      return <Icon icon={meta.customIcon} style={{ fontSize: '18px' }} />
    }
    if (meta?.icon) {
      return <Icon icon={meta.icon} style={{ fontSize: '18px' }} />
    }
    return null
  }

  // 转换菜单项 - 对应Vue版本的 getMenuItem
  const getMenuItem = (route: any, basePath = ''): MenuItem => {
    let menuItem: MenuItem = {
      label: (route.meta && route.meta.title) || route.name,
      key: route.name,
      icon: getIcon(route.meta),
    }

    // 添加路径信息用于导航
    ;(menuItem as any).path = resolvePath(basePath, route.path)
    ;(menuItem as any).order = route.meta?.order || 0

    const visibleChildren = route.children
      ? route.children.filter((item: any) => item.name && !item.isHidden)
      : []

    if (!visibleChildren.length) return menuItem

    if (visibleChildren.length === 1) {
      // 单个子路由处理 - 对应Vue版本的单个子路由逻辑
      const singleRoute = visibleChildren[0]
      menuItem = {
        ...menuItem,
        label: singleRoute.meta?.title || singleRoute.name,
        key: singleRoute.name,
        icon: getIcon(singleRoute.meta),
      }
      ;(menuItem as any).path = resolvePath((menuItem as any).path, singleRoute.path)

      const visibleItems = singleRoute.children
        ? singleRoute.children.filter((item: any) => item.name && !item.isHidden)
        : []

      if (visibleItems.length === 1) {
        menuItem = getMenuItem(visibleItems[0], (menuItem as any).path)
      } else if (visibleItems.length > 1) {
        menuItem.children = visibleItems
          .map((item: any) => getMenuItem(item, (menuItem as any).path))
          .sort((a: any, b: any) => a.order - b.order)
      }
    } else {
      menuItem.children = visibleChildren
        .map((item: any) => getMenuItem(item, (menuItem as any).path))
        .sort((a: any, b: any) => a.order - b.order)
    }

    return menuItem
  }

  // 菜单选项 - 对应Vue版本的 menuOptions
  const menuOptions = useMemo(() => {
    return menus
      .map((item) => getMenuItem(item))
      .sort((a: any, b: any) => a.order - b.order)
  }, [menus])

  // 处理菜单点击 - 对应Vue版本的 handleMenuSelect
  const handleMenuClick = ({ key }: { key: string }) => {
    const findMenuItem = (items: MenuItem[], targetKey: string): any => {
      for (const item of items) {
        if (item?.key === targetKey) {
          return item
        }
        if ((item as any)?.children) {
          const found = findMenuItem((item as any).children, targetKey)
          if (found) return found
        }
      }
      return null
    }

    const menuItem = findMenuItem(menuOptions, key)
    if (!menuItem) return

    const path = (menuItem as any).path

    if (isExternal(path)) {
      // 外链菜单新窗口打开
      window.open(path)
    } else {
      if (path === location.pathname) {
        // 相同路由点击刷新页面 - 对应Vue版本的 appStore.reloadPage()
        setReloading(true)
        setTimeout(() => {
          setReloading(false)
        }, 100)
      } else {
        navigate(path)
      }
    }
  }

  return (
    <Menu
      className="side-menu"
      mode="inline"
      selectedKeys={[activeKey]}
      items={menuOptions}
      onClick={handleMenuClick}
      inlineIndent={18}
      style={{
        border: 'none',
        background: 'transparent',
      }}
    />
  )
}

export default SideMenu
