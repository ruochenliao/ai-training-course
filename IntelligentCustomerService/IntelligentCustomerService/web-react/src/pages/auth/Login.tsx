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

  // 获取重定向路径，默认跳转到智能客服页面
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
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '登录失败，请检查用户名和密码'
      message.error(errorMessage)
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
    <div className={`login-page ${isDark ? 'login-page-dark' : 'login-page-light'}`}>
      {/* 装饰元素 */}
      <div className="login-decoration"></div>
      
      <div className="login-card">
        <div className="flex-col-center">
          <div className={`logo-container ${isDark ? 'logo-container-dark' : ''}`}>
            <UserOutlined className="text-white text-2xl" />
          </div>
          
          <h1 className="login-title">智能客服系统</h1>
          <p className="login-subtitle">基于React+FastAPI+Ant Design的管理平台</p>
        </div>

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
          className="login-form"
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

          <Form.Item className="mb-4">
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="login-button"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider className={isDark ? 'border-gray-600 text-gray-400' : 'border-gray-200 text-gray-500'}>演示账号</Divider>
        
        {/* 快速登录按钮 */}
        <div className="flex justify-center gap-4 mb-4">
          <Button 
            onClick={() => handleDemoLogin('admin')}
            className={cn(
              "flex-1 demo-button",
              isDark ? 'demo-button-dark' : ''
            )}
          >
            管理员
          </Button>
          <Button 
            onClick={() => handleDemoLogin('user')}
            className={cn(
              "flex-1 demo-button",
              isDark ? 'demo-button-dark' : ''
            )}
          >
            普通用户
          </Button>
        </div>
        
        {/* 版权信息 */}
        <div className="login-footer">
          © {new Date().getFullYear()} 智能客服系统 • 版权所有
        </div>
      </div>
    </div>
  )
}

export default Login