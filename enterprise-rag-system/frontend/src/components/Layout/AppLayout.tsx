import React, { useState } from 'react'
import type { MenuProps } from 'antd'
import { Avatar, Badge, Button, Dropdown, Layout, Menu, Space, Typography } from 'antd'
import {
  BellOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  SearchOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useSimpleAuthStore } from '@/store/simple-auth'

const { Header, Sider, Content } = Layout
const { Text } = Typography

// 菜单项配置
const menuItems: MenuProps['items'] = [
  {
    key: '/',
    icon: <HomeOutlined />,
    label: '首页',
  },
  {
    key: '/chat',
    icon: <MessageOutlined />,
    label: '智能对话',
  },
  {
    key: '/knowledge',
    icon: <DatabaseOutlined />,
    label: '知识库管理',
    children: [
      {
        key: '/knowledge/bases',
        label: '知识库列表',
      },
      {
        key: '/knowledge/documents',
        label: '文档管理',
      },
    ],
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: '文档中心',
  },
  {
    key: '/users',
    icon: <UserOutlined />,
    label: '用户管理',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
]

// 用户下拉菜单
const userMenuItems: MenuProps['items'] = [
  {
    key: 'profile',
    icon: <UserOutlined />,
    label: '个人资料',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '账户设置',
  },
  {
    type: 'divider',
  },
  {
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
    danger: true,
  },
]

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useSimpleAuthStore()

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        navigate('/profile')
        break
      case 'settings':
        navigate('/account/settings')
        break
      case 'logout':
        logout()
        navigate('/login')
        break
      default:
        break
    }
  }

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    const pathname = location.pathname
    // 处理子菜单的选中状态
    if (pathname.startsWith('/knowledge/')) {
      return [pathname]
    }
    return [pathname]
  }

  // 获取当前展开的菜单项
  const getOpenKeys = () => {
    const pathname = location.pathname
    if (pathname.startsWith('/knowledge/')) {
      return ['/knowledge']
    }
    return []
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        collapsedWidth={80}
        style={{
          background: '#ffffff',
          borderRight: '1px solid #f0f0f0',
          boxShadow: '2px 0 8px 0 rgba(29, 35, 41, 0.05)',
        }}
      >
        {/* Logo 区域 */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 24px',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          {collapsed ? (
            <div
              style={{
                width: 32,
                height: 32,
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: 16,
              }}
            >
              R
            </div>
          ) : (
            <Space>
              <div
                style={{
                  width: 32,
                  height: 32,
                  background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: 16,
                }}
              >
                R
              </div>
              <Text strong style={{ fontSize: 18, color: '#1e293b' }}>
                RAG 系统
              </Text>
            </Space>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          mode='inline'
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            border: 'none',
            background: 'transparent',
          }}
        />
      </Sider>

      {/* 主内容区域 */}
      <Layout>
        {/* 顶部导航栏 */}
        <Header
          style={{
            padding: '0 24px',
            background: '#ffffff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          {/* 左侧：折叠按钮 */}
          <Button
            type='text'
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: 16,
              width: 40,
              height: 40,
            }}
          />

          {/* 右侧：搜索、通知、用户信息 */}
          <Space size='middle'>
            {/* 搜索按钮 */}
            <Button
              type='text'
              icon={<SearchOutlined />}
              style={{
                fontSize: 16,
                width: 40,
                height: 40,
              }}
            />

            {/* 通知按钮 */}
            <Badge count={5} size='small'>
              <Button
                type='text'
                icon={<BellOutlined />}
                style={{
                  fontSize: 16,
                  width: 40,
                  height: 40,
                }}
              />
            </Badge>

            {/* 用户下拉菜单 */}
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement='bottomRight'
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size='default'
                  src={user?.avatar_url}
                  icon={<UserOutlined />}
                  style={{
                    background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                  }}
                />
                <Text strong>{user?.full_name || user?.username || '用户'}</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            margin: 0,
            padding: 0,
            background: '#f8fafc',
            overflow: 'auto',
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
