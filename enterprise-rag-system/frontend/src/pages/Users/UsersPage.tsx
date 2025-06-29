import React from 'react'
import { Button, Card, Space, Typography } from 'antd'
import { UserAddOutlined, UserOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const UsersPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          用户管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>管理系统用户和权限</Paragraph>
      </div>

      <Card
        style={{
          textAlign: 'center',
          minHeight: 400,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Space direction='vertical' size='large'>
          <UserOutlined style={{ fontSize: 64, color: '#94a3b8' }} />
          <Title level={3} style={{ color: '#64748b' }}>
            用户管理功能开发中
          </Title>
          <Paragraph style={{ color: '#94a3b8', fontSize: 16 }}>此页面将包含用户的增删改查、权限管理等功能</Paragraph>
          <Button
            type='primary'
            size='large'
            icon={<UserAddOutlined />}
            style={{
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              border: 'none',
            }}
          >
            添加用户
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default UsersPage
