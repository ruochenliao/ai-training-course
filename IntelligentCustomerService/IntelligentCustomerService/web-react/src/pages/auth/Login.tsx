import React, { useState } from 'react'
import { Form, Input, Button, Checkbox, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/store/auth'
import type { LoginParams } from '@/types/auth'

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const { login } = useAuthStore()

  const from = (location.state as any)?.from?.pathname || '/dashboard'

  const onFinish = async (values: LoginParams) => {
    setLoading(true)
    try {
      await login(values)
      message.success(t('loginSuccess'))
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error.message || t('loginFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-96 shadow-lg">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            {t('title')}
          </h1>
          <p className="text-gray-600">{t('login')}</p>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              {
                required: true,
                message: t('usernameRequired'),
              },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder={t('username')}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              {
                required: true,
                message: t('passwordRequired'),
              },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t('password')}
            />
          </Form.Item>

          <Form.Item>
            <div className="flex-between">
              <Form.Item name="rememberMe" valuePropName="checked" noStyle>
                <Checkbox>{t('rememberMe')}</Checkbox>
              </Form.Item>
              <a className="text-primary-600 hover:text-primary-700">
                {t('forgotPassword')}
              </a>
            </div>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="w-full"
            >
              {t('login')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login