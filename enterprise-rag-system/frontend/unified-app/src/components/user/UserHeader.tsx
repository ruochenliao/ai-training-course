'use client';

import {useState} from 'react';
import {usePathname} from 'next/navigation';
import {Badge, Breadcrumb, Button, Dropdown, Input, Layout, Typography} from 'antd';
import {BellOutlined, QuestionCircleOutlined, SearchOutlined, SettingOutlined,} from '@ant-design/icons';
import {motion} from 'framer-motion';
import {useAuth} from '@/contexts/AuthContext';

const { Header } = Layout;
const { Search } = Input;
const { Text } = Typography;

export default function UserHeader() {
  const [searchValue, setSearchValue] = useState('');
  const { user } = useAuth();
  const pathname = usePathname();

  // 根据路径生成面包屑
  const getBreadcrumbItems = () => {
    const pathMap: Record<string, string> = {
      '/chat': '智能问答',
      '/search': '知识搜索',
      '/knowledge': '知识库',
      '/history': '对话历史',
      '/profile': '个人资料',
      '/settings': '设置',
      '/admin': '管理后台',
    };

    const items = [
      {
        title: '首页',
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
      '/chat': '智能问答',
      '/search': '知识搜索',
      '/knowledge': '知识库管理',
      '/history': '对话历史',
      '/profile': '个人资料',
      '/settings': '系统设置',
      '/admin': '管理后台',
    };

    return titleMap[pathname] || '企业级RAG知识库系统';
  };

  const handleSearch = (value: string) => {
    if (value.trim()) {
      // 执行搜索逻辑
      console.log('搜索:', value);
    }
  };

  const notificationItems = [
    {
      key: '1',
      label: (
        <div className="p-2">
          <div className="font-medium">系统通知</div>
          <div className="text-sm text-gray-500">您有新的消息</div>
          <div className="text-xs text-gray-400 mt-1">2分钟前</div>
        </div>
      ),
    },
    {
      key: '2',
      label: (
        <div className="p-2">
          <div className="font-medium">知识库更新</div>
          <div className="text-sm text-gray-500">技术文档已更新</div>
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

  const helpItems = [
    {
      key: 'guide',
      label: '使用指南',
    },
    {
      key: 'faq',
      label: '常见问题',
    },
    {
      key: 'contact',
      label: '联系支持',
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
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white m-0 truncate">
            {getPageTitle()}
          </h1>
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
            placeholder="搜索知识库..."
            allowClear
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 280 }}
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

        {/* 通知 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Dropdown
            menu={{ items: notificationItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Badge count={2} size="small">
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
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Dropdown
            menu={{ items: helpItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Button
              type="text"
              icon={<QuestionCircleOutlined />}
              className="flex items-center justify-center"
            />
          </Dropdown>
        </motion.div>

        {/* 设置 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.5 }}
          className="hidden lg:block"
        >
          <Button
            type="text"
            icon={<SettingOutlined />}
            className="flex items-center justify-center"
          />
        </motion.div>

        {/* 用户信息 */}
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
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {user?.is_superuser ? '管理员' : '用户'}
            </div>
          </div>
        </motion.div>
      </div>
    </Header>
  );
}
