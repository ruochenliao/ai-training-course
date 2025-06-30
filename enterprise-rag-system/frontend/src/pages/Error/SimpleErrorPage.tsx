import React from 'react'
import { Result, Button } from 'antd'

const SimpleErrorPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Result
        status="error"
        title="页面加载失败"
        subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面。"
        extra={[
          <Button type="primary" key="refresh" onClick={() => window.location.reload()}>
            刷新页面
          </Button>,
          <Button key="home" onClick={() => window.location.href = '/'}>
            返回首页
          </Button>
        ]}
      />
    </div>
  )
}

export default SimpleErrorPage
