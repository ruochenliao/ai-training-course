import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/api/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, token, setUser, clearAuth, loading } = useAuthStore()
  const location = useLocation()
  const [verifying, setVerifying] = React.useState(false)

  useEffect(() => {
    // 如果有token但未认证，尝试验证token
    if (token && !isAuthenticated && !verifying) {
      setVerifying(true)
      authApi
        .verifyToken()
        .then((response) => {
          setUser(response.data)
        })
        .catch(() => {
          clearAuth()
        })
        .finally(() => {
          setVerifying(false)
        })
    }
  }, [token, isAuthenticated, setUser, clearAuth, verifying])

  // 显示加载状态
  if (loading || verifying) {
    return (
      <div className='flex-center h-screen'>
        <Spin size='large' />
      </div>
    )
  }

  // 未认证则跳转到登录页
  if (!isAuthenticated) {
    return <Navigate to='/login' state={{ from: location }} replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
