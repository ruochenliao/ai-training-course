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
import {ApartmentOutlined, DeleteOutlined, EditOutlined, PlusOutlined, UserOutlined,} from '@ant-design/icons';
import {PermissionGuard} from '@/components/common/PermissionGuard';
import {CreateDepartmentRequest, Department, UpdateDepartmentRequest, User} from '@/types';
import {apiClient} from '@/utils/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface DepartmentManagementProps {
  className?: string;
}

export const DepartmentManagement: React.FC<DepartmentManagementProps> = ({ className }) => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [form] = Form.useForm();

  // 获取部门列表
  const fetchDepartments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getDepartments();
      setDepartments(response.departments || []);
    } catch (error) {
      message.error('获取部门列表失败');
      console.error('Failed to fetch departments:', error);
    } finally {
      setLoading(false);
    }
  };

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

  useEffect(() => {
    fetchDepartments();
    fetchUsers();
  }, []);

  // 创建部门
  const handleCreate = async (values: CreateDepartmentRequest) => {
    try {
      await api.post('/rbac/departments', values);
      message.success('部门创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchDepartments();
    } catch (error) {
      message.error('部门创建失败');
      console.error('Failed to create department:', error);
    }
  };

  // 更新部门
  const handleUpdate = async (values: UpdateDepartmentRequest) => {
    if (!editingDepartment) return;

    try {
      await api.put(`/rbac/departments/${editingDepartment.id}`, values);
      message.success('部门更新成功');
      setModalVisible(false);
      form.resetFields();
      setEditingDepartment(null);
      fetchDepartments();
    } catch (error) {
      message.error('部门更新失败');
      console.error('Failed to update department:', error);
    }
  };

  // 删除部门
  const handleDelete = async (department: Department) => {
    try {
      await api.delete(`/rbac/departments/${department.id}`);
      message.success('部门删除成功');
      fetchDepartments();
    } catch (error) {
      message.error('部门删除失败');
      console.error('Failed to delete department:', error);
    }
  };

  // 打开创建模态框
  const openCreateModal = () => {
    setEditingDepartment(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑模态框
  const openEditModal = (department: Department) => {
    setEditingDepartment(department);
    form.setFieldsValue({
      name: department.name,
      code: department.code,
      description: department.description,
      parent_id: department.parent_id,
      sort_order: department.sort_order,
      manager_id: department.manager_id,
      status: department.status,
    });
    setModalVisible(true);
  };

  // 构建部门树数据
  const buildDepartmentTree = () => {
    const departmentMap = new Map<number, Department>();
    departments.forEach(dept => departmentMap.set(dept.id, dept));

    const tree: Department[] = [];
    departments.forEach(dept => {
      if (dept.parent_id === null) {
        tree.push({
          ...dept,
          children: buildChildren(dept.id, departmentMap)
        });
      }
    });

    return tree.sort((a, b) => a.sort_order - b.sort_order);
  };

  const buildChildren = (parentId: number, departmentMap: Map<number, Department>): Department[] => {
    const children: Department[] = [];
    departments.forEach(dept => {
      if (dept.parent_id === parentId) {
        children.push({
          ...dept,
          children: buildChildren(dept.id, departmentMap)
        });
      }
    });
    return children.sort((a, b) => a.sort_order - b.sort_order);
  };

  // 获取用户名
  const getUserName = (userId: number | null) => {
    if (!userId) return '-';
    const user = users.find(u => u.id === userId);
    return user ? user.full_name || user.username : '-';
  };

  const columns = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Department) => (
        <Space>
          <ApartmentOutlined />
          <span>{text}</span>
          <Text type="secondary">({record.code})</Text>
        </Space>
      ),
    },
    {
      title: '部门描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '部门负责人',
      dataIndex: 'manager_id',
      key: 'manager_id',
      render: (managerId: number) => (
        <Space>
          <UserOutlined />
          <span>{getUserName(managerId)}</span>
        </Space>
      ),
    },
    {
      title: '层级',
      dataIndex: 'level',
      key: 'level',
      render: (level: number) => <Tag color="blue">L{level}</Tag>,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
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
      render: (_, record: Department) => (
        <Space>
          <PermissionGuard permission="dept:update">
            <Tooltip title="编辑部门">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEditModal(record)}
              />
            </Tooltip>
          </PermissionGuard>
          <PermissionGuard permission="dept:delete">
            <Popconfirm
              title="确定要删除这个部门吗？"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除部门">
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
    <PermissionGuard permission="dept:view">
      <div className={className}>
        <Card>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Col>
              <Title level={4}>
                <ApartmentOutlined /> 部门管理
              </Title>
            </Col>
            <Col>
              <PermissionGuard permission="dept:create">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateModal}
                >
                  新建部门
                </Button>
              </PermissionGuard>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={buildDepartmentTree()}
            rowKey="id"
            loading={loading}
            pagination={false}
            expandable={{
              defaultExpandAllRows: true,
            }}
          />
        </Card>

        {/* 创建/编辑部门模态框 */}
        <Modal
          title={editingDepartment ? '编辑部门' : '新建部门'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
            setEditingDepartment(null);
          }}
          footer={null}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={editingDepartment ? handleUpdate : handleCreate}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="部门名称"
                  rules={[{ required: true, message: '请输入部门名称' }]}
                >
                  <Input placeholder="请输入部门名称" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="code"
                  label="部门代码"
                  rules={[{ required: true, message: '请输入部门代码' }]}
                >
                  <Input placeholder="请输入部门代码" disabled={!!editingDepartment} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="description"
              label="部门描述"
            >
              <TextArea rows={3} placeholder="请输入部门描述" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="parent_id"
                  label="上级部门"
                >
                  <Select placeholder="请选择上级部门" allowClear>
                    {departments
                      .filter(dept => !editingDepartment || dept.id !== editingDepartment.id)
                      .map(dept => (
                        <Option key={dept.id} value={dept.id}>
                          {dept.name}
                        </Option>
                      ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="manager_id"
                  label="部门负责人"
                >
                  <Select placeholder="请选择部门负责人" allowClear showSearch>
                    {users.map(user => (
                      <Option key={user.id} value={user.id}>
                        {user.full_name || user.username} ({user.email})
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="sort_order"
                  label="排序"
                  initialValue={0}
                >
                  <Input type="number" placeholder="排序" />
                </Form.Item>
              </Col>
              {editingDepartment && (
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
                  {editingDepartment ? '更新' : '创建'}
                </Button>
              </Col>
            </Row>
          </Form>
        </Modal>
      </div>
    </PermissionGuard>
  );
};
