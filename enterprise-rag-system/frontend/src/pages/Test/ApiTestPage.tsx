import React, { useState } from 'react'
import { Card, Button, Space, Typography, Divider, Alert, Spin, Tag, Row, Col, Statistic, message } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ApiOutlined,
  DatabaseOutlined,
  UserOutlined,
  FileTextOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { api } from '@/api'

const { Title, Text, Paragraph } = Typography

interface TestResult {
  name: string
  status: 'pending' | 'success' | 'error'
  message?: string
  responseTime?: number
  data?: any
}

const ApiTestPage: React.FC = () => {
  const [testing, setTesting] = useState(false)
  const [results, setResults] = useState<TestResult[]>([])

  // 测试项目配置
  const testItems = [
    {
      name: '系统健康检查',
      icon: <ApiOutlined />,
      test: () => api.system.healthCheck(),
      description: '检查系统各服务状态',
    },
    {
      name: '用户认证',
      icon: <UserOutlined />,
      test: () => api.auth.getCurrentUser(),
      description: '验证用户认证状态',
    },
    {
      name: '知识库列表',
      icon: <DatabaseOutlined />,
      test: () => api.knowledge.getKnowledgeBases({ page: 1, size: 5 }),
      description: '获取知识库列表',
    },
    {
      name: '文档列表',
      icon: <FileTextOutlined />,
      test: () => api.documents.getDocuments({ page: 1, size: 5 }),
      description: '获取文档列表',
    },
    {
      name: '对话列表',
      icon: <MessageOutlined />,
      test: () => api.chat.getConversations({ page: 1, size: 5 }),
      description: '获取对话历史',
    },
  ]

  // 执行单个测试
  const runSingleTest = async (item: any, index: number) => {
    const startTime = Date.now()

    try {
      const response = await item.test()
      const responseTime = Date.now() - startTime

      setResults(prev =>
        prev.map((result, i) =>
          i === index
            ? {
                ...result,
                status: 'success',
                message: '测试通过',
                responseTime,
                data: response.data,
              }
            : result
        )
      )
    } catch (error: any) {
      const responseTime = Date.now() - startTime

      setResults(prev =>
        prev.map((result, i) =>
          i === index
            ? {
                ...result,
                status: 'error',
                message: error.response?.data?.message || error.message || '测试失败',
                responseTime,
              }
            : result
        )
      )
    }
  }

  // 执行所有测试
  const runAllTests = async () => {
    setTesting(true)

    // 初始化测试结果
    const initialResults = testItems.map(item => ({
      name: item.name,
      status: 'pending' as const,
    }))
    setResults(initialResults)

    // 依次执行测试
    for (let i = 0; i < testItems.length; i++) {
      await runSingleTest(testItems[i], i)
      // 添加小延迟，避免请求过于频繁
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    setTesting(false)
    message.success('API测试完成')
  }

  // 渲染测试结果
  const renderTestResult = (result: TestResult, item: any) => {
    const getStatusIcon = () => {
      switch (result.status) {
        case 'pending':
          return <LoadingOutlined style={{ color: '#1890ff' }} />
        case 'success':
          return <CheckCircleOutlined style={{ color: '#52c41a' }} />
        case 'error':
          return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      }
    }

    const getStatusColor = () => {
      switch (result.status) {
        case 'pending':
          return 'processing'
        case 'success':
          return 'success'
        case 'error':
          return 'error'
      }
    }

    return (
      <Card key={result.name} size='small' style={{ marginBottom: 16 }}>
        <Row align='middle' gutter={16}>
          <Col flex='none'>{item.icon}</Col>
          <Col flex='auto'>
            <div>
              <Text strong>{result.name}</Text>
              <div>
                <Text type='secondary' style={{ fontSize: 12 }}>
                  {item.description}
                </Text>
              </div>
            </div>
          </Col>
          <Col flex='none'>
            <Space>
              {result.responseTime && (
                <Text type='secondary' style={{ fontSize: 12 }}>
                  {result.responseTime}ms
                </Text>
              )}
              <Tag color={getStatusColor()}>
                {getStatusIcon()}
                <span style={{ marginLeft: 4 }}>
                  {result.status === 'pending' ? '测试中' : result.status === 'success' ? '成功' : '失败'}
                </span>
              </Tag>
            </Space>
          </Col>
        </Row>

        {result.message && result.status === 'error' && (
          <Alert message={result.message} type='error' size='small' style={{ marginTop: 8 }} />
        )}

        {result.data && result.status === 'success' && (
          <div style={{ marginTop: 8 }}>
            <Text type='secondary' style={{ fontSize: 12 }}>
              返回数据: {JSON.stringify(result.data).substring(0, 100)}...
            </Text>
          </div>
        )}
      </Card>
    )
  }

  // 计算统计信息
  const getStats = () => {
    const total = results.length
    const success = results.filter(r => r.status === 'success').length
    const error = results.filter(r => r.status === 'error').length
    const avgResponseTime =
      results.filter(r => r.responseTime).reduce((sum, r) => sum + (r.responseTime || 0), 0) /
        results.filter(r => r.responseTime).length || 0

    return { total, success, error, avgResponseTime }
  }

  const stats = getStats()

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          API 连接测试
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>测试前后端API接口连接状态</Paragraph>
      </div>

      {/* 统计信息 */}
      {results.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic title='总测试数' value={stats.total} prefix={<ApiOutlined style={{ color: '#1890ff' }} />} />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title='成功'
                value={stats.success}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title='失败'
                value={stats.error}
                prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title='平均响应时间'
                value={Math.round(stats.avgResponseTime)}
                suffix='ms'
                prefix={<LoadingOutlined style={{ color: '#722ed1' }} />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作按钮 */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Button
            type='primary'
            icon={<ApiOutlined />}
            onClick={runAllTests}
            loading={testing}
            style={{
              background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
              border: 'none',
            }}
          >
            开始测试
          </Button>
          <Button onClick={() => setResults([])} disabled={testing}>
            清空结果
          </Button>
        </Space>
      </Card>

      {/* 测试结果 */}
      <Card title='测试结果'>
        {results.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <ApiOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
            <div>
              <Text type='secondary'>点击"开始测试"按钮开始API连接测试</Text>
            </div>
          </div>
        ) : (
          <Spin spinning={testing}>{results.map((result, index) => renderTestResult(result, testItems[index]))}</Spin>
        )}
      </Card>
    </div>
  )
}

export default ApiTestPage
