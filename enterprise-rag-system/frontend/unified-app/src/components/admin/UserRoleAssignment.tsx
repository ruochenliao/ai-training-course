'use client';

import React, {useEffect, useState} from 'react';
import {
    Button,
    Card,
    Col,
    DatePicker,
    Divider,
    Form,
    message,
    Modal,
    Row,
    Select,
    Space,
    Table,
    Tag,
    Tooltip,
    Transfer,
    Typography,
} from 'antd';
import {ClockCircleOutlined, SettingOutlined, TeamOutlined, UserOutlined,} from '@ant-design/icons';
import {PermissionGuard} from '@/components/common/PermissionGuard';
import {AssignUserRolesRequest, Department, Role, User, UserRole} from '@/types';
import {apiClient} from '@/utils/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface UserRoleAssignmentProps {
  className?: string;
}

interface TransferItem {
  key: string;
  title: string;
  description?: string;
  disabled?: boolean;
}

export const UserRoleAssignment: React.FC<UserRoleAssignmentProps> = ({ className }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [userRoles, setUserRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await apiClient.getUsers({ size: 1000 });
      setUsers(response.users || []);
    } catch (error) {
      message.error('获取用户列表失败');
      console.error('Failed to fetch users:', error);
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
      const response = await api.get<{
        departments: Department[];
        total: number;
      }>('/rbac/departments');
      setDepartments(response.data.departments);
    } catch (error) {
      message.error('获取部门列表失败');
      console.error('Failed to fetch departments:', error);
    }
  };

  // 获取用户角色列表
  const fetchUserRoles = async () => {
    try {
      setLoading(true);
      const response = await api.get<UserRole[]>('/rbac/user-roles');
      setUserRoles(response.data);
    } catch (error) {
      message.error('获取用户角色列表失败');
      console.error('Failed to fetch user roles:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchDepartments();
    fetchUserRoles();
  }, []);

  // 分配用户角色
  const handleAssignRoles = async (values: {
    role_ids: string[];
    expires_at?: dayjs.Dayjs;
    dept_ids?: number[];
  }) => {
    if (!selectedUser) return;

    try {
      const assignData: AssignUserRolesRequest = {
        user_id: selectedUser.id,
        role_ids: values.role_ids.map(id => parseInt(id)),
        expires_at: values.expires_at?.toISOString(),
        dept_ids: values.dept_ids || [],
      };

      await api.post('/rbac/user-roles', assignData);
      message.success('角色分配成功');
      setModalVisible(false);
      form.resetFields();
      setSelectedUser(null);
      fetchUserRoles();
    } catch (error) {
      message.error('角色分配失败');
      console.error('Failed to assign roles:', error);
    }
  };

  // 打开角色分配模态框
  const openAssignModal = async (user: User) => {
    setSelectedUser(user);
    
    try {
      // 获取用户当前角色
      const response = await api.get<UserRole[]>(`/rbac/users/${user.id}/roles`);
      const currentRoles = response.data;
      
      form.setFieldsValue({
        role_ids: currentRoles.map(ur => ur.role_id.toString()),
        dept_ids: currentRoles.length > 0 ? currentRoles[0].dept_ids : [],
      });
    } catch (error) {
      console.error('Failed to fetch user roles:', error);
    }
    
    setModalVisible(true);
  };

  // 构建用户角色数据
  const buildUserRoleData = () => {
    const userRoleMap = new Map<number, UserRole[]>();
    
    userRoles.forEach(ur => {
      if (!userRoleMap.has(ur.user_id)) {
        userRoleMap.set(ur.user_id, []);
      }
      userRoleMap.get(ur.user_id)!.push(ur);
    });

    return users.map(user => ({
      ...user,
      roles: userRoleMap.get(user.id) || [],
    }));
  };

  // 构建角色穿梭框数据
  const buildRoleTransferData = (): [TransferItem[], string[]] => {
    const dataSource: TransferItem[] = roles.map(role => ({
      key: role.id.toString(),
      title: role.name,
      description: role.description,
      disabled: false,
    }));

    const targetKeys = form.getFieldValue('role_ids') || [];
    
    return [dataSource, targetKeys];
  };

  // 构建部门树数据
  const buildDepartmentOptions = (depts: Department[], parentId: number | null = null, level = 0): React.ReactNode[] => {
    return depts
      .filter(dept => dept.parent_id === parentId)
      .map(dept => (
        <Option key={dept.id} value={dept.id}>
          {'　'.repeat(level)}{dept.name}
        </Option>
      ))
      .concat(
        depts
          .filter(dept => dept.parent_id === parentId)
          .flatMap(dept => buildDepartmentOptions(depts, dept.id, level + 1))
      );
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
          {record.is_superuser && <Tag color="red">超级管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text: string) => text || '-',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '当前角色',
      key: 'roles',
      render: (_, record: User & { roles: UserRole[] }) => (
        <Space wrap>
          {record.roles.map(ur => (
            <Tag key={ur.id} color="blue">
              {ur.role?.name}
              {ur.expires_at && (
                <Tooltip title={`过期时间: ${dayjs(ur.expires_at).format('YYYY-MM-DD HH:mm')}`}>
                  <ClockCircleOutlined style={{ marginLeft: 4 }} />
                </Tooltip>
              )}
            </Tag>
          ))}
          {record.roles.length === 0 && <Text type="secondary">未分配角色</Text>}
        </Space>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record: User) => (
        <Tag color={record.is_active ? 'green' : 'red'}>
          {record.is_active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: User) => (
        <PermissionGuard permission="user_role:manage">
          <Button
            type="link"
            icon={<SettingOutlined />}
            onClick={() => openAssignModal(record)}
          >
            分配角色
          </Button>
        </PermissionGuard>
      ),
    },
  ];

  const [roleDataSource, roleTargetKeys] = buildRoleTransferData();

  return (
    <PermissionGuard permission="user_role:manage">
      <div className={className}>
        <Card>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Col>
              <Title level={4}>
                <TeamOutlined /> 用户角色分配
              </Title>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={buildUserRoleData()}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
          />
        </Card>

        {/* 角色分配模态框 */}
        <Modal
          title={`为用户 "${selectedUser?.username}" 分配角色`}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
            setSelectedUser(null);
          }}
          footer={null}
          width={800}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleAssignRoles}
          >
            <Form.Item
              name="role_ids"
              label="选择角色"
              rules={[{ required: true, message: '请选择至少一个角色' }]}
            >
              <Transfer
                dataSource={roleDataSource}
                targetKeys={roleTargetKeys}
                onChange={(targetKeys) => {
                  form.setFieldsValue({ role_ids: targetKeys });
                }}
                render={item => item.title}
                titles={['可选角色', '已选角色']}
                showSearch
                filterOption={(inputValue, option) =>
                  option.title.toLowerCase().includes(inputValue.toLowerCase()) ||
                  (option.description && option.description.toLowerCase().includes(inputValue.toLowerCase()))
                }
                listStyle={{
                  width: 300,
                  height: 300,
                }}
              />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="expires_at"
                  label="过期时间"
                >
                  <DatePicker
                    showTime
                    placeholder="选择过期时间（可选）"
                    style={{ width: '100%' }}
                    disabledDate={(current) => current && current < dayjs().startOf('day')}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="dept_ids"
                  label="数据权限部门"
                >
                  <Select
                    mode="multiple"
                    placeholder="选择数据权限部门（可选）"
                    allowClear
                  >
                    {buildDepartmentOptions(departments)}
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
