import React, {useCallback, useEffect, useState} from 'react'
import {Avatar, Card, Col, DatePicker, message, Progress, Row, Select, Space, Spin, Statistic, Table, Tag} from 'antd'
import {
    CheckCircleOutlined,
    ClockCircleOutlined,
    FallOutlined,
    GlobalOutlined,
    MessageOutlined,
    PhoneOutlined,
    RiseOutlined,
    TeamOutlined,
    UserOutlined
} from '@ant-design/icons'
import {Area, Column, Line, Pie} from '@ant-design/plots'
import {AgentStats, customerServiceApi, SessionStats} from '@/api/customerService'
import {formatDuration} from '@/utils/time'
import dayjs, {Dayjs} from 'dayjs'
import './StatsDashboard.less'

interface StatsDashboardProps {
  agentId?: string // 如果指定了agentId，则显示该客服的统计数据
}

const { RangePicker } = DatePicker
const { Option } = Select

const StatsDashboard: React.FC<StatsDashboardProps> = ({ agentId }) => {
  const [loading, setLoading] = useState(false)
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(7, 'day'),
    dayjs()
  ])
  const [timeUnit, setTimeUnit] = useState<'hour' | 'day' | 'week' | 'month'>('day')
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null)
  const [agentStats, setAgentStats] = useState<AgentStats[]>([])
  const [trendData, setTrendData] = useState<any[]>([])
  const [categoryData, setCategoryData] = useState<any[]>([])
  const [satisfactionData, setSatisfactionData] = useState<any[]>([])
  const [responseTimeData, setResponseTimeData] = useState<any[]>([])

  // 加载统计数据
  const loadStats = useCallback(async () => {
    try {
      setLoading(true)
      const [startDate, endDate] = dateRange
      const params = {
        startDate: startDate.format('YYYY-MM-DD'),
        endDate: endDate.format('YYYY-MM-DD'),
        agentId,
        timeUnit
      }

      // 并行加载各种统计数据
      const [sessionStatsRes, agentStatsRes, trendRes, categoryRes, satisfactionRes, responseTimeRes] = await Promise.all([
        customerServiceApi.getSessionStats(params),
        agentId ? Promise.resolve([]) : customerServiceApi.getAgentStats(params),
        customerServiceApi.getSessionTrend(params),
        customerServiceApi.getCategoryStats(params),
        customerServiceApi.getSatisfactionStats(params),
        customerServiceApi.getResponseTimeStats(params)
      ])

      setSessionStats(sessionStatsRes)
      setAgentStats(agentStatsRes)
      setTrendData(trendRes)
      setCategoryData(categoryRes)
      setSatisfactionData(satisfactionRes)
      setResponseTimeData(responseTimeRes)
    } catch (error) {
      message.error('加载统计数据失败')
    } finally {
      setLoading(false)
    }
  }, [dateRange, timeUnit, agentId])

  // 格式化数值
  const formatNumber = useCallback((num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }, [])

  // 获取趋势图配置
  const getTrendConfig = useCallback(() => {
    return {
      data: trendData,
      xField: 'date',
      yField: 'count',
      seriesField: 'type',
      smooth: true,
      animation: {
        appear: {
          animation: 'path-in',
          duration: 1000
        }
      },
      color: ['#1890ff', '#52c41a', '#faad14', '#f5222d'],
      legend: {
        position: 'top' as const
      },
      tooltip: {
        formatter: (datum: any) => {
          return {
            name: datum.type,
            value: formatNumber(datum.count)
          }
        }
      }
    }
  }, [trendData, formatNumber])

  // 获取分类统计图配置
  const getCategoryConfig = useCallback(() => {
    return {
      data: categoryData,
      angleField: 'count',
      colorField: 'category',
      radius: 0.8,
      label: {
        type: 'outer',
        content: '{name} {percentage}'
      },
      interactions: [
        {
          type: 'element-selected'
        },
        {
          type: 'element-active'
        }
      ],
      statistic: {
        title: false,
        content: {
          style: {
            whiteSpace: 'pre-wrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          },
          content: '问题分类'
        }
      }
    }
  }, [categoryData])

  // 获取满意度统计图配置
  const getSatisfactionConfig = useCallback(() => {
    return {
      data: satisfactionData,
      xField: 'rating',
      yField: 'count',
      color: '#52c41a',
      columnWidthRatio: 0.6,
      meta: {
        rating: {
          alias: '满意度评分'
        },
        count: {
          alias: '数量'
        }
      },
      label: {
        position: 'middle' as const,
        style: {
          fill: '#FFFFFF',
          opacity: 0.6
        }
      }
    }
  }, [satisfactionData])

  // 获取响应时间图配置
  const getResponseTimeConfig = useCallback(() => {
    return {
      data: responseTimeData,
      xField: 'date',
      yField: 'avgResponseTime',
      smooth: true,
      color: '#722ed1',
      areaStyle: {
        fill: 'l(270) 0:#ffffff 0.5:#722ed1 1:#722ed1',
        opacity: 0.3
      },
      meta: {
        avgResponseTime: {
          alias: '平均响应时间(秒)'
        }
      }
    }
  }, [responseTimeData])

  // 客服排行表格列配置
  const agentColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank: number) => (
        <div className={`rank-badge rank-${rank <= 3 ? rank : 'other'}`}>
          {rank}
        </div>
      )
    },
    {
      title: '客服',
      dataIndex: 'agentName',
      key: 'agentName',
      render: (name: string, record: AgentStats) => (
        <div className="agent-info">
          <Avatar size="small" icon={<UserOutlined />} />
          <span className="agent-name">{name}</span>
          <Tag color={record.status === 'online' ? 'green' : 'default'} size="small">
            {record.status === 'online' ? '在线' : '离线'}
          </Tag>
        </div>
      )
    },
    {
      title: '处理会话',
      dataIndex: 'sessionCount',
      key: 'sessionCount',
      sorter: (a: AgentStats, b: AgentStats) => a.sessionCount - b.sessionCount,
      render: (count: number) => formatNumber(count)
    },
    {
      title: '平均响应时间',
      dataIndex: 'avgResponseTime',
      key: 'avgResponseTime',
      sorter: (a: AgentStats, b: AgentStats) => a.avgResponseTime - b.avgResponseTime,
      render: (time: number) => formatDuration(time)
    },
    {
      title: '满意度',
      dataIndex: 'satisfaction',
      key: 'satisfaction',
      sorter: (a: AgentStats, b: AgentStats) => a.satisfaction - b.satisfaction,
      render: (satisfaction: number) => (
        <div className="satisfaction-cell">
          <Progress
            percent={satisfaction * 20}
            size="small"
            strokeColor={satisfaction >= 4 ? '#52c41a' : satisfaction >= 3 ? '#faad14' : '#f5222d'}
            showInfo={false}
          />
          <span className="satisfaction-text">{satisfaction.toFixed(1)}</span>
        </div>
      )
    },
    {
      title: '工作时长',
      dataIndex: 'workDuration',
      key: 'workDuration',
      render: (duration: number) => formatDuration(duration)
    }
  ]

  // 初始化加载
  useEffect(() => {
    loadStats()
  }, [loadStats])

  return (
    <div className="stats-dashboard">
      <Spin spinning={loading}>
        {/* 筛选条件 */}
        <Card className="filter-card" size="small">
          <Space wrap>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates) {
                  setDateRange([dates[0]!, dates[1]!])
                }
              }}
              format="YYYY-MM-DD"
            />
            
            <Select
              value={timeUnit}
              onChange={setTimeUnit}
              style={{ width: 120 }}
            >
              <Option value="hour">按小时</Option>
              <Option value="day">按天</Option>
              <Option value="week">按周</Option>
              <Option value="month">按月</Option>
            </Select>
          </Space>
        </Card>

        {/* 核心指标 */}
        {sessionStats && (
          <Row gutter={[16, 16]} className="stats-overview">
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="总会话数"
                  value={sessionStats.totalSessions}
                  prefix={<MessageOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                  formatter={(value) => formatNumber(Number(value))}
                />
                <div className="stat-trend">
                  {sessionStats.sessionGrowth >= 0 ? (
                    <span className="trend-up">
                      <RiseOutlined /> +{sessionStats.sessionGrowth.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="trend-down">
                      <FallOutlined /> {sessionStats.sessionGrowth.toFixed(1)}%
                    </span>
                  )}
                </div>
              </Card>
            </Col>
            
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="活跃用户"
                  value={sessionStats.activeUsers}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                  formatter={(value) => formatNumber(Number(value))}
                />
                <div className="stat-trend">
                  {sessionStats.userGrowth >= 0 ? (
                    <span className="trend-up">
                      <RiseOutlined /> +{sessionStats.userGrowth.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="trend-down">
                      <FallOutlined /> {sessionStats.userGrowth.toFixed(1)}%
                    </span>
                  )}
                </div>
              </Card>
            </Col>
            
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="平均响应时间"
                  value={sessionStats.avgResponseTime}
                  prefix={<ClockCircleOutlined />}
                  suffix="秒"
                  valueStyle={{ color: '#faad14' }}
                />
                <div className="stat-trend">
                  {sessionStats.responseTimeImprovement >= 0 ? (
                    <span className="trend-up">
                      <RiseOutlined /> +{sessionStats.responseTimeImprovement.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="trend-down">
                      <FallOutlined /> {sessionStats.responseTimeImprovement.toFixed(1)}%
                    </span>
                  )}
                </div>
              </Card>
            </Col>
            
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="解决率"
                  value={sessionStats.resolutionRate * 100}
                  prefix={<CheckCircleOutlined />}
                  suffix="%"
                  precision={1}
                  valueStyle={{ color: '#722ed1' }}
                />
                <div className="stat-trend">
                  {sessionStats.resolutionImprovement >= 0 ? (
                    <span className="trend-up">
                      <RiseOutlined /> +{sessionStats.resolutionImprovement.toFixed(1)}%
                    </span>
                  ) : (
                    <span className="trend-down">
                      <FallOutlined /> {sessionStats.resolutionImprovement.toFixed(1)}%
                    </span>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        )}

        {/* 图表区域 */}
        <Row gutter={[16, 16]} className="charts-section">
          {/* 趋势图 */}
          <Col xs={24} lg={12}>
            <Card title="会话趋势" className="chart-card">
              {trendData.length > 0 ? (
                <Line {...getTrendConfig()} height={300} />
              ) : (
                <div className="empty-chart">暂无数据</div>
              )}
            </Card>
          </Col>
          
          {/* 问题分类 */}
          <Col xs={24} lg={12}>
            <Card title="问题分类分布" className="chart-card">
              {categoryData.length > 0 ? (
                <Pie {...getCategoryConfig()} height={300} />
              ) : (
                <div className="empty-chart">暂无数据</div>
              )}
            </Card>
          </Col>
          
          {/* 满意度分布 */}
          <Col xs={24} lg={12}>
            <Card title="满意度分布" className="chart-card">
              {satisfactionData.length > 0 ? (
                <Column {...getSatisfactionConfig()} height={300} />
              ) : (
                <div className="empty-chart">暂无数据</div>
              )}
            </Card>
          </Col>
          
          {/* 响应时间趋势 */}
          <Col xs={24} lg={12}>
            <Card title="响应时间趋势" className="chart-card">
              {responseTimeData.length > 0 ? (
                <Area {...getResponseTimeConfig()} height={300} />
              ) : (
                <div className="empty-chart">暂无数据</div>
              )}
            </Card>
          </Col>
        </Row>

        {/* 客服排行榜 */}
        {!agentId && agentStats.length > 0 && (
          <Card title="客服排行榜" className="agent-ranking-card">
            <Table
              dataSource={agentStats.map((agent, index) => ({
                ...agent,
                rank: index + 1,
                key: agent.agentId
              }))}
              columns={agentColumns}
              pagination={false}
              size="small"
              scroll={{ x: 800 }}
            />
          </Card>
        )}

        {/* 实时指标 */}
        <Row gutter={[16, 16]} className="realtime-section">
          <Col xs={24} sm={8}>
            <Card className="realtime-card">
              <div className="realtime-header">
                <TeamOutlined className="realtime-icon" />
                <span>在线客服</span>
              </div>
              <div className="realtime-value">
                {sessionStats?.onlineAgents || 0}
              </div>
              <div className="realtime-desc">当前在线</div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card className="realtime-card">
              <div className="realtime-header">
                <PhoneOutlined className="realtime-icon" />
                <span>排队用户</span>
              </div>
              <div className="realtime-value">
                {sessionStats?.queuedUsers || 0}
              </div>
              <div className="realtime-desc">等待接入</div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card className="realtime-card">
              <div className="realtime-header">
                <GlobalOutlined className="realtime-icon" />
                <span>活跃会话</span>
              </div>
              <div className="realtime-value">
                {sessionStats?.activeSessions || 0}
              </div>
              <div className="realtime-desc">进行中</div>
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  )
}

export default StatsDashboard