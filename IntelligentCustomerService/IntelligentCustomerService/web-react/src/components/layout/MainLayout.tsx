import React, {useEffect, useState} from 'react'
import {Avatar, Badge, Button, Drawer, Dropdown, Layout, Menu, Space} from 'antd'
import {
    BellOutlined,
    FullscreenExitOutlined,
    FullscreenOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    MoonOutlined,
    SettingOutlined,
    SunOutlined,
    UserOutlined,
} from '@ant-design/icons'
import {Outlet, useLocation, useNavigate} from 'react-router-dom'
import {useAppStore} from '../../store/app'
import {useAuthStore} from '../../store/auth'
import {usePermissionStore} from '../../store/permission'
import {useTagsStore} from '../../store/tags'
import {cn} from '../../utils'
import TagsView from '@/components/layout/TagsView'
import Breadcrumb from '@/components/layout/Breadcrumb'

const { Header, Sider, Content } = Layout

interface MainLayoutProps {
  children?: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobile, setIsMobile] = useState(false)

  const {
    collapsed,
    theme,
    fullscreen,
    setCollapsed,
    toggleTheme,
    toggleFullscreen,
  } = useAppStore()

  const { user, logout } = useAuthStore()
  const { menus } = usePermissionStore()
  const { addTag } = useTagsStore()

  // 检测移动端
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 监听路由变化，添加标签
  useEffect(() => {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    if (pathSegments.length > 0) {
      const title = getPageTitle(location.pathname)
      addTag({
        name: title,
        title,
        path: location.pathname,
        closable: location.pathname !== '/dashboard',
      })
    }
  }, [location.pathname, addTag])

  // 获取页面标题
  const getPageTitle = (path: string): string => {
    const titleMap: Record<string, string> = {
      '/dashboard': '工作台',
      '/profile': '个人资料',
      '/system/users': '用户管理',
      '/system/roles': '角色管理',
      '/system/menus': '菜单管理',
      '/system/departments': '部门管理',
      '/system/apis': 'API管理',
      '/system/audit-logs': '审计日志',
    }
    return titleMap[path] || '未知页面'
  }

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
        navigate('/settings')
        break
      case 'logout':
        logout()
        navigate('/login')
        break
    }
  }

  // 切换侧边栏
  const toggleSidebar = () => {
    setCollapsed(!collapsed)
  }

  // 全屏切换
  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
    toggleFullscreen()
  }

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  // 转换菜单数据
  const convertMenus = (menuList: any[]): any[] => {
    return menuList.map(menu => ({
      key: menu.path,
      icon: menu.icon ? React.createElement(menu.icon) : null,
      label: menu.title,
      children: menu.children ? convertMenus(menu.children) : undefined,
    }))
  }

  const menuItems = convertMenus(menus)

  return (
    <Layout className="min-h-screen">
      {/* 侧边栏 */}
      {isMobile ? (
        <Drawer
          title="智能客服系统"
          placement="left"
          onClose={() => setCollapsed(true)}
          open={!collapsed}
          bodyStyle={{ padding: 0 }}
          width={256}
        >
          <Menu
            theme={theme}
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Drawer>
      ) : (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          theme={theme}
          width={256}
          className="shadow-md"
        >
          <div className="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
            <h1 className={cn(
              "font-bold text-lg transition-all duration-300",
              collapsed ? "text-xs" : "text-lg",
              theme === 'dark' ? "text-white" : "text-gray-800"
            )}>
              {collapsed ? "智客" : "智能客服系统"}
            </h1>
          </div>
          <Menu
            theme={theme}
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            className="border-r-0"
          />
        </Sider>
      )}

      <Layout>
        {/* 头部 */}
        <Header className={cn(
          "px-4 flex items-center justify-between shadow-sm",
          theme === 'dark' ? "bg-gray-800" : "bg-white"
        )}>
          <div className="flex items-center">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
              className="mr-4"
            />
            <Breadcrumb />
          </div>

          <Space size="middle">
            {/* 主题切换 */}
            <Button
              type="text"
              icon={theme === 'dark' ? <SunOutlined /> : <MoonOutlined />}
              onClick={toggleTheme}
            />

            {/* 全屏切换 */}
            <Button
              type="text"
              icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={handleFullscreen}
            />

            {/* 通知 */}
            <Badge count={5} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => {/* TODO: 实现通知功能 */}}
              />
            </Badge>

            {/* 用户信息 */}
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <Space className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 rounded">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  src={user?.avatar}
                />
                <span className={cn(
                  "text-sm",
                  theme === 'dark' ? "text-white" : "text-gray-700"
                )}>
                  {user?.username || '用户'}
                </span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 标签页 */}
        <TagsView />

        {/* 内容区域 */}
        <Content className={cn(
          "m-4 p-6 rounded-lg shadow-sm min-h-[calc(100vh-200px)]",
          theme === 'dark' ? "bg-gray-800" : "bg-white"
        )}>
          {children || <Outlet />}
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout