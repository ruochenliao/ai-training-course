import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  DatePicker,
  Select,
  Space,
  Typography,
  Table,
  Tag,
  Progress,
  List,
  Avatar,
  Button,
  Tooltip,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  UserOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  SmileOutlined,
  TeamOutlined,
  TrophyOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { StateWrapper } from '../components/common/LoadingEmpty';
import { useRequest } from '../hooks/useRequest';
import { analyticsApi } from '../api/analytics';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 统计数据接口
interface StatisticsData {
  totalSessions: number;
  totalMessages: number;
  avgResponseTime: number;
  satisfactionRate: number;
  activeAgents: number;
  resolvedSessions: number;
  pendingSessions: number;
  transferredSessions: number;
  // 趋势数据
  sessionsTrend: number;
  messagesTrend: number;
  responseTimeTrend: number;
  satisfactionTrend: number;
}

// 图表数据接口
interface ChartData {
  sessionTrend: Array<{ date: string; sessions: number; messages: number }>;
  responseTimeChart: Array<{ hour: string; avgTime: number; count: number }>;
  satisfactionChart: Array<{ date: string; rate: number; total: number }>;
  channelDistribution: Array<{ channel: string; count: number; percentage: number }>;
  agentPerformance: Array<{
    agentId: string;
    agentName: string;
    sessions: number;
    avgResponseTime: number;
    satisfaction: number;
    efficiency: number;
  }>;
}

// 热门问题接口
interface PopularIssue {
  id: string;
  question: string;
  category: string;
  count: number;
  trend: number;
  avgResolutionTime: number;
}

// 客服排行接口
interface AgentRanking {
  agentId: string;
  agentName: string;
  avatar?: string;
  sessionsHandled: number;
  avgResponseTime: number;
  satisfactionRate: number;
  efficiency: number;
  rank: number;
  change: number;
}

