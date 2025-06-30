import React from 'react'
import { Card, Typography, Space, Button, Alert } from 'antd'
import { CheckCircleOutlined, ApiOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const SimpleTestPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
            <Title level={2}>前端系统正常运行</Title>
            <Paragraph>
              恭喜！前端应用已成功启动，所有基础组件工作正常。
            </Paragraph>
          </div>

          <Alert
            message="系统状态"
            description="React 18 + TypeScript + Ant Design + Vite 技术栈运行正常"
            type="success"
            showIcon
          />

          <div style={{ textAlign: 'center' }}>
            <Button 
              type="primary" 
              icon={<ApiOutlined />}
              onClick={() => window.location.href = '/test/api'}
            >
              进行API连接测试
            </Button>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default SimpleTestPage
