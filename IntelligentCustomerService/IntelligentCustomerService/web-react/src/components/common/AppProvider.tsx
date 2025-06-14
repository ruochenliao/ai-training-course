import React from 'react'
import { App, ConfigProvider } from 'antd'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../../contexts/ThemeContext'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'

interface AppProviderProps {
  children: React.ReactNode
}

/**
 * 应用程序提供者组件
 * 对应Vue版本的AppProvider.vue
 * 提供全局配置和主题设置
 */
const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const { i18n } = useTranslation()
  const { theme, isDark } = useTheme()

  // 根据当前语言选择Ant Design的语言包
  const locale = i18n.language === 'zh-CN' ? zhCN : enUS

  // Ant Design主题配置
  const antdTheme = {
    token: {
      colorPrimary: theme.primaryColor,
      colorSuccess: theme.successColor,
      colorWarning: theme.warningColor,
      colorError: theme.errorColor,
      colorInfo: theme.infoColor,
      borderRadius: 6,
      wireframe: false,
    },
    algorithm: isDark ? [ConfigProvider.theme?.darkAlgorithm] : [ConfigProvider.theme?.defaultAlgorithm],
    components: {
      Layout: {
        bodyBg: isDark ? '#141414' : '#f5f5f5',
        headerBg: isDark ? '#1f1f1f' : '#ffffff',
        siderBg: isDark ? '#1f1f1f' : '#ffffff',
      },
      Menu: {
        itemBg: 'transparent',
        subMenuItemBg: 'transparent',
        itemSelectedBg: theme.primaryColor + '15',
        itemHoverBg: theme.primaryColor + '08',
      },
      Card: {
        colorBgContainer: isDark ? '#1f1f1f' : '#ffffff',
      },
      Table: {
        headerBg: isDark ? '#262626' : '#fafafa',
        rowHoverBg: isDark ? '#262626' : '#f5f5f5',
      },
      Modal: {
        contentBg: isDark ? '#1f1f1f' : '#ffffff',
        headerBg: isDark ? '#1f1f1f' : '#ffffff',
      },
    },
  }

  return (
    <ConfigProvider locale={locale} theme={antdTheme}>
      <App>{children}</App>
    </ConfigProvider>
  )
}

export default AppProvider
