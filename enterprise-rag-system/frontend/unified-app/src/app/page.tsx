'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Spin } from 'antd';
import { motion } from 'framer-motion';

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        // 已登录用户重定向到聊天界面
        router.push('/chat');
      } else {
        // 未登录用户重定向到登录页面
        router.push('/login');
      }
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <div className="mb-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-16 h-16 mx-auto mb-4"
            >
              <Spin size="large" />
            </motion.div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
              企业级RAG知识库系统
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              正在初始化系统...
            </p>
          </div>
          
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: "100%" }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            className="h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
          />
        </motion.div>
      </div>
    );
  }

  return null;
}
