'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  MessageOutlined,
  SearchOutlined,
  BookOutlined,
  HistoryOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CrownOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/components/common/ThemeToggle';

const { Sider } = Layout;
const { Text } = Typography;

export default function UserSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '智能问答',
    },
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: '知识搜索',
    },
    {
      key: '/knowledge',
      icon: <BookOutlined />,
      label: '知识库',
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: '对话历史',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => router.push('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => router.push('/settings'),
    },
    ...(user?.is_superuser ? [{
      key: 'admin',
      icon: <CrownOutlined />,
      label: '管理后台',
      onClick: () => router.push('/admin'),
    }] : []),
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    router.push(key);
  };

  const sidebarVariants = {
    expanded: {
      width: 256,
      transition: { duration: 0.3, ease: "easeInOut" }
    },
    collapsed: {
      width: 80,
      transition: { duration: 0.3, ease: "easeInOut" }
    }
  };

  return (
    <motion.div
      variants={sidebarVariants}
      animate={collapsed ? "collapsed" : "expanded"}
      className="fixed left-0 top-0 h-full z-50 lg:relative lg:z-auto"
    >
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={256}
        collapsedWidth={80}
        className="h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-lg lg:shadow-none"
      >
        <div className="flex flex-col h-full">
          {/* Logo 和折叠按钮 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <AnimatePresence mode="wait">
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex items-center space-x-3"
                >
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">R</span>
                  </div>
                  <div>
                    <Text strong className="text-sm">RAG系统</Text>
                    <div className="text-xs text-gray-500">智能知识库</div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="flex items-center justify-center"
            />
          </div>

          {/* 新建对话按钮 */}
          <div className="p-4">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                block={!collapsed}
                size="large"
                onClick={() => router.push('/chat/new')}
                className="bg-gradient-to-r from-blue-500 to-purple-600 border-0 rounded-lg shadow-md hover:shadow-lg transition-all duration-300"
              >
                {!collapsed && '新建对话'}
              </Button>
            </motion.div>
          </div>

          {/* 主菜单 */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <Menu
              mode="inline"
              selectedKeys={[pathname]}
              items={menuItems}
              onClick={handleMenuClick}
              className="border-none bg-transparent"
              inlineIndent={collapsed ? 0 : 24}
            />
          </div>

          {/* 用户信息 */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-3">
              <ThemeToggle />
              {!collapsed && (
                <Dropdown
                  menu={{ items: userMenuItems }}
                  placement="topRight"
                  trigger={['click']}
                >
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="flex items-center space-x-3 cursor-pointer p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Avatar
                      size="small"
                      src={user?.avatar_url}
                      icon={<UserOutlined />}
                      className="bg-gradient-to-r from-blue-500 to-purple-600"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {user?.full_name || user?.username}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {user?.email}
                      </div>
                    </div>
                  </motion.div>
                </Dropdown>
              )}
            </div>
            
            {collapsed && (
              <div className="flex justify-center">
                <Dropdown
                  menu={{ items: userMenuItems }}
                  placement="topRight"
                  trigger={['click']}
                >
                  <motion.div whileHover={{ scale: 1.1 }}>
                    <Avatar
                      src={user?.avatar_url}
                      icon={<UserOutlined />}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 cursor-pointer"
                    />
                  </motion.div>
                </Dropdown>
              </div>
            )}
          </div>
        </div>
      </Sider>
    </motion.div>
  );
}
