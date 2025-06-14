import React from 'react'
import { RouterProvider } from 'react-router-dom'
import { App as AntdApp, ConfigProvider, theme } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/en'
import { router } from './router'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { useTranslation } from 'react-i18next'
import './i18n'
import './styles/global.css'

// 配置 dayjs
dayjs.locale('zh-cn')

// 创建 QueryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5分钟
      gcTime: 10 * 60 * 1000, // 10分钟
    },
    mutations: {
      retry: 1,
    },
  },
})

// 内部应用组件
const InnerApp: React.FC = () => {
  const { i18n } = useTranslation()

  // 根据语言设置 dayjs 国际化
  React.useEffect(() => {
    dayjs.locale(i18n.language === 'en' ? 'en' : 'zh-cn')
  }, [i18n.language])

  return (
    <ConfigProvider
      theme={{
        token: {
          // 企业级产品配色方案 - 参考vue-fastapi-admin
          colorPrimary: '#1890ff',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorInfo: '#1890ff',
          borderRadius: 6,
          // 优化字体和间距
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif',
          fontSize: 14,
          lineHeight: 1.5715,
          // 阴影优化
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          boxShadowSecondary: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
        algorithm: theme.defaultAlgorithm,
        components: {
          Layout: {
            bodyBg: '#f0f2f5',
            headerBg: '#ffffff',
            siderBg: '#ffffff',
            headerHeight: 64,
            headerPadding: '0 24px',
          },
          Menu: {
            itemBg: 'transparent',
            itemSelectedBg: '#e6f7ff',
            itemSelectedColor: '#1890ff',
            itemHoverBg: '#f5f5f5',
            itemHoverColor: '#1890ff',
            subMenuItemBg: 'transparent',
            itemBorderRadius: 6,
            itemMarginBlock: 4,
            itemMarginInline: 8,
            itemPaddingInline: 12,
          },
          Card: {
            borderRadiusLG: 8,
            paddingLG: 24,
          },
          Button: {
            borderRadius: 6,
            controlHeight: 36,
          },
        },
      }}
    >
      <AntdApp>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </AntdApp>
    </ConfigProvider>
  )
}

// 应用主组件
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <InnerApp />
      </ThemeProvider>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}

export default App