const Analytics: React.FC = () => {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(7, 'day'),
    dayjs(),
  ]);
  const [timeGranularity, setTimeGranularity] = useState<'hour' | 'day' | 'week' | 'month'>('day');

  // 获取统计数据
  const {
    data: statistics,
    loading: statisticsLoading,
    error: statisticsError,
    run: fetchStatistics,
  } = useRequest(analyticsApi.getStatistics, {
    defaultParams: [{
      startDate: dateRange[0].format('YYYY-MM-DD'),
      endDate: dateRange[1].format('YYYY-MM-DD'),
    }],
  });

  // 获取图表数据
  const {
    data: chartData,
    loading: chartLoading,
    error: chartError,
    run: fetchChartData,
  } = useRequest(analyticsApi.getChartData, {
    defaultParams: [{
      startDate: dateRange[0].format('YYYY-MM-DD'),
      endDate: dateRange[1].format('YYYY-MM-DD'),
      granularity: timeGranularity,
    }],
  });

  // 获取热门问题
  const {
    data: popularIssues = [],
    loading: issuesLoading,
    run: fetchPopularIssues,
  } = useRequest(analyticsApi.getPopularIssues, {
    defaultParams: [{
      startDate: dateRange[0].format('YYYY-MM-DD'),
      endDate: dateRange[1].format('YYYY-MM-DD'),
      limit: 10,
    }],
  });

  // 获取客服排行
  const {
    data: agentRankings = [],
    loading: rankingsLoading,
    run: fetchAgentRankings,
  } = useRequest(analyticsApi.getAgentRankings, {
    defaultParams: [{
      startDate: dateRange[0].format('YYYY-MM-DD'),
      endDate: dateRange[1].format('YYYY-MM-DD'),
      limit: 10,
    }],
  });

  // 刷新所有数据
  const refreshData = () => {
    const params = {
      startDate: dateRange[0].format('YYYY-MM-DD'),
      endDate: dateRange[1].format('YYYY-MM-DD'),
    };
    fetchStatistics(params);
    fetchChartData({ ...params, granularity: timeGranularity });
    fetchPopularIssues({ ...params, limit: 10 });
    fetchAgentRankings({ ...params, limit: 10 });
  };

  // 导出报告
  const exportReport = () => {
    // 这里可以调用导出API
    console.log('Export report for:', dateRange);
  };

  // 日期范围变化
  const handleDateRangeChange = (dates: any) => {
    if (dates) {
      setDateRange(dates);
    }
  };

  // 时间粒度变化
  const handleGranularityChange = (value: string) => {
    setTimeGranularity(value as any);
  };

  useEffect(() => {
    refreshData();
  }, [dateRange, timeGranularity]);

  // 获取趋势图标
  const getTrendIcon = (trend: number) => {
    if (trend > 0) {
      return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
    } else if (trend < 0) {
      return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />;
    }
    return null;
  };

  // 获取趋势颜色
  const getTrendColor = (trend: number) => {
    if (trend > 0) return '#52c41a';
    if (trend < 0) return '#ff4d4f';
    return '#666';
  };

  // 热门问题表格列
  const issueColumns = [
    {
      title: t('analytics.question'),
      dataIndex: 'question',
      key: 'question',
      ellipsis: true,
    },
    {
      title: t('analytics.category'),
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => <Tag>{category}</Tag>,
    },
    {
      title: t('analytics.count'),
      dataIndex: 'count',
      key: 'count',
      sorter: (a: PopularIssue, b: PopularIssue) => a.count - b.count,
    },
    {
      title: t('analytics.trend'),
      dataIndex: 'trend',
      key: 'trend',
      render: (trend: number) => (
        <Space>
          {getTrendIcon(trend)}
          <Text style={{ color: getTrendColor(trend) }}>
            {trend > 0 ? '+' : ''}{trend}%
          </Text>
        </Space>
      ),
    },
    {
      title: t('analytics.avgResolutionTime'),
      dataIndex: 'avgResolutionTime',
      key: 'avgResolutionTime',
      render: (time: number) => `${time}${t('common.minutes')}`,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面头部 */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>
          {t('analytics.title')}
        </Title>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={handleDateRangeChange}
            format="YYYY-MM-DD"
          />
          <Select
            value={timeGranularity}
            onChange={handleGranularityChange}
            style={{ width: 120 }}
          >
            <Option value="hour">{t('analytics.hour')}</Option>
            <Option value="day">{t('analytics.day')}</Option>
            <Option value="week">{t('analytics.week')}</Option>
            <Option value="month">{t('analytics.month')}</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={refreshData}>
            {t('common.refresh')}
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={exportReport}>
            {t('analytics.export')}
          </Button>
        </Space>
      </div>

      <StateWrapper
        loading={statisticsLoading}
        error={statisticsError}
        onRetry={refreshData}
      >
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('analytics.totalSessions')}
                value={statistics?.totalSessions || 0}
                prefix={<MessageOutlined />}
                suffix={
                  <Space>
                    {getTrendIcon(statistics?.sessionsTrend || 0)}
                    <Text style={{ color: getTrendColor(statistics?.sessionsTrend || 0), fontSize: '14px' }}>
                      {statistics?.sessionsTrend || 0}%
                    </Text>
                  </Space>
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('analytics.totalMessages')}
                value={statistics?.totalMessages || 0}
                prefix={<UserOutlined />}
                suffix={
                  <Space>
                    {getTrendIcon(statistics?.messagesTrend || 0)}
                    <Text style={{ color: getTrendColor(statistics?.messagesTrend || 0), fontSize: '14px' }}>
                      {statistics?.messagesTrend || 0}%
                    </Text>
                  </Space>
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('analytics.avgResponseTime')}
                value={statistics?.avgResponseTime || 0}
                precision={1}
                suffix={t('common.seconds')}
                prefix={<ClockCircleOutlined />}
                valueStyle={{
                  color: (statistics?.avgResponseTime || 0) < 30 ? '#52c41a' : '#ff4d4f',
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('analytics.satisfactionRate')}
                value={statistics?.satisfactionRate || 0}
                precision={1}
                suffix="%"
                prefix={<SmileOutlined />}
                valueStyle={{
                  color: (statistics?.satisfactionRate || 0) > 80 ? '#52c41a' : '#ff4d4f',
                }}
              />
            </Card>
          </Col>
        </Row>

        {/* 详细统计 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={8}>
            <Card title={t('analytics.sessionStatus')} size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>{t('analytics.resolved')}</Text>
                  <Text strong>{statistics?.resolvedSessions || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>{t('analytics.pending')}</Text>
                  <Text strong>{statistics?.pendingSessions || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>{t('analytics.transferred')}</Text>
                  <Text strong>{statistics?.transferredSessions || 0}</Text>
                </div>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card title={t('analytics.activeAgents')} size="small">
              <Statistic
                value={statistics?.activeAgents || 0}
                prefix={<TeamOutlined />}
                suffix={`/ ${agentRankings.length}`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card title={t('analytics.efficiency')} size="small">
              <Progress
                type="circle"
                percent={Math.round((statistics?.satisfactionRate || 0))}
                format={(percent) => `${percent}%`}
                size={80}
              />
            </Card>
          </Col>
        </Row>

        {/* 图表区域 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} lg={12}>
            <Card title={t('analytics.sessionTrend')} loading={chartLoading}>
              {/* 这里可以集成图表库如 ECharts 或 Chart.js */}
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Text type="secondary">{t('analytics.chartPlaceholder')}</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title={t('analytics.responseTimeChart')} loading={chartLoading}>
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Text type="secondary">{t('analytics.chartPlaceholder')}</Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 热门问题和客服排行 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={14}>
            <Card title={t('analytics.popularIssues')} loading={issuesLoading}>
              <Table
                dataSource={popularIssues}
                columns={issueColumns}
                rowKey="id"
                pagination={{ pageSize: 5, showSizeChanger: false }}
                size="small"
              />
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title={t('analytics.agentRankings')} loading={rankingsLoading}>
              <List
                dataSource={agentRankings.slice(0, 5)}
                renderItem={(agent, index) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <div style={{ position: 'relative' }}>
                          <Avatar src={agent.avatar} icon={<UserOutlined />} />
                          {index < 3 && (
                            <div
                              style={{
                                position: 'absolute',
                                top: -5,
                                right: -5,
                                background: index === 0 ? '#ffd700' : index === 1 ? '#c0c0c0' : '#cd7f32',
                                borderRadius: '50%',
                                width: 20,
                                height: 20,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '12px',
                                color: 'white',
                              }}
                            >
                              {index + 1}
                            </div>
                          )}
                        </div>
                      }
                      title={
                        <Space>
                          <Text strong>{agent.agentName}</Text>
                          {agent.change !== 0 && (
                            <Tooltip title={`${t('analytics.rankChange')}: ${agent.change > 0 ? '+' : ''}${agent.change}`}>
                              {getTrendIcon(agent.change)}
                            </Tooltip>
                          )}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">
                            {t('analytics.sessions')}: {agent.sessionsHandled}
                          </Text>
                          <Text type="secondary">
                            {t('analytics.satisfaction')}: {agent.satisfactionRate}%
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </StateWrapper>
    </div>
  );
};

export default Analytics;