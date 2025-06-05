import React from 'react'
import { Layout, Button, Dropdown, Avatar, Space, Switch } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MoonOutlined,
  SunOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'

const { Header: AntdHeader } = Layout

const Header: React.FC = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar, isDark, toggleTheme } = useThemeStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('auth.logout'),
      onClick: handleLogout,
    },
  ]

  return (
    <AntdHeader className="header flex-between px-6 h-16">
      <div className="flex items-center">
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          className="text-lg"
        />
      </div>

      <div className="flex items-center space-x-4">
        {/* 主题切换 */}
        <Switch
          checked={isDark}
          onChange={toggleTheme}
          checkedChildren={<MoonOutlined />}
          unCheckedChildren={<SunOutlined />}
        />

        {/* 通知 */}
        <Button
          type="text"
          icon={<BellOutlined />}
          className="text-lg"
        />

        {/* 用户菜单 */}
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space className="cursor-pointer hover:bg-gray-50 px-2 py-1 rounded">
            <Avatar
              size="small"
              src={user?.avatar}
              icon={<UserOutlined />}
            />
            <span className="text-sm">{user?.nickname || user?.username}</span>
          </Space>
        </Dropdown>
      </div>
    </AntdHeader>
  )
}

export default Header