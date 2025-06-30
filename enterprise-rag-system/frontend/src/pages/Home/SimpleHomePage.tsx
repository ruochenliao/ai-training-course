import React from 'react'
import { Button, Card, Space, Typography } from 'antd'
import { RobotOutlined, MessageOutlined, DatabaseOutlined, ApiOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const SimpleHomePage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      {/* 欢迎区域 */}
      <div style={{ marginBottom: 32 }}>
        <div
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 16,
            padding: 48,
            color: 'white',
            textAlign: 'center',
          }}
        >
          <RobotOutlined style={{ fontSize: 64, marginBottom: 16 }} />
          <Title level={1} style={{ color: 'white', margin: 0 }}>
            企业级 RAG 知识库系统
          </Title>
          <Paragraph style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: 18, margin: '16px 0 32px' }}>
            基于 AutoGen 智能体协作的下一代企业知识管理平台
          </Paragraph>
          <Space size='large'>
            <Button
              type='primary'
              size='large'
              icon={<MessageOutlined />}
              onClick={() => window.location.href = '/chat'}
              style={{
                background: 'rgba(255, 255, 255, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              开始对话
            </Button>
            <Button
              size='large'
              icon={<DatabaseOutlined />}
              onClick={() => window.location.href = '/knowledge/bases'}
              style={{
                background: 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.5)',
                color: 'white',
              }}
            >
              知识库管理
            </Button>
          </Space>
        </div>
      </div>

      {/* 功能卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
        <Card
          title="智能对话"
          extra={<MessageOutlined style={{ color: '#0ea5e9' }} />}
          hoverable
          onClick={() => window.location.href = '/chat'}
          style={{ cursor: 'pointer' }}
        >
          <Paragraph>
            基于企业知识库的智能问答系统，支持多智能体协作，提供准确、专业的回答。
          </Paragraph>
        </Card>

        <Card
          title="知识库管理"
          extra={<DatabaseOutlined style={{ color: '#8b5cf6' }} />}
          hoverable
          onClick={() => window.location.href = '/knowledge/bases'}
          style={{ cursor: 'pointer' }}
        >
          <Paragraph>
            创建和管理企业知识库，支持多种文档格式，智能分析和向量化处理。
          </Paragraph>
        </Card>

        <Card
          title="系统测试"
          extra={<ApiOutlined style={{ color: '#10b981' }} />}
          hoverable
          onClick={() => window.location.href = '/test/simple'}
          style={{ cursor: 'pointer' }}
        >
          <Paragraph>
            测试系统各项功能，验证前后端连接状态，确保系统正常运行。
          </Paragraph>
        </Card>
      </div>
    </div>
  )
}

export default SimpleHomePage
