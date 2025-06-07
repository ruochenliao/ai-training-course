import React, {useCallback, useEffect, useState} from 'react';
import {
    Button,
    Card,
    Form,
    Input,
    Layout,
    message,
    Modal,
    Popconfirm,
    Select,
    Space,
    Switch,
    Table,
    Tag,
    Tree
} from 'antd';
import {DeleteOutlined, EditOutlined, KeyOutlined, PlusOutlined, ReloadOutlined} from '@ant-design/icons';

import {type CreateUserParams, type UpdateUserParams, type User, userApi, type UserQueryParams} from '@/api/user';
import {type Role, roleApi} from '@/api/role';
import {type Dept, deptApi} from '@/api/dept';

const { Sider, Content } = Layout;

interface RoleOption {
  value: number;
  label: string;
}

interface DepartmentOption {
  value: number;
  label: string;
}

const UserManagement: React.FC = () => {

  const [loading, setLoading] = useState<boolean>(false);
  const [userData, setUserData] = useState<User[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [searchParams, setSearchParams] = useState<UserQueryParams>({});
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([]);
  const [deptOptions, setDepartmentOptions] = useState<DepartmentOption[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<number | null>(null);
  const [lastClickedNodeId, setLastClickedNodeId] = useState<number | null>(null);
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  
  // 获取角色和部门数据
  const fetchRolesAndDepts = useCallback(async () => {
    try {
      const [rolesRes, deptsRes] = await Promise.all([
        roleApi.list({ page: 1, page_size: 1000 }),
        deptApi.list({ page: 1, page_size: 1000 })
      ]);
      
      if (rolesRes.code === 200 && rolesRes.data) {
        const roleData = rolesRes.data.data || rolesRes.data;
        setRoleOptions(roleData.map((role: Role) => ({
          value: role.id,
          label: role.name
        })));
      } else {
        console.warn('Failed to fetch roles:', rolesRes.message);
      }
      
      if (deptsRes.code === 200 && deptsRes.data) {
        setDepartmentOptions(deptsRes.data.map((dept: Dept) => ({
          value: dept.id,
          label: dept.name
        })));
      } else {
        console.warn('Failed to fetch departments:', deptsRes.message);
      }
    } catch (error) {
      console.error('Failed to fetch roles and departments:', error);
      message.error('获取角色和部门数据失败');
    }
  }, []);

  // 获取用户数据
  const fetchUserData = useCallback(async (params?: UserQueryParams) => {
    setLoading(true);
    try {
      const queryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        ...searchParams,
        ...params,
        ...(selectedDeptId && { dept_id: selectedDeptId })
      };
      
      const response = await userApi.getUsers(queryParams);
      
      if (response.code === 200 && response.data) {
        // 处理分页数据结构
        const userData = response.data.data || response.data || [];
        setUserData(userData);
        setPagination({
          current: response.data.page || queryParams.page || 1,
          pageSize: response.data.page_size || queryParams.page_size || 10,
          total: response.data.total || 0,
        });
      } else {
        message.error(response.message || '获取用户数据失败');
        setUserData([]);
      }
    } catch (error) {
      console.error('Fetch user data error:', error);
      message.error('获取用户数据失败');
      setUserData([]);
    } finally {
      setLoading(false);
    }
  }, [pagination.current, pagination.pageSize, searchParams, selectedDeptId]);

  useEffect(() => {
    fetchRolesAndDepts();
    fetchUserData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedDeptId !== null) {
      fetchUserData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDeptId]);

  // 处理部门树点击
  const handleDeptSelect = (selectedKeys: React.Key[], info: any) => {
    const nodeId = selectedKeys[0] as number;
    
    if (lastClickedNodeId === nodeId) {
      // 如果点击的是同一个节点，则取消选择
      setSelectedDeptId(null);
      setLastClickedNodeId(null);
    } else {
      // 选择新的部门
      setSelectedDeptId(nodeId);
      setLastClickedNodeId(nodeId);
    }
  };

  const handleToggleUserStatus = async (userId: number, isActive: boolean) => {
    try {
      // 找到当前用户的完整信息
      const currentUser = userData.find(user => user.id === userId);
      if (!currentUser) {
        message.error('用户信息不存在');
        return;
      }
      
      const response = await userApi.updateUser({ 
        id: userId, 
        email: currentUser.email,
        username: currentUser.username,
        is_active: isActive,
        is_superuser: currentUser.is_superuser,
        role_ids: currentUser.roles?.map(role => role.id) || [],
        dept_id: currentUser.dept_id || currentUser.dept?.id || 0
      });
      if (response.code === 200) {
        message.success('用户状态更新成功');
        fetchUserData();
      } else {
        message.error(response.message || '用户状态更新失败');
      }
    } catch (error) {
      console.error('Toggle user status error:', error);
      message.error('用户状态更新失败');
    }
  };



  const handleAddUser = () => {
    setModalTitle('新增用户');
    setCurrentUser(null);
    form.resetFields();
    setConfirmPassword('');
    setModalVisible(true);
  };

  const handleEditUser = (record: User) => {
    setModalTitle('编辑用户');
    setCurrentUser(record);
    form.setFieldsValue({
      username: record.username,
      email: record.email,
      roles: record.roles && record.roles.length > 0 ? record.roles.map(role => role.id) : [],
      department: record.dept_id || (record.dept && record.dept.id) || undefined,
      is_superuser: record.is_superuser,
      is_active: !record.is_active, // 注意：表单中的is_active表示"禁用"状态
    });
    setConfirmPassword('');
    setModalVisible(true);
  };

  const handleDeleteUser = async (id: number) => {
    try {
      const response = await userApi.deleteUser(id);
      
      if (response.code === 200) {
        message.success('删除成功');
        fetchUserData();
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      console.error('Delete user error:', error);
      message.error('删除失败');
    }
  };

  const handleResetPassword = async (id: number) => {
    try {
      const response = await userApi.resetPassword({
        user_id: id
      });
      
      if (response.code === 200) {
        message.success('密码重置成功');
      } else {
        message.error(response.message || '密码重置失败');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      message.error('密码重置失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      // 如果是新增用户，验证确认密码
      if (!currentUser) {
        if (values.password !== confirmPassword) {
          message.error('两次密码输入不一致');
          return;
        }
      }
      
      if (currentUser) {
        // 更新用户
        const updateParams: UpdateUserParams = {
          id: currentUser.id,
          username: values.username,
          email: values.email,
          role_ids: values.roles,
          dept_id: values.department,
          is_active: !values.is_active, // 表单中的is_active表示"禁用"，需要取反
          is_superuser: values.is_superuser,
        };
        
        const response = await userApi.updateUser(updateParams);
        
        if (response.code === 200) {
          message.success('更新成功');
          fetchUserData();
          setModalVisible(false);
        } else {
          message.error(response.message || '更新失败');
        }
      } else {
        // 添加用户
        const createParams: CreateUserParams = {
          username: values.username,
          email: values.email,
          password: values.password,
          role_ids: values.roles,
          dept_id: values.department,
        };
        
        const response = await userApi.createUser(createParams);
        
        if (response.code === 200) {
          message.success('添加成功');
          fetchUserData();
          setModalVisible(false);
        } else {
          message.error(response.message || '添加失败');
        }
      }
    } catch (error) {
      // 表单验证失败或API调用失败
      console.error('Failed to save user:', error);
      message.error('操作失败，请重试');
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: Role[]) => (
        <Space>
          {roles && roles.length > 0 ? (
            roles.map(role => (
              <Tag key={role.id} color="blue">{role.name}</Tag>
            ))
          ) : (
            <span>-</span>
          )}
        </Space>
      ),
    },
    {
      title: '部门',
      dataIndex: 'dept',
      key: 'dept',
      render: (dept: Dept) => (dept && Object.keys(dept).length > 0) ? dept.name : '-',
    },
    {
      title: '超级用户',
      dataIndex: 'is_superuser',
      key: 'is_superuser',
      render: (is_superuser: boolean) => (
        <Tag color={is_superuser ? 'red' : 'default'}>
          {is_superuser ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '上次登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (last_login: string) => last_login ? new Date(last_login).toLocaleString() : '-',
    },
    {
      title: '禁用',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean, record: User) => (
        <Switch
          checked={!is_active}
          onChange={(checked) => handleToggleUserStatus(record.id, !checked)}
          checkedChildren="禁用"
          unCheckedChildren="启用"
          disabled={record.is_superuser}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
          >
            编辑
          </Button>
          {!record.is_superuser && (
            <Button
              type="link"
              icon={<KeyOutlined />}
              onClick={() => handleResetPassword(record.id)}
            >
              重置密码
            </Button>
          )}
          <Popconfirm
            title="确认删除"
            onConfirm={() => handleDeleteUser(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-6">
      <Layout style={{ minHeight: '600px', background: '#fff' }}>
        <Sider 
          width={240} 
          style={{ 
            background: '#fff', 
            borderRight: '1px solid #f0f0f0',
            padding: '24px'
          }}
        >
          <h3 style={{ marginBottom: '16px' }}>部门列表</h3>
          <Tree
            treeData={deptOptions.map(dept => ({
              title: dept.label,
              key: dept.value,
              value: dept.value
            }))}
            onSelect={handleDeptSelect}
            selectedKeys={selectedDeptId ? [selectedDeptId] : []}
            defaultExpandAll
          />
        </Sider>
        <Content style={{ padding: '0 24px' }}>
          <Card>
            <div className="mb-4" style={{ 
              background: '#fafafc', 
              minHeight: '60px', 
              display: 'flex', 
              alignItems: 'flex-start', 
              justifyContent: 'space-between', 
              border: '1px solid #ccc', 
              borderRadius: '8px', 
              padding: '15px' 
            }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '35px 15px', alignItems: 'flex-start', flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ minWidth: '40px' }}>名称</span>
                  <Input 
                    style={{ width: '200px' }}
                    placeholder="请输入用户名"
                    value={searchParams.username}
                    onChange={(e) => setSearchParams({ ...searchParams, username: e.target.value })}
                    onPressEnter={() => fetchUserData()}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ minWidth: '40px' }}>邮箱</span>
                  <Input 
                    style={{ width: '200px' }}
                    placeholder="请输入邮箱"
                    value={searchParams.email}
                    onChange={(e) => setSearchParams({ ...searchParams, email: e.target.value })}
                    onPressEnter={() => fetchUserData()}
                  />
                </div>
                <div style={{ display: 'flex', gap: '20px' }}>
                  <Button 
                    onClick={() => {
                      setSearchParams({});
                      setSelectedDeptId(null);
                      setLastClickedNodeId(null);
                      fetchUserData({});
                    }}
                  >
                    重置
                  </Button>
                  <Button 
                    type="primary"
                    onClick={() => fetchUserData()}
                  >
                    搜索
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="mb-4" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleAddUser}
                >
                  新增用户
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    setSearchParams({});
                    setSelectedDeptId(null);
                    setLastClickedNodeId(null);
                    fetchUserData({});
                  }}
                >
                  刷新
                </Button>
              </Space>
            </div>
            
            <Table 
              columns={columns}
              dataSource={userData}
              rowKey="id"
              loading={loading}
              pagination={{
                ...pagination,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} items`,
                onChange: (page, pageSize) => {
                  setPagination({ ...pagination, current: page, pageSize });
                  fetchUserData({ page, pageSize });
                },
              }}
            />
          </Card>
        </Content>
      </Layout>
        
      <Modal
          title={modalTitle}
          open={modalVisible}
          onOk={handleModalOk}
          onCancel={() => setModalVisible(false)}
          maskClosable={false}
        >
          <Form
            form={form}
            layout="vertical"
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' }
              ]}
            >
              <Input />
            </Form.Item>
            
            <Form.Item
              name="email"
              label="邮箱"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input />
            </Form.Item>
            
            {!currentUser && (
              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password />
              </Form.Item>
            )}
            
            {!currentUser && (
              <Form.Item
                label="确认密码"
                rules={[
                  { required: true, message: '请再次输入密码' }
                ]}
              >
                <Input.Password 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="请确认密码"
                />
              </Form.Item>
            )}
            
            <Form.Item
              name="roles"
              label="角色"
              rules={[
                { required: true, message: '请选择角色' }
              ]}
            >
              <Select
                mode="multiple"
                options={roleOptions}
                placeholder="请选择角色"
                allowClear
              />
            </Form.Item>
            
            {currentUser && (
              <>
                <Form.Item
                  name="is_superuser"
                  label="超级用户"
                  valuePropName="checked"
                >
                  <Switch 
                    checkedChildren="是" 
                    unCheckedChildren="否"
                  />
                </Form.Item>
                
                <Form.Item
                  name="is_active"
                  label="禁用"
                  valuePropName="checked"
                >
                  <Switch 
                    checkedChildren="禁用" 
                    unCheckedChildren="启用"
                  />
                </Form.Item>
              </>
            )}
            
            <Form.Item
              name="department"
              label="部门"
            >
              <Select 
                options={deptOptions}
                placeholder="请选择部门"
                allowClear
              />
            </Form.Item>

          </Form>
        </Modal>
    </div>
  );
};

export default UserManagement;