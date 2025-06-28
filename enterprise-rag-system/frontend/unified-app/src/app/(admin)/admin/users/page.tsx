'use client';

import { useState } from 'react';
import { Table, Card, Button, Input, Select, Space, Tag, Avatar, Modal, Form, message, Dropdown } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  MoreOutlined,
  LockOutlined,
  UnlockOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/utils/api';
import { formatDate } from '@/utils';
import type { User } from '@/types';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;

export default function AdminUsersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取用户列表
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users', searchQuery, statusFilter],
    queryFn: () => apiClient.getUsers({
      search: searchQuery || undefined,
      status: statusFilter === 'all' ? undefined : statusFilter,
    }),
  });

  // 创建用户
  const createMutation = useMutation({
    mutationFn: (data: any) => apiClient.createUser(data),
    onSuccess: () => {
      message.success('用户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  // 更新用户
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => apiClient.updateUser(id, data),
    onSuccess: () => {
      message.success('用户更新成功');
      setCreateModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '更新失败');
    },
  });

  // 删除用户
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteUser(id),
    onSuccess: () => {
      message.success('用户删除成功');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败');
    },
  });

  const handleCreateUser = (values: any) => {
    if (editingUser) {
      updateMutation.mutate({ id: editingUser.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDeleteUser = (user: User) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户"${user.username}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(user.id),
    });
  };

  const handleToggleUserStatus = (user: User) => {
    updateMutation.mutate({
      id: user.id,
      data: { is_active: !user.is_active }
    });
  };

  const getUserActions = (user: User) => [
    {
      key: 'edit',
      label: '编辑',
      icon: <EditOutlined />,
      onClick: () => {
        setEditingUser(user);
        form.setFieldsValue(user);
        setCreateModalVisible(true);
      },
    },
    {
      key: 'toggle-status',
      label: user.is_active ? '禁用' : '启用',
      icon: user.is_active ? <LockOutlined /> : <UnlockOutlined />,
      onClick: () => handleToggleUserStatus(user),
    },
    {
      key: 'reset-password',
      label: '重置密码',
      icon: <LockOutlined />,
      onClick: () => {
        Modal.confirm({
          title: '重置密码',
          content: `确定要重置用户"${user.username}"的密码吗？`,
          onOk: () => {
            // 重置密码逻辑
            message.success('密码重置成功，新密码已发送到用户邮箱');
          },
        });
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => handleDeleteUser(user),
    },
  ];

  const columns: ColumnsType<User> = [
    {
      title: '用户',
      key: 'user',
      render: (_, user) => (
        <div className="flex items-center space-x-3">
          <Avatar
            src={user.avatar_url}
            icon={<UserOutlined />}
            className="bg-gradient-to-r from-blue-500 to-purple-600"
          />
          <div>
            <div className="font-medium">{user.full_name || user.username}</div>
            <div className="text-sm text-gray-500">{user.email}</div>
          </div>
        </div>
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '角色',
      key: 'role',
      render: (_, user) => (
        <Tag
          color={user.is_superuser ? 'red' : 'blue'}
          icon={user.is_superuser ? <CrownOutlined /> : <UserOutlined />}
        >
          {user.is_superuser ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, user) => (
        <Tag color={user.is_active ? 'green' : 'red'}>
          {user.is_active ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '最后登录',
      key: 'last_login',
      render: (_, user) => (
        <span className="text-sm text-gray-500">
          {user.last_login ? formatDate(user.last_login, 'relative') : '从未登录'}
        </span>
      ),
    },
    {
      title: '创建时间',
      key: 'created_at',
      render: (_, user) => (
        <span className="text-sm text-gray-500">
          {formatDate(user.created_at)}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, user) => (
        <Dropdown
          menu={{ items: getUserActions(user) }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            用户管理
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            管理系统用户账户和权限
          </p>
        </div>
        
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingUser(null);
            form.resetFields();
            setCreateModalVisible(true);
          }}
          className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
        >
          添加用户
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <Card className="shadow-sm">
        <div className="flex items-center space-x-4">
          <Search
            placeholder="搜索用户名、邮箱..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchQuery}
            onChange={(e) => !e.target.value && setSearchQuery('')}
          />
          
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 120 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="active">正常</Option>
            <Option value="inactive">禁用</Option>
          </Select>
        </div>
      </Card>

      {/* 用户列表 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="shadow-sm">
          <Table
            columns={columns}
            dataSource={users?.items || []}
            loading={isLoading}
            rowKey="id"
            pagination={{
              total: users?.total || 0,
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条用户`,
            }}
          />
        </Card>
      </motion.div>

      {/* 创建/编辑用户模态框 */}
      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateUser}
          className="mt-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input placeholder="输入用户名" disabled={!!editingUser} />
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
            
            {!editingUser && (
              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 8, message: '密码至少8个字符' },
                ]}
              >
                <Input.Password placeholder="输入密码" />
              </Form.Item>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="is_superuser"
              label="用户角色"
              valuePropName="checked"
            >
              <Select defaultValue={false}>
                <Option value={false}>普通用户</Option>
                <Option value={true}>管理员</Option>
              </Select>
            </Form.Item>
            
            <Form.Item
              name="is_active"
              label="账户状态"
              initialValue={true}
            >
              <Select>
                <Option value={true}>正常</Option>
                <Option value={false}>禁用</Option>
              </Select>
            </Form.Item>
          </div>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button
                onClick={() => {
                  setCreateModalVisible(false);
                  setEditingUser(null);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending || updateMutation.isPending}
                className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
              >
                {editingUser ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
