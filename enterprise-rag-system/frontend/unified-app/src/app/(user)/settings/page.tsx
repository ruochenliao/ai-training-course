'use client';

import { useState } from 'react';
import { Card, Form, Input, Button, Switch, Select, Upload, Avatar, message, Divider, Space, Typography } from 'antd';
import { UserOutlined, UploadOutlined, SaveOutlined, LockOutlined } from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { validatePassword } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;

export default function SettingsPage() {
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { user, refreshUser } = useAuth();
  const { theme, setTheme } = useTheme();

  const handleProfileUpdate = async (values: any) => {
    setLoading(true);
    try {
      // 更新用户资料的API调用
      console.log('更新用户资料:', values);
      message.success('个人资料更新成功');
      await refreshUser();
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    setLoading(true);
    try {
      // 修改密码的API调用
      console.log('修改密码:', values);
      message.success('密码修改成功');
      passwordForm.resetFields();
    } catch (error) {
      message.error('密码修改失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = (info: any) => {
    if (info.file.status === 'done') {
      message.success('头像上传成功');
    } else if (info.file.status === 'error') {
      message.error('头像上传失败');
    }
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Title level={2}>个人设置</Title>
          <Text type="secondary">管理您的账户信息和偏好设置</Text>
        </motion.div>

        {/* 个人资料 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card title="个人资料" className="shadow-sm">
            <Form
              form={profileForm}
              layout="vertical"
              onFinish={handleProfileUpdate}
              initialValues={{
                username: user?.username,
                email: user?.email,
                full_name: user?.full_name,
              }}
            >
              {/* 头像上传 */}
              <div className="flex items-center space-x-6 mb-6">
                <Avatar
                  size={80}
                  src={user?.avatar_url}
                  icon={<UserOutlined />}
                  className="bg-gradient-to-r from-blue-500 to-purple-600"
                />
                <div>
                  <Upload
                    name="avatar"
                    showUploadList={false}
                    action="/api/v1/users/avatar"
                    onChange={handleAvatarUpload}
                  >
                    <Button icon={<UploadOutlined />}>更换头像</Button>
                  </Upload>
                  <div className="mt-2 text-sm text-gray-500">
                    支持 JPG、PNG 格式，文件大小不超过 2MB
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Form.Item
                  name="username"
                  label="用户名"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}
                >
                  <Input placeholder="输入用户名" disabled />
                </Form.Item>

                <Form.Item
                  name="email"
                  label="邮箱地址"
                  rules={[
                    { required: true, message: '请输入邮箱地址' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                >
                  <Input placeholder="输入邮箱地址" />
                </Form.Item>

                <Form.Item
                  name="full_name"
                  label="姓名"
                  rules={[{ required: true, message: '请输入姓名' }]}
                >
                  <Input placeholder="输入姓名" />
                </Form.Item>

                <Form.Item name="phone" label="手机号码">
                  <Input placeholder="输入手机号码" />
                </Form.Item>

                <Form.Item name="department" label="部门">
                  <Input placeholder="输入部门" />
                </Form.Item>

                <Form.Item name="position" label="职位">
                  <Input placeholder="输入职位" />
                </Form.Item>
              </div>

              <Form.Item name="bio" label="个人简介">
                <Input.TextArea
                  placeholder="介绍一下自己..."
                  rows={3}
                  maxLength={200}
                  showCount
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={loading}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
                >
                  保存更改
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </motion.div>

        {/* 偏好设置 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card title="偏好设置" className="shadow-sm">
            <div className="space-y-6">
              {/* 主题设置 */}
              <div className="flex items-center justify-between">
                <div>
                  <Text strong>主题模式</Text>
                  <div className="text-sm text-gray-500 mt-1">
                    选择您喜欢的界面主题
                  </div>
                </div>
                <Select
                  value={theme}
                  onChange={setTheme}
                  style={{ width: 120 }}
                >
                  <Option value="light">浅色</Option>
                  <Option value="dark">深色</Option>
                </Select>
              </div>

              <Divider />

              {/* 语言设置 */}
              <div className="flex items-center justify-between">
                <div>
                  <Text strong>语言</Text>
                  <div className="text-sm text-gray-500 mt-1">
                    选择界面显示语言
                  </div>
                </div>
                <Select defaultValue="zh-CN" style={{ width: 120 }}>
                  <Option value="zh-CN">简体中文</Option>
                  <Option value="en-US">English</Option>
                </Select>
              </div>

              <Divider />

              {/* 通知设置 */}
              <div>
                <Text strong className="block mb-4">通知设置</Text>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Text>邮件通知</Text>
                      <div className="text-sm text-gray-500">
                        接收重要系统通知邮件
                      </div>
                    </div>
                    <Switch defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Text>浏览器通知</Text>
                      <div className="text-sm text-gray-500">
                        在浏览器中显示通知
                      </div>
                    </div>
                    <Switch defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Text>对话提醒</Text>
                      <div className="text-sm text-gray-500">
                        新消息到达时提醒
                      </div>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* 安全设置 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card title="安全设置" className="shadow-sm">
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordChange}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Form.Item
                  name="current_password"
                  label="当前密码"
                  rules={[{ required: true, message: '请输入当前密码' }]}
                >
                  <Input.Password
                    placeholder="输入当前密码"
                    prefix={<LockOutlined />}
                  />
                </Form.Item>

                <div></div>

                <Form.Item
                  name="new_password"
                  label="新密码"
                  rules={[
                    { required: true, message: '请输入新密码' },
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
                    placeholder="输入新密码"
                    prefix={<LockOutlined />}
                  />
                </Form.Item>

                <Form.Item
                  name="confirm_password"
                  label="确认新密码"
                  dependencies={['new_password']}
                  rules={[
                    { required: true, message: '请确认新密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('new_password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'));
                      },
                    }),
                  ]}
                >
                  <Input.Password
                    placeholder="再次输入新密码"
                    prefix={<LockOutlined />}
                  />
                </Form.Item>
              </div>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<LockOutlined />}
                  loading={loading}
                  className="bg-gradient-to-r from-red-500 to-pink-600 border-0"
                >
                  修改密码
                </Button>
              </Form.Item>
            </Form>

            <Divider />

            {/* 其他安全选项 */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Text strong>两步验证</Text>
                  <div className="text-sm text-gray-500">
                    为您的账户添加额外的安全保护
                  </div>
                </div>
                <Button>设置</Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Text strong>登录设备管理</Text>
                  <div className="text-sm text-gray-500">
                    查看和管理已登录的设备
                  </div>
                </div>
                <Button>管理</Button>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
