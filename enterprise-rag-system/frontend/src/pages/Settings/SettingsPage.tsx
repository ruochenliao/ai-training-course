import React from 'react'
import { Card, Space, Typography } from 'antd'
import { SettingOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const SettingsPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          系统设置
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>配置系统参数和选项</Paragraph>
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
          <SettingOutlined style={{ fontSize: 64, color: '#94a3b8' }} />
          <Title level={3} style={{ color: '#64748b' }}>
            系统设置功能开发中
          </Title>
          <Paragraph style={{ color: '#94a3b8', fontSize: 16 }}>此页面将提供系统配置、主题设置等功能</Paragraph>
        </Space>
      </Card>
    </div>
  )
}

export default SettingsPage
