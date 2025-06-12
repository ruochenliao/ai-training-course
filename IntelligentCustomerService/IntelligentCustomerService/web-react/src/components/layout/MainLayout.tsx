import React, { useEffect } from 'react'
import { Layout } from 'antd'
import { Outlet, useLocation } from 'react-router-dom'
import { useResponsive } from 'ahooks'
import { useAppStore } from '../../store/app'
import { useTagsStore } from '../../store/tags'
import SideBar from './Sidebar'
import AppHeader from './Header'
import AppTags from './TagsView'
import AppMain from './AppMain'
import { layoutSettings } from '../../settings'

const { Sider } = Layout

interface MainLayoutProps {
  children?: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation()
  const { collapsed, setCollapsed, setFullScreen } = useAppStore()
  const { addTag } = useTagsStore()

  // 响应式断点配置 - 对应Vue版本的useBreakpoints
  const responsive = useResponsive({
    xl: 1600,
    lg: 1199,
    md: 991,
    sm: 666,
    xs: 575,
  })

  // 响应式处理 - 对应Vue版本的watchEffect
  useEffect(() => {
    if (!responsive.sm) {
      // Mobile - 对应Vue版本的isMobile.value
      setCollapsed(true)
      setFullScreen(false)
    } else if (responsive.sm && !responsive.md) {
      // iPad - 对应Vue版本的isPad.value
      setCollapsed(true)
      setFullScreen(false)
    } else if (responsive.md) {
      // PC - 对应Vue版本的isPC.value
      setCollapsed(false)
      setFullScreen(true)
    }
  }, [responsive, setCollapsed, setFullScreen])

  // 监听路由变化，添加标签 - 对应Vue版本的watch(() => route.path)
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

  // 获取页面标题 - 对应Vue版本的route.meta?.title
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
    return titleMap[path] || ''
  }

  return (
    <Layout className="wh-full">
      {/* 左侧边栏 - 对应Vue版本的n-layout-sider */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        collapsedWidth={64}
        width={220}
        className="border-r border-gray-200 dark:border-gray-700"
      >
        <SideBar />
      </Sider>

      {/* 右侧主内容区域 - 对应Vue版本的article */}
      <Layout className="flex-col flex-1 overflow-hidden">
        {/* 顶部导航栏 - 对应Vue版本的header */}
        <div
          className="flex items-center border-b bg-white px-15 bc-eee dark:bg-dark dark:border-0"
          style={{ height: `${layoutSettings.header.height}px` }}
        >
          <AppHeader />
        </div>

        {/* 标签页（可选） - 对应Vue版本的section v-if="tags.visible" */}
        {layoutSettings.tags.visible && (
          <div
            className="border-b bc-eee dark:border-0"
            style={{ height: `${layoutSettings.tags.height}px` }}
          >
            <AppTags />
          </div>
        )}

        {/* 主体内容区域 - 对应Vue版本的section */}
        <div className="flex-1 overflow-hidden bg-hex-f5f6fb dark:bg-hex-101014">
          <AppMain>
            {children || <Outlet />}
          </AppMain>
        </div>
      </Layout>
    </Layout>
  )
}

export default MainLayout