import React from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Tag, Avatar, Button, Space } from 'antd'
import {
  MessageOutlined,
  UserOutlined,
  ClockCircleOutlined,
  SmileOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ProjectOutlined,
  MoreOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../store/auth'
import type { ColumnsType } from 'antd/es/table'

interface ConversationData {
  key: string
  id: string
  user: string
  status: 'active' | 'waiting' | 'closed'
  messages: number
  startTime: string
  agent: string
}

interface ProjectData {
  key: string
  id: string
  name: string
  description: string
  status: 'active' | 'inactive' | 'maintenance'
  createTime: string
}

const Dashboard: React.FC = () => {
  const { t } = useTranslation()
  const { user } = useAuthStore()

  // 统计数据
  const statisticData = [
    {
      id: 0,
      label: t('dashboard.projectCount'),
      value: '25',
    },
    {
      id: 1,
      label: t('dashboard.pendingTasks'),
      value: '4/16',
    },
    {
      id: 2,
      label: t('dashboard.messageCount'),
      value: '12',
    },
  ]

  // 项目数据
  const projectData: ProjectData[] = Array.from({ length: 9 }, (_, i) => ({
    key: `project-${i + 1}`,
    id: `PROJ${String(i + 1).padStart(3, '0')}`,
    name: 'Vue FastAPI Admin',
    description: '一个基于 Vue3.0、FastAPI、Naive UI 的轻量级后台管理模板',
    status: i % 3 === 0 ? 'active' : i % 3 === 1 ? 'inactive' : 'maintenance',
    createTime: '2024-01-15',
  }))

  // 模拟数据
  const conversationData: ConversationData[] = [
    {
      key: '1',
      id: 'CONV001',
      user: '张三',
      status: 'active',
      messages: 15,
      startTime: '2024-01-15 10:30',
      agent: '客服小王',
    },
    {
      key: '2',
      id: 'CONV002',
      user: '李四',
      status: 'waiting',
      messages: 3,
      startTime: '2024-01-15 11:15',
      agent: '-',
    },
    {
      key: '3',
      id: 'CONV003',
      user: '王五',
      status: 'closed',
      messages: 28,
      startTime: '2024-01-15 09:45',
      agent: '客服小李',
    },
  ]

  const columns: ColumnsType<ConversationData> = [
    {
      title: '会话ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          active: { color: 'green', text: '进行中' },
          waiting: { color: 'orange', text: '等待中' },
          closed: { color: 'default', text: '已结束' },
        }
        const { color, text } = statusMap[status as keyof typeof statusMap]
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '消息数',
      dataIndex: 'messages',
      key: 'messages',
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
    },
    {
      title: '客服',
      dataIndex: 'agent',
      key: 'agent',
    },
  ]

  return (
    <div className="space-y-6">
      {/* 用户欢迎卡片 */}
      <Card className="rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Avatar size={60} src={user?.avatar} icon={<UserOutlined />} />
            <div className="ml-4">
              <p className="text-xl font-semibold">
                {t('dashboard.hello', { username: user?.username || '用户' })}
              </p>
              <p className="mt-1 text-sm text-gray-600">{t('dashboard.welcomeMessage')}</p>
            </div>
          </div>
          <Space size={24}>
            {statisticData.map((item) => (
              <Statistic
                key={item.id}
                title={item.label}
                value={item.value}
                valueStyle={{ fontSize: '18px', fontWeight: 'bold' }}
              />
            ))}
          </Space>
        </div>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.totalConversations')}
              value={1234}
              prefix={<MessageOutlined />}
              suffix={
                <span className="text-green-500 text-sm ml-2">
                  <ArrowUpOutlined /> 12%
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.activeUsers')}
              value={89}
              prefix={<UserOutlined />}
              suffix={
                <span className="text-green-500 text-sm ml-2">
                  <ArrowUpOutlined /> 8%
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.avgResponseTime')}
              value={2.3}
              precision={1}
              suffix="分钟"
              prefix={<ClockCircleOutlined />}
              valueStyle={{
                color: '#52c41a',
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.satisfactionRate')}
              value={95.6}
              precision={1}
              suffix="%"
              prefix={<SmileOutlined />}
              valueStyle={{
                color: '#1890ff',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表和表格 */}
      <Row gutter={[16, 16]}>
        {/* 系统状态 */}
        <Col xs={24} lg={8}>
          <Card title={t('dashboard.systemStatus')} className="h-96">
            <div className="space-y-4">
              <div>
                <div className="flex-between mb-2">
                  <span>{t('dashboard.cpuUsage')}</span>
                  <span>45%</span>
                </div>
                <Progress percent={45} status="active" />
              </div>
              <div>
                <div className="flex-between mb-2">
                  <span>{t('dashboard.memoryUsage')}</span>
                  <span>67%</span>
                </div>
                <Progress percent={67} status="active" />
              </div>
              <div>
                <div className="flex-between mb-2">
                  <span>{t('dashboard.diskUsage')}</span>
                  <span>23%</span>
                </div>
                <Progress percent={23} />
              </div>
              <div>
                <div className="flex-between mb-2">
                  <span>{t('dashboard.networkLatency')}</span>
                  <span>12ms</span>
                </div>
                <Progress percent={88} strokeColor="#52c41a" />
              </div>
            </div>
          </Card>
        </Col>

        {/* 最近会话 */}
        <Col xs={24} lg={16}>
          <Card title={t('dashboard.recentConversations')} className="h-96">
            <Table
              columns={columns}
              dataSource={conversationData}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      <Card 
        title={(
          <div className="flex items-center">
            <ProjectOutlined className="mr-2" />
            {t('dashboard.projectList')}
          </div>
        )}
        extra={<Button type="link" icon={<MoreOutlined />}>{t('dashboard.more')}</Button>}
        className="rounded-lg"
      >
        <Row gutter={[16, 16]}>
          {projectData.map((project) => {
            const statusMap = {
              active: { color: 'green', text: t('dashboard.running') },
              inactive: { color: 'default', text: t('dashboard.stopped') },
              maintenance: { color: 'orange', text: t('dashboard.maintenance') },
            }
            const { color, text } = statusMap[project.status]
            
            return (
              <Col xs={24} sm={12} lg={8} key={project.key}>
                <Card 
                  size="small" 
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  title={project.name}
                  extra={<Tag color={color}>{text}</Tag>}
                >
                  <p className="text-gray-600 text-sm mb-2">{project.description}</p>
                  <p className="text-xs text-gray-400">{t('dashboard.createTime')}: {project.createTime}</p>
                </Card>
              </Col>
            )
          })}
        </Row>
      </Card>
    </div>
  )
}

export default Dashboard