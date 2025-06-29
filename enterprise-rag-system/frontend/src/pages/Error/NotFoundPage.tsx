import React from 'react'
import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div
      style={{
        padding: 24,
        height: 'calc(100vh - 64px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Result
        status='404'
        title='404'
        subTitle='抱歉，您访问的页面不存在。'
        extra={
          <Button
            type='primary'
            onClick={() => navigate('/')}
            style={{
              background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
              border: 'none',
            }}
          >
            返回首页
          </Button>
        }
      />
    </div>
  )
}

export default NotFoundPage
