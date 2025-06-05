import React, { useState } from 'react';
import { Card, Form, Input, Button, Avatar, Upload, message, Divider } from 'antd';
import { UserOutlined, UploadOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

interface ProfileFormData {
  username: string;
  email: string;
  phone?: string;
  department?: string;
}

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: ProfileFormData) => {
    setLoading(true);
    try {
      // 这里应该调用更新用户信息的 API
      console.log('更新用户信息:', values);
      message.success('个人信息更新成功');
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (info: any) => {
    if (info.file.status === 'done') {
      message.success('头像上传成功');
    } else if (info.file.status === 'error') {
      message.error('头像上传失败');
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card title="个人资料" bordered={false}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px' }}>
          <Avatar size={80} icon={<UserOutlined />} style={{ marginRight: '16px' }} />
          <div>
            <Upload
              name="avatar"
              showUploadList={false}
              onChange={handleAvatarChange}
            >
              <Button icon={<UploadOutlined />}>更换头像</Button>
            </Upload>
          </div>
        </div>
        
        <Divider />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            username: user?.username || '',
            email: user?.email || '',
            phone: user?.phone || '',
            department: user?.department || ''
          }}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          
          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          
          <Form.Item
            label="手机号"
            name="phone"
          >
            <Input placeholder="请输入手机号" />
          </Form.Item>
          
          <Form.Item
            label="部门"
            name="department"
          >
            <Input placeholder="请输入部门" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Profile;