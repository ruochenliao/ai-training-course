import React from 'react'
import { Card, Space, Typography } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const DocumentCenterPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          文档中心
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>浏览和搜索所有文档</Paragraph>
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
            文档中心功能开发中
          </Title>
          <Paragraph style={{ color: '#94a3b8', fontSize: 16 }}>此页面将提供文档搜索、分类浏览等功能</Paragraph>
        </Space>
      </Card>
    </div>
  )
}

export default DocumentCenterPage
