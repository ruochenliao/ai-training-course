import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Row,
  Space,
  Typography,
  Table,
  Tag,
  Avatar,
  Dropdown,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Tooltip,
  Statistic
} from 'antd'
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LockOutlined,
  UnlockOutlined,
  MoreOutlined,
  CrownOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  MailOutlined
} from '@ant-design/icons'
import { usersApi, type User, type UserCreateRequest, type UserUpdateRequest } from '@/api/users'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()

  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await usersApi.getUsers({
        page,
        size: pageSize,
        search: searchText,
        status: statusFilter
      })

      if (response.data) {
        setUsers(response.data.items)
        setTotal(response.data.total)
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [page, pageSize, searchText, statusFilter])

  // 创建用户
  const handleCreate = async (values: UserCreateRequest) => {
    try {
      await usersApi.createUser(values)
      message.success('用户创建成功')
      setCreateModalVisible(false)
      createForm.resetFields()
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.message || '创建用户失败')
    }
  }

  // 编辑用户
  const handleEdit = (user: User) => {
    setEditingUser(user)
    editForm.setFieldsValue({
      email: user.email,
      full_name: user.full_name,
      is_staff: user.is_staff,
      is_superuser: user.is_superuser,
      status: user.status
    })
    setEditModalVisible(true)
  }

  // 更新用户
  const handleUpdate = async (values: UserUpdateRequest) => {
    if (!editingUser) return

    try {
      await usersApi.updateUser(editingUser.id, values)
      message.success('用户更新成功')
      setEditModalVisible(false)
      setEditingUser(null)
      editForm.resetFields()
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.message || '更新用户失败')
    }
  }

  // 删除用户
  const handleDelete = async (id: number) => {
    try {
      await usersApi.deleteUser(id)
      message.success('用户删除成功')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除用户失败')
    }
  }

  // 激活/禁用用户
  const handleToggleStatus = async (user: User) => {
    try {
      if (user.status === 'active') {
        await usersApi.deactivateUser(user.id)
        message.success('用户已禁用')
      } else {
        await usersApi.activateUser(user.id)
        message.success('用户已激活')
      }
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.message || '操作失败')
    }
  }

  // 重置密码
  const handleResetPassword = async (id: number) => {
    try {
      await usersApi.resetUserPassword(id)
      message.success('密码重置成功')
    } catch (error: any) {
      message.error(error.response?.data?.message || '密码重置失败')
    }
  }

  // 渲染用户状态
  const renderStatus = (status: string) => {
    const statusConfig = {
      active: { color: 'success', text: '正常' },
      inactive: { color: 'default', text: '未激活' },
      locked: { color: 'error', text: '已锁定' },
      disabled: { color: 'warning', text: '已禁用' }
    }

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    return <Tag color={config.color}>{config.text}</Tag>
  }

  // 表格列定义
  const columns = [
    {
      title: '用户信息',
      key: 'user_info',
      render: (_, record: User) => (
        <Space>
          <Avatar
            src={record.avatar_url}
            icon={<UserOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />
          <div>
            <div>
              <Text strong>{record.full_name || record.username}</Text>
              {record.is_superuser && (
                <CrownOutlined style={{ color: '#faad14', marginLeft: 4 }} />
              )}
              {record.is_staff && (
                <TeamOutlined style={{ color: '#52c41a', marginLeft: 4 }} />
              )}
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              @{record.username}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => (
        <Space>
          <MailOutlined />
          <Text>{email}</Text>
        </Space>
      )
    },
    {
      title: '角色',
      key: 'role',
      render: (_, record: User) => (
        <Space direction="vertical" size={2}>
          {record.is_superuser && <Tag color="red">超级管理员</Tag>}
          {record.is_staff && <Tag color="blue">管理员</Tag>}
          {!record.is_superuser && !record.is_staff && <Tag color="default">普通用户</Tag>}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: renderStatus
    },
    {
      title: '登录次数',
      dataIndex: 'login_count',
      key: 'login_count',
      render: (count: number) => count || 0
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      render: (date: string) => (
        date ? (
          <Tooltip title={new Date(date).toLocaleString()}>
            <Space>
              <ClockCircleOutlined />
              <Text>{new Date(date).toLocaleDateString()}</Text>
            </Space>
          </Tooltip>
        ) : (
          <Text type="secondary">从未登录</Text>
        )
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: User) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'edit',
                icon: <EditOutlined />,
                label: '编辑',
                onClick: () => handleEdit(record)
              },
              {
                key: 'toggle_status',
                icon: record.status === 'active' ? <LockOutlined /> : <UnlockOutlined />,
                label: record.status === 'active' ? '禁用' : '激活',
                onClick: () => handleToggleStatus(record)
              },
              {
                key: 'reset_password',
                icon: <LockOutlined />,
                label: '重置密码',
                onClick: () => {
                  Modal.confirm({
                    title: '确认重置密码',
                    content: `确定要重置用户"${record.username}"的密码吗？`,
                    okText: '确认',
                    cancelText: '取消',
                    onOk: () => handleResetPassword(record.id)
                  })
                }
              },
              {
                type: 'divider'
              },
              {
                key: 'delete',
                icon: <DeleteOutlined />,
                label: '删除',
                danger: true,
                onClick: () => {
                  Modal.confirm({
                    title: '确认删除',
                    content: `确定要删除用户"${record.username}"吗？此操作不可恢复。`,
                    okText: '删除',
                    okType: 'danger',
                    cancelText: '取消',
                    onOk: () => handleDelete(record.id)
                  })
                }
              }
            ]
          }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      )
    }
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          用户管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>
          管理系统用户和权限
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={total}
              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={users.filter(user => user.status === 'active').length}
              prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="管理员"
              value={users.filter(user => user.is_staff || user.is_superuser).length}
              prefix={<CrownOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="今日登录"
              value={users.filter(user => {
                if (!user.last_login_at) return false
                const today = new Date().toDateString()
                return new Date(user.last_login_at).toDateString() === today
              }).length}
              prefix={<ClockCircleOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Input
                placeholder="搜索用户名或邮箱"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: 200 }}
              />
              <Select
                placeholder="状态筛选"
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 120 }}
                allowClear
              >
                <Option value="active">正常</Option>
                <Option value="inactive">未激活</Option>
                <Option value="locked">已锁定</Option>
                <Option value="disabled">已禁用</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
              style={{
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
              }}
            >
              添加用户
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 用户表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setPage(page)
              setPageSize(size || 20)
            }
          }}
        />
      </Card>

      {/* 创建用户模态框 */}
      <Modal
        title="添加用户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          createForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名不能超过50个字符' }
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="姓名"
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="is_staff"
                label="管理员权限"
                valuePropName="checked"
                initialValue={false}
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_superuser"
                label="超级管理员"
                valuePropName="checked"
                initialValue={false}
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setCreateModalVisible(false)
                createForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户模态框 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false)
          setEditingUser(null)
          editForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
        >
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="姓名"
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Option value="active">正常</Option>
              <Option value="inactive">未激活</Option>
              <Option value="disabled">已禁用</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="is_staff"
                label="管理员权限"
                valuePropName="checked"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_superuser"
                label="超级管理员"
                valuePropName="checked"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false)
                setEditingUser(null)
                editForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default UsersPage
