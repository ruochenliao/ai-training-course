import React from 'react';
import {RouterProvider} from 'react-router-dom';
import {App as AntdApp, ConfigProvider, theme} from 'antd';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {ReactQueryDevtools} from '@tanstack/react-query-devtools';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import {router} from './router';
import {AuthProvider} from './contexts/AuthContext';
import {ThemeProvider} from './contexts/ThemeContext';
import {useTranslation} from 'react-i18next';
import './i18n';
import './styles/global.css';

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

// 内部应用组件
const InnerApp: React.FC = () => {
  const { i18n } = useTranslation();
  
  // 根据语言设置 dayjs 国际化
  React.useEffect(() => {
    dayjs.locale(i18n.language === 'en' ? 'en' : 'zh-cn');
  }, [i18n.language]);

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#2080f0',
          colorSuccess: '#18a058',
          colorWarning: '#f0a020',
          colorError: '#d03050',
          colorInfo: '#2080f0',
          borderRadius: 4,
        },
        algorithm: theme.defaultAlgorithm,
      }}
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
      {import.meta.env.DEV && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

export default App;