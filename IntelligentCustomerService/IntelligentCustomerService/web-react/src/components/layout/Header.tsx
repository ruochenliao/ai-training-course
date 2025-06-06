import React from 'react'
import type {MenuProps} from 'antd'
import {Avatar, Button, Dropdown, Layout, Typography} from 'antd'
import {GithubOutlined, MenuFoldOutlined, MenuUnfoldOutlined, UserOutlined,} from '@ant-design/icons'
import {useNavigate} from 'react-router-dom'
import {useAuthStore} from '@/store/auth'
import {useThemeStore} from '@/store/theme'

const { Header: AntdHeader } = Layout
const { Text } = Typography

const Header: React.FC = () => {
  const navigate = useNavigate()
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
      type: 'divider',
    },
    {
      key: 'logout',
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntdHeader className="flex-between px-4 h-14 bg-white border-b border-gray-200" style={{ padding: '0 16px' }}>
      <div className="flex items-center">
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          className="text-lg"
        />
      </div>

      <div className="flex items-center space-x-4">
        <Button
          type="text"
          icon={<GithubOutlined />}
          href="https://github.com/"
          target="_blank"
          className="text-lg"
        />

        {/* 用户菜单 */}
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <div className="flex items-center cursor-pointer">
            <Avatar
              size="small"
              icon={<UserOutlined />}
            />
            <Text className="ml-2">{user?.username || 'admin'}</Text>
          </div>
        </Dropdown>
      </div>
    </AntdHeader>
  )
}

export default Header