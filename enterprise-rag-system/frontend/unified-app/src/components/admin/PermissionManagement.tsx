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
    Typography,
} from 'antd';
import {
    ApiOutlined,
    ControlOutlined,
    DeleteOutlined,
    EditOutlined,
    MenuOutlined,
    PlusOutlined,
    SafetyOutlined,
} from '@ant-design/icons';
import {PermissionGuard} from '@/components/common/PermissionGuard';
import {CreatePermissionRequest, Permission, UpdatePermissionRequest} from '@/types';
import {apiClient} from '@/utils/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface PermissionManagementProps {
  className?: string;
}

export const PermissionManagement: React.FC<PermissionManagementProps> = ({ className }) => {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  // 获取权限列表
  const fetchPermissions = async () => {
    try {
      setLoading(true);
      const params: any = { size: 1000 };
      if (searchText) params.search = searchText;
      if (selectedGroup) params.group = selectedGroup;
      if (selectedType) params.permission_type = selectedType;

      const response = await apiClient.getPermissions(params);
      setPermissions(response.permissions || []);
    } catch (error) {
      message.error('获取权限列表失败');
      console.error('Failed to fetch permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [searchText, selectedGroup, selectedType]);

  // 创建权限
  const handleCreate = async (values: CreatePermissionRequest) => {
    try {
      await api.post('/rbac/permissions', values);
      message.success('权限创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchPermissions();
    } catch (error) {
      message.error('权限创建失败');
      console.error('Failed to create permission:', error);
    }
  };

  // 更新权限
  const handleUpdate = async (values: UpdatePermissionRequest) => {
    if (!editingPermission) return;

    try {
      await api.put(`/rbac/permissions/${editingPermission.id}`, values);
      message.success('权限更新成功');
      setModalVisible(false);
      form.resetFields();
      setEditingPermission(null);
      fetchPermissions();
    } catch (error) {
      message.error('权限更新失败');
      console.error('Failed to update permission:', error);
    }
  };

  // 删除权限
  const handleDelete = async (permission: Permission) => {
    try {
      await api.delete(`/rbac/permissions/${permission.id}`);
      message.success('权限删除成功');
      fetchPermissions();
    } catch (error) {
      message.error('权限删除失败');
      console.error('Failed to delete permission:', error);
    }
  };

  // 打开创建模态框
  const openCreateModal = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑模态框
  const openEditModal = (permission: Permission) => {
    setEditingPermission(permission);
    form.setFieldsValue({
      name: permission.name,
      code: permission.code,
      description: permission.description,
      group: permission.group,
      resource: permission.resource,
      action: permission.action,
      permission_type: permission.permission_type,
      menu_path: permission.menu_path,
      menu_component: permission.menu_component,
      menu_icon: permission.menu_icon,
      sort_order: permission.sort_order,
      status: permission.status,
    });
    setModalVisible(true);
  };

  // 获取权限分组
  const getPermissionGroups = () => {
    const groups = [...new Set(permissions.map(p => p.group))];
    return groups.sort();
  };

  // 获取权限类型图标
  const getPermissionTypeIcon = (type: string) => {
    switch (type) {
      case 'menu':
        return <MenuOutlined style={{ color: '#1890ff' }} />;
      case 'api':
        return <ApiOutlined style={{ color: '#52c41a' }} />;
      case 'button':
        return <ControlOutlined style={{ color: '#faad14' }} />;
      default:
        return <SafetyOutlined />;
    }
  };

  const columns = [
    {
      title: '权限名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Permission) => (
        <Space>
          {getPermissionTypeIcon(record.permission_type)}
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '权限代码',
      dataIndex: 'code',
      key: 'code',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: '权限分组',
      dataIndex: 'group',
      key: 'group',
      render: (group: string) => <Tag color="blue">{group}</Tag>,
    },
    {
      title: '资源',
      dataIndex: 'resource',
      key: 'resource',
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '类型',
      dataIndex: 'permission_type',
      key: 'permission_type',
      render: (type: string) => {
        const typeMap = {
          menu: { text: '菜单', color: 'blue' },
          api: { text: 'API', color: 'green' },
          button: { text: '按钮', color: 'orange' },
        };
        const config = typeMap[type as keyof typeof typeMap] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '菜单路径',
      dataIndex: 'menu_path',
      key: 'menu_path',
      ellipsis: true,
      render: (path: string) => path ? <Text code>{path}</Text> : '-',
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
      render: (_, record: Permission) => (
        <Space>
          <PermissionGuard permission="permission:update">
            <Tooltip title="编辑权限">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEditModal(record)}
              />
            </Tooltip>
          </PermissionGuard>
          <PermissionGuard permission="permission:delete">
            <Popconfirm
              title="确定要删除这个权限吗？"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除权限">
                <Button
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          </PermissionGuard>
        </Space>
      ),
    },
  ];

  return (
    <PermissionGuard permission="permission:view">
      <div className={className}>
        <Card>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Col>
              <Title level={4}>
                <SafetyOutlined /> 权限管理
              </Title>
            </Col>
            <Col>
              <PermissionGuard permission="permission:create">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateModal}
                >
                  新建权限
                </Button>
              </PermissionGuard>
            </Col>
          </Row>

          {/* 搜索和筛选 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Input.Search
                placeholder="搜索权限名称"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onSearch={fetchPermissions}
                allowClear
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择权限分组"
                value={selectedGroup}
                onChange={setSelectedGroup}
                allowClear
                style={{ width: '100%' }}
              >
                {getPermissionGroups().map(group => (
                  <Option key={group} value={group}>{group}</Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择权限类型"
                value={selectedType}
                onChange={setSelectedType}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="menu">菜单</Option>
                <Option value="api">API</Option>
                <Option value="button">按钮</Option>
              </Select>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={permissions}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
          />
        </Card>

        {/* 创建/编辑权限模态框 */}
        <Modal
          title={editingPermission ? '编辑权限' : '新建权限'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
            setEditingPermission(null);
          }}
          footer={null}
          width={800}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={editingPermission ? handleUpdate : handleCreate}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="权限名称"
                  rules={[{ required: true, message: '请输入权限名称' }]}
                >
                  <Input placeholder="请输入权限名称" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="code"
                  label="权限代码"
                  rules={[{ required: true, message: '请输入权限代码' }]}
                >
                  <Input placeholder="请输入权限代码" disabled={!!editingPermission} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="description"
              label="权限描述"
            >
              <TextArea rows={2} placeholder="请输入权限描述" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="group"
                  label="权限分组"
                  rules={[{ required: true, message: '请输入权限分组' }]}
                >
                  <Input placeholder="请输入权限分组" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="resource"
                  label="资源"
                  rules={[{ required: true, message: '请输入资源' }]}
                >
                  <Input placeholder="请输入资源" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="action"
                  label="操作"
                  rules={[{ required: true, message: '请输入操作' }]}
                >
                  <Input placeholder="请输入操作" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="permission_type"
                  label="权限类型"
                  initialValue="api"
                >
                  <Select placeholder="请选择权限类型">
                    <Option value="menu">菜单</Option>
                    <Option value="api">API</Option>
                    <Option value="button">按钮</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="sort_order"
                  label="排序"
                  initialValue={0}
                >
                  <Input type="number" placeholder="排序" />
                </Form.Item>
              </Col>
              {editingPermission && (
                <Col span={8}>
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

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.permission_type !== currentValues.permission_type
              }
            >
              {({ getFieldValue }) => {
                const permissionType = getFieldValue('permission_type');
                if (permissionType === 'menu') {
                  return (
                    <>
                      <Divider orientation="left">菜单配置</Divider>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            name="menu_path"
                            label="菜单路径"
                          >
                            <Input placeholder="请输入菜单路径" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            name="menu_component"
                            label="菜单组件"
                          >
                            <Input placeholder="请输入菜单组件" />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Form.Item
                        name="menu_icon"
                        label="菜单图标"
                      >
                        <Input placeholder="请输入菜单图标" />
                      </Form.Item>
                    </>
                  );
                }
                return null;
              }}
            </Form.Item>

            <Divider />

            <Row justify="end" gutter={8}>
              <Col>
                <Button onClick={() => setModalVisible(false)}>
                  取消
                </Button>
              </Col>
              <Col>
                <Button type="primary" htmlType="submit">
                  {editingPermission ? '更新' : '创建'}
                </Button>
              </Col>
            </Row>
          </Form>
        </Modal>
      </div>
    </PermissionGuard>
  );
};
