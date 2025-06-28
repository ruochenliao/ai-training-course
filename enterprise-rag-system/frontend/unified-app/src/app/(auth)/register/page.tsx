'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Form, Input, Card, Typography, Divider, Space, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/utils/api';
import ThemeToggle from '@/components/common/ThemeToggle';
import { validatePassword, isValidEmail } from '@/utils';

const { Title, Text, Link } = Typography;

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  const [form] = Form.useForm();

  const handleRegister = async (values: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
    fullName?: string;
  }) => {
    setLoading(true);
    try {
      // 注册用户
      await apiClient.post('/api/v1/auth/register', {
        username: values.username,
        email: values.email,
        password: values.password,
        confirm_password: values.confirmPassword,
        full_name: values.fullName,
      });

      message.success('注册成功！正在为您登录...');

      // 自动登录
      const success = await login(values.username, values.password);
      if (success) {
        router.push('/chat');
      }
    } catch (error: any) {
      console.error('注册失败:', error);
      const errorMessage = error.response?.data?.detail || error.message || '注册失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut",
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden py-8">
      {/* 背景动画 */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-purple-900 dark:to-blue-900">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
        
        <motion.div
          animate={{
            x: [0, -100, 0],
            y: [0, 100, 0],
          }}
          transition={{
            duration: 22,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute top-1/3 right-1/4 w-72 h-72 bg-purple-200/30 dark:bg-purple-500/20 rounded-full blur-3xl"
        />
        
        <motion.div
          animate={{
            x: [0, 120, 0],
            y: [0, -80, 0],
          }}
          transition={{
            duration: 28,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-blue-200/30 dark:bg-blue-500/20 rounded-full blur-3xl"
        />
      </div>

      {/* 主题切换按钮 */}
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      {/* 注册表单 */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 w-full max-w-md px-6"
      >
        <Card
          className="shadow-2xl border-0 backdrop-blur-sm bg-white/80 dark:bg-gray-800/80"
          style={{ borderRadius: 16 }}
        >
          <motion.div variants={itemVariants} className="text-center mb-8">
            <div className="mb-4">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="w-16 h-16 mx-auto bg-gradient-to-r from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center mb-4"
              >
                <span className="text-2xl text-white">🚀</span>
              </motion.div>
            </div>
            
            <Title level={2} className="!mb-2 text-gradient">
              加入我们
            </Title>
            <Text type="secondary" className="text-base">
              创建您的智能知识管理账户
            </Text>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Form
              form={form}
              name="register"
              onFinish={handleRegister}
              layout="vertical"
              size="large"
              requiredMark={false}
            >
              <Form.Item
                name="fullName"
                rules={[
                  { required: true, message: '请输入您的姓名' },
                  { min: 2, message: '姓名至少2个字符' }
                ]}
              >
                <Input
                  prefix={<UserOutlined className="text-gray-400" />}
                  placeholder="姓名"
                  className="rounded-lg"
                />
              </Form.Item>

              <Form.Item
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
                ]}
              >
                <Input
                  prefix={<UserOutlined className="text-gray-400" />}
                  placeholder="用户名"
                  className="rounded-lg"
                />
              </Form.Item>

              <Form.Item
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱地址' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input
                  prefix={<MailOutlined className="text-gray-400" />}
                  placeholder="邮箱地址"
                  className="rounded-lg"
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 8, message: '密码至少8个字符' },
                  {
                    validator: (_, value) => {
                      if (!value) return Promise.resolve();
                      const validation = validatePassword(value);
                      if (validation.isValid) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error(validation.errors[0]));
                    }
                  }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined className="text-gray-400" />}
                  placeholder="密码"
                  className="rounded-lg"
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>

              <Form.Item
                name="confirmPassword"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'));
                    },
                  }),
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined className="text-gray-400" />}
                  placeholder="确认密码"
                  className="rounded-lg"
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>

              <Form.Item className="mb-6">
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    block
                    className="h-12 rounded-lg bg-gradient-to-r from-purple-500 to-blue-600 border-0 font-medium text-base shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    {loading ? '注册中...' : '立即注册'}
                  </Button>
                </motion.div>
              </Form.Item>
            </Form>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Divider className="!my-6">
              <Text type="secondary" className="text-sm">
                已有账户？
              </Text>
            </Divider>

            <div className="text-center">
              <Text type="secondary" className="text-sm">
                <Link href="/login" className="font-medium">
                  立即登录
                </Link>
              </Text>
            </div>
          </motion.div>
        </Card>

        {/* 底部信息 */}
        <motion.div
          variants={itemVariants}
          className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400"
        >
          <p>注册即表示您同意我们的服务条款和隐私政策</p>
        </motion.div>
      </motion.div>
    </div>
  );
}
