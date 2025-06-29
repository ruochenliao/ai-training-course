import React, {useEffect} from 'react'
import {Layout} from 'antd'
import {Outlet, useLocation} from 'react-router-dom'
import {useResponsive} from 'ahooks'
import {useAppStore} from '@/store/app.ts'
import {useTagsStore} from '@/store/tags.ts'
import SideBar from './Sidebar.tsx'
import AppHeader from './Header.tsx'
import AppTags from './TagsView.tsx'
import AppMain from './AppMain.tsx'
import {layoutSettings} from '@/settings'

const { Sider, Content } = Layout

interface MainLayoutProps {
  children?: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation()
  const { collapsed, setCollapsed, setFullScreen } = useAppStore()
  const { addTag } = useTagsStore()

  // 响应式断点配置
  const responsive = useResponsive({
    xl: 1600,
    lg: 1199,
    md: 991,
    sm: 666,
    xs: 575,
  })

  // 响应式处理
  useEffect(() => {
    if (!responsive.sm) {
      // Mobile
      setCollapsed(true)
      setFullScreen(false)
    } else if (responsive.sm && !responsive.md) {
      // iPad
      setCollapsed(true)
      setFullScreen(false)
    } else if (responsive.md) {
      // PC
      setCollapsed(false)
      setFullScreen(true)
    }
  }, [responsive, setCollapsed, setFullScreen])

  // 监听路由变化，添加标签
  useEffect(() => {
    const { pathname } = location
    const title = getPageTitle(pathname)
    if (title) {
      addTag({
        name: pathname,
        path: pathname,
        title,
        closable: pathname !== '/dashboard',
      })
    }
  }, [location.pathname, addTag])

  // 获取页面标题
  const getPageTitle = (path: string): string => {
    const titleMap: Record<string, string> = {
      '/dashboard': '工作台',
      '/workbench': '工作台',
      '/profile': '个人资料',
      '/system/user': '用户管理',
      '/system/role': '角色管理',
      '/system/menu': '菜单管理',
      '/system/dept': '部门管理',
      '/system/api': 'API管理',
      '/system/auditlog': '审计日志',
    }
    return titleMap[path] || ''
  }

  return (
    <Layout className='h-screen w-full enterprise-layout'>
      {/* 企业级侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        collapsedWidth={64}
        width={240}
        className='enterprise-sidebar'
        style={{
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: '#ffffff',
          borderRight: '1px solid #f0f0f0',
          boxShadow: '2px 0 8px 0 rgba(29, 35, 41, 0.05)',
          zIndex: 100,
        }}
      >
        <SideBar />
      </Sider>

      {/* 主内容区域 */}
      <Layout
        className='enterprise-main-layout'
        style={{
          marginLeft: collapsed ? '64px' : '240px',
          transition: 'margin-left 0.2s ease-in-out',
        }}
      >
        {/* 企业级顶部导航栏 */}
        <div
          className='enterprise-header'
          style={{
            height: `${layoutSettings.header.height}px`,
            background: '#ffffff',
            borderBottom: '1px solid #f0f0f0',
            boxShadow: '0 2px 8px 0 rgba(29, 35, 41, 0.05)',
            position: 'fixed',
            top: 0,
            right: 0,
            left: collapsed ? '64px' : '240px',
            zIndex: 99,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'left 0.2s ease-in-out',
          }}
        >
          <AppHeader />
        </div>

        {/* 主体内容区 */}
        <Content
          className='enterprise-content'
          style={{
            marginTop: `${layoutSettings.header.height}px`,
            minHeight: `calc(100vh - ${layoutSettings.header.height}px)`,
            background: '#f0f2f5',
          }}
        >
          {/* 标签页（可选） */}
          {layoutSettings.tags.visible && (
            <div
              className='enterprise-tags'
              style={{
                height: `${layoutSettings.tags.height}px`,
                background: '#ffffff',
                borderBottom: '1px solid #f0f0f0',
                padding: '0 24px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <AppTags />
            </div>
          )}

          {/* 主内容容器 */}
          <div
            className='enterprise-page-container'
            style={{
              padding: '24px',
              minHeight: layoutSettings.tags.visible
                ? `calc(100vh - ${layoutSettings.header.height}px - ${layoutSettings.tags.height}px)`
                : `calc(100vh - ${layoutSettings.header.height}px)`,
            }}
          >
            <AppMain>{children || <Outlet />}</AppMain>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
