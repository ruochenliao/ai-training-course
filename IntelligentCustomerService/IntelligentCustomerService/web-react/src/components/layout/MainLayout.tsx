import React, {useEffect, useState} from 'react'
import {Avatar, Badge, Button, Drawer, Dropdown, Layout, Menu, Tooltip} from 'antd'
import {
    BellOutlined,
    FullscreenExitOutlined,
    FullscreenOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    SettingOutlined,
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
import {useTheme} from '../../contexts/ThemeContext'
import ThemeSettings from '../ThemeSettings'

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
    fullscreen,
    setCollapsed,
    toggleFullscreen,
  } = useAppStore()

  const { isDark, primaryColor } = useTheme()
  const theme = isDark ? 'dark' : 'light'

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
          title={
            <div className="flex items-center gap-2">
              <div 
                className="w-6 h-6 rounded-full flex-center" 
                style={{ backgroundColor: primaryColor }}
              >
                <span className="text-white text-sm font-bold">智</span>
              </div>
              <span className={isDark ? "text-white" : "text-gray-800"}>智能客服系统</span>
            </div>
          }
          placement="left"
          onClose={() => setCollapsed(true)}
          open={!collapsed}
          bodyStyle={{ padding: 0 }}
          width={256}
        >
          <Menu
            theme={theme as "light" | "dark"}
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
          theme={theme as "light" | "dark"}
          width={256}
          className={cn(
            "shadow-md relative z-10",
            isDark ? "bg-gray-900" : "bg-white"
          )}
          style={{ 
            boxShadow: isDark ? '0 0 10px rgba(0,0,0,0.2)' : '0 0 10px rgba(0,0,0,0.05)',
            borderRight: isDark ? '1px solid #333' : '1px solid #f0f0f0'
          }}
        >
          <div className={cn(
            "h-16 flex items-center px-4 border-b transition-all duration-300",
            isDark ? "border-gray-700" : "border-gray-200"
          )}>
            <div className="flex items-center gap-3">
              <div 
                className="w-8 h-8 rounded-full flex-center"
                style={{ backgroundColor: primaryColor }}
              >
                <span className="text-white text-sm font-bold">智</span>
              </div>
              {!collapsed && (
                <h1 className={cn(
                  "font-bold transition-all duration-300 whitespace-nowrap",
                  isDark ? "text-white" : "text-gray-800"
                )}>
                  智能客服系统
                </h1>
              )}
            </div>
          </div>
          <Menu
            theme={theme as "light" | "dark"}
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            className={cn(
              "border-r-0",
              isDark ? "bg-gray-900" : "bg-white"
            )}
          />
        </Sider>
      )}

      <Layout>
        {/* 头部 */}
        <Header className={cn(
          "px-4 flex items-center justify-between h-16 z-10",
          isDark ? "bg-gray-900 border-b border-gray-700" : "bg-white border-b border-gray-200"
        )}
        style={{ 
          boxShadow: isDark ? '0 2px 4px rgba(0,0,0,0.1)' : '0 2px 4px rgba(0,0,0,0.03)',
          padding: '0 16px'
        }}
        >
          <div className="flex items-center">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
              className={cn(
                "mr-4 flex-center",
                isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
              )}
            />
            <Breadcrumb />
          </div>

          <div className="flex items-center gap-2">
            {/* 全屏切换 */}
            <Tooltip title={fullscreen ? '退出全屏' : '全屏'}>
              <Button
                type="text"
                icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                onClick={handleFullscreen}
                className={cn(
                  "flex-center",
                  isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
                )}
              />
            </Tooltip>

            {/* 通知 */}
            <Tooltip title="通知">
              <Badge count={5} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  onClick={() => {/* TODO: 实现通知功能 */}}
                  className={cn(
                    "flex-center",
                    isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
                  )}
                />
              </Badge>
            </Tooltip>

            {/* 主题设置 */}
            <ThemeSettings />

            {/* 用户信息 */}
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <div className={cn(
                "flex items-center gap-2 cursor-pointer py-1 px-2 rounded-md transition-colors", 
                isDark 
                  ? "hover:bg-gray-800" 
                  : "hover:bg-gray-100"
              )}>
                <Avatar
                  size={32}
                  icon={<UserOutlined />}
                  src={user?.avatar}
                  style={{ backgroundColor: primaryColor }}
                />
                <span className={cn(
                  "text-sm hidden md:inline",
                  isDark ? "text-gray-200" : "text-gray-700"
                )}>
                  {user?.username || '用户'}
                </span>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 标签页 */}
        <TagsView />

        {/* 内容区域 */}
        <Content 
          className={cn(
            "m-4 overflow-auto",
            isDark ? "bg-gray-900" : "bg-gray-50"
          )}
          style={{ 
            minHeight: 'calc(100vh - 112px)',
            padding: '16px'
          }}
        >
          <div className={cn(
            "rounded-lg h-full",
            isDark ? "bg-gray-800" : "bg-white"
          )}
          style={{ 
            boxShadow: isDark ? '0 0 10px rgba(0,0,0,0.1)' : '0 0 10px rgba(0,0,0,0.03)',
            padding: '16px'
          }}
          >
            {children || <Outlet />}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout