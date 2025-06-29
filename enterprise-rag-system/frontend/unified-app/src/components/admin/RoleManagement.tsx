'use client';

import React, {useEffect, useState} from 'react';
import {
    Button,
    Card,
    Col,
    Divider,
    Form,
    Input,
    message,
    Modal,
    Popconfirm,
    Row,
    Select,
    Space,
    Table,
    Tag,
    Tooltip,
    Tree,
    Typography,
} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined, SafetyOutlined, TeamOutlined,} from '@ant-design/icons';
import {PermissionGuard} from '@/components/common/PermissionGuard';
import {CreateRoleRequest, Permission, Role, UpdateRoleRequest} from '@/types';
import {apiClient} from '@/utils/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface RoleManagementProps {
  className?: string;
}

export const RoleManagement: React.FC<RoleManagementProps> = ({ className }) => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [form] = Form.useForm();
  const [permissionForm] = Form.useForm();

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getRoles();
      setRoles(response.roles || []);
    } catch (error) {
      message.error('获取角色列表失败');
      console.error('Failed to fetch roles:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取权限列表
  const fetchPermissions = async () => {
    try {
      const response = await apiClient.getPermissions({ size: 1000 });
      setPermissions(response.permissions || []);
    } catch (error) {
      message.error('获取权限列表失败');
      console.error('Failed to fetch permissions:', error);
    }
  };

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, []);

  // 创建角色
  const handleCreate = async (values: CreateRoleRequest) => {
    try {
      await api.post('/rbac/roles', values);
      message.success('角色创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchRoles();
    } catch (error) {
      message.error('角色创建失败');
      console.error('Failed to create role:', error);
    }
  };

  // 更新角色
  const handleUpdate = async (values: UpdateRoleRequest) => {
    if (!editingRole) return;

    try {
      await api.put(`/rbac/roles/${editingRole.id}`, values);
      message.success('角色更新成功');
      setModalVisible(false);
      form.resetFields();
      setEditingRole(null);
      fetchRoles();
    } catch (error) {
      message.error('角色更新失败');
      console.error('Failed to update role:', error);
    }
  };

  // 删除角色
  const handleDelete = async (role: Role) => {
    try {
      await apiClient.deleteRole(role.id);
      message.success('角色删除成功');
      fetchRoles();
    } catch (error) {
      message.error('角色删除失败');
      console.error('Failed to delete role:', error);
    }
  };

  // 分配权限
  const handleAssignPermissions = async (values: { permission_ids: number[] }) => {
    if (!selectedRole) return;

    try {
      await apiClient.updateRole(selectedRole.id, {
        permission_ids: values.permission_ids,
      });
      message.success('权限分配成功');
      setPermissionModalVisible(false);
      permissionForm.resetFields();
      setSelectedRole(null);
      fetchRoles();
    } catch (error) {
      message.error('权限分配失败');
      console.error('Failed to assign permissions:', error);
    }
  };

  // 打开创建模态框
  const openCreateModal = () => {
    setEditingRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑模态框
  const openEditModal = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue({
      name: role.name,
      code: role.code,
      description: role.description,
      data_scope: role.data_scope,
      status: role.status,
    });
    setModalVisible(true);
  };

  // 打开权限分配模态框
  const openPermissionModal = (role: Role) => {
    setSelectedRole(role);
    const permissionIds = role.permissions?.map(p => p.id) || [];
    permissionForm.setFieldsValue({
      permission_ids: permissionIds,
    });
    setPermissionModalVisible(true);
  };

  // 构建权限树数据
  const buildPermissionTree = () => {
    const groupedPermissions = permissions.reduce((acc, permission) => {
      if (!acc[permission.group]) {
        acc[permission.group] = [];
      }
      acc[permission.group].push(permission);
      return acc;
    }, {} as Record<string, Permission[]>);

    return Object.entries(groupedPermissions).map(([group, perms]) => ({
      title: group,
      key: group,
      children: perms.map(perm => ({
        title: perm.name,
        key: perm.id,
        isLeaf: true,
      })),
    }));
  };

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Role) => (
        <Space>
          <TeamOutlined />
          <span>{text}</span>
          {record.role_type === 'system' && (
            <Tag color="blue">系统角色</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '角色代码',
      dataIndex: 'code',
      key: 'code',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '数据权限',
      dataIndex: 'data_scope',
      key: 'data_scope',
      render: (scope: string) => {
        const scopeMap = {
          all: { text: '全部数据', color: 'red' },
          dept_and_child: { text: '本部门及子部门', color: 'orange' },
          dept: { text: '本部门', color: 'blue' },
          custom: { text: '自定义', color: 'green' },
        };
        const config = scopeMap[scope as keyof typeof scopeMap] || { text: scope, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '用户数',
      dataIndex: 'user_count',
      key: 'user_count',
      render: (count: number) => <Text>{count || 0}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Role) => (
        <Space>
          <PermissionGuard permission="role:update">
            <Tooltip title="编辑角色">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEditModal(record)}
              />
            </Tooltip>
          </PermissionGuard>
          <PermissionGuard permission="role:assign_permission">
            <Tooltip title="分配权限">
              <Button
                type="link"
                icon={<SafetyOutlined />}
                onClick={() => openPermissionModal(record)}
              />
            </Tooltip>
          </PermissionGuard>
          <PermissionGuard permission="role:delete">
            {record.role_type !== 'system' && (
              <Popconfirm
                title="确定要删除这个角色吗？"
                onConfirm={() => handleDelete(record)}
                okText="确定"
                cancelText="取消"
              >
                <Tooltip title="删除角色">
                  <Button
                    type="link"
                    danger
                    icon={<DeleteOutlined />}
                  />
                </Tooltip>
              </Popconfirm>
            )}
          </PermissionGuard>
        </Space>
      ),
    },
  ];

  return (
    <PermissionGuard permission="role:view">
      <div className={className}>
        <Card>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Col>
              <Title level={4}>
                <TeamOutlined /> 角色管理
              </Title>
            </Col>
            <Col>
              <PermissionGuard permission="role:create">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateModal}
                >
                  新建角色
                </Button>
              </PermissionGuard>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={roles}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
          />
        </Card>

        {/* 创建/编辑角色模态框 */}
        <Modal
          title={editingRole ? '编辑角色' : '新建角色'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
            setEditingRole(null);
          }}
          footer={null}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={editingRole ? handleUpdate : handleCreate}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="角色名称"
                  rules={[{ required: true, message: '请输入角色名称' }]}
                >
                  <Input placeholder="请输入角色名称" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="code"
                  label="角色代码"
                  rules={[{ required: true, message: '请输入角色代码' }]}
                >
                  <Input placeholder="请输入角色代码" disabled={!!editingRole} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="description"
              label="角色描述"
            >
              <TextArea rows={3} placeholder="请输入角色描述" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="data_scope"
                  label="数据权限"
                  initialValue="custom"
                >
                  <Select placeholder="请选择数据权限范围">
                    <Option value="all">全部数据</Option>
                    <Option value="dept_and_child">本部门及子部门</Option>
                    <Option value="dept">本部门</Option>
                    <Option value="custom">自定义</Option>
                  </Select>
                </Form.Item>
              </Col>
              {editingRole && (
                <Col span={12}>
                  <Form.Item
                    name="status"
                    label="状态"
                  >
                    <Select placeholder="请选择状态">
                      <Option value="active">启用</Option>
                      <Option value="inactive">禁用</Option>
                    </Select>
                  </Form.Item>
                </Col>
              )}
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
                  {editingRole ? '更新' : '创建'}
                </Button>
              </Col>
            </Row>
          </Form>
        </Modal>

        {/* 权限分配模态框 */}
        <Modal
          title={`为角色 "${selectedRole?.name}" 分配权限`}
          open={permissionModalVisible}
          onCancel={() => {
            setPermissionModalVisible(false);
            permissionForm.resetFields();
            setSelectedRole(null);
          }}
          footer={null}
          width={800}
        >
          <Form
            form={permissionForm}
            layout="vertical"
            onFinish={handleAssignPermissions}
          >
            <Form.Item
              name="permission_ids"
              label="选择权限"
            >
              <Tree
                checkable
                treeData={buildPermissionTree()}
                height={400}
              />
            </Form.Item>

            <Divider />

            <Row justify="end" gutter={8}>
              <Col>
                <Button onClick={() => setPermissionModalVisible(false)}>
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
