'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Layout, message } from 'antd';
import { useAuth } from '@/contexts/AuthContext';
import AdminSidebar from '@/components/admin/AdminSidebar';
import AdminHeader from '@/components/admin/AdminHeader';
import { motion } from 'framer-motion';

const { Content } = Layout;

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login');
        return;
      }
      
      if (!user?.is_superuser) {
        message.error('您没有访问管理后台的权限');
        router.push('/chat');
        return;
      }
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (!isAuthenticated || !user?.is_superuser) {
    return null;
  }

  return (
    <Layout className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <AdminSidebar />
      <Layout className="ml-0 lg:ml-64 transition-all duration-300">
        <AdminHeader />
        <Content className="flex-1 overflow-hidden">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full p-6"
          >
            {children}
          </motion.div>
        </Content>
      </Layout>
    </Layout>
  );
}
