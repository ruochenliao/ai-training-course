'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Layout, Breadcrumb, Input, Badge, Button, Dropdown, Space, Typography, Statistic } from 'antd';
import {
  SearchOutlined,
  BellOutlined,
  ReloadOutlined,
  DownloadOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';

const { Header } = Layout;
const { Search } = Input;
const { Text } = Typography;

export default function AdminHeader() {
  const [searchValue, setSearchValue] = useState('');
  const { user } = useAuth();
  const pathname = usePathname();

  // 根据路径生成面包屑
  const getBreadcrumbItems = () => {
    const pathMap: Record<string, string> = {
      '/admin/dashboard': '仪表板',
      '/admin/users': '用户管理',
      '/admin/knowledge-bases': '知识库管理',
      '/admin/documents': '文档管理',
      '/admin/conversations': '对话管理',
      '/admin/analytics': '数据分析',
      '/admin/system': '系统监控',
      '/admin/settings': '系统设置',
    };

    const items = [
      {
        title: '管理后台',
      },
    ];

    if (pathMap[pathname]) {
      items.push({
        title: pathMap[pathname],
      });
    }

    return items;
  };

  // 获取页面标题
  const getPageTitle = () => {
    const titleMap: Record<string, string> = {
      '/admin/dashboard': '系统仪表板',
      '/admin/users': '用户管理',
      '/admin/knowledge-bases': '知识库管理',
      '/admin/documents': '文档管理',
      '/admin/conversations': '对话管理',
      '/admin/analytics': '数据分析',
      '/admin/system': '系统监控',
      '/admin/settings': '系统设置',
    };

    return titleMap[pathname] || '管理后台';
  };

  const handleSearch = (value: string) => {
    if (value.trim()) {
      console.log('管理端搜索:', value);
    }
  };

  const notificationItems = [
    {
      key: '1',
      label: (
        <div className="p-2">
          <div className="font-medium text-red-600">系统警告</div>
          <div className="text-sm text-gray-500">磁盘空间不足</div>
          <div className="text-xs text-gray-400 mt-1">5分钟前</div>
        </div>
      ),
    },
    {
      key: '2',
      label: (
        <div className="p-2">
          <div className="font-medium text-blue-600">新用户注册</div>
          <div className="text-sm text-gray-500">3个新用户注册</div>
          <div className="text-xs text-gray-400 mt-1">10分钟前</div>
        </div>
      ),
    },
    {
      key: '3',
      label: (
        <div className="p-2">
          <div className="font-medium text-green-600">备份完成</div>
          <div className="text-sm text-gray-500">数据库备份成功</div>
          <div className="text-xs text-gray-400 mt-1">1小时前</div>
        </div>
      ),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'all',
      label: (
        <div className="text-center p-2">
          <Button type="link" size="small">
            查看全部通知
          </Button>
        </div>
      ),
    },
  ];

  const actionItems = [
    {
      key: 'refresh',
      label: '刷新数据',
      icon: <ReloadOutlined />,
    },
    {
      key: 'export',
      label: '导出报告',
      icon: <DownloadOutlined />,
    },
    {
      key: 'settings',
      label: '页面设置',
      icon: <SettingOutlined />,
    },
  ];

  return (
    <Header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-0 h-16 flex items-center justify-between shadow-sm">
      {/* 左侧：面包屑和标题 */}
      <div className="flex-1 min-w-0">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Breadcrumb
            items={getBreadcrumbItems()}
            className="mb-1 text-sm"
          />
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white m-0 truncate">
              {getPageTitle()}
            </h1>
            
            {/* 实时状态指示器 */}
            <div className="hidden lg:flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <Text type="secondary" className="text-xs">
                  系统正常
                </Text>
              </div>
              
              <div className="flex items-center space-x-4 text-xs">
                <Statistic
                  title=""
                  value={24}
                  suffix="在线"
                  valueStyle={{ fontSize: '12px', color: '#52c41a' }}
                />
                <Statistic
                  title=""
                  value={1.2}
                  suffix="GB"
                  prefix="内存:"
                  valueStyle={{ fontSize: '12px', color: '#1890ff' }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* 右侧：搜索和操作按钮 */}
      <div className="flex items-center space-x-4 ml-4">
        {/* 全局搜索 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="hidden md:block"
        >
          <Search
            placeholder="搜索用户、文档、设置..."
            allowClear
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 300 }}
            className="rounded-lg"
          />
        </motion.div>

        {/* 移动端搜索按钮 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="md:hidden"
        >
          <Button
            type="text"
            icon={<SearchOutlined />}
            className="flex items-center justify-center"
          />
        </motion.div>

        {/* 快捷操作 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.3 }}
          className="hidden lg:block"
        >
          <Dropdown
            menu={{ items: actionItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Button
              type="text"
              icon={<SettingOutlined />}
              className="flex items-center justify-center"
            />
          </Dropdown>
        </motion.div>

        {/* 通知 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Dropdown
            menu={{ items: notificationItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Badge count={5} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                className="flex items-center justify-center"
              />
            </Badge>
          </Dropdown>
        </motion.div>

        {/* 帮助 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.5 }}
        >
          <Button
            type="text"
            icon={<QuestionCircleOutlined />}
            className="flex items-center justify-center"
          />
        </motion.div>

        {/* 管理员信息 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.6 }}
          className="hidden sm:flex items-center space-x-2 pl-4 border-l border-gray-200 dark:border-gray-700"
        >
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {user?.full_name || user?.username}
            </div>
            <div className="text-xs text-purple-600 dark:text-purple-400">
              系统管理员
            </div>
          </div>
        </motion.div>
      </div>
    </Header>
  );
}
