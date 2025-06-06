import React from 'react'
import {Button, Result} from 'antd'
import {useNavigate} from 'react-router-dom'
import {useAppStore} from '../store/app'
import {cn} from '../utils'

// 403 权限不足页面
export const Error403: React.FC = () => {
  const navigate = useNavigate()
  const { theme } = useAppStore()

  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center",
      theme === 'dark' ? "bg-gray-900" : "bg-gray-50"
    )}>
      <Result
        status="403"
        title={<span className={theme === 'dark' ? 'text-white' : 'text-gray-800'}>403</span>}
        subTitle={<span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>抱歉，您没有权限访问此页面</span>}
        extra={
          <div className="space-x-4">
            <Button type="primary" onClick={() => navigate(-1)}>
              返回上页
            </Button>
            <Button onClick={() => navigate('/dashboard')}>
              回到首页
            </Button>
          </div>
        }
      />
    </div>
  )
}

// 404 页面不存在
export const Error404: React.FC = () => {
  const navigate = useNavigate()
  const { theme } = useAppStore()

  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center",
      theme === 'dark' ? "bg-gray-900" : "bg-gray-50"
    )}>
      <Result
        status="404"
        title={<span className={theme === 'dark' ? 'text-white' : 'text-gray-800'}>404</span>}
        subTitle={<span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>抱歉，您访问的页面不存在</span>}
        extra={
          <div className="space-x-4">
            <Button type="primary" onClick={() => navigate('/dashboard')}>
              回到首页
            </Button>
            <Button onClick={() => navigate(-1)}>
              返回上页
            </Button>
          </div>
        }
      />
    </div>
  )
}

// 500 服务器错误
export const Error500: React.FC = () => {
  const navigate = useNavigate()
  const { theme } = useAppStore()

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center",
      theme === 'dark' ? "bg-gray-900" : "bg-gray-50"
    )}>
      <Result
        status="500"
        title={<span className={theme === 'dark' ? 'text-white' : 'text-gray-800'}>500</span>}
        subTitle={<span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>抱歉，服务器出现了一些问题</span>}
        extra={
          <div className="space-x-4">
            <Button type="primary" onClick={handleRefresh}>
              刷新页面
            </Button>
            <Button onClick={() => navigate('/dashboard')}>
              回到首页
            </Button>
          </div>
        }
      />
    </div>
  )
}

// 通用错误页面
interface ErrorPageProps {
  status?: '403' | '404' | '500'
  title?: string
  subTitle?: string
  showBackButton?: boolean
  showHomeButton?: boolean
  showRefreshButton?: boolean
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
  status = '404',
  title,
  subTitle,
  showBackButton = true,
  showHomeButton = true,
  showRefreshButton = false
}) => {
  const navigate = useNavigate()
  const { theme } = useAppStore()

  const defaultTitles = {
    '403': '403',
    '404': '404',
    '500': '500'
  }

  const defaultSubTitles = {
    '403': '抱歉，您没有权限访问此页面',
    '404': '抱歉，您访问的页面不存在',
    '500': '抱歉，服务器出现了一些问题'
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center",
      theme === 'dark' ? "bg-gray-900" : "bg-gray-50"
    )}>
      <Result
        status={status}
        title={<span className={theme === 'dark' ? 'text-white' : 'text-gray-800'}>{title || defaultTitles[status]}</span>}
        subTitle={<span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>{subTitle || defaultSubTitles[status]}</span>}
        extra={
          <div className="space-x-4">
            {showRefreshButton && (
              <Button type="primary" onClick={handleRefresh}>
                刷新页面
              </Button>
            )}
            {showHomeButton && (
              <Button type={showRefreshButton ? 'default' : 'primary'} onClick={() => navigate('/dashboard')}>
                回到首页
              </Button>
            )}
            {showBackButton && (
              <Button onClick={() => navigate(-1)}>
                返回上页
              </Button>
            )}
          </div>
        }
      />
    </div>
  )
}