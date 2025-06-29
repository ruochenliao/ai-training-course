import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Spin } from 'antd'

// 懒加载页面组件
const HomePage = React.lazy(() => import('@/pages/Home/HomePage'))
const ChatPage = React.lazy(() => import('@/pages/Chat/ChatPage'))
const KnowledgeBasesPage = React.lazy(() => import('@/pages/Knowledge/KnowledgeBasesPage'))
const DocumentsPage = React.lazy(() => import('@/pages/Knowledge/DocumentsPage'))
const DocumentCenterPage = React.lazy(() => import('@/pages/Documents/DocumentCenterPage'))
const UsersPage = React.lazy(() => import('@/pages/Users/UsersPage'))
const SettingsPage = React.lazy(() => import('@/pages/Settings/SettingsPage'))
const NotFoundPage = React.lazy(() => import('@/pages/Error/NotFoundPage'))

// 加载中组件
const LoadingSpinner: React.FC = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '50vh',
    }}
  >
    <Spin size='large' tip='页面加载中...' />
  </div>
)

// 路由配置
const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        {/* 首页 */}
        <Route path='/' element={<HomePage />} />

        {/* 智能对话 */}
        <Route path='/chat' element={<ChatPage />} />

        {/* 知识库管理 */}
        <Route path='/knowledge/bases' element={<KnowledgeBasesPage />} />
        <Route path='/knowledge/documents' element={<DocumentsPage />} />

        {/* 文档中心 */}
        <Route path='/documents' element={<DocumentCenterPage />} />

        {/* 用户管理 */}
        <Route path='/users' element={<UsersPage />} />

        {/* 系统设置 */}
        <Route path='/settings' element={<SettingsPage />} />

        {/* 重定向 */}
        <Route path='/knowledge' element={<Navigate to='/knowledge/bases' replace />} />

        {/* 404 页面 */}
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}

export default AppRoutes
