import React from 'react'
import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  const handleBackHome = () => {
    navigate('/')
  }

  const handleGoBack = () => {
    navigate(-1)
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        padding: '24px',
      }}
    >
      <Result
        status='404'
        title='404'
        subTitle='抱歉，您访问的页面不存在。'
        extra={
          <div>
            <Button type='primary' onClick={handleBackHome} style={{ marginRight: '8px' }}>
              返回首页
            </Button>
            <Button onClick={handleGoBack}>返回上一页</Button>
          </div>
        }
      />
    </div>
  )
}

export default NotFound
