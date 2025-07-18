import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Button,
  Space,
  Select,
  DatePicker,
  Alert,
  Tag,
  Tooltip,
  Spin
} from 'antd'
import {
  DashboardOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  ReloadOutlined,
  DownloadOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { Line, Column, Gauge, Area } from '@ant-design/plots'
import './PerformanceDashboard.css'

const { RangePicker } = DatePicker
const { Option } = Select

interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  network: number
  responseTime: number
  throughput: number
  errorRate: number
  activeUsers: number
}

interface PerformanceData {
  timestamp: string
  responseTime: number
  throughput: number
  errorRate: number
  cpuUsage: number
  memoryUsage: number
}

const PerformanceDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])
  const [timeRange, setTimeRange] = useState<string>('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    loadMetrics()
    loadPerformanceData()
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadMetrics()
        loadPerformanceData()
      }, 30000) // 30秒刷新一次
      
      return () => clearInterval(interval)
    }
  }, [timeRange, autoRefresh])

  const loadMetrics = async () => {
    try {
      // 模拟API调用
      const mockMetrics: SystemMetrics = {
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        disk: Math.random() * 100,
        network: Math.random() * 100,
        responseTime: Math.random() * 2000 + 100,
        throughput: Math.random() * 1000 + 500,
        errorRate: Math.random() * 5,
        activeUsers: Math.floor(Math.random() * 500 + 100)
      }
      
      setMetrics(mockMetrics)
    } catch (error) {
      console.error('加载系统指标失败:', error)
    }
  }

  const loadPerformanceData = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      const mockData: PerformanceData[] = Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
        responseTime: Math.random() * 1000 + 200,
        throughput: Math.random() * 800 + 400,
        errorRate: Math.random() * 3,
        cpuUsage: Math.random() * 80 + 10,
        memoryUsage: Math.random() * 70 + 20
      }))
      
      setPerformanceData(mockData)
    } catch (error) {
      console.error('加载性能数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return '#ff4d4f'
    if (value >= thresholds.warning) return '#faad14'
    return '#52c41a'
  }

  const getStatusIcon = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return <WarningOutlined style={{ color: '#ff4d4f' }} />
    if (value >= thresholds.warning) return <WarningOutlined style={{ color: '#faad14' }} />
    return <CheckCircleOutlined style={{ color: '#52c41a' }} />
  }

  // 响应时间图表配置
  const responseTimeConfig = {
    data: performanceData,
    xField: 'timestamp',
    yField: 'responseTime',
    smooth: true,
    color: '#1890ff',
    point: {
      size: 3,
      shape: 'circle',
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: '响应时间',
        value: `${datum.responseTime.toFixed(2)}ms`
      })
    },
    xAxis: {
      type: 'time',
      tickCount: 6,
    },
    yAxis: {
      label: {
        formatter: (v: string) => `${v}ms`
      }
    }
  }

  // 吞吐量图表配置
  const throughputConfig = {
    data: performanceData,
    xField: 'timestamp',
    yField: 'throughput',
    color: '#52c41a',
    columnWidthRatio: 0.8,
    tooltip: {
      formatter: (datum: any) => ({
        name: '吞吐量',
        value: `${datum.throughput.toFixed(0)} req/s`
      })
    },
    xAxis: {
      type: 'time',
      tickCount: 6,
    },
    yAxis: {
      label: {
        formatter: (v: string) => `${v} req/s`
      }
    }
  }

  // CPU使用率仪表盘配置
  const cpuGaugeConfig = {
    percent: (metrics?.cpu || 0) / 100,
    color: getStatusColor(metrics?.cpu || 0, { warning: 70, critical: 90 }),
    innerRadius: 0.75,
    radius: 0.95,
    startAngle: Math.PI,
    endAngle: 2 * Math.PI,
    indicator: {
      pointer: {
        style: {
          stroke: '#D0D0D0',
        },
      },
      pin: {
        style: {
          stroke: '#D0D0D0',
        },
      },
    },
    statistic: {
      title: {
        formatter: () => 'CPU',
        style: {
          fontSize: '12px',
          color: '#666',
        },
      },
      content: {
        formatter: () => `${(metrics?.cpu || 0).toFixed(1)}%`,
        style: {
          fontSize: '16px',
          fontWeight: 'bold',
          color: getStatusColor(metrics?.cpu || 0, { warning: 70, critical: 90 }),
        },
      },
    },
  }

  // 内存使用率仪表盘配置
  const memoryGaugeConfig = {
    ...cpuGaugeConfig,
    percent: (metrics?.memory || 0) / 100,
    color: getStatusColor(metrics?.memory || 0, { warning: 80, critical: 95 }),
    statistic: {
      title: {
        formatter: () => '内存',
        style: {
          fontSize: '12px',
          color: '#666',
        },
      },
      content: {
        formatter: () => `${(metrics?.memory || 0).toFixed(1)}%`,
        style: {
          fontSize: '16px',
          fontWeight: 'bold',
          color: getStatusColor(metrics?.memory || 0, { warning: 80, critical: 95 }),
        },
      },
    },
  }

  // 系统资源使用情况表格
  const resourceColumns = [
    {
      title: '资源类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '当前使用率',
      dataIndex: 'usage',
      key: 'usage',
      render: (usage: number, record: any) => (
        <Space>
          <Progress
            percent={usage}
            size="small"
            strokeColor={getStatusColor(usage, record.thresholds)}
            style={{ width: 100 }}
          />
          <span>{usage.toFixed(1)}%</span>
          {getStatusIcon(usage, record.thresholds)}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'normal' ? 'green' : status === 'warning' ? 'orange' : 'red'}>
          {status === 'normal' ? '正常' : status === 'warning' ? '警告' : '严重'}
        </Tag>
      ),
    },
  ]

  const resourceData = metrics ? [
    {
      key: 'cpu',
      type: 'CPU',
      usage: metrics.cpu,
      status: metrics.cpu >= 90 ? 'critical' : metrics.cpu >= 70 ? 'warning' : 'normal',
      thresholds: { warning: 70, critical: 90 }
    },
    {
      key: 'memory',
      type: '内存',
      usage: metrics.memory,
      status: metrics.memory >= 95 ? 'critical' : metrics.memory >= 80 ? 'warning' : 'normal',
      thresholds: { warning: 80, critical: 95 }
    },
    {
      key: 'disk',
      type: '磁盘',
      usage: metrics.disk,
      status: metrics.disk >= 90 ? 'critical' : metrics.disk >= 80 ? 'warning' : 'normal',
      thresholds: { warning: 80, critical: 90 }
    },
    {
      key: 'network',
      type: '网络',
      usage: metrics.network,
      status: metrics.network >= 90 ? 'critical' : metrics.network >= 80 ? 'warning' : 'normal',
      thresholds: { warning: 80, critical: 90 }
    }
  ] : []

  return (
    <div className="performance-dashboard">
      {/* 控制面板 */}
      <Card className="control-panel" size="small">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Select value={timeRange} onChange={setTimeRange} style={{ width: 120 }}>
                <Option value="1h">最近1小时</Option>
                <Option value="6h">最近6小时</Option>
                <Option value="24h">最近24小时</Option>
                <Option value="7d">最近7天</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  loadMetrics()
                  loadPerformanceData()
                }}
              >
                刷新
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <span>自动刷新:</span>
              <Button
                type={autoRefresh ? 'primary' : 'default'}
                size="small"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? '开启' : '关闭'}
              </Button>
              <Button icon={<DownloadOutlined />}>导出报告</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={metrics?.responseTime || 0}
              precision={0}
              suffix="ms"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                color: getStatusColor(metrics?.responseTime || 0, { warning: 1000, critical: 2000 })
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统吞吐量"
              value={metrics?.throughput || 0}
              precision={0}
              suffix="req/s"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="错误率"
              value={metrics?.errorRate || 0}
              precision={2}
              suffix="%"
              prefix={<WarningOutlined />}
              valueStyle={{ 
                color: getStatusColor(metrics?.errorRate || 0, { warning: 1, critical: 5 })
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={metrics?.activeUsers || 0}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 系统资源监控 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="CPU使用率" size="small">
            {metrics && <Gauge {...cpuGaugeConfig} height={200} />}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="内存使用率" size="small">
            {metrics && <Gauge {...memoryGaugeConfig} height={200} />}
          </Card>
        </Col>
      </Row>

      {/* 性能趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="响应时间趋势" size="small">
            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px 0' }}>
                <Spin />
              </div>
            ) : (
              <Line {...responseTimeConfig} height={300} />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="吞吐量趋势" size="small">
            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px 0' }}>
                <Spin />
              </div>
            ) : (
              <Column {...throughputConfig} height={300} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 系统资源详情 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="系统资源使用情况" size="small">
            <Table
              columns={resourceColumns}
              dataSource={resourceData}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="系统状态" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {metrics && metrics.cpu >= 90 && (
                <Alert
                  message="CPU使用率过高"
                  description="当前CPU使用率超过90%，建议检查系统负载"
                  type="error"
                  showIcon
                />
              )}
              {metrics && metrics.memory >= 95 && (
                <Alert
                  message="内存使用率过高"
                  description="当前内存使用率超过95%，建议释放内存"
                  type="error"
                  showIcon
                />
              )}
              {metrics && metrics.errorRate >= 5 && (
                <Alert
                  message="错误率过高"
                  description="当前系统错误率超过5%，建议检查系统状态"
                  type="warning"
                  showIcon
                />
              )}
              {(!metrics || (metrics.cpu < 70 && metrics.memory < 80 && metrics.errorRate < 1)) && (
                <Alert
                  message="系统运行正常"
                  description="所有指标都在正常范围内"
                  type="success"
                  showIcon
                />
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default PerformanceDashboard
