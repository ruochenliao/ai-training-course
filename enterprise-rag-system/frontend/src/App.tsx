import React, { useEffect } from 'react'
import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter, useLocation } from 'react-router-dom'

// 导入样式
import '@/assets/css/reset.css'
import '@/assets/css/global.css'

// 导入组件
import AppLayout from '@/components/Layout/AppLayout'
import AppRoutes from '@/components/Routes/AppRoutes'
import ErrorBoundary from '@/components/ErrorBoundary/ErrorBoundary'

// 导入消息服务
import { messageService } from '@/services/messageService'

// Ant Design 主题配置
const antdTheme = {
  token: {
    colorPrimary: '#0ea5e9',
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    borderRadius: 8,
    fontFamily: '"Inter", "Google Sans", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
    fontSize: 14,
    lineHeight: 1.6,
    wireframe: false,
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#ffffff',
      bodyBg: '#f8fafc',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#e0f2fe',
      itemSelectedColor: '#0ea5e9',
      itemHoverBg: '#f0f9ff',
      itemHoverColor: '#0ea5e9',
    },
    Button: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Card: {
      borderRadius: 12,
      boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    },
  },
}

// 内容组件，根据路由决定是否显示布局
const AppContent: React.FC = () => {
  const location = useLocation()
  const isLoginPage = location.pathname === '/login'
  const { message } = AntdApp.useApp()

  // 初始化消息服务
  useEffect(() => {
    messageService.setMessageApi(message)
  }, [message])

  if (isLoginPage) {
    return (
      <ErrorBoundary>
        <AppRoutes />
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <AppLayout>
        <AppRoutes />
      </AppLayout>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={antdTheme} componentSize='middle'>
      <AntdApp>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <AppContent />
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  )
}

export default App
