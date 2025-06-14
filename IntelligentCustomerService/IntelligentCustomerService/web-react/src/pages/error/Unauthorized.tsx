import React from 'react'
import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useThemeStore } from '@/store/theme'
import { cn } from '@/utils'

// 401 未授权页面
const Unauthorized: React.FC = () => {
  const navigate = useNavigate()
  const { isDark } = useThemeStore()

  return (
    <div className={cn('min-h-screen flex items-center justify-center', isDark ? 'bg-gray-900' : 'bg-gray-50')}>
      <Result
        status='warning'
        title={<span className={isDark ? 'text-white' : 'text-gray-800'}>401</span>}
        subTitle={<span className={isDark ? 'text-gray-300' : 'text-gray-600'}>抱歉，您未授权访问此页面</span>}
        extra={
          <div className='space-x-4'>
            <Button type='primary' onClick={() => navigate('/login')}>
              去登录
            </Button>
            <Button onClick={() => navigate('/')}>回到首页</Button>
          </div>
        }
      />
    </div>
  )
}

export default Unauthorized
