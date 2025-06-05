import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import Layout from '../components/layout/Layout';
import { AuthGuard, PermissionGuard, AdminGuard } from '../components/auth/RouteGuard';
import { Loading } from '../components/common/LoadingEmpty';

// 懒加载组件
const Login = React.lazy(() => import('../pages/auth/Login'));
const Dashboard = React.lazy(() => import('../pages/dashboard/Dashboard'));
const CustomerService = React.lazy(() => import('../pages/CustomerService'));
const Analytics = React.lazy(() => import('../pages/Analytics'));
const Users = React.lazy(() => import('../pages/system/Users'));
const Roles = React.lazy(() => import('../pages/system/Roles'));
const Permissions = React.lazy(() => import('../pages/system/Permissions'));
const Settings = React.lazy(() => import('../pages/system/Settings'));
const Profile = React.lazy(() => import('../pages/Profile'));
const NotFound = React.lazy(() => import('../pages/NotFound'));

// 加载组件包装器
const SuspenseWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<Loading />}>
    {children}
  </Suspense>
);

// 路由配置
export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <SuspenseWrapper>
        <Login />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <Layout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: (
          <SuspenseWrapper>
            <Dashboard />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'customer-service',
        element: (
          <PermissionGuard permission="customer_service:view">
            <SuspenseWrapper>
              <CustomerService />
            </SuspenseWrapper>
          </PermissionGuard>
        ),
      },
      {
        path: 'analytics',
        element: (
          <PermissionGuard permission="analytics:view">
            <SuspenseWrapper>
              <Analytics />
            </SuspenseWrapper>
          </PermissionGuard>
        ),
      },
      {
        path: 'profile',
        element: (
          <SuspenseWrapper>
            <Profile />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'system',
        children: [
          {
            index: true,
            element: <Navigate to="/system/users" replace />,
          },
          {
            path: 'users',
            element: (
              <AdminGuard>
                <PermissionGuard permission="system:user:view">
                  <SuspenseWrapper>
                    <Users />
                  </SuspenseWrapper>
                </PermissionGuard>
              </AdminGuard>
            ),
          },
          {
            path: 'roles',
            element: (
              <AdminGuard>
                <PermissionGuard permission="system:role:view">
                  <SuspenseWrapper>
                    <Roles />
                  </SuspenseWrapper>
                </PermissionGuard>
              </AdminGuard>
            ),
          },
          {
            path: 'permissions',
            element: (
              <AdminGuard>
                <PermissionGuard permission="system:permission:view">
                  <SuspenseWrapper>
                    <Permissions />
                  </SuspenseWrapper>
                </PermissionGuard>
              </AdminGuard>
            ),
          },
          {
            path: 'settings',
            element: (
              <AdminGuard>
                <PermissionGuard permission="system:settings:view">
                  <SuspenseWrapper>
                    <Settings />
                  </SuspenseWrapper>
                </PermissionGuard>
              </AdminGuard>
            ),
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: (
      <SuspenseWrapper>
        <NotFound />
      </SuspenseWrapper>
    ),
  },
]);

// 菜单配置
export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  permission?: string;
  children?: MenuItem[];
  hidden?: boolean;
}

// 菜单数据
export const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    label: 'menu.dashboard',
    icon: 'DashboardOutlined',
    path: '/dashboard',
  },
  {
    key: 'customer-service',
    label: 'menu.customerService',
    icon: 'CustomerServiceOutlined',
    path: '/customer-service',
    permission: 'customer_service:view',
  },
  {
    key: 'analytics',
    label: 'menu.analytics',
    icon: 'BarChartOutlined',
    path: '/analytics',
    permission: 'analytics:view',
  },
  {
    key: 'system',
    label: 'menu.system',
    icon: 'SettingOutlined',
    permission: 'system:view',
    children: [
      {
        key: 'system-users',
        label: 'menu.system.users',
        icon: 'UserOutlined',
        path: '/system/users',
        permission: 'system:user:view',
      },
      {
        key: 'system-roles',
        label: 'menu.system.roles',
        icon: 'TeamOutlined',
        path: '/system/roles',
        permission: 'system:role:view',
      },
      {
        key: 'system-permissions',
        label: 'menu.system.permissions',
        icon: 'SafetyOutlined',
        path: '/system/permissions',
        permission: 'system:permission:view',
      },
      {
        key: 'system-settings',
        label: 'menu.system.settings',
        icon: 'ControlOutlined',
        path: '/system/settings',
        permission: 'system:settings:view',
      },
    ],
  },
];

// 面包屑配置
export const breadcrumbConfig: Record<string, { title: string; path?: string }[]> = {
  '/dashboard': [
    { title: 'menu.dashboard' },
  ],
  '/customer-service': [
    { title: 'menu.customerService' },
  ],
  '/analytics': [
    { title: 'menu.analytics' },
  ],
  '/profile': [
    { title: 'menu.profile' },
  ],
  '/system/users': [
    { title: 'menu.system', path: '/system' },
    { title: 'menu.system.users' },
  ],
  '/system/roles': [
    { title: 'menu.system', path: '/system' },
    { title: 'menu.system.roles' },
  ],
  '/system/permissions': [
    { title: 'menu.system', path: '/system' },
    { title: 'menu.system.permissions' },
  ],
  '/system/settings': [
    { title: 'menu.system', path: '/system' },
    { title: 'menu.system.settings' },
  ],
};

// 路由权限配置
export const routePermissions: Record<string, string> = {
  '/customer-service': 'customer_service:view',
  '/analytics': 'analytics:view',
  '/system/users': 'system:user:view',
  '/system/roles': 'system:role:view',
  '/system/permissions': 'system:permission:view',
  '/system/settings': 'system:settings:view',
};

// 公开路由（不需要认证）
export const publicRoutes = ['/login', '/register', '/forgot-password'];

// 管理员路由（需要管理员权限）
export const adminRoutes = [
  '/system/users',
  '/system/roles',
  '/system/permissions',
  '/system/settings',
];

// 路由工具函数
export const routeUtils = {
  // 检查是否为公开路由
  isPublicRoute: (path: string): boolean => {
    return publicRoutes.includes(path);
  },

  // 检查是否为管理员路由
  isAdminRoute: (path: string): boolean => {
    return adminRoutes.some(route => path.startsWith(route));
  },

  // 获取路由权限
  getRoutePermission: (path: string): string | undefined => {
    return routePermissions[path];
  },

  // 获取面包屑
  getBreadcrumb: (path: string): { title: string; path?: string }[] => {
    return breadcrumbConfig[path] || [];
  },

  // 过滤有权限的菜单
  filterMenuByPermissions: (
    menus: MenuItem[],
    permissions: string[]
  ): MenuItem[] => {
    return menus
      .filter(menu => {
        if (menu.hidden) return false;
        if (!menu.permission) return true;
        return permissions.includes(menu.permission);
      })
      .map(menu => ({
        ...menu,
        children: menu.children
          ? routeUtils.filterMenuByPermissions(menu.children, permissions)
          : undefined,
      }))
      .filter(menu => !menu.children || menu.children.length > 0);
  },

  // 获取默认打开的菜单
  getDefaultOpenKeys: (path: string): string[] => {
    const keys: string[] = [];
    const pathSegments = path.split('/').filter(Boolean);
    
    for (let i = 0; i < pathSegments.length; i++) {
      const key = pathSegments.slice(0, i + 1).join('-');
      keys.push(key);
    }
    
    return keys;
  },

  // 获取当前选中的菜单
  getSelectedKeys: (path: string): string[] => {
    // 移除查询参数和哈希
    const cleanPath = path.split('?')[0].split('#')[0];
    
    // 特殊处理系统管理子页面
    if (cleanPath.startsWith('/system/')) {
      const subPath = cleanPath.replace('/system/', '');
      return [`system-${subPath}`];
    }
    
    // 移除开头的斜杠并替换为连字符
    return [cleanPath.substring(1).replace(/\//g, '-') || 'dashboard'];
  },

  // 构建路由路径
  buildPath: (segments: string[]): string => {
    return '/' + segments.filter(Boolean).join('/');
  },

  // 解析路由参数
  parseParams: (search: string): Record<string, string> => {
    const params = new URLSearchParams(search);
    const result: Record<string, string> = {};
    
    for (const [key, value] of params.entries()) {
      result[key] = value;
    }
    
    return result;
  },

  // 构建查询字符串
  buildQuery: (params: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    
    const query = searchParams.toString();
    return query ? `?${query}` : '';
  },
};