import React from 'react'
import { Layout as AntdLayout } from 'antd'
import { useThemeStore } from '@/store/theme'
import Header from './Header'
import Sidebar from './Sidebar'
import './Layout.css'

const { Content } = AntdLayout

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { sidebarCollapsed } = useThemeStore()

  return (
    <AntdLayout className="min-h-screen">
      <Sidebar />
      <AntdLayout className={`transition-all duration-300 ${
        sidebarCollapsed ? 'ml-20' : 'ml-64'
      }`}>
        <Header />
        <Content className="p-6 bg-gray-50">
          <div className="min-h-full bg-white rounded-lg shadow-sm p-6">
            {children}
          </div>
        </Content>
      </AntdLayout>
    </AntdLayout>
  )
}

export default Layout