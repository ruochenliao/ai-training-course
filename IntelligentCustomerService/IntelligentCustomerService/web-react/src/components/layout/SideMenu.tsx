import React, { useMemo, useEffect } from 'react'
import { Menu } from 'antd'
import type { MenuProps } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { Icon } from '@iconify/react'
import { usePermissionStore, type MenuItem } from '../../store/permission'
import { useAppStore } from '../../store/app'
import { isExternal } from '../../utils'
import MenuStats from './MenuStats'

/**
 * 企业级侧边栏菜单组件 - 支持动态菜单
 *
 * 功能特性：
 * 1. 从API动态获取菜单数据
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
  const { menus, menuLoading, generateRoutes } = usePermissionStore()
  const { reloading, setReloading, collapsed } = useAppStore()

  // 组件挂载时获取动态菜单
  useEffect(() => {
    if (menus.length === 0 && !menuLoading) {
      generateRoutes()
    }
  }, [menus.length, menuLoading, generateRoutes])

  // 当前激活的菜单key
  const activeKey = useMemo(() => {
    return location.pathname
  }, [location.pathname])

  // 默认展开的菜单
  const defaultOpenKeys = useMemo(() => {
    if (collapsed) return []

    const paths = location.pathname.split('/').filter(Boolean)
    const keys: string[] = []

    // 构建父级路径数组
    for (let i = 0; i < paths.length - 1; i++) {
      const parentPath = '/' + paths.slice(0, i + 1).join('/')
      keys.push(parentPath)
    }

    return keys
  }, [location.pathname, collapsed])

  // 菜单选项 - 直接使用从store获取的已转换菜单数据
  const menuOptions = useMemo(() => {
    return menus
  }, [menus])

  // 处理菜单点击 - 简化版本，直接使用key作为路径
  const handleMenuClick = ({ key }: { key: string }) => {
    const path = key

    console.log('🎯 菜单点击调试信息:', {
      clickedKey: key,
      targetPath: path,
      currentPath: location.pathname,
      isExternal: isExternal(path)
    })

    if (isExternal(path)) {
      // 外链菜单新窗口打开
      console.log('🔗 打开外链:', path)
      window.open(path)
    } else {
      if (path === location.pathname) {
        // 相同路由点击刷新页面
        console.log('🔄 刷新当前页面:', path)
        setReloading(true)
        setTimeout(() => {
          setReloading(false)
        }, 100)
      } else {
        console.log('🚀 导航到新路径:', path)
        navigate(path)
      }
    }
  }

  // 菜单加载状态
  if (menuLoading) {
    return (
      <div className="enterprise-side-menu-container">
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '200px',
          color: '#8c8c8c'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            border: '2px solid #f0f0f0',
            borderTop: '2px solid #1890ff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginBottom: '12px'
          }} />
          <span style={{ fontSize: '12px' }}>加载菜单中...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="enterprise-side-menu-container">
      {/* 菜单标题 */}
      {!collapsed && (
        <div style={{
          padding: '12px 24px 8px',
          fontSize: '12px',
          color: '#8c8c8c',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          borderBottom: '1px solid #f0f0f0',
          marginBottom: '8px',
        }}>
          导航菜单
        </div>
      )}

      <Menu
        className={`enterprise-side-menu ${collapsed ? 'ant-menu-inline-collapsed' : ''}`}
        mode="inline"
        selectedKeys={[activeKey]}
        defaultOpenKeys={defaultOpenKeys}
        items={menuOptions as any}
        onClick={handleMenuClick}
        inlineIndent={20}
        inlineCollapsed={collapsed}
        style={{
          borderRight: 0,
          background: 'transparent',
          fontSize: '14px',
        }}
        theme="light"
      />

      {/* 菜单统计信息 */}
      {!collapsed && (
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '0',
          right: '0',
        }}>
          <MenuStats />
        </div>
      )}
    </div>
  )
}

export default SideMenu
