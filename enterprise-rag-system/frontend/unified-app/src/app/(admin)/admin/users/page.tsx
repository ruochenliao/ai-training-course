'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Typography, Button, Space } from 'antd';
import { UserOutlined, ArrowRightOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

export default function AdminUsersPage() {
  const router = useRouter();

  useEffect(() => {
    // 自动重定向到新的用户管理页面
    const timer = setTimeout(() => {
      router.push('/admin/rbac/users');
    }, 3000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="h-full flex items-center justify-center">
      <Card className="max-w-md text-center">
        <Space direction="vertical" size="large">
          <UserOutlined className="text-6xl text-blue-500" />
          <Title level={3}>用户管理已迁移</Title>
          <Paragraph>
            用户管理功能已迁移到权限管理模块中，
            为您提供更完整的用户权限管理体验。
          </Paragraph>
          <Paragraph type="secondary">
            页面将在3秒后自动跳转...
          </Paragraph>
          <Button
            type="primary"
            icon={<ArrowRightOutlined />}
            onClick={() => router.push('/admin/rbac/users')}
          >
            立即前往新页面
          </Button>
        </Space>
      </Card>
    </div>
  );
}


