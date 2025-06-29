'use client';

import {useState} from 'react';
import {usePathname, useRouter} from 'next/navigation';
import {Avatar, Badge, Button, Dropdown, Layout, Menu, Typography} from 'antd';
import {
    ApartmentOutlined,
    ArrowLeftOutlined,
    BarChartOutlined,
    BookOutlined,
    CrownOutlined,
    DashboardOutlined,
    FileTextOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    MessageOutlined,
    MonitorOutlined,
    SafetyOutlined,
    SettingOutlined,
    TeamOutlined,
    UserOutlined,
    UserSwitchOutlined,
} from '@ant-design/icons';
import {AnimatePresence, motion} from 'framer-motion';
import {useAuth} from '@/contexts/AuthContext';
import {usePermissions} from '@/contexts/PermissionContext';
import ThemeToggle from '@/components/common/ThemeToggle';

const { Sider } = Layout;
const { Text } = Typography;

export default function AdminSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const { hasPermission } = usePermissions();
  const router = useRouter();
  const pathname = usePathname();

  // 定义所有菜单项及其权限要求
  const allMenuItems = [
    {
      key: '/admin/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
      permission: null, // 所有管理员都可以访问
    },
    {
      key: 'rbac',
      icon: <SafetyOutlined />,
      label: '权限管理',
      permission: null, // 如果有子菜单权限则显示
      children: [
        {
          key: '/admin/rbac',
          icon: <DashboardOutlined />,
          label: '权限概览',
          permission: null, // 有任何RBAC权限都可以访问
        },
        {
          key: '/admin/rbac/users',
          icon: <UserOutlined />,
          label: '用户管理',
          permission: 'user:view',
        },
        {
          key: '/admin/rbac/roles',
          icon: <TeamOutlined />,
          label: '角色管理',
          permission: 'role:view',
        },
        {
          key: '/admin/rbac/permissions',
          icon: <SafetyOutlined />,
          label: '权限管理',
          permission: 'permission:view',
        },
        {
          key: '/admin/rbac/departments',
          icon: <ApartmentOutlined />,
          label: '部门管理',
          permission: 'dept:view',
        },
        {
          key: '/admin/rbac/user-roles',
          icon: <UserSwitchOutlined />,
          label: '用户角色分配',
          permission: 'user_role:manage',
        },
      ],
    },
    {
      key: '/admin/knowledge-bases',
      icon: <BookOutlined />,
      label: '知识库管理',
      permission: 'knowledge:view',
    },
    {
      key: '/admin/documents',
      icon: <FileTextOutlined />,
      label: '文档管理',
      permission: 'document:view',
    },
    {
      key: '/admin/conversations',
      icon: <MessageOutlined />,
      label: '对话管理',
      permission: 'chat:history',
    },
    {
      key: '/admin/analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
      permission: 'monitor:business',
    },
    {
      key: '/admin/monitoring',
      icon: <MonitorOutlined />,
      label: '系统监控',
      permission: 'monitor:system',
    },
    {
      key: '/admin/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      permission: 'system:config',
    },
  ];

  // 根据权限过滤菜单项
  const filterMenuItems = (items: any[]) => {
    return items.filter(item => {
      // 如果是超级用户，显示所有菜单
      if (user?.is_superuser) {
        if (item.children) {
          item.children = filterMenuItems(item.children);
        }
        return true;
      }

      // 检查权限
      if (item.permission && !hasPermission(item.permission)) {
        return false;
      }

      // 如果有子菜单，递归过滤
      if (item.children) {
        const filteredChildren = filterMenuItems(item.children);
        if (filteredChildren.length === 0) {
          return false; // 如果没有可访问的子菜单，隐藏父菜单
        }
        item.children = filteredChildren;
      }

      return true;
    });
  };

  const menuItems = filterMenuItems([...allMenuItems]);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => router.push('/profile'),
    },
    {
      key: 'back-to-user',
      icon: <ArrowLeftOutlined />,
      label: '返回用户端',
      onClick: () => router.push('/chat'),
    },
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
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                    <CrownOutlined className="text-white text-sm" />
                  </div>
                  <div>
                    <Text strong className="text-sm">管理后台</Text>
                    <div className="text-xs text-gray-500">系统管理</div>
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

          {/* 返回用户端按钮 */}
          <div className="p-4">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                icon={<ArrowLeftOutlined />}
                block={!collapsed}
                size="large"
                onClick={() => router.push('/chat')}
                className="rounded-lg border-dashed border-gray-300 dark:border-gray-600 hover:border-blue-500 hover:text-blue-500 transition-all duration-300"
              >
                {!collapsed && '返回用户端'}
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

          {/* 系统状态 */}
          {!collapsed && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-sm font-medium text-green-800 dark:text-green-400">
                    系统状态
                  </Text>
                  <Badge status="success" />
                </div>
                <div className="space-y-1 text-xs text-green-600 dark:text-green-400">
                  <div className="flex justify-between">
                    <span>在线用户:</span>
                    <span>24</span>
                  </div>
                  <div className="flex justify-between">
                    <span>系统负载:</span>
                    <span>正常</span>
                  </div>
                </div>
              </div>
            </div>
          )}

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
                      className="bg-gradient-to-r from-purple-500 to-pink-600"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {user?.full_name || user?.username}
                      </div>
                      <div className="text-xs text-purple-600 dark:text-purple-400 truncate">
                        系统管理员
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
                      className="bg-gradient-to-r from-purple-500 to-pink-600 cursor-pointer"
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
