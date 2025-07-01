import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, Space, App } from 'antd'
import { UserOutlined, LockOutlined, RobotOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useSimpleAuthStore } from '@/store/simple-auth'

const { Title, Text, Paragraph } = Typography

const SimpleLoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useSimpleAuthStore()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const { message } = App.useApp()

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true)

    try {
      const success = await login(values.username, values.password)
      if (success) {
        message.success('登录成功')
        navigate('/')
      } else {
        message.error('用户名或密码错误')
      }
    } catch (error) {
      message.error('登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
          borderRadius: 16,
          border: 'none',
        }}
        styles={{
          body: {
            padding: 40,
          },
        }}
      >
        {/* Logo和标题 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div
            style={{
              width: 64,
              height: 64,
              background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
              borderRadius: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              boxShadow: '0 8px 24px rgba(14, 165, 233, 0.3)',
            }}
          >
            <RobotOutlined style={{ fontSize: 32, color: 'white' }} />
          </div>
          <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
            企业级 RAG 系统
          </Title>
          <Text style={{ color: '#64748b' }}>基于 AutoGen 智能体协作的知识库平台</Text>
        </div>

        {/* 登录表单 */}
        <Form
          form={form}
          layout='vertical'
          onFinish={handleLogin}
          size='large'
          initialValues={{
            username: 'admin',
            password: 'admin123',
          }}
        >
          <Form.Item name='username' rules={[{ required: true, message: '请输入用户名' }]}>
            <Input
              prefix={<UserOutlined style={{ color: '#94a3b8' }} />}
              placeholder='用户名'
              style={{
                borderRadius: 8,
                height: 48,
              }}
            />
          </Form.Item>

          <Form.Item name='password' rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password
              prefix={<LockOutlined style={{ color: '#94a3b8' }} />}
              placeholder='密码'
              style={{
                borderRadius: 8,
                height: 48,
              }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type='primary'
              htmlType='submit'
              loading={loading}
              style={{
                width: '100%',
                height: 48,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
                fontSize: 16,
                fontWeight: 500,
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        {/* 演示说明 */}
        <div
          style={{
            background: '#f8fafc',
            padding: 16,
            borderRadius: 8,
            marginTop: 16,
          }}
        >
          <Text strong style={{ color: '#475569', fontSize: 14 }}>
            演示账号：
          </Text>
          <div style={{ marginTop: 8 }}>
            <Space direction='vertical' size={4}>
              <Text style={{ fontSize: 12, color: '#64748b' }}>用户名：admin</Text>
              <Text style={{ fontSize: 12, color: '#64748b' }}>密码：admin123</Text>
            </Space>
          </div>
        </div>

        {/* 底部信息 */}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text style={{ fontSize: 12, color: '#94a3b8' }}>© 2024 企业级RAG知识库系统. All rights reserved.</Text>
        </div>
      </Card>
    </div>
  )
}

export default SimpleLoginPage
