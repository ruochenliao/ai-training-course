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

// 临时页面组件
const TempPage = ({ title }: { title: string }) => (
  <div className="p-8">
    <h1 className="text-2xl font-bold mb-4">{title}</h1>
    <p>这是一个临时页面，等待实际功能实现。</p>
  </div>
);

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
        element: <Navigate to="/workbench" replace />,
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
        element: <TempPage title="个人资料" />,
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
            element: <TempPage title="用户管理" />,
          },
          {
            path: 'role',
            element: <TempPage title="角色管理" />,
          },
          {
            path: 'menu',
            element: <TempPage title="菜单管理" />,
          },
          {
            path: 'dept',
            element: <TempPage title="部门管理" />,
          },
          {
            path: 'api',
            element: <TempPage title="API管理" />,
          },
          {
            path: 'auditlog',
            element: <TempPage title="审计日志" />,
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