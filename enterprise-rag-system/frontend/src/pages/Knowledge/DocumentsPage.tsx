import React from 'react'
import { Button, Card, Space, Typography } from 'antd'
import { FileTextOutlined, UploadOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const DocumentsPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          文档管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>上传和管理知识库文档</Paragraph>
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
          <FileTextOutlined style={{ fontSize: 64, color: '#94a3b8' }} />
          <Title level={3} style={{ color: '#64748b' }}>
            文档管理功能开发中
          </Title>
          <Paragraph style={{ color: '#94a3b8', fontSize: 16 }}>此页面将包含文档的上传、预览、编辑等功能</Paragraph>
          <Button
            type='primary'
            size='large'
            icon={<UploadOutlined />}
            style={{
              background: 'linear-gradient(135deg, #8b5cf6, #a855f7)',
              border: 'none',
            }}
          >
            上传文档
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default DocumentsPage
