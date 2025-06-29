import React from 'react'
import { Button, Card, Space, Typography } from 'antd'
import { DatabaseOutlined, PlusOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const KnowledgeBasesPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          知识库管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>管理和维护企业知识库</Paragraph>
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
          <DatabaseOutlined style={{ fontSize: 64, color: '#94a3b8' }} />
          <Title level={3} style={{ color: '#64748b' }}>
            知识库管理功能开发中
          </Title>
          <Paragraph style={{ color: '#94a3b8', fontSize: 16 }}>此页面将包含知识库的创建、编辑、删除等功能</Paragraph>
          <Button
            type='primary'
            size='large'
            icon={<PlusOutlined />}
            style={{
              background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
              border: 'none',
            }}
          >
            创建知识库
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default KnowledgeBasesPage
