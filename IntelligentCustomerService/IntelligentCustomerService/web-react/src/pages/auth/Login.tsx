import React, {useEffect, useState} from 'react'
import {Button, Card, Checkbox, Divider, Form, Input, message} from 'antd'
import {LockOutlined, UserOutlined} from '@ant-design/icons'
import {useLocation, useNavigate} from 'react-router-dom'
import {useAuthStore} from '../../store/auth'
import {cn} from '../../utils'
import {useTheme} from '../../contexts/ThemeContext'

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
  const { primaryColor, isDark } = useTheme()

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
    <div 
      className="min-h-screen flex-col-center overflow-hidden relative"
      style={{ 
        backgroundImage: isDark 
          ? 'radial-gradient(circle at 20% 20%, #17183b, #0f0f1a)' 
          : 'radial-gradient(circle at 20% 20%, #e6f7ff, #f0f5ff)',
      }}
    >
      {/* 装饰背景 */}
      <div className="absolute top-0 left-0 right-0 bottom-0">
        <div className="absolute top-[20%] left-[10%] w-[400px] h-[400px] rounded-full opacity-10"
          style={{ background: isDark ? '#3366ff' : '#1890ff', filter: 'blur(150px)' }}
        ></div>
        <div className="absolute bottom-[10%] right-[10%] w-[300px] h-[300px] rounded-full opacity-10"
          style={{ background: isDark ? '#ff4d4f' : '#ff7a45', filter: 'blur(150px)' }}
        ></div>
      </div>

      {/* 登录内容 */}
      <div className="relative z-10 flex-col-center w-full max-w-[900px] px-4 py-10">
        {/* 顶部标题 */}
        <div className="flex-col-center mb-8">
          <div 
            className="w-16 h-16 rounded-full flex-center mb-6"
            style={{ background: primaryColor }}
          >
            <UserOutlined className="text-white text-2xl" />
          </div>
          <h1 className={cn(
            "text-3xl font-bold mb-2",
            isDark ? "text-white" : "text-gray-800"
          )}>智能客服系统</h1>
          <p className={cn(
            "text-base",
            isDark ? "text-gray-300" : "text-gray-600"
          )}>基于React+FastAPI+Ant Design的管理平台</p>
        </div>

        {/* 登录表单 */}
        <Card 
          bordered={false}
          className={cn(
            "w-full max-w-[420px] shadow-lg",
            isDark ? "bg-gray-800/50 backdrop-blur" : "bg-white/80 backdrop-blur"
          )}
          style={{ 
            borderRadius: '12px',
            border: isDark ? '1px solid rgba(255,255,255,0.1)' : 'none',
          }}
          bodyStyle={{ padding: '24px 32px' }}
        >
          <h2 className={cn(
            "text-xl font-bold mb-6 text-center",
            isDark ? "text-white" : "text-gray-800"
          )}>
            账号登录
          </h2>

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
            className="flex flex-col gap-4"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名！' },
                { min: 3, message: '用户名至少3个字符！' }
              ]}
            >
              <Input
                prefix={<UserOutlined className={isDark ? 'text-gray-400' : 'text-gray-500'} />}
                placeholder="用户名"
                className={cn(
                  "py-2 rounded-lg",
                  isDark ? "bg-gray-700 border-gray-600 text-white" : ""
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
                prefix={<LockOutlined className={isDark ? 'text-gray-400' : 'text-gray-500'} />}
                placeholder="密码"
                className={cn(
                  "py-2 rounded-lg",
                  isDark ? "bg-gray-700 border-gray-600 text-white" : ""
                )}
              />
            </Form.Item>

            <Form.Item>
              <div className="flex items-center justify-between">
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox className={isDark ? 'text-gray-300' : 'text-gray-600'}>
                    记住我
                  </Checkbox>
                </Form.Item>
                <Button 
                  type="link" 
                  className={cn(
                    "p-0 h-auto",
                    isDark ? 'text-blue-400' : 'text-blue-600'
                  )}
                >
                  忘记密码？
                </Button>
              </div>
            </Form.Item>

            <Form.Item className="mb-0">
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{ 
                  height: '44px', 
                  borderRadius: '8px',
                  background: primaryColor,
                }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          {/* 演示账号 */}
          <Divider className={isDark ? 'border-gray-600' : 'border-gray-200'}>
            <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>
              快速登录
            </span>
          </Divider>

          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleDemoLogin('admin')}
              className={cn(
                "h-10 rounded-lg",
                isDark 
                  ? "bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600" 
                  : "bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100"
              )}
            >
              管理员
            </Button>
            <Button
              onClick={() => handleDemoLogin('user')}
              className={cn(
                "h-10 rounded-lg",
                isDark 
                  ? "bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600" 
                  : "bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100"
              )}
            >
              用户
            </Button>
          </div>
        </Card>

        {/* 底部版权 */}
        <div className="mt-10 text-center">
          <p className={cn(
            "text-sm",
            isDark ? "text-gray-400" : "text-gray-500"
          )}>
            © 2024 智能客服系统 · 基于 React+FastAPI 构建
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login