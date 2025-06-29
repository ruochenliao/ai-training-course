'use client';

import React from 'react';
import {useRouter} from 'next/navigation';
import {Button, Card, Col, Row, Statistic, Typography} from 'antd';
import {
    ApartmentOutlined,
    ArrowRightOutlined,
    SafetyOutlined,
    TeamOutlined,
    UserOutlined,
    UserSwitchOutlined,
} from '@ant-design/icons';
// import { motion } from 'framer-motion';

const { Title, Paragraph } = Typography;

export default function RBACOverviewPage() {
  const router = useRouter();

  const cards = [
    {
      title: '用户管理',
      description: '管理系统用户账户，配置用户信息',
      icon: <UserOutlined className="text-4xl text-indigo-500" />,
      path: '/admin/rbac/users',
      color: 'border-indigo-200 hover:border-indigo-400',
      bgColor: 'bg-indigo-50 hover:bg-indigo-100',
    },
    {
      title: '角色管理',
      description: '管理系统角色，配置角色权限',
      icon: <TeamOutlined className="text-4xl text-blue-500" />,
      path: '/admin/rbac/roles',
      color: 'border-blue-200 hover:border-blue-400',
      bgColor: 'bg-blue-50 hover:bg-blue-100',
    },
    {
      title: '权限管理',
      description: '管理系统权限，配置权限分组',
      icon: <SafetyOutlined className="text-4xl text-green-500" />,
      path: '/admin/rbac/permissions',
      color: 'border-green-200 hover:border-green-400',
      bgColor: 'bg-green-50 hover:bg-green-100',
    },
    {
      title: '部门管理',
      description: '管理组织架构，配置部门层级',
      icon: <ApartmentOutlined className="text-4xl text-purple-500" />,
      path: '/admin/rbac/departments',
      color: 'border-purple-200 hover:border-purple-400',
      bgColor: 'bg-purple-50 hover:bg-purple-100',
    },
    {
      title: '用户角色分配',
      description: '为用户分配角色，管理权限关系',
      icon: <UserSwitchOutlined className="text-4xl text-orange-500" />,
      path: '/admin/rbac/user-roles',
      color: 'border-orange-200 hover:border-orange-400',
      bgColor: 'bg-orange-50 hover:bg-orange-100',
    },
  ];

  return (
    <div className="p-6">
      <div>
        {/* 页面标题 */}
        <div className="mb-8">
          <Card className="border-0 shadow-sm">
            <div className="text-center">
              <SafetyOutlined className="text-6xl text-blue-500 mb-4" />
              <Title level={2} className="mb-2">
                RBAC权限管理系统
              </Title>
              <Paragraph className="text-lg text-gray-600 max-w-2xl mx-auto">
                基于角色的访问控制系统，提供完整的用户、角色、权限管理功能，
                支持细粒度的权限控制和灵活的组织架构管理。
              </Paragraph>
            </div>
          </Card>
        </div>

        {/* 统计信息 */}
        <div className="mb-8">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="系统角色"
                  value={5}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="系统权限"
                  value={48}
                  prefix={<SafetyOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="组织部门"
                  value={4}
                  prefix={<ApartmentOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="活跃用户"
                  value={12}
                  prefix={<UserSwitchOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
          </Row>
        </div>

        {/* 功能卡片 */}
        <Row gutter={[20, 20]}>
          {cards.map((card, index) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={index}>
              <div>
                <Card
                  className={`h-full cursor-pointer transition-all duration-300 border-2 ${card.color} ${card.bgColor}`}
                  hoverable
                  onClick={() => router.push(card.path)}
                >
                  <div className="text-center p-4">
                    <div className="mb-4">
                      {card.icon}
                    </div>
                    <Title level={4} className="mb-2">
                      {card.title}
                    </Title>
                    <Paragraph className="text-gray-600 mb-4">
                      {card.description}
                    </Paragraph>
                    <Button
                      type="primary"
                      icon={<ArrowRightOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(card.path);
                      }}
                    >
                      进入管理
                    </Button>
                  </div>
                </Card>
              </div>
            </Col>
          ))}
        </Row>

        {/* 快速操作 */}
        <div className="mt-8">
          <Card title="快速操作" className="shadow-sm">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Button
                  block
                  size="large"
                  icon={<UserOutlined />}
                  onClick={() => router.push('/admin/rbac/users')}
                >
                  创建新用户
                </Button>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Button
                  block
                  size="large"
                  icon={<TeamOutlined />}
                  onClick={() => router.push('/admin/rbac/roles')}
                >
                  创建新角色
                </Button>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Button
                  block
                  size="large"
                  icon={<ApartmentOutlined />}
                  onClick={() => router.push('/admin/rbac/departments')}
                >
                  管理部门
                </Button>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Button
                  block
                  size="large"
                  icon={<UserSwitchOutlined />}
                  onClick={() => router.push('/admin/rbac/user-roles')}
                >
                  分配角色
                </Button>
              </Col>
            </Row>
          </Card>
        </div>

        {/* 系统说明 */}
        <div className="mt-8">
          <Card title="系统说明" className="shadow-sm">
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Title level={5}>权限模型</Title>
                <ul className="list-disc list-inside space-y-2 text-gray-600">
                  <li>基于RBAC（基于角色的访问控制）模型</li>
                  <li>支持用户-角色-权限三层架构</li>
                  <li>支持角色继承和权限覆盖</li>
                  <li>支持数据权限和功能权限分离</li>
                </ul>
              </Col>
              <Col xs={24} lg={12}>
                <Title level={5}>核心特性</Title>
                <ul className="list-disc list-inside space-y-2 text-gray-600">
                  <li>细粒度的权限控制</li>
                  <li>灵活的组织架构管理</li>
                  <li>支持权限过期时间</li>
                  <li>完整的审计日志</li>
                </ul>
              </Col>
            </Row>
          </Card>
        </div>
      </div>
    </div>
  );
}
