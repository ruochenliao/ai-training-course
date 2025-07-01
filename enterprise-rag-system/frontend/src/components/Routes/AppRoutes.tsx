import React, { Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useSimpleAuthStore } from '@/store/simple-auth'

// 直接导入页面组件
import HomePage from '../../pages/Home/HomePage'
import SimpleHomePage from '../../pages/Home/SimpleHomePage'
import ChatPage from '../../pages/Chat/ChatPage'
import KnowledgeBasesPage from '../../pages/Knowledge/KnowledgeBasesPage'
import DocumentsPage from '../../pages/Knowledge/DocumentsPage'
import DocumentCenterPage from '../../pages/Documents/DocumentCenterPage'
import UsersPage from '../../pages/Users/UsersPage'
import SettingsPage from '../../pages/Settings/SettingsPage'
import NotFoundPage from '../../pages/Error/NotFoundPage'
import LoginPage from '../../pages/Auth/LoginPage'
import SimpleLoginPage from '../../pages/Auth/SimpleLoginPage'
import ApiTestPage from '../../pages/Test/ApiTestPage'
import SimpleTestPage from '../../pages/Test/SimpleTestPage'

// 加载中组件
const LoadingSpinner: React.FC = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '50vh',
      flexDirection: 'column',
      gap: 16,
    }}
  >
    <Spin size='large' />
    <div style={{ color: '#64748b', fontSize: 14 }}>页面加载中...</div>
  </div>
)

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, checkAuth } = useSimpleAuthStore()
  const location = useLocation()

  useEffect(() => {
    if (!isAuthenticated) {
      const hasAuth = checkAuth()
      if (!hasAuth) {
        // 如果没有认证信息，重定向到登录页
      }
    }
  }, [isAuthenticated, checkAuth])

  if (!isAuthenticated) {
    return <Navigate to='/login' state={{ from: location }} replace />
  }

  return <>{children}</>
}

// 路由配置
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 登录页面 */}
      <Route path='/login' element={<SimpleLoginPage />} />
      <Route path='/login-full' element={<LoginPage />} />

      {/* 受保护的路由 */}
      <Route
        path='/'
        element={
          <ProtectedRoute>
            <SimpleHomePage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/home'
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/chat'
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/knowledge/bases'
        element={
          <ProtectedRoute>
            <KnowledgeBasesPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/knowledge/documents'
        element={
          <ProtectedRoute>
            <DocumentsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/documents'
        element={
          <ProtectedRoute>
            <DocumentCenterPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/users'
        element={
          <ProtectedRoute>
            <UsersPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/settings'
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/test/api'
        element={
          <ProtectedRoute>
            <ApiTestPage />
          </ProtectedRoute>
        }
      />

      <Route
        path='/test/simple'
        element={
          <ProtectedRoute>
            <SimpleTestPage />
          </ProtectedRoute>
        }
      />

      {/* 重定向 */}
      <Route path='/knowledge' element={<Navigate to='/knowledge/bases' replace />} />

      {/* 404 页面 */}
      <Route path='*' element={<NotFoundPage />} />
    </Routes>
  )
}

export default AppRoutes
