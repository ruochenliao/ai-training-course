import React, {useEffect, useState} from 'react';
import {Button, Card, Col, Form, Input, message, Modal, Popconfirm, Row, Select, Space, Switch, Table, Tag} from 'antd';
import {
    DeleteOutlined,
    EditOutlined,
    KeyOutlined,
    PlusOutlined,
    ReloadOutlined,
    SearchOutlined
} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';

interface UserData {
  id: string;
  username: string;
  email: string;
  role: string[];
  department: string;
  isAdmin: boolean;
  status: boolean;
  lastLogin: string;
}

interface RoleOption {
  value: string;
  label: string;
}

interface DepartmentOption {
  value: string;
  label: string;
}

const UserManagement: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);
  const [userData, setUserData] = useState<UserData[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);
  const [form] = Form.useForm();
  
  // 模拟角色和部门数据
  const roleOptions: RoleOption[] = [
    { value: 'admin', label: t('system.user.roles.admin') },
    { value: 'manager', label: t('system.user.roles.manager') },
    { value: 'operator', label: t('system.user.roles.operator') },
    { value: 'viewer', label: t('system.user.roles.viewer') },
  ];
  
  const deptOptions: DepartmentOption[] = [
    { value: 'tech', label: t('system.user.departments.tech') },
    { value: 'sales', label: t('system.user.departments.sales') },
    { value: 'hr', label: t('system.user.departments.hr') },
    { value: 'finance', label: t('system.user.departments.finance') },
  ];

  // 模拟获取用户数据
  const fetchUserData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const mockData: UserData[] = [
        {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          role: ['admin'],
          department: 'tech',
          isAdmin: true,
          status: true,
          lastLogin: '2023-12-25 08:30:00',
        },
        {
          id: '2',
          username: 'manager',
          email: 'manager@example.com',
          role: ['manager'],
          department: 'sales',
          isAdmin: false,
          status: true,
          lastLogin: '2023-12-24 16:45:00',
        },
        {
          id: '3',
          username: 'operator1',
          email: 'operator1@example.com',
          role: ['operator'],
          department: 'hr',
          isAdmin: false,
          status: true,
          lastLogin: '2023-12-23 12:15:00',
        },
        {
          id: '4',
          username: 'viewer1',
          email: 'viewer1@example.com',
          role: ['viewer'],
          department: 'finance',
          isAdmin: false,
          status: false,
          lastLogin: '2023-12-20 09:10:00',
        },
      ];
      
      setUserData(mockData);
      setPagination({
        ...pagination,
        total: mockData.length,
      });
    } catch (error) {
      message.error(t('system.user.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStatusChange = async (checked: boolean, record: UserData) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const newData = userData.map(item => {
        if (item.id === record.id) {
          return { ...item, status: checked };
        }
        return item;
      });
      
      setUserData(newData);
      message.success(
        checked 
          ? t('system.user.enableSuccess', { username: record.username })
          : t('system.user.disableSuccess', { username: record.username })
      );
    } catch (error) {
      message.error(t('system.user.updateFailed'));
    }
  };

  const handleAddUser = () => {
    setModalTitle(t('system.user.addUser'));
    setCurrentUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditUser = (record: UserData) => {
    setModalTitle(t('system.user.editUser'));
    setCurrentUser(record);
    form.setFieldsValue({
      username: record.username,
      email: record.email,
      roles: record.role,
      department: record.department,
      isAdmin: record.isAdmin,
    });
    setModalVisible(true);
  };

  const handleDeleteUser = async (id: string) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const newData = userData.filter(item => item.id !== id);
      setUserData(newData);
      setPagination({
        ...pagination,
        total: newData.length,
      });
      
      message.success(t('system.user.deleteSuccess'));
    } catch (error) {
      message.error(t('system.user.deleteFailed'));
    }
  };

  const handleResetPassword = async (id: string) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      message.success(t('system.user.resetPasswordSuccess'));
    } catch (error) {
      message.error(t('system.user.resetPasswordFailed'));
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (currentUser) {
        // 更新用户
        const newData = userData.map(item => {
          if (item.id === currentUser.id) {
            return { 
              ...item, 
              username: values.username,
              email: values.email,
              role: values.roles,
              department: values.department,
              isAdmin: values.isAdmin,
            };
          }
          return item;
        });
        
        setUserData(newData);
        message.success(t('system.user.updateSuccess'));
      } else {
        // 添加用户
        const newUser: UserData = {
          id: Math.random().toString(36).substring(2, 10),
          username: values.username,
          email: values.email,
          role: values.roles,
          department: values.department,
          isAdmin: values.isAdmin || false,
          status: true,
          lastLogin: '-',
        };
        
        setUserData([...userData, newUser]);
        setPagination({
          ...pagination,
          total: userData.length + 1,
        });
        
        message.success(t('system.user.addSuccess'));
      }
      
      setModalVisible(false);
    } catch (error) {
      // 表单验证失败
    }
  };

  const columns = [
    {
      title: t('system.user.username'),
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: t('system.user.email'),
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: t('system.user.role'),
      dataIndex: 'role',
      key: 'role',
      render: (roles: string[]) => (
        <>
          {roles.map(role => {
            let color = '';
            let text = '';
            
            switch (role) {
              case 'admin':
                color = 'red';
                text = t('system.user.roles.admin');
                break;
              case 'manager':
                color = 'blue';
                text = t('system.user.roles.manager');
                break;
              case 'operator':
                color = 'green';
                text = t('system.user.roles.operator');
                break;
              case 'viewer':
                color = 'gray';
                text = t('system.user.roles.viewer');
                break;
              default:
                color = 'default';
                text = role;
            }
            
            return (
              <Tag color={color} key={role}>
                {text}
              </Tag>
            );
          })}
        </>
      ),
    },
    {
      title: t('system.user.department'),
      dataIndex: 'department',
      key: 'department',
      render: (dept: string) => {
        const deptMap: Record<string, string> = {
          'tech': t('system.user.departments.tech'),
          'sales': t('system.user.departments.sales'),
          'hr': t('system.user.departments.hr'),
          'finance': t('system.user.departments.finance'),
        };
        
        return deptMap[dept] || dept;
      },
    },
    {
      title: t('system.user.isAdmin'),
      dataIndex: 'isAdmin',
      key: 'isAdmin',
      render: (isAdmin: boolean) => (
        isAdmin ? <Tag color="red">{t('system.user.superUser')}</Tag> : '-'
      ),
    },
    {
      title: t('system.user.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: boolean, record: UserData) => (
        <Switch 
          checked={status}
          onChange={(checked) => handleStatusChange(checked, record)}
        />
      ),
    },
    {
      title: t('system.user.lastLogin'),
      dataIndex: 'lastLogin',
      key: 'lastLogin',
    },
    {
      title: t('common.actions'),
      key: 'action',
      render: (_: any, record: UserData) => (
        <Space size="small">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => handleEditUser(record)}
          />
          <Popconfirm
            title={t('system.user.deleteConfirm')}
            onConfirm={() => handleDeleteUser(record.id)}
            okText={t('common.yes')}
            cancelText={t('common.no')}
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />} 
            />
          </Popconfirm>
          <Popconfirm
            title={t('system.user.resetPasswordConfirm')}
            onConfirm={() => handleResetPassword(record.id)}
            okText={t('common.yes')}
            cancelText={t('common.no')}
          >
            <Button 
              type="text" 
              icon={<KeyOutlined />} 
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-6">
      <Card>
        <div className="mb-4">
          <Row gutter={16}>
            <Col span={6}>
              <Input 
                prefix={<SearchOutlined />}
                placeholder={t('system.user.search')} 
              />
            </Col>
            <Col span={18} className="flex justify-end">
              <Space>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleAddUser}
                >
                  {t('system.user.add')}
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => fetchUserData()}
                >
                  {t('common.refresh')}
                </Button>
              </Space>
            </Col>
          </Row>
        </div>
        
        <Table 
          columns={columns}
          dataSource={userData}
          rowKey="id"
          loading={loading}
          pagination={pagination}
        />
        
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
              label={t('system.user.username')}
              rules={[
                { required: true, message: t('system.user.usernameRequired') },
                { min: 3, message: t('system.user.usernameLength') }
              ]}
            >
              <Input />
            </Form.Item>
            
            <Form.Item
              name="email"
              label={t('system.user.email')}
              rules={[
                { required: true, message: t('system.user.emailRequired') },
                { type: 'email', message: t('system.user.emailInvalid') }
              ]}
            >
              <Input />
            </Form.Item>
            
            {!currentUser && (
              <Form.Item
                name="password"
                label={t('system.user.password')}
                rules={[
                  { required: true, message: t('system.user.passwordRequired') },
                  { min: 6, message: t('system.user.passwordLength') }
                ]}
              >
                <Input.Password />
              </Form.Item>
            )}
            
            <Form.Item
              name="roles"
              label={t('system.user.roles.title')}
              rules={[
                { required: true, message: t('system.user.roleRequired') }
              ]}
            >
              <Select 
                mode="multiple"
                options={roleOptions}
                placeholder={t('system.user.selectRole')}
              />
            </Form.Item>
            
            <Form.Item
              name="department"
              label={t('system.user.department')}
              rules={[
                { required: true, message: t('system.user.departmentRequired') }
              ]}
            >
              <Select 
                options={deptOptions}
                placeholder={t('system.user.selectDepartment')}
              />
            </Form.Item>
            
            <Form.Item
              name="isAdmin"
              valuePropName="checked"
            >
              <Switch checkedChildren={t('system.user.superUser')} unCheckedChildren={t('system.user.normalUser')} />
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default UserManagement; 