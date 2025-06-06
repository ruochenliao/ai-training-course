import React, {useEffect, useState} from 'react'
import {Button, Card, Checkbox, Divider, Form, Input, message, Space} from 'antd'
import {EyeInvisibleOutlined, EyeTwoTone, LockOutlined, UserOutlined} from '@ant-design/icons'
import {useLocation, useNavigate} from 'react-router-dom'
import {useAuthStore} from '../../store/auth'
import {useAppStore} from '../../store/app'
import {cn} from '../../utils'

interface LoginForm {
  username: string
  password: string
  remember: boolean
}

const Login: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  
  const { login, isAuthenticated } = useAuthStore()
  const { theme } = useAppStore()

  // 获取重定向路径
  const from = (location.state as any)?.from?.pathname || '/'

  // 如果已登录，重定向到目标页面
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  // 处理登录
  const handleLogin = async (values: LoginForm) => {
    setLoading(true)
    try {
      await login({
        username: values.username,
        password: values.password
      })
      
      message.success('登录成功！')
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error.message || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  // 演示账号登录
  const handleDemoLogin = (role: 'admin' | 'user') => {
    const demoAccounts = {
      admin: { username: 'admin', password: '123456' },
      user: { username: 'user', password: 'user123' }
    }
    
    const account = demoAccounts[role]
    form.setFieldsValue(account)
    handleLogin({ ...account, remember: false })
  }

  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center px-4",
      theme === 'dark' 
        ? "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900" 
        : "bg-gradient-to-br from-blue-50 via-white to-blue-50"
    )}>
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className={cn(
          "absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-20",
          theme === 'dark' ? "bg-blue-500" : "bg-blue-200"
        )} />
        <div className={cn(
          "absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-20",
          theme === 'dark' ? "bg-purple-500" : "bg-purple-200"
        )} />
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Logo和标题 */}
        <div className="text-center mb-8">
          <div className={cn(
            "inline-flex items-center justify-center w-16 h-16 rounded-full mb-4",
            theme === 'dark' ? "bg-blue-600" : "bg-blue-500"
          )}>
            <UserOutlined className="text-2xl text-white" />
          </div>
          <h1 className={cn(
            "text-3xl font-bold mb-2",
            theme === 'dark' ? "text-white" : "text-gray-800"
          )}>
            智能客服系统
          </h1>
          <p className={cn(
            "text-base",
            theme === 'dark' ? "text-gray-300" : "text-gray-600"
          )}>
            欢迎登录管理后台
          </p>
        </div>

        {/* 登录表单 */}
        <Card 
          className={cn(
            "shadow-2xl border-0",
            theme === 'dark' 
              ? "bg-gray-800/80 backdrop-blur-sm" 
              : "bg-white/80 backdrop-blur-sm"
          )}
        >
          <Form
            form={form}
            name="login"
            onFinish={handleLogin}
            autoComplete="off"
            size="large"
            initialValues={{
              remember: true,
              username: 'admin',
              password: '123456'
            }}
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名！' },
                { min: 3, message: '用户名至少3个字符！' }
              ]}
            >
              <Input
                prefix={<UserOutlined className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'} />}
                placeholder="用户名"
                className={cn(
                  "rounded-lg",
                  theme === 'dark' ? "bg-gray-700 border-gray-600" : ""
                )}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码！' },
                { min: 6, message: '密码至少6个字符！' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'} />}
                placeholder="密码"
                iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                className={cn(
                  "rounded-lg",
                  theme === 'dark' ? "bg-gray-700 border-gray-600" : ""
                )}
              />
            </Form.Item>

            <Form.Item>
              <div className="flex items-center justify-between">
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
                    记住我
                  </Checkbox>
                </Form.Item>
                <Button 
                  type="link" 
                  className={cn(
                    "p-0 h-auto",
                    theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                  )}
                >
                  忘记密码？
                </Button>
              </div>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                className="w-full h-12 rounded-lg font-medium text-base"
                size="large"
              >
                {loading ? '登录中...' : '登录'}
              </Button>
            </Form.Item>
          </Form>

          {/* 演示账号 */}
          <Divider className={theme === 'dark' ? 'border-gray-600' : 'border-gray-200'}>
            <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
              演示账号
            </span>
          </Divider>

          <Space direction="vertical" className="w-full" size="middle">
            <Button
              block
              onClick={() => handleDemoLogin('admin')}
              className={cn(
                "h-10 rounded-lg",
                theme === 'dark' 
                  ? "bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600" 
                  : "bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100"
              )}
            >
              管理员登录 (admin/123456)
            </Button>
            <Button
              block
              onClick={() => handleDemoLogin('user')}
              className={cn(
                "h-10 rounded-lg",
                theme === 'dark' 
                  ? "bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600" 
                  : "bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100"
              )}
            >
              普通用户登录 (user/user123)
            </Button>
          </Space>
        </Card>

        {/* 底部信息 */}
        <div className="text-center mt-8">
          <p className={cn(
            "text-sm",
            theme === 'dark' ? "text-gray-400" : "text-gray-500"
          )}>
            © 2024 智能客服系统. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login