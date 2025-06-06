import React from 'react';
import {RouterProvider} from 'react-router-dom';
import {App as AntdApp, ConfigProvider} from 'antd';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {ReactQueryDevtools} from '@tanstack/react-query-devtools';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import {router} from './router';
import {AuthProvider} from './contexts/AuthContext';
import {ThemeProvider, useTheme} from './contexts/ThemeContext';
import {useTranslation} from 'react-i18next';
import './i18n';
import './App.css';

// 配置 dayjs
dayjs.locale('zh-cn');

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
});

// Ant Design 主题配置
const getAntdTheme = (isDark: boolean) => ({
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  algorithm: isDark ? undefined : undefined, // 这里可以根据需要配置暗色主题
  components: {
    Layout: {
      headerBg: isDark ? '#001529' : '#ffffff',
      siderBg: isDark ? '#001529' : '#ffffff',
      bodyBg: isDark ? '#141414' : '#f0f2f5',
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#000c17',
      darkItemSelectedBg: '#1890ff',
    },
  },
});

// 内部应用组件
const InnerApp: React.FC = () => {
  const { i18n } = useTranslation();
  const { isDark } = useTheme();
  
  // 根据语言设置 Ant Design 国际化
  const antdLocale = i18n.language === 'en' ? enUS : zhCN;
  
  // 根据语言设置 dayjs 国际化
  React.useEffect(() => {
    dayjs.locale(i18n.language === 'en' ? 'en' : 'zh-cn');
  }, [i18n.language]);

  return (
    <ConfigProvider
      locale={antdLocale}
      theme={getAntdTheme(isDark)}
      componentSize="middle"
    >
      <AntdApp>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </AntdApp>
    </ConfigProvider>
  );
};

// 应用主组件
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <InnerApp />
      </ThemeProvider>
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export default App;