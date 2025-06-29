'use client';

import React from 'react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';

// 创建 QueryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分钟
      cacheTime: 10 * 60 * 1000, // 10 分钟
      retry: (failureCount, error: any) => {
        // 对于 401 错误不重试
        if (error?.response?.status === 401) {
          return false;
        }
        // 最多重试 2 次
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
