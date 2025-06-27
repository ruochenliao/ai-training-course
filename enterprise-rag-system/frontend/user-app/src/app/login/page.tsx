'use client';

import { useState } from 'react';
import { Button, Form, Input, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/v1/auth/login', values);
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        message.success('登录成功');
        router.push('/dashboard');
      } else {
        message.error('登录失败：' + (response.data.message || '未知错误'));
      }
    } catch (error) {
      console.error('登录失败:', error);
      message.error('登录失败：' + (error.response?.data?.message || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md shadow-md">
        <div className="text-center mb-6">
          <Title level={2}>企业级RAG知识库系统</Title>
          <Text type="secondary">请登录您的账户</Text>
        </div>
        
        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={handleLogin}
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
              size="large" 
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>
          
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}