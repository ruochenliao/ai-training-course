import React from 'react'
import {Button, Result} from 'antd'
import {useNavigate} from 'react-router-dom'

const ServerError: React.FC = () => {
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
        status='500'
        title='500'
        subTitle='抱歉，服务器出现了错误。'
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

export default ServerError
