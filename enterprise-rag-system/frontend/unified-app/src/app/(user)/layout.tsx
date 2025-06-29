'use client';

import {useEffect} from 'react';
import {useRouter} from 'next/navigation';
import {Layout} from 'antd';
import {useAuth} from '@/contexts/AuthContext';
import UserSidebar from '@/components/user/UserSidebar';
import UserHeader from '@/components/user/UserHeader';
import {motion} from 'framer-motion';

const { Content } = Layout;

export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

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

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <UserSidebar />
      <Layout className="ml-0 lg:ml-64 transition-all duration-300">
        <UserHeader />
        <Content className="flex-1 overflow-hidden">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </Content>
      </Layout>
    </Layout>
  );
}
