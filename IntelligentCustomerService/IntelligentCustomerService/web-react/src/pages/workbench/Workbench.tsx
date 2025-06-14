import React, { useMemo } from 'react'
import { Avatar, Badge, Button, Card, Col, Progress, Row } from 'antd'
import {
  ArrowRightOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FallOutlined,
  MessageOutlined,
  RiseOutlined,
  TeamOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../store/auth'

// 企业级项目描述文本
const projectDescription = '基于 React + TypeScript + Ant Design 的现代化企业级管理平台'

const Workbench: React.FC = () => {
  const { t } = useTranslation()

  const { user } = useAuthStore()

  // 企业级统计数据
  const statisticData = useMemo(
    () => [
      {
        id: 0,
        title: '今日咨询',
        value: 1234,
        icon: <MessageOutlined style={{ color: '#1890ff' }} />,
        trend: 'up',
        trendValue: '12.5%',
        suffix: '次',
      },
      {
        id: 1,
        title: '处理完成',
        value: 987,
        icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        trend: 'up',
        trendValue: '8.2%',
        suffix: '次',
      },
      {
        id: 2,
        title: '待处理',
        value: 156,
        icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
        trend: 'down',
        trendValue: '3.1%',
        suffix: '次',
      },
      {
        id: 3,
        title: '客户满意度',
        value: 98.5,
        icon: <TrophyOutlined style={{ color: '#722ed1' }} />,
        trend: 'up',
        trendValue: '2.3%',
        suffix: '%',
      },
    ],
    [],
  )

  // 快捷操作数据
  const quickActions = useMemo(
    () => [
      { title: '新建工单', icon: <MessageOutlined />, color: '#1890ff' },
      { title: '客户管理', icon: <TeamOutlined />, color: '#52c41a' },
      { title: '数据报表', icon: <TrophyOutlined />, color: '#faad14' },
      { title: '系统设置', icon: <UserOutlined />, color: '#722ed1' },
    ],
    [],
  )

  // 用户头像 - 如果没有头像则使用默认头像
  const userAvatar = user?.avatar || 'https://api.dicebear.com/7.x/miniavs/svg?seed=1'
  const userName = user?.username || 'admin'

  return (
    <div className='enterprise-workbench'>
      {/* 欢迎横幅 */}
      <Card
        bordered={false}
        className='enterprise-welcome-card'
        style={{
          marginBottom: '24px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '12px',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* 左侧用户信息 */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Avatar
              size={64}
              src={userAvatar}
              icon={<UserOutlined />}
              style={{
                border: '3px solid rgba(255, 255, 255, 0.3)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              }}
            />
            <div style={{ marginLeft: '20px', color: '#ffffff' }}>
              <h2
                style={{
                  fontSize: '24px',
                  fontWeight: 600,
                  margin: 0,
                  color: '#ffffff',
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                }}
              >
                {t('workbench.text_hello', { username: userName })}
              </h2>
              <p
                style={{
                  fontSize: '16px',
                  margin: '8px 0 0 0',
                  color: 'rgba(255, 255, 255, 0.8)',
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
                }}
              >
                {t('workbench.text_welcome')}
              </p>
            </div>
          </div>

          {/* 右侧快捷操作 */}
          <div style={{ display: 'flex', gap: '12px' }}>
            {quickActions.map((action, index) => (
              <Button
                key={index}
                type='primary'
                ghost
                icon={action.icon}
                style={{
                  borderColor: 'rgba(255, 255, 255, 0.4)',
                  color: '#ffffff',
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                }}
              >
                {action.title}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* 数据统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        {statisticData.map((item) => (
          <Col xs={24} sm={12} lg={6} key={item.id}>
            <Card
              bordered={false}
              className='enterprise-stat-card'
              style={{
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                transition: 'all 0.3s ease',
              }}
              bodyStyle={{ padding: '24px' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ flex: 1 }}>
                  <p
                    style={{
                      fontSize: '14px',
                      color: '#8c8c8c',
                      margin: '0 0 8px 0',
                      fontWeight: 500,
                    }}
                  >
                    {item.title}
                  </p>
                  <h3
                    style={{
                      fontSize: '28px',
                      fontWeight: 600,
                      margin: '0 0 8px 0',
                      color: '#262626',
                    }}
                  >
                    {item.value}
                    <span style={{ fontSize: '16px', fontWeight: 400 }}>{item.suffix}</span>
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    {item.trend === 'up' ? (
                      <RiseOutlined style={{ color: '#52c41a', marginRight: '4px' }} />
                    ) : (
                      <FallOutlined style={{ color: '#ff4d4f', marginRight: '4px' }} />
                    )}
                    <span
                      style={{
                        fontSize: '12px',
                        color: item.trend === 'up' ? '#52c41a' : '#ff4d4f',
                        fontWeight: 500,
                      }}
                    >
                      {item.trendValue}
                    </span>
                    <span style={{ fontSize: '12px', color: '#8c8c8c', marginLeft: '4px' }}>vs 昨日</span>
                  </div>
                </div>
                <div
                  style={{
                    fontSize: '32px',
                    opacity: 0.8,
                  }}
                >
                  {item.icon}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 项目展示区域 */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{t('workbench.label_project')}</span>
            <Button type='link' icon={<ArrowRightOutlined />}>
              {t('workbench.label_more')}
            </Button>
          </div>
        }
        bordered={false}
        style={{ borderRadius: '12px' }}
        bodyStyle={{ padding: '24px' }}
      >
        <Row gutter={[24, 24]}>
          {Array.from({ length: 6 }, (_, i) => (
            <Col xs={24} sm={12} lg={8} key={i + 1}>
              <Card
                hoverable
                className='enterprise-project-card'
                style={{
                  borderRadius: '8px',
                  border: '1px solid #f0f0f0',
                  transition: 'all 0.3s ease',
                }}
                bodyStyle={{ padding: '20px' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '8px',
                      background: `linear-gradient(135deg, ${['#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96', '#13c2c2'][i % 6]} 0%, ${['#096dd9', '#389e0d', '#d48806', '#531dab', '#c41d7f', '#08979c'][i % 6]} 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '12px',
                      flexShrink: 0,
                    }}
                  >
                    <span style={{ color: '#ffffff', fontSize: '18px', fontWeight: 600 }}>{String.fromCharCode(65 + i)}</span>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h4
                      style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        margin: '0 0 4px 0',
                        color: '#262626',
                      }}
                    >
                      智能客服系统 v{i + 1}.0
                    </h4>
                    <Badge
                      status={i % 3 === 0 ? 'success' : i % 3 === 1 ? 'processing' : 'warning'}
                      text={i % 3 === 0 ? '运行中' : i % 3 === 1 ? '开发中' : '测试中'}
                      style={{ fontSize: '12px' }}
                    />
                  </div>
                </div>
                <p
                  style={{
                    fontSize: '14px',
                    color: '#8c8c8c',
                    margin: '0 0 16px 0',
                    lineHeight: '20px',
                  }}
                >
                  {projectDescription}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ fontSize: '12px', color: '#8c8c8c' }}>更新于 2024-01-{String(15 + i).padStart(2, '0')}</div>
                  <Progress
                    percent={Math.floor(Math.random() * 40) + 60}
                    size='small'
                    style={{ width: '80px' }}
                    strokeColor={{
                      '0%': '#1890ff',
                      '100%': '#096dd9',
                    }}
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  )
}

export default Workbench
