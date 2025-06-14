import React, { useCallback, useEffect, useState } from 'react'
import { Avatar, Button, Card, Col, Form, Input, Layout, message, Modal, Popconfirm, Row, Select, Space, Switch, Table, Tag, Tree } from 'antd'
import { DeleteOutlined, EditOutlined, KeyOutlined, PlusOutlined, ReloadOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons'

import { type CreateUserParams, type UpdateUserParams, type User, userApi, type UserQueryParams } from '@/api/user'
import { type Role, roleApi } from '@/api/role'
import { type Dept, deptApi } from '@/api/dept'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/utils'
import CommonPagination from '@/components/CommonPagination'

const { Sider, Content } = Layout

interface RoleOption {
  value: number
  label: string
}

interface DepartmentOption {
  value: number
  label: string
}

const UserManagement: React.FC = () => {
  const { isDark, primaryColor } = useTheme()
  const [loading, setLoading] = useState<boolean>(false)
  const [userData, setUserData] = useState<User[]>([])
  const [total, setTotal] = useState<number>(0)
  const [current, setCurrent] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [modalVisible, setModalVisible] = useState<boolean>(false)
  const [modalTitle, setModalTitle] = useState<string>('')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [form] = Form.useForm()
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState<UserQueryParams>({})
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([])
  const [deptOptions, setDepartmentOptions] = useState<DepartmentOption[]>([])
  const [selectedDeptId, setSelectedDeptId] = useState<number | null>(null)
  const [lastClickedNodeId, setLastClickedNodeId] = useState<number | null>(null)
  const [confirmPassword, setConfirmPassword] = useState<string>('')

  // 获取角色和部门数据
  const fetchRolesAndDepts = useCallback(async () => {
    try {
      // 分开获取角色和部门以避免类型错误
      try {
        const rolesRes = await roleApi.list({ page: 1, page_size: 1000 })
        if (rolesRes.code === 200 && rolesRes.data) {
          // 使用any类型处理复杂的返回类型
          const data: any = rolesRes.data
          const roleData = Array.isArray(data) ? data : data.data || []
          setRoleOptions(
            roleData.map((role: Role) => ({
              value: role.id,
              label: role.name,
            })),
          )
        }
      } catch (error) {
        console.warn('Failed to fetch roles:', error)
      }

      try {
        const deptsRes = await deptApi.list()
        if (deptsRes.code === 200 && deptsRes.data) {
          setDepartmentOptions(
            deptsRes.data.map((dept: Dept) => ({
              value: dept.id,
              label: dept.name,
            })),
          )
        }
      } catch (error) {
        console.warn('Failed to fetch departments:', error)
      }
    } catch (error) {
      console.error('Failed to fetch roles and departments:', error)
      message.error('获取角色和部门数据失败')
    }
  }, [])

  // 获取用户数据
  const fetchUserData = useCallback(
    async (params?: UserQueryParams) => {
      setLoading(true)
      try {
        const queryParams = {
          page: current,
          page_size: pageSize,
          ...searchParams,
          ...params,
          ...(selectedDeptId && { dept_id: selectedDeptId }),
        }

        const response = await userApi.getUsers(queryParams)

        if (response.code === 200 && response.data) {
          // 处理分页数据结构
          const userData = response.data.data || response.data || []
          setUserData(userData)
          setTotal(response.data.total || 0)
          setCurrent(response.data.page || queryParams.page || 1)
          setPageSize(response.data.page_size || queryParams.page_size || 10)
        } else {
          message.error(response.message || '获取用户数据失败')
          setUserData([])
        }
      } catch (error) {
        console.error('Fetch user data error:', error)
        message.error('获取用户数据失败')
        setUserData([])
      } finally {
        setLoading(false)
      }
    },
    [current, pageSize, searchParams, selectedDeptId],
  )

  useEffect(() => {
    fetchRolesAndDepts()
    fetchUserData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedDeptId !== null) {
      fetchUserData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDeptId])

  // 处理部门树点击
  const handleDeptSelect = (selectedKeys: React.Key[]) => {
    const nodeId = selectedKeys[0] as number

    if (lastClickedNodeId === nodeId) {
      // 如果点击的是同一个节点，则取消选择
      setSelectedDeptId(null)
      setLastClickedNodeId(null)
    } else {
      // 选择新的部门
      setSelectedDeptId(nodeId)
      setLastClickedNodeId(nodeId)
    }
  }

  const handleToggleUserStatus = async (userId: number, isActive: boolean) => {
    try {
      // 找到当前用户的完整信息
      const currentUser = userData.find((user) => user.id === userId)
      if (!currentUser) {
        message.error('用户信息不存在')
        return
      }

      const response = await userApi.updateUser({
        id: userId,
        email: currentUser.email,
        username: currentUser.username,
        is_active: isActive,
        role_ids: currentUser.roles?.map((role) => role.id) || [],
        dept_id: currentUser.dept_id || currentUser.dept?.id || 0,
      })
      if (response.code === 200) {
        message.success('用户状态更新成功')
        fetchUserData()
      } else {
        message.error(response.message || '用户状态更新失败')
      }
    } catch (error) {
      console.error('Toggle user status error:', error)
      message.error('用户状态更新失败')
    }
  }

  const handleAddUser = () => {
    setModalTitle('新增用户')
    setCurrentUser(null)
    form.resetFields()
    setConfirmPassword('')
    setModalVisible(true)
  }

  const handleEditUser = (record: User) => {
    setModalTitle('编辑用户')
    setCurrentUser(record)
    form.setFieldsValue({
      username: record.username,
      email: record.email,
      roles: record.roles && record.roles.length > 0 ? record.roles.map((role) => role.id) : [],
      department: record.dept_id || (record.dept && record.dept.id) || undefined,
      is_superuser: record.is_superuser,
      is_active: !record.is_active, // 注意：表单中的is_active表示"禁用"状态
    })
    setConfirmPassword('')
    setModalVisible(true)
  }

  const handleDeleteUser = async (id: number) => {
    try {
      const response = await userApi.deleteUser(id)
      if (response.code === 200) {
        message.success('用户删除成功')
        fetchUserData()
      } else {
        message.error(response.message || '用户删除失败')
      }
    } catch (error) {
      console.error('Delete user error:', error)
      message.error('用户删除失败')
    }
  }

  const handleResetPassword = async (id: number) => {
    try {
      const response = await userApi.resetPassword({ user_id: id })
      if (response.code === 200) {
        message.success('密码重置成功')
      } else {
        message.error(response.message || '密码重置失败')
      }
    } catch (error) {
      console.error('Reset password error:', error)
      message.error('密码重置失败')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()

      // 检查密码字段
      if (!currentUser && values.password !== confirmPassword) {
        message.error('两次输入的密码不一致')
        return
      }

      // 处理表单数据
      const userData = {
        username: values.username,
        email: values.email,
        role_ids: values.roles || [],
        dept_id: values.department || 0,
        is_superuser: values.is_superuser || false,
        is_active: !values.is_active, // 表单中is_active代表"是否禁用"，需要取反
        ...(currentUser ? { id: currentUser.id } : {}),
        ...(!currentUser || values.password ? { password: values.password } : {}),
      }

      const response = currentUser ? await userApi.updateUser(userData as UpdateUserParams) : await userApi.createUser(userData as CreateUserParams)

      if (response.code === 200) {
        message.success(`${currentUser ? '更新' : '创建'}用户成功`)
        setModalVisible(false)
        fetchUserData()
      } else {
        message.error(response.message || `${currentUser ? '更新' : '创建'}用户失败`)
      }
    } catch (error) {
      console.error('Save user error:', error)
      message.error(`${currentUser ? '更新' : '创建'}用户失败`)
    }
  }

  const handleSearch = (values: any) => {
    const params: UserQueryParams = {}

    if (values.username) {
      params.username = values.username
    }

    if (values.email) {
      params.email = values.email
    }

    if (values.role_id) {
      // 角色ID查询在API中可能不支持，将在API调用前过滤相关结果
      // 暂时保留前端过滤方案
    }

    setSearchParams(params)
    setCurrent(1) // 重置为第一页
    fetchUserData({ ...params, page: 1 })
  }

  const resetSearch = () => {
    searchForm.resetFields()
    setSearchParams({})
    setSelectedDeptId(null)
    setLastClickedNodeId(null)
    setCurrent(1) // 重置为第一页
    fetchUserData({ page: 1 })
  }

  // 处理分页变化
  const handleTableChange = (page: number, size: number) => {
    setCurrent(page)
    setPageSize(size)
    fetchUserData({ page, page_size: size })
  }

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <div className='flex items-center gap-2'>
          <Avatar
            icon={<UserOutlined />}
            style={{
              backgroundColor: record.is_superuser ? '#ff4d4f' : primaryColor,
              fontSize: '14px',
            }}
            size='small'
          />
          <span>{text}</span>
          {record.is_superuser && (
            <Tag color='red' className='ml-2'>
              管理员
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '所属部门',
      dataIndex: 'dept',
      key: 'dept',
      render: (dept: any) => (dept ? dept.name : '-'),
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: Role[]) => (
        <Space size={[0, 4]} wrap>
          {roles && roles.length > 0
            ? roles.map((role) => (
                <Tag key={role.id} color='blue'>
                  {role.name}
                </Tag>
              ))
            : '-'}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean, record: User) => (
        <Switch
          checked={isActive}
          onChange={(checked) => handleToggleUserStatus(record.id, checked)}
          checkedChildren='启用'
          unCheckedChildren='禁用'
          disabled={record.is_superuser && record.username === 'admin'} // 禁止修改admin超级管理员
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (text: string, record: User) => (
        <Space size='small' wrap>
          <Button
            type='link'
            size='small'
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
            disabled={record.is_superuser && record.username === 'admin' && !record.is_superuser} // 非管理员禁止修改admin
            className='action-button'
          >
            编辑
          </Button>
          <Popconfirm title='确定要重置该用户的密码吗？' onConfirm={() => handleResetPassword(record.id)} okText='确定' cancelText='取消'>
            <Button
              type='link'
              size='small'
              icon={<KeyOutlined />}
              disabled={record.is_superuser && record.username === 'admin' && !record.is_superuser} // 非管理员禁止重置admin密码
              className='action-button'
            >
              重置密码
            </Button>
          </Popconfirm>
          <Popconfirm
            title='确定要删除该用户吗？'
            onConfirm={() => handleDeleteUser(record.id)}
            okText='确定'
            cancelText='取消'
            disabled={record.is_superuser || record.username === 'admin'} // 禁止删除超级管理员或admin
          >
            <Button
              type='link'
              size='small'
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_superuser || record.username === 'admin'} // 禁止删除超级管理员或admin
              className='action-button delete-button'
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className='user-management h-full'>
      <Layout className={cn('h-full rounded-lg overflow-hidden', isDark ? 'bg-gray-800' : 'bg-white')}>
        {/* 左侧部门树 */}
        <Sider
          width={250}
          theme={isDark ? 'dark' : 'light'}
          className={cn('border-r', isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white')}
        >
          <div className={cn('p-4 border-b', isDark ? 'border-gray-700' : 'border-gray-200')}>
            <h3 className={cn('text-lg font-medium', isDark ? 'text-white' : 'text-gray-800')}>部门列表</h3>
          </div>
          <div className='p-4'>
            <Tree
              defaultExpandAll
              blockNode
              treeData={deptOptions.map((dept) => ({
                title: dept.label,
                key: dept.value,
              }))}
              selectedKeys={selectedDeptId ? [selectedDeptId] : []}
              onSelect={handleDeptSelect}
              className={isDark ? 'ant-tree-dark' : ''}
            />
          </div>
        </Sider>

        {/* 右侧内容区 */}
        <Content className={cn('p-4', isDark ? 'bg-gray-800' : 'bg-white')}>
          {/* 搜索表单 */}
          <Card className={cn('mb-4 system-card', isDark ? 'bg-gray-800 border-gray-700' : 'bg-white')} bordered={false}>
            <Form form={searchForm} layout='inline' onFinish={handleSearch} className='gap-4 flex-wrap system-form' style={{ rowGap: '12px' }}>
              <Form.Item name='username' label='用户名'>
                <Input placeholder='请输入用户名' allowClear />
              </Form.Item>
              <Form.Item name='email' label='邮箱'>
                <Input placeholder='请输入邮箱' allowClear />
              </Form.Item>
              <Form.Item name='role_id' label='角色'>
                <Select placeholder='请选择角色' style={{ width: 180 }} options={roleOptions} allowClear />
              </Form.Item>
              <Form.Item className='flex-none'>
                <Space>
                  <Button
                    type='primary'
                    htmlType='submit'
                    icon={<SearchOutlined />}
                    style={{ backgroundColor: primaryColor }}
                    className='search-button'
                  >
                    搜索
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={resetSearch} className='reset-button'>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* 用户表格 */}
          <Card
            className={cn('system-card', isDark ? 'bg-gray-800 border-gray-700' : 'bg-white')}
            bordered={false}
            title={
              <div className={cn('flex items-center justify-between', isDark ? 'text-white' : 'text-gray-800')}>
                <span className='font-medium'>用户列表</span>
                <Space>
                  <Button
                    type='primary'
                    icon={<PlusOutlined />}
                    onClick={handleAddUser}
                    style={{ backgroundColor: primaryColor }}
                    className='add-button'
                  >
                    新增用户
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={() => fetchUserData()} className='reset-button'>
                    刷新
                  </Button>
                </Space>
              </div>
            }
          >
            <Table
              columns={columns}
              dataSource={userData}
              rowKey='id'
              pagination={CommonPagination({
                current,
                pageSize,
                total,
                onChange: handleTableChange,
              })}
              loading={loading}
              className={cn('system-table', isDark ? 'ant-table-dark' : '')}
              bordered
              size='middle'
            />
          </Card>
        </Content>
      </Layout>

      {/* 用户表单弹窗 */}
      <Modal title={modalTitle} open={modalVisible} onOk={handleModalOk} onCancel={() => setModalVisible(false)} width={600} className='system-modal'>
        <Form
          form={form}
          layout='vertical'
          initialValues={{
            is_active: false, // 默认启用（表单中的is_active表示"禁用"状态）
            is_superuser: false,
          }}
          className='mt-4 system-form'
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name='username'
                label='用户名'
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名长度不能少于3个字符' },
                ]}
              >
                <Input placeholder='请输入用户名' />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name='email'
                label='邮箱'
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input placeholder='请输入邮箱地址' />
              </Form.Item>
            </Col>
          </Row>

          {!currentUser && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name='password'
                  label='密码'
                  rules={[
                    { required: !currentUser, message: '请输入密码' },
                    { min: 6, message: '密码长度不能少于6个字符' },
                  ]}
                >
                  <Input.Password placeholder='请输入密码' />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label='确认密码'
                  rules={[
                    { required: !currentUser, message: '请确认密码' },
                    {
                      validator: (_, value) => {
                        const password = form.getFieldValue('password')
                        if (!value || password === value) {
                          return Promise.resolve()
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'))
                      },
                    },
                  ]}
                >
                  <Input.Password placeholder='请再次输入密码' value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
                </Form.Item>
              </Col>
            </Row>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name='department' label='所属部门' rules={[{ required: true, message: '请选择部门' }]}>
                <Select placeholder='请选择部门' options={deptOptions} showSearch optionFilterProp='label' />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name='roles' label='角色' rules={[{ required: true, message: '请选择角色' }]}>
                <Select placeholder='请选择角色' mode='multiple' options={roleOptions} showSearch optionFilterProp='label' />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name='is_superuser' valuePropName='checked' label='超级管理员'>
                <Switch checkedChildren='是' unCheckedChildren='否' className='custom-switch' />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name='is_active' valuePropName='checked' label='禁用账号'>
                <Switch checkedChildren='是' unCheckedChildren='否' className='custom-switch' />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default UserManagement
