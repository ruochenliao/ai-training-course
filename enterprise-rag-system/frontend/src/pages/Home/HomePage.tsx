import React from 'react'
import { Button, Card, Col, Progress, Row, Space, Statistic, Typography } from 'antd'
import {
  ArrowUpOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  MessageOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons'

const { Title, Paragraph } = Typography

const HomePage: React.FC = () => {
  // 模拟数据
  const stats = {
    totalConversations: 1234,
    totalDocuments: 5678,
    totalKnowledgeBases: 42,
    activeUsers: 89,
    conversationGrowth: 12.5,
    documentGrowth: 8.3,
    knowledgeBaseGrowth: 15.2,
    userGrowth: 6.7,
  }

  const systemStatus = {
    cpu: 45,
    memory: 62,
    storage: 38,
    network: 85,
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          欢迎使用企业级 RAG 知识库系统
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>
          基于 AutoGen 智能体协作的企业级知识库管理平台
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title='总对话数'
              value={stats.totalConversations}
              prefix={<MessageOutlined style={{ color: '#0ea5e9' }} />}
              suffix={
                <Space>
                  <ArrowUpOutlined style={{ color: '#10b981' }} />
                  <span style={{ color: '#10b981', fontSize: 12 }}>{stats.conversationGrowth}%</span>
                </Space>
              }
              valueStyle={{ color: '#1e293b' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title='文档总数'
              value={stats.totalDocuments}
              prefix={<FileTextOutlined style={{ color: '#8b5cf6' }} />}
              suffix={
                <Space>
                  <ArrowUpOutlined style={{ color: '#10b981' }} />
                  <span style={{ color: '#10b981', fontSize: 12 }}>{stats.documentGrowth}%</span>
                </Space>
              }
              valueStyle={{ color: '#1e293b' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title='知识库数量'
              value={stats.totalKnowledgeBases}
              prefix={<DatabaseOutlined style={{ color: '#f59e0b' }} />}
              suffix={
                <Space>
                  <ArrowUpOutlined style={{ color: '#10b981' }} />
                  <span style={{ color: '#10b981', fontSize: 12 }}>{stats.knowledgeBaseGrowth}%</span>
                </Space>
              }
              valueStyle={{ color: '#1e293b' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title='活跃用户'
              value={stats.activeUsers}
              prefix={<UserOutlined style={{ color: '#ef4444' }} />}
              suffix={
                <Space>
                  <ArrowUpOutlined style={{ color: '#10b981' }} />
                  <span style={{ color: '#10b981', fontSize: 12 }}>{stats.userGrowth}%</span>
                </Space>
              }
              valueStyle={{ color: '#1e293b' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 快速操作 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <RobotOutlined style={{ color: '#0ea5e9' }} />
                快速操作
              </Space>
            }
            style={{ height: '100%' }}
          >
            <Space direction='vertical' size='middle' style={{ width: '100%' }}>
              <Button
                type='primary'
                size='large'
                icon={<MessageOutlined />}
                block
                style={{
                  background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                  border: 'none',
                  height: 48,
                }}
              >
                开始智能对话
              </Button>

              <Button size='large' icon={<DatabaseOutlined />} block style={{ height: 48 }}>
                创建知识库
              </Button>

              <Button size='large' icon={<FileTextOutlined />} block style={{ height: 48 }}>
                上传文档
              </Button>

              <Button size='large' icon={<UserOutlined />} block style={{ height: 48 }}>
                用户管理
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 系统状态 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <CloudServerOutlined style={{ color: '#10b981' }} />
                系统状态
              </Space>
            }
            style={{ height: '100%' }}
          >
            <Space direction='vertical' size='large' style={{ width: '100%' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>CPU 使用率</span>
                  <span>{systemStatus.cpu}%</span>
                </div>
                <Progress
                  percent={systemStatus.cpu}
                  strokeColor={systemStatus.cpu > 80 ? '#ef4444' : '#10b981'}
                  showInfo={false}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>内存使用率</span>
                  <span>{systemStatus.memory}%</span>
                </div>
                <Progress
                  percent={systemStatus.memory}
                  strokeColor={systemStatus.memory > 80 ? '#ef4444' : '#f59e0b'}
                  showInfo={false}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>存储使用率</span>
                  <span>{systemStatus.storage}%</span>
                </div>
                <Progress percent={systemStatus.storage} strokeColor='#10b981' showInfo={false} />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>网络状态</span>
                  <span>{systemStatus.network}%</span>
                </div>
                <Progress percent={systemStatus.network} strokeColor='#0ea5e9' showInfo={false} />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 最近活动 */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title='最近活动' extra={<Button type='link'>查看全部</Button>}>
            <Space direction='vertical' size='middle' style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <MessageOutlined style={{ color: '#0ea5e9' }} />
                  <span>用户 张三 发起了新的对话</span>
                </Space>
                <span style={{ color: '#64748b', fontSize: 12 }}>2 分钟前</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <FileTextOutlined style={{ color: '#8b5cf6' }} />
                  <span>文档 "产品手册.pdf" 上传成功</span>
                </Space>
                <span style={{ color: '#64748b', fontSize: 12 }}>5 分钟前</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <DatabaseOutlined style={{ color: '#f59e0b' }} />
                  <span>知识库 "技术文档" 创建成功</span>
                </Space>
                <span style={{ color: '#64748b', fontSize: 12 }}>10 分钟前</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <UserOutlined style={{ color: '#ef4444' }} />
                  <span>新用户 李四 注册成功</span>
                </Space>
                <span style={{ color: '#64748b', fontSize: 12 }}>15 分钟前</span>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default HomePage
