import React from 'react'
import { Alert, Button, Card, Col, Divider, Row, Tag, Typography } from 'antd'
import {
  AppstoreOutlined,
  DashboardOutlined,
  FileTextOutlined,
  SafetyOutlined,
  SettingOutlined,
  TeamOutlined,
  ToolOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Icon } from '@iconify/react'

const { Title, Paragraph, Text } = Typography

/**
 * 一级菜单页面 - 对应API中的 "/top-menu" 路径
 * 展示系统的主要功能模块和快捷入口
 */
const TopMenu: React.FC = () => {
  // 主要功能模块
  const mainModules = [
    {
      title: '工作台',
      description: '系统概览和数据统计',
      icon: <DashboardOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
      path: '/dashboard/workbench',
      color: '#1890ff',
      features: ['数据统计', '快捷操作', '系统概览'],
    },
    {
      title: '系统管理',
      description: '用户、角色、权限管理',
      icon: <SettingOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
      path: '/dashboard/system/user',
      color: '#52c41a',
      features: ['用户管理', '角色管理', '菜单管理'],
    },
    {
      title: '个人中心',
      description: '个人信息和设置',
      icon: <UserOutlined style={{ fontSize: '32px', color: '#faad14' }} />,
      path: '/dashboard/profile',
      color: '#faad14',
      features: ['个人信息', '密码修改', '偏好设置'],
    },
    {
      title: '帮助文档',
      description: '系统使用说明和帮助',
      icon: <FileTextOutlined style={{ fontSize: '32px', color: '#722ed1' }} />,
      path: '/dashboard/help',
      color: '#722ed1',
      features: ['使用指南', '常见问题', '联系支持'],
    },
  ]

  // 快捷功能
  const quickActions = [
    { title: '新建用户', icon: <TeamOutlined />, action: () => console.log('新建用户') },
    { title: '系统设置', icon: <ToolOutlined />, action: () => console.log('系统设置') },
    { title: '安全中心', icon: <SafetyOutlined />, action: () => console.log('安全中心') },
    { title: '应用管理', icon: <AppstoreOutlined />, action: () => console.log('应用管理') },
  ]

  const handleModuleClick = (path: string) => {
    window.location.href = path
  }

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <Title level={1} style={{ marginBottom: '8px' }}>
          <Icon icon='material-symbols:featured-play-list-outline' style={{ marginRight: '12px', color: '#1890ff' }} />
          一级菜单
        </Title>
        <Paragraph style={{ fontSize: '16px', color: '#666' }}>系统主要功能模块导航，提供快捷访问入口</Paragraph>
      </div>

      {/* 功能提示 */}
      <Alert
        message='功能导航'
        description='这是一个一级菜单页面，展示了系统的主要功能模块。您可以点击下方的模块卡片快速访问相应功能。'
        type='info'
        showIcon
        style={{ marginBottom: '32px' }}
      />

      {/* 主要功能模块 */}
      <Title level={2} style={{ marginBottom: '24px' }}>
        <AppstoreOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
        主要功能模块
      </Title>

      <Row gutter={[24, 24]} style={{ marginBottom: '48px' }}>
        {mainModules.map((module, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card
              hoverable
              style={{
                height: '280px',
                borderRadius: '12px',
                border: `2px solid ${module.color}20`,
                transition: 'all 0.3s ease',
              }}
              bodyStyle={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
              }}
              onClick={() => handleModuleClick(module.path)}
            >
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>{module.icon}</div>

              <Title level={4} style={{ textAlign: 'center', marginBottom: '12px' }}>
                {module.title}
              </Title>

              <Paragraph
                style={{
                  textAlign: 'center',
                  color: '#666',
                  marginBottom: '16px',
                  flex: 1,
                }}
              >
                {module.description}
              </Paragraph>

              <div style={{ marginBottom: '16px' }}>
                <Text strong style={{ fontSize: '12px', color: '#999' }}>
                  主要功能：
                </Text>
                <div style={{ marginTop: '8px' }}>
                  {module.features.map((feature, idx) => (
                    <Tag
                      key={idx}
                      color={module.color}
                      style={{
                        margin: '2px',
                        fontSize: '11px',
                      }}
                    >
                      {feature}
                    </Tag>
                  ))}
                </div>
              </div>

              <Button
                type='primary'
                block
                style={{
                  backgroundColor: module.color,
                  borderColor: module.color,
                }}
              >
                进入模块
              </Button>
            </Card>
          </Col>
        ))}
      </Row>

      <Divider />

      {/* 快捷操作 */}
      <Title level={2} style={{ marginBottom: '24px' }}>
        <ToolOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
        快捷操作
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        {quickActions.map((action, index) => (
          <Col xs={12} sm={6} lg={3} key={index}>
            <Card
              hoverable
              size='small'
              style={{
                textAlign: 'center',
                borderRadius: '8px',
                transition: 'all 0.3s ease',
              }}
              bodyStyle={{ padding: '16px' }}
              onClick={action.action}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px', color: '#1890ff' }}>{action.icon}</div>
              <Text style={{ fontSize: '12px' }}>{action.title}</Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 系统信息 */}
      <Card title='系统信息' style={{ borderRadius: '12px' }} extra={<Tag color='green'>运行正常</Tag>}>
        <Row gutter={[24, 16]}>
          <Col xs={24} sm={8}>
            <Text strong>系统版本：</Text>
            <Text>v1.0.0</Text>
          </Col>
          <Col xs={24} sm={8}>
            <Text strong>最后更新：</Text>
            <Text>2024-12-19</Text>
          </Col>
          <Col xs={24} sm={8}>
            <Text strong>在线用户：</Text>
            <Text>12 人</Text>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default TopMenu
