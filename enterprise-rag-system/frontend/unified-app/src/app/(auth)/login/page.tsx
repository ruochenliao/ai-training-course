'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Form, Input, Card, Typography, Divider, Space } from 'antd';
import { UserOutlined, LockOutlined, EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import ThemeToggle from '@/components/common/ThemeToggle';

const { Title, Text, Link } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const { theme } = useTheme();
  const router = useRouter();
  const [form] = Form.useForm();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/chat');
    }
  }, [isAuthenticated, router]);

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (success) {
        router.push('/chat');
      }
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
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* 背景动画 */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900 dark:to-purple-900">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
        
        {/* 浮动元素 */}
        <motion.div
          animate={{
            x: [0, 100, 0],
            y: [0, -100, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-200/30 dark:bg-blue-500/20 rounded-full blur-3xl"
        />
        
        <motion.div
          animate={{
            x: [0, -120, 0],
            y: [0, 80, 0],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-200/30 dark:bg-purple-500/20 rounded-full blur-3xl"
        />
      </div>

      {/* 主题切换按钮 */}
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      {/* 登录表单 */}
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
                className="w-16 h-16 mx-auto bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4"
              >
                <span className="text-2xl text-white">🧠</span>
              </motion.div>
            </div>
            
            <Title level={2} className="!mb-2 text-gradient">
              企业级RAG知识库系统
            </Title>
            <Text type="secondary" className="text-base">
              智能问答 · 知识管理 · 协作平台
            </Text>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Form
              form={form}
              name="login"
              onFinish={handleLogin}
              layout="vertical"
              size="large"
              requiredMark={false}
            >
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名或邮箱' }]}
              >
                <Input
                  prefix={<UserOutlined className="text-gray-400" />}
                  placeholder="用户名或邮箱"
                  className="rounded-lg"
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined className="text-gray-400" />}
                  placeholder="密码"
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
                    className="h-12 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 border-0 font-medium text-base shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    {loading ? '登录中...' : '立即登录'}
                  </Button>
                </motion.div>
              </Form.Item>
            </Form>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Divider className="!my-6">
              <Text type="secondary" className="text-sm">
                其他选项
              </Text>
            </Divider>

            <Space direction="vertical" className="w-full" size="middle">
              <div className="text-center">
                <Text type="secondary" className="text-sm">
                  还没有账户？{' '}
                  <Link href="/register" className="font-medium">
                    立即注册
                  </Link>
                </Text>
              </div>
              
              <div className="text-center">
                <Link href="/forgot-password" className="text-sm text-gray-500 hover:text-blue-500">
                  忘记密码？
                </Link>
              </div>
            </Space>
          </motion.div>
        </Card>

        {/* 底部信息 */}
        <motion.div
          variants={itemVariants}
          className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400"
        >
          <p>© 2024 企业级RAG知识库系统. 保留所有权利.</p>
          <p className="mt-1">
            基于 AutoGen + RAG 技术构建的智能知识管理平台
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
