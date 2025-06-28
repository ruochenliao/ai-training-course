'use client';

import { useState } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Table,
  Tag,
  Input,
  Form,
  Tabs,
  Alert,
  Progress,
  Divider,
  Row,
  Col,
  Statistic,
  message
} from 'antd';
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  ApiOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { apiTester, quickTest, TestResult } from '@/utils/apiTest';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export default function ApiTestPage() {
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [quickTestResults, setQuickTestResults] = useState<{
    basic: boolean | null;
    auth: boolean | null;
    api: { available: number; total: number } | null;
  }>({
    basic: null,
    auth: null,
    api: null
  });

  // 运行完整测试套件
  const runFullTest = async () => {
    setLoading(true);
    try {
      const results = await apiTester.runFullTestSuite(
        credentials.username && credentials.password ? credentials : undefined
      );
      setTestResults(results);
    } catch (error) {
      message.error('测试执行失败');
    } finally {
      setLoading(false);
    }
  };

  // 运行快速测试
  const runQuickTests = async () => {
    setLoading(true);
    try {
      const [basic, auth, api] = await Promise.all([
        quickTest.basic(),
        credentials.username && credentials.password 
          ? quickTest.auth(credentials.username, credentials.password)
          : Promise.resolve(null),
        quickTest.api()
      ]);

      setQuickTestResults({ basic, auth, api });
      
      if (basic) {
        message.success('基础连接测试通过');
      } else {
        message.error('基础连接测试失败');
      }
    } catch (error) {
      message.error('快速测试执行失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试结果表格列定义
  const columns = [
    {
      title: '接口',
      dataIndex: 'endpoint',
      key: 'endpoint',
      width: 300,
      render: (text: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {text}
        </Text>
      ),
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: string) => (
        <Tag color={method === 'GET' ? 'blue' : method === 'POST' ? 'green' : 'orange'}>
          {method}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 100,
      render: (success: boolean) => (
        <Tag
          icon={success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          color={success ? 'success' : 'error'}
        >
          {success ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
      width: 120,
      render: (time: number) => (
        <Text>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {time}ms
        </Text>
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error',
      key: 'error',
      render: (error: string) => (
        error ? <Text type="danger" style={{ fontSize: '12px' }}>{error}</Text> : '-'
      ),
    },
  ];

  // 计算统计信息
  const stats = {
    total: testResults.length,
    successful: testResults.filter(r => r.success).length,
    failed: testResults.filter(r => !r.success).length,
    avgResponseTime: testResults.length > 0 
      ? testResults.reduce((sum, r) => sum + r.responseTime, 0) / testResults.length 
      : 0,
    successRate: testResults.length > 0 
      ? (testResults.filter(r => r.success).length / testResults.length) * 100 
      : 0
  };

  return (
    <div style={{ padding: '24px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Title level={2}>
          <ApiOutlined style={{ marginRight: 8 }} />
          API接口测试与联调
        </Title>
        <Text type="secondary">
          测试前后端接口连通性，验证数据格式和响应状态
        </Text>

        <Divider />

        <Tabs defaultActiveKey="quick" type="card">
          <TabPane tab="快速测试" key="quick">
            <Card>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="快速测试"
                  description="快速验证基础连接和核心功能是否正常"
                  type="info"
                  showIcon
                />

                <Form layout="inline">
                  <Form.Item label="用户名">
                    <Input
                      placeholder="输入测试用户名"
                      value={credentials.username}
                      onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                    />
                  </Form.Item>
                  <Form.Item label="密码">
                    <Input.Password
                      placeholder="输入测试密码"
                      value={credentials.password}
                      onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      onClick={runQuickTests}
                      loading={loading}
                    >
                      开始快速测试
                    </Button>
                  </Form.Item>
                </Form>

                {(quickTestResults.basic !== null || quickTestResults.api !== null) && (
                  <Row gutter={16}>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="基础连接"
                          value={quickTestResults.basic ? '正常' : '异常'}
                          valueStyle={{ 
                            color: quickTestResults.basic ? '#3f8600' : '#cf1322' 
                          }}
                          prefix={
                            quickTestResults.basic 
                              ? <CheckCircleOutlined /> 
                              : <CloseCircleOutlined />
                          }
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="用户认证"
                          value={
                            quickTestResults.auth === null 
                              ? '未测试' 
                              : quickTestResults.auth 
                                ? '成功' 
                                : '失败'
                          }
                          valueStyle={{ 
                            color: quickTestResults.auth === null 
                              ? '#666' 
                              : quickTestResults.auth 
                                ? '#3f8600' 
                                : '#cf1322' 
                          }}
                          prefix={
                            quickTestResults.auth === null 
                              ? null
                              : quickTestResults.auth 
                                ? <CheckCircleOutlined /> 
                                : <CloseCircleOutlined />
                          }
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="API可用性"
                          value={
                            quickTestResults.api 
                              ? `${quickTestResults.api.available}/${quickTestResults.api.total}`
                              : '未测试'
                          }
                          suffix={
                            quickTestResults.api 
                              ? `(${Math.round((quickTestResults.api.available / quickTestResults.api.total) * 100)}%)`
                              : ''
                          }
                          valueStyle={{ 
                            color: quickTestResults.api && quickTestResults.api.available === quickTestResults.api.total
                              ? '#3f8600' 
                              : '#cf1322' 
                          }}
                        />
                      </Card>
                    </Col>
                  </Row>
                )}
              </Space>
            </Card>
          </TabPane>

          <TabPane tab="完整测试" key="full">
            <Card>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="完整测试套件"
                  description="测试所有API接口的连通性和功能完整性"
                  type="warning"
                  showIcon
                />

                <Space>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={runFullTest}
                    loading={loading}
                    size="large"
                  >
                    运行完整测试
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      setTestResults([]);
                      apiTester.clearResults();
                    }}
                  >
                    清除结果
                  </Button>
                </Space>

                {testResults.length > 0 && (
                  <>
                    <Row gutter={16}>
                      <Col span={6}>
                        <Statistic title="总接口数" value={stats.total} />
                      </Col>
                      <Col span={6}>
                        <Statistic 
                          title="成功数" 
                          value={stats.successful} 
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic 
                          title="失败数" 
                          value={stats.failed} 
                          valueStyle={{ color: '#cf1322' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic 
                          title="成功率" 
                          value={stats.successRate} 
                          precision={1}
                          suffix="%" 
                          valueStyle={{ 
                            color: stats.successRate > 80 ? '#3f8600' : '#cf1322' 
                          }}
                        />
                      </Col>
                    </Row>

                    <Progress 
                      percent={stats.successRate} 
                      status={stats.successRate === 100 ? 'success' : 'active'}
                      strokeColor={{
                        '0%': '#108ee9',
                        '100%': '#87d068',
                      }}
                    />

                    <Table
                      columns={columns}
                      dataSource={testResults.map((result, index) => ({
                        ...result,
                        key: index
                      }))}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 条记录`
                      }}
                      scroll={{ x: 800 }}
                    />
                  </>
                )}
              </Space>
            </Card>
          </TabPane>
        </Tabs>
      </motion.div>
    </div>
  );
}
