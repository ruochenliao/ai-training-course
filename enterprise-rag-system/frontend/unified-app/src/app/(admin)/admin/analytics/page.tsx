'use client';

import { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Select,
  DatePicker,
  Button,
  Space,
  Typography,
  Tabs,
  Progress,
  Tag,
  Tooltip,
  Empty
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrendingUpOutlined,
  UserOutlined,
  FileTextOutlined,
  MessageOutlined,
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { apiClient } from '@/utils/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [selectedMetric, setSelectedMetric] = useState('overview');
  const [refreshKey, setRefreshKey] = useState(0);

  // 获取系统统计数据
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats', refreshKey],
    queryFn: () => apiClient.getSystemStats(),
  });

  // 模拟数据
  const mockStats = {
    overview: {
      totalUsers: 1248,
      totalDocuments: 3567,
      totalConversations: 8934,
      totalSearches: 15672,
      avgResponseTime: 1.2,
      systemUptime: 99.8
    },
    trends: {
      userGrowth: [
        { date: '2024-01', users: 800, documents: 2100, conversations: 5200 },
        { date: '2024-02', users: 950, documents: 2800, conversations: 6800 },
        { date: '2024-03', users: 1100, documents: 3200, conversations: 7900 },
        { date: '2024-04', users: 1248, documents: 3567, conversations: 8934 },
      ],
      dailyActivity: [
        { hour: '00', searches: 45, conversations: 23 },
        { hour: '01', searches: 32, conversations: 18 },
        { hour: '02', searches: 28, conversations: 15 },
        { hour: '03', searches: 25, conversations: 12 },
        { hour: '04', searches: 30, conversations: 16 },
        { hour: '05', searches: 42, conversations: 25 },
        { hour: '06', searches: 68, conversations: 45 },
        { hour: '07', searches: 95, conversations: 72 },
        { hour: '08', searches: 125, conversations: 98 },
        { hour: '09', searches: 156, conversations: 125 },
        { hour: '10', searches: 178, conversations: 145 },
        { hour: '11', searches: 189, conversations: 156 },
        { hour: '12', searches: 165, conversations: 132 },
        { hour: '13', searches: 142, conversations: 118 },
        { hour: '14', searches: 167, conversations: 138 },
        { hour: '15', searches: 185, conversations: 152 },
        { hour: '16', searches: 172, conversations: 142 },
        { hour: '17', searches: 158, conversations: 128 },
        { hour: '18', searches: 135, conversations: 108 },
        { hour: '19', searches: 112, conversations: 89 },
        { hour: '20', searches: 95, conversations: 75 },
        { hour: '21', searches: 78, conversations: 62 },
        { hour: '22', searches: 65, conversations: 48 },
        { hour: '23', searches: 52, conversations: 35 },
      ]
    },
    distribution: {
      documentTypes: [
        { name: 'PDF', value: 45, color: '#8884d8' },
        { name: 'Word', value: 30, color: '#82ca9d' },
        { name: 'Text', value: 15, color: '#ffc658' },
        { name: 'Markdown', value: 10, color: '#ff7300' }
      ],
      knowledgeBases: [
        { name: '技术文档', documents: 1200, conversations: 3400 },
        { name: '业务知识', documents: 890, conversations: 2100 },
        { name: '法律法规', documents: 567, conversations: 1800 },
        { name: '产品手册', documents: 910, conversations: 1634 }
      ],
      userActivity: [
        { level: '高活跃', count: 156, percentage: 12.5 },
        { level: '中活跃', count: 487, percentage: 39.0 },
        { level: '低活跃', count: 605, percentage: 48.5 }
      ]
    },
    performance: {
      responseTime: [
        { date: '2024-04-01', avgTime: 1.1, p95Time: 2.3 },
        { date: '2024-04-02', avgTime: 1.2, p95Time: 2.5 },
        { date: '2024-04-03', avgTime: 1.0, p95Time: 2.1 },
        { date: '2024-04-04', avgTime: 1.3, p95Time: 2.8 },
        { date: '2024-04-05', avgTime: 1.1, p95Time: 2.2 },
        { date: '2024-04-06', avgTime: 1.2, p95Time: 2.4 },
        { date: '2024-04-07', avgTime: 1.0, p95Time: 2.0 },
      ],
      searchAccuracy: [
        { type: '向量搜索', accuracy: 85.6, count: 5678 },
        { type: '图谱搜索', accuracy: 78.9, count: 3456 },
        { type: '混合搜索', accuracy: 91.2, count: 6538 }
      ]
    }
  };

  const currentStats = statsData || mockStats;

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleExport = () => {
    // 导出数据逻辑
    const data = {
      timestamp: new Date().toISOString(),
      stats: currentStats
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-2">
            数据分析
          </Title>
          <Text type="secondary">
            系统使用情况分析和性能监控
          </Text>
        </div>
        
        <Space>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            placeholder={['开始日期', '结束日期']}
          />
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出数据
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={statsLoading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 核心指标概览 */}
      <Row gutter={16}>
        <Col span={4}>
          <Card>
            <Statistic
              title="总用户数"
              value={currentStats.overview.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="总文档数"
              value={currentStats.overview.totalDocuments}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="总对话数"
              value={currentStats.overview.totalConversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="总搜索数"
              value={currentStats.overview.totalSearches}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={currentStats.overview.avgResponseTime}
              suffix="s"
              precision={1}
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="系统可用率"
              value={currentStats.overview.systemUptime}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 详细分析 */}
      <Card>
        <Tabs defaultActiveKey="trends">
          {/* 趋势分析 */}
          <TabPane tab={<span><LineChartOutlined />趋势分析</span>} key="trends">
            <Row gutter={16}>
              <Col span={12}>
                <Card title="用户增长趋势" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={currentStats.trends.userGrowth}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Line type="monotone" dataKey="users" stroke="#8884d8" name="用户数" />
                      <Line type="monotone" dataKey="documents" stroke="#82ca9d" name="文档数" />
                      <Line type="monotone" dataKey="conversations" stroke="#ffc658" name="对话数" />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="每日活动分布" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={currentStats.trends.dailyActivity}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Area type="monotone" dataKey="searches" stackId="1" stroke="#8884d8" fill="#8884d8" name="搜索" />
                      <Area type="monotone" dataKey="conversations" stackId="1" stroke="#82ca9d" fill="#82ca9d" name="对话" />
                    </AreaChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* 分布分析 */}
          <TabPane tab={<span><PieChartOutlined />分布分析</span>} key="distribution">
            <Row gutter={16}>
              <Col span={8}>
                <Card title="文档类型分布" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={currentStats.distribution.documentTypes}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {currentStats.distribution.documentTypes.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col span={8}>
                <Card title="知识库使用情况" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={currentStats.distribution.knowledgeBases}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="documents" fill="#8884d8" name="文档数" />
                      <Bar dataKey="conversations" fill="#82ca9d" name="对话数" />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col span={8}>
                <Card title="用户活跃度分布" size="small">
                  <div className="space-y-4">
                    {currentStats.distribution.userActivity.map((item, index) => (
                      <div key={index}>
                        <div className="flex justify-between mb-1">
                          <Text>{item.level}</Text>
                          <Text>{item.count} 人 ({item.percentage}%)</Text>
                        </div>
                        <Progress 
                          percent={item.percentage} 
                          size="small"
                          strokeColor={
                            item.level === '高活跃' ? '#52c41a' :
                            item.level === '中活跃' ? '#faad14' : '#ff4d4f'
                          }
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* 性能分析 */}
          <TabPane tab={<span><BarChartOutlined />性能分析</span>} key="performance">
            <Row gutter={16}>
              <Col span={12}>
                <Card title="响应时间趋势" size="small">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={currentStats.performance.responseTime}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Line type="monotone" dataKey="avgTime" stroke="#8884d8" name="平均响应时间" />
                      <Line type="monotone" dataKey="p95Time" stroke="#82ca9d" name="P95响应时间" />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="搜索准确率" size="small">
                  <div className="space-y-4">
                    {currentStats.performance.searchAccuracy.map((item, index) => (
                      <div key={index} className="border-b pb-3 last:border-b-0">
                        <div className="flex justify-between items-center mb-2">
                          <Text strong>{item.type}</Text>
                          <div className="flex items-center space-x-2">
                            <Tag color="blue">{item.count} 次</Tag>
                            <Text>{item.accuracy}%</Text>
                          </div>
                        </div>
                        <Progress 
                          percent={item.accuracy} 
                          size="small"
                          strokeColor={
                            item.accuracy >= 90 ? '#52c41a' :
                            item.accuracy >= 80 ? '#faad14' : '#ff4d4f'
                          }
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* 详细报表 */}
          <TabPane tab="详细报表" key="reports">
            <Row gutter={16}>
              <Col span={24}>
                <Card title="热门搜索关键词" size="small">
                  <Table
                    size="small"
                    columns={[
                      { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
                      { title: '搜索次数', dataIndex: 'count', key: 'count', sorter: true },
                      { title: '平均相关度', dataIndex: 'relevance', key: 'relevance', render: (val) => `${val}%` },
                      { title: '趋势', dataIndex: 'trend', key: 'trend', render: (val) => (
                        <Tag color={val > 0 ? 'green' : val < 0 ? 'red' : 'default'}>
                          {val > 0 ? '↑' : val < 0 ? '↓' : '→'} {Math.abs(val)}%
                        </Tag>
                      )}
                    ]}
                    dataSource={[
                      { key: 1, keyword: 'API文档', count: 1234, relevance: 92, trend: 15 },
                      { key: 2, keyword: '用户指南', count: 987, relevance: 88, trend: 8 },
                      { key: 3, keyword: '故障排除', count: 756, relevance: 85, trend: -3 },
                      { key: 4, keyword: '配置说明', count: 654, relevance: 90, trend: 12 },
                      { key: 5, keyword: '最佳实践', count: 543, relevance: 87, trend: 5 },
                    ]}
                    pagination={{ pageSize: 10 }}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
