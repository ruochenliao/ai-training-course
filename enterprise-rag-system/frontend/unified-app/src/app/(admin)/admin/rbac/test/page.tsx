'use client';

import React from 'react';
import { Card, Typography, Space, Tag } from 'antd';
import { SafetyOutlined } from '@ant-design/icons';
import { usePermissions } from '@/contexts/PermissionContext';
import { useAuth } from '@/contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;

export default function RBACTestPage() {
  const { permissions, roles, hasPermission } = usePermissions();
  const { user } = useAuth();

  const testPermissions = [
    'user:view',
    'user:manage',
    'role:view',
    'role:manage',
    'permission:view',
    'permission:manage',
    'dept:view',
    'dept:manage',
    'user_role:manage',
  ];

  return (
    <div className="p-6">
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={3}>
              <SafetyOutlined /> RBAC权限系统测试页面
            </Title>
            <Paragraph>
              这个页面用于测试RBAC权限系统是否正常工作。
            </Paragraph>
          </div>

          <div>
            <Title level={4}>当前用户信息</Title>
            <Space direction="vertical">
              <Text><strong>用户名:</strong> {user?.username}</Text>
              <Text><strong>邮箱:</strong> {user?.email}</Text>
              <Text><strong>超级用户:</strong> {user?.is_superuser ? '是' : '否'}</Text>
              <Text><strong>员工:</strong> {user?.is_staff ? '是' : '否'}</Text>
            </Space>
          </div>

          <div>
            <Title level={4}>用户角色</Title>
            <Space wrap>
              {roles.length > 0 ? (
                roles.map(role => (
                  <Tag key={role} color="blue">{role}</Tag>
                ))
              ) : (
                <Text type="secondary">暂无角色</Text>
              )}
            </Space>
          </div>

          <div>
            <Title level={4}>用户权限</Title>
            <Paragraph>
              <Text type="secondary">权限总数: {permissions.length}</Text>
            </Paragraph>
            <Space wrap>
              {permissions.length > 0 ? (
                permissions.slice(0, 20).map(permission => (
                  <Tag key={permission} color="green">{permission}</Tag>
                ))
              ) : (
                <Text type="secondary">暂无权限</Text>
              )}
              {permissions.length > 20 && (
                <Tag>... 还有 {permissions.length - 20} 个权限</Tag>
              )}
            </Space>
          </div>

          <div>
            <Title level={4}>权限测试</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              {testPermissions.map(permission => (
                <div key={permission} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text code>{permission}</Text>
                  <Tag color={hasPermission(permission) ? 'green' : 'red'}>
                    {hasPermission(permission) ? '有权限' : '无权限'}
                  </Tag>
                </div>
              ))}
            </Space>
          </div>

          <div>
            <Title level={4}>系统状态</Title>
            <Space direction="vertical">
              <Text><strong>权限上下文:</strong> {permissions.length > 0 ? '已加载' : '未加载'}</Text>
              <Text><strong>角色上下文:</strong> {roles.length > 0 ? '已加载' : '未加载'}</Text>
              <Text><strong>用户认证:</strong> {user ? '已认证' : '未认证'}</Text>
            </Space>
          </div>
        </Space>
      </Card>
    </div>
  );
}
