import React, {useEffect, useState} from 'react'
import {Button, Checkbox, Divider, Form, Input, message} from 'antd'
import {LockOutlined, UserOutlined} from '@ant-design/icons'
import {useLocation, useNavigate} from 'react-router-dom'
import {useTranslation} from 'react-i18next'
import {useAuthStore} from '../../store/auth'
import {cn} from '../../utils'
import {useTheme} from '../../contexts/ThemeContext'
import useLocalStorage from '../../hooks/useLocalStorage'

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
  const { t } = useTranslation()

  const { login, isAuthenticated } = useAuthStore()
  const { isDark } = useTheme()

  // 本地存储登录信息
  const [loginInfo, setLoginInfo] = useLocalStorage('loginInfo', {
    username: '',
    password: '',
    remember: false,
  })

  // 获取重定向路径，默认跳转到智能客服前台
  const from = (location.state as any)?.from?.pathname || '/chat'

  // 初始化登录信息
  useEffect(() => {
    if (loginInfo.username || loginInfo.password) {
      form.setFieldsValue({
        username: loginInfo.username,
        password: loginInfo.password,
        remember: loginInfo.remember,
      })
    }
  }, [form, loginInfo])

  // 如果已登录，重定向到目标页面
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  // 处理登录
  const handleLogin = async (values: LoginForm) => {
    const { username, password, remember } = values

    if (!username || !password) {
      message.warning(t('auth.usernameRequired') + '和' + t('auth.passwordRequired'))
      return
    }

    setLoading(true)
    message.loading(t('common.loading'), 0)

    try {
      // 保存登录信息到本地存储
      if (remember) {
        setLoginInfo({ username, password, remember })
      } else {
        setLoginInfo({ username: '', password: '', remember: false })
      }

      await login({ username, password })

      message.destroy()
      message.success(t('auth.loginSuccess'))

      // 检查是否有重定向参数
      const redirectPath = new URLSearchParams(location.search).get('redirect')
      if (redirectPath) {
        navigate(redirectPath, { replace: true })
      } else {
        navigate(from, { replace: true })
      }
    } catch (error: unknown) {
      message.destroy()
      const errorMessage = error instanceof Error ? error.message : t('auth.loginFailed')
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 演示账号登录
  const handleDemoLogin = (role: 'admin' | 'user') => {
    const demoAccounts = {
      admin: { username: 'admin', password: '123456' },
      user: { username: 'user', password: 'user123' },
    }

    const account = demoAccounts[role]
    form.setFieldsValue({ ...account, remember: false })
    handleLogin({ ...account, remember: false })
  }

  // 处理回车键登录
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      form.submit()
    }
  }

  return (
    <div className={`login-page ${isDark ? 'login-page-dark' : 'login-page-light'}`}>
      {/* 装饰元素 */}
      <div className='login-decoration'></div>

      <div className='login-card'>
        <div className='flex-col-center'>
          <div className={`logo-container ${isDark ? 'logo-container-dark' : ''}`}>
            <UserOutlined className='text-white text-2xl' />
          </div>

          <h1 className='login-title'>{t('dashboard.title')}</h1>
          <p className='login-subtitle'>基于React+FastAPI+Ant Design的管理平台</p>
        </div>

        <Form
          form={form}
          name='login'
          onFinish={handleLogin}
          autoComplete='off'
          size='large'
          initialValues={{
            remember: true,
            username: loginInfo.username || 'admin',
            password: loginInfo.password || '123456',
          }}
          className='login-form'
          onKeyPress={handleKeyPress}
        >
          <Form.Item
            name='username'
            rules={[
              { required: true, message: t('auth.usernameRequired') },
              { min: 3, message: '用户名至少3个字符！' },
              { max: 20, message: '用户名最多20个字符！' },
            ]}
          >
            <Input
              prefix={<UserOutlined className={isDark ? 'text-gray-400' : 'text-gray-500'} />}
              placeholder={t('auth.username')}
              className={cn(isDark ? 'bg-gray-700 border-gray-600 text-white' : '')}
              autoFocus
            />
          </Form.Item>

          <Form.Item
            name='password'
            rules={[
              { required: true, message: t('auth.passwordRequired') },
              { min: 6, message: '密码至少6个字符！' },
              { max: 20, message: '密码最多20个字符！' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className={isDark ? 'text-gray-400' : 'text-gray-500'} />}
              placeholder={t('auth.password')}
              className={cn(isDark ? 'bg-gray-700 border-gray-600 text-white' : '')}
              visibilityToggle={{ visible: true }}
            />
          </Form.Item>

          <Form.Item>
            <div className='flex items-center justify-between'>
              <Form.Item name='remember' valuePropName='checked' noStyle>
                <Checkbox className={isDark ? 'text-gray-300' : 'text-gray-600'}>{t('auth.rememberMe')}</Checkbox>
              </Form.Item>
              <Button type='link' className={cn('p-0 h-auto', isDark ? 'text-blue-400' : 'text-blue-600')}>
                {t('auth.forgotPassword')}
              </Button>
            </div>
          </Form.Item>

          <Form.Item className='mb-4'>
            <Button type='primary' htmlType='submit' loading={loading} className='login-button'>
              {t('auth.login')}
            </Button>
          </Form.Item>
        </Form>

        <Divider className={isDark ? 'border-gray-600 text-gray-400' : 'border-gray-200 text-gray-500'}>{t('auth.demoAccount')}</Divider>

        {/* 快速登录按钮 */}
        <div className='flex justify-center gap-4 mb-4'>
          <Button onClick={() => handleDemoLogin('admin')} className={cn('flex-1 demo-button', isDark ? 'demo-button-dark' : '')}>
            {t('auth.adminAccount')}
          </Button>
          <Button onClick={() => handleDemoLogin('user')} className={cn('flex-1 demo-button', isDark ? 'demo-button-dark' : '')}>
            {t('auth.userAccount')}
          </Button>
        </div>

        {/* 版权信息 */}
        <div className='login-footer'>
          © {new Date().getFullYear()} {t('dashboard.title')} • 版权所有
        </div>
      </div>
    </div>
  )
}

export default Login
