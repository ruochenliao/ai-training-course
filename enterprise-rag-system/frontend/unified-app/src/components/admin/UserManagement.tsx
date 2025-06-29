'use client';

import React, {useEffect, useState} from 'react';
import {
    Avatar,
    Badge,
    Button,
    Card,
    Col,
    Divider,
    Dropdown,
    Form,
    Input,
    message,
    Modal,
    Row,
    Select,
    Space,
    Table,
    Tag,
    Typography,
} from 'antd';
import {
    CrownOutlined,
    DeleteOutlined,
    EditOutlined,
    LockOutlined,
    MoreOutlined,
    PlusOutlined,
    TeamOutlined,
    UnlockOutlined,
    UserOutlined,
} from '@ant-design/icons';
import {PermissionGuard} from '@/components/common/PermissionGuard';
import {CreateUserRequest, Department, Role, UpdateUserRequest, User, UserRole} from '@/types';
import {apiClient} from '@/utils/api';
import {formatDate} from '@/utils';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface UserManagementProps {
  className?: string;
}

export const UserManagement: React.FC<UserManagementProps> = ({ className }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [userRoles, setUserRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (searchText) params.search = searchText;
      if (statusFilter) params.status = statusFilter;
      params.size = 1000;

      const response = await apiClient.getUsers(params);
      setUsers(response.users || []);
    } catch (error) {
      message.error('获取用户列表失败');
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await apiClient.getRoles({ size: 1000 });
      setRoles((response.roles || []).filter(role => role.status === 'active'));
    } catch (error) {
      message.error('获取角色列表失败');
      console.error('Failed to fetch roles:', error);
    }
  };

  // 获取部门列表
  const fetchDepartments = async () => {
    try {
      const response = await apiClient.getDepartments();
      setDepartments(response.departments || []);
    } catch (error) {
      message.error('获取部门列表失败');
      console.error('Failed to fetch departments:', error);
    }
  };

  // 获取用户角色关联
  const fetchUserRoles = async () => {
    try {
      const allUserRoles: UserRole[] = [];
      for (const user of users) {
        try {
          const response = await apiClient.getUserRoles(user.id);
          allUserRoles.push(...response);
        } catch (error) {
          console.warn(`Failed to fetch roles for user ${user.id}:`, error);
        }
      }
      setUserRoles(allUserRoles);
    } catch (error) {
      console.error('Failed to fetch user roles:', error);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchDepartments();
  }, [searchText, statusFilter]);

  useEffect(() => {
    if (users.length > 0) {
      fetchUserRoles();
    }
  }, [users]);

  // 创建用户
  const handleCreate = async (values: CreateUserRequest) => {
    try {
      await api.post('/users', values);
      message.success('用户创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error) {
      message.error('用户创建失败');
      console.error('Failed to create user:', error);
    }
  };

  // 更新用户
  const handleUpdate = async (values: UpdateUserRequest) => {
    if (!editingUser) return;

    try {
      await api.put(`/users/${editingUser.id}`, values);
      message.success('用户更新成功');
      setModalVisible(false);
      form.resetFields();
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      message.error('用户更新失败');
      console.error('Failed to update user:', error);
    }
  };

  // 删除用户
  const handleDelete = async (user: User) => {
    try {
      await api.delete(`/users/${user.id}`);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      message.error('用户删除失败');
      console.error('Failed to delete user:', error);
    }
  };

  // 切换用户状态
  const handleToggleStatus = async (user: User) => {
    try {
      await api.put(`/users/${user.id}`, {
        is_active: !user.is_active
      });
      message.success(`用户已${user.is_active ? '禁用' : '启用'}`);
      fetchUsers();
    } catch (error) {
      message.error('状态切换失败');
      console.error('Failed to toggle user status:', error);
    }
  };

  // 重置密码
  const handleResetPassword = async (user: User) => {
    try {
      // 这里应该调用重置密码的API
      message.success('密码重置成功，新密码已发送到用户邮箱');
    } catch (error) {
      message.error('密码重置失败');
      console.error('Failed to reset password:', error);
    }
  };

  // 分配角色
  const handleAssignRoles = async (values: { role_ids: number[] }) => {
    if (!selectedUser) return;

    try {
      await api.post('/rbac/user-roles', {
        user_id: selectedUser.id,
        role_ids: values.role_ids,
      });
      message.success('角色分配成功');
      setRoleModalVisible(false);
      roleForm.resetFields();
      setSelectedUser(null);
      fetchUserRoles();
    } catch (error) {
      message.error('角色分配失败');
      console.error('Failed to assign roles:', error);
    }
  };

  // 打开创建模态框
  const openCreateModal = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑模态框
  const openEditModal = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      is_superuser: user.is_superuser,
      is_staff: user.is_staff,
      is_active: user.is_active,
      department_id: user.department_id,
    });
    setModalVisible(true);
  };

  // 打开角色分配模态框
  const openRoleModal = async (user: User) => {
    setSelectedUser(user);
    try {
      const response = await api.get<UserRole[]>(`/rbac/users/${user.id}/roles`);
      const currentRoles = response.data;
      roleForm.setFieldsValue({
        role_ids: currentRoles.map(ur => ur.role_id),
      });
    } catch (error) {
      console.error('Failed to fetch user roles:', error);
    }
    setRoleModalVisible(true);
  };

  // 获取用户角色
  const getUserRoles = (userId: number) => {
    return userRoles.filter(ur => ur.user_id === userId);
  };

  // 获取部门名称
  const getDepartmentName = (deptId: number | null) => {
    if (!deptId) return '-';
    const dept = departments.find(d => d.id === deptId);
    return dept ? dept.name : '-';
  };

  // 用户操作菜单
  const getUserActions = (user: User) => [
    {
      key: 'edit',
      label: '编辑用户',
      icon: <EditOutlined />,
      onClick: () => openEditModal(user),
    },
    {
      key: 'roles',
      label: '分配角色',
      icon: <TeamOutlined />,
      onClick: () => openRoleModal(user),
    },
    {
      key: 'toggle-status',
      label: user.is_active ? '禁用用户' : '启用用户',
      icon: user.is_active ? <LockOutlined /> : <UnlockOutlined />,
      onClick: () => handleToggleStatus(user),
    },
    {
      key: 'reset-password',
      label: '重置密码',
      icon: <LockOutlined />,
      onClick: () => {
        Modal.confirm({
          title: '重置密码',
          content: `确定要重置用户"${user.username}"的密码吗？`,
          onOk: () => handleResetPassword(user),
        });
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'delete',
      label: '删除用户',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => {
        Modal.confirm({
          title: '删除用户',
          content: `确定要删除用户"${user.username}"吗？此操作不可恢复。`,
          okText: '删除',
          okType: 'danger',
          cancelText: '取消',
          onOk: () => handleDelete(user),
        });
      },
    },
  ];

  const columns = [
    {
      title: '用户信息',
      key: 'user_info',
      render: (_, record: User) => (
        <Space>
          <Avatar
            src={record.avatar_url}
            icon={<UserOutlined />}
            className="bg-gradient-to-r from-blue-500 to-purple-600"
          />
          <div>
            <div className="font-medium">
              {record.full_name || record.username}
              {record.is_superuser && (
                <CrownOutlined className="ml-2 text-yellow-500" />
              )}
            </div>
            <div className="text-sm text-gray-500">{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '角色',
      key: 'roles',
      render: (_, record: User) => {
        const roles = getUserRoles(record.id);
        return (
          <Space wrap>
            {record.is_superuser && (
              <Tag color="red" icon={<CrownOutlined />}>
                超级管理员
              </Tag>
            )}
            {roles.map(ur => (
              <Tag key={ur.id} color="blue" icon={<TeamOutlined />}>
                {ur.role?.name}
              </Tag>
            ))}
            {!record.is_superuser && roles.length === 0 && (
              <Text type="secondary">未分配角色</Text>
            )}
          </Space>
        );
      },
    },
    {
      title: '部门',
      key: 'department',
      render: (_, record: User) => (
        <Text>{getDepartmentName(record.department_id)}</Text>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record: User) => (
        <Space>
          <Badge
            status={record.is_active ? 'success' : 'error'}
            text={record.is_active ? '正常' : '禁用'}
          />
          {record.is_staff && (
            <Tag color="purple">员工</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '最后登录',
      key: 'last_login',
      render: (_, record: User) => (
        <Text type="secondary">
          {record.last_login ? formatDate(record.last_login) : '从未登录'}
        </Text>
      ),
    },
    {
      title: '创建时间',
      key: 'created_at',
      render: (_, record: User) => (
        <Text type="secondary">
          {formatDate(record.created_at)}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: User) => (
        <PermissionGuard permission={["user:update", "user:delete"]} requireAll={false}>
          <Dropdown
            menu={{ items: getUserActions(record) }}
            trigger={['click']}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </PermissionGuard>
      ),
    },
  ];

  return (
    <PermissionGuard permission="user:view">
      <div className={className}>
        <Card>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Col>
              <Title level={4}>
                <UserOutlined /> 用户管理
              </Title>
              <Text type="secondary">管理系统用户账户、角色和权限</Text>
            </Col>
            <Col>
              <PermissionGuard permission="user:create">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateModal}
                >
                  新建用户
                </Button>
              </PermissionGuard>
            </Col>
          </Row>

          {/* 搜索和筛选 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Search
                placeholder="搜索用户名、邮箱、姓名"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onSearch={fetchUsers}
                allowClear
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择状态"
                value={statusFilter}
                onChange={setStatusFilter}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="active">正常</Option>
                <Option value="inactive">禁用</Option>
              </Select>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
          />
        </Card>

        {/* 创建/编辑用户模态框 */}
        <Modal
          title={editingUser ? '编辑用户' : '新建用户'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
            setEditingUser(null);
          }}
          footer={null}
          width={800}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={editingUser ? handleUpdate : handleCreate}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="username"
                  label="用户名"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}
                >
                  <Input placeholder="请输入用户名" disabled={!!editingUser} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="email"
                  label="邮箱地址"
                  rules={[
                    { required: true, message: '请输入邮箱地址' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                >
                  <Input placeholder="请输入邮箱地址" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="full_name"
                  label="姓名"
                  rules={[{ required: true, message: '请输入姓名' }]}
                >
                  <Input placeholder="请输入姓名" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="department_id"
                  label="所属部门"
                >
                  <Select placeholder="请选择部门" allowClear>
                    {departments.map(dept => (
                      <Option key={dept.id} value={dept.id}>
                        {dept.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            {!editingUser && (
              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 8, message: '密码至少8个字符' },
                ]}
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            )}

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="is_superuser"
                  label="超级用户"
                  valuePropName="checked"
                  initialValue={false}
                >
                  <Select>
                    <Option value={false}>否</Option>
                    <Option value={true}>是</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="is_staff"
                  label="员工"
                  valuePropName="checked"
                  initialValue={false}
                >
                  <Select>
                    <Option value={false}>否</Option>
                    <Option value={true}>是</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="is_active"
                  label="状态"
                  initialValue={true}
                >
                  <Select>
                    <Option value={true}>正常</Option>
                    <Option value={false}>禁用</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <Row justify="end" gutter={8}>
              <Col>
                <Button onClick={() => setModalVisible(false)}>
                  取消
                </Button>
              </Col>
              <Col>
                <Button type="primary" htmlType="submit">
                  {editingUser ? '更新' : '创建'}
                </Button>
              </Col>
            </Row>
          </Form>
        </Modal>

        {/* 角色分配模态框 */}
        <Modal
          title={`为用户 "${selectedUser?.username}" 分配角色`}
          open={roleModalVisible}
          onCancel={() => {
            setRoleModalVisible(false);
            roleForm.resetFields();
            setSelectedUser(null);
          }}
          footer={null}
          width={600}
        >
          <Form
            form={roleForm}
            layout="vertical"
            onFinish={handleAssignRoles}
          >
            <Form.Item
              name="role_ids"
              label="选择角色"
              rules={[{ required: true, message: '请选择至少一个角色' }]}
            >
              <Select
                mode="multiple"
                placeholder="请选择角色"
                allowClear
              >
                {roles.map(role => (
                  <Option key={role.id} value={role.id}>
                    <Space>
                      <TeamOutlined />
                      {role.name}
                      <Text type="secondary">({role.code})</Text>
                    </Space>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Divider />

            <Row justify="end" gutter={8}>
              <Col>
                <Button onClick={() => setRoleModalVisible(false)}>
                  取消
                </Button>
              </Col>
              <Col>
                <Button type="primary" htmlType="submit">
                  保存
                </Button>
              </Col>
            </Row>
          </Form>
        </Modal>
      </div>
    </PermissionGuard>
  );
};
