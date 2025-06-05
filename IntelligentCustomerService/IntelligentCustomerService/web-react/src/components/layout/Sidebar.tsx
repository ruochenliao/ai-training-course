import React from 'react'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  CustomerServiceOutlined,
  MessageOutlined,
  BookOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  SafetyOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useThemeStore } from '@/store/theme'
import type { MenuProps } from 'antd'

const { Sider } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const { sidebarCollapsed } = useThemeStore()

  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: t('menu.dashboard'),
    },
    {
      key: '/customer-service',
      icon: <CustomerServiceOutlined />,
      label: t('menu.customerService'),
      children: [
        {
          key: '/customer-service/conversations',
          icon: <MessageOutlined />,
          label: t('menu.conversation'),
        },
        {
          key: '/customer-service/knowledge',
          icon: <BookOutlined />,
          label: t('menu.knowledge'),
        },
      ],
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: t('menu.analytics'),
    },
    {
      key: '/system',
      icon: <SettingOutlined />,
      label: t('menu.system'),
      children: [
        {
          key: '/system/users',
          icon: <UserOutlined />,
          label: t('menu.user'),
        },
        {
          key: '/system/roles',
          icon: <SafetyOutlined />,
          label: t('menu.role'),
        },
        {
          key: '/system/settings',
          icon: <ToolOutlined />,
          label: t('menu.settings'),
        },
      ],
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    return [location.pathname]
  }

  // 获取当前展开的菜单项
  const getOpenKeys = () => {
    const pathname = location.pathname
    const openKeys: string[] = []
    
    if (pathname.startsWith('/customer-service')) {
      openKeys.push('/customer-service')
    }
    if (pathname.startsWith('/system')) {
      openKeys.push('/system')
    }
    
    return openKeys
  }

  return (
    <Sider
      className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}
      collapsed={sidebarCollapsed}
      width={256}
      collapsedWidth={80}
      theme="light"
    >
      {/* Logo */}
      <div className="h-16 flex-center border-b border-gray-200">
        {sidebarCollapsed ? (
          <div className="text-xl font-bold text-primary-600">ICS</div>
        ) : (
          <div className="text-lg font-bold text-primary-600">
            智能客服系统
          </div>
        )}
      </div>

      {/* 菜单 */}
      <Menu
        mode="inline"
        selectedKeys={getSelectedKeys()}
        defaultOpenKeys={getOpenKeys()}
        items={menuItems}
        onClick={handleMenuClick}
        className="border-r-0"
      />
    </Sider>
  )
}

export default Sidebar