import React, {Suspense} from 'react';
import {createBrowserRouter, Navigate} from 'react-router-dom';
import Layout from '../components/layout/Layout';
import {AuthGuard} from '../components/auth/RouteGuard';
import {Loading} from '../components/common/LoadingEmpty';

// 工作台页面
const Workbench = React.lazy(() => import('../pages/workbench/Workbench'));

// 懒加载组件
const Login = React.lazy(() => import('../pages/auth/Login'));

// 错误页面
const NotFound = React.lazy(() => import('../pages/error/NotFound'));
const Forbidden = React.lazy(() => import('../pages/error/Forbidden'));
const ServerError = React.lazy(() => import('../pages/error/ServerError'));
const Unauthorized = React.lazy(() => import('../pages/error/Unauthorized'));

// 一级菜单
const SimpleMenu = React.lazy(() => import('../pages/menu/SimpleMenu'));

// 智能客服页面已删除

// 系统管理页面
const UserManagement = React.lazy(() => import('../pages/system/user/UserManagement'));
const RoleManagement = React.lazy(() => import('../pages/system/role/RoleManagement'));
const MenuManagement = React.lazy(() => import('../pages/system/menu/MenuManagement'));
const DeptManagement = React.lazy(() => import('../pages/system/dept/DeptManagement'));
const ApiManagement = React.lazy(() => import('../pages/system/api/ApiManagement'));
const AuditLog = React.lazy(() => import('../pages/system/auditlog/AuditLog'));

// 个人资料页面
const Profile = React.lazy(() => import('../pages/profile/Profile'));

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
      <Navigate to="/dashboard" replace />
    ),
  },
  {
    path: '/dashboard',
    element: (
      <AuthGuard>
        <Layout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard/workbench" replace />,
      },
      {
        path: 'workbench',
        element: (
          <SuspenseWrapper>
            <Workbench />
          </SuspenseWrapper>
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
        path: 'menu',
        element: (
          <SuspenseWrapper>
            <SimpleMenu />
          </SuspenseWrapper>
        ),
      },

      {
        path: 'system',
        children: [
          {
            index: true,
            element: <Navigate to="/system/user" replace />,
          },
          {
            path: 'user',
            element: (
              <SuspenseWrapper>
                <UserManagement />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'role',
            element: (
              <SuspenseWrapper>
                <RoleManagement />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'menu',
            element: (
              <SuspenseWrapper>
                <MenuManagement />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dept',
            element: (
              <SuspenseWrapper>
                <DeptManagement />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'api',
            element: (
              <SuspenseWrapper>
                <ApiManagement />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'auditlog',
            element: (
              <SuspenseWrapper>
                <AuditLog />
              </SuspenseWrapper>
            ),
          },
        ],
      },
      {
        path: 'error',
        children: [
          {
            path: '401',
            element: (
              <SuspenseWrapper>
                <Unauthorized />
              </SuspenseWrapper>
            ),
          },
          {
            path: '403',
            element: (
              <SuspenseWrapper>
                <Forbidden />
              </SuspenseWrapper>
            ),
          },
          {
            path: '404',
            element: (
              <SuspenseWrapper>
                <NotFound />
              </SuspenseWrapper>
            ),
          },
          {
            path: '500',
            element: (
              <SuspenseWrapper>
                <ServerError />
              </SuspenseWrapper>
            ),
          },
        ],
      },
    ],
  },
  {
    path: '/401',
    element: (
      <SuspenseWrapper>
        <Unauthorized />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/403',
    element: (
      <SuspenseWrapper>
        <Forbidden />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/500',
    element: (
      <SuspenseWrapper>
        <ServerError />
      </SuspenseWrapper>
    ),
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

// 公开路由（不需要认证）
export const publicRoutes = ['/login', '/register', '/forgot-password', '/401', '/403', '/404', '/500'];