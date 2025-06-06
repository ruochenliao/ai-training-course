import React from 'react'
import {Layout as AntdLayout} from 'antd'
import {useThemeStore} from '@/store/theme'
import Header from './Header'
import Sidebar from './Sidebar'
import {Outlet} from 'react-router-dom'
import './Layout.css'

const { Content } = AntdLayout

const Layout: React.FC = () => {
  const { sidebarCollapsed } = useThemeStore()

  return (
    <AntdLayout className="min-h-screen">
      <Sidebar />
      <AntdLayout className={`transition-all duration-300 ${
        sidebarCollapsed ? 'ml-16' : 'ml-55'
      }`}>
        <Header />
        <Content className="p-4 bg-gray-50">
          <div className="bg-white rounded-sm">
            <Outlet />
          </div>
        </Content>
      </AntdLayout>
    </AntdLayout>
  )
}

export default Layout