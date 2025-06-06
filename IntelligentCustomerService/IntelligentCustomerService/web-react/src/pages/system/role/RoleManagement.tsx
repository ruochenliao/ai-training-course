import React, {useEffect, useState} from 'react';
import {
    Button,
    Card,
    Col,
    Form,
    Input,
    message,
    Modal,
    Popconfirm,
    Row,
    Select,
    Space,
    Switch,
    Table,
    Tree
} from 'antd';
import {
    DeleteOutlined,
    EditOutlined,
    KeyOutlined,
    PlusOutlined,
    ReloadOutlined,
    SearchOutlined
} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';

interface RoleData {
  id: string;
  roleName: string;
  roleKey: string;
  roleSort: number;
  status: boolean;
  description: string;
  createTime: string;
  permissions: string[];
}

interface PermissionTreeData {
  key: string;
  title: string;
  children?: PermissionTreeData[];
}

const RoleManagement: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);
  const [roleData, setRoleData] = useState<RoleData[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [permissionModalVisible, setPermissionModalVisible] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [currentRole, setCurrentRole] = useState<RoleData | null>(null);
  const [permissionTree, setPermissionTree] = useState<PermissionTreeData[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [form] = Form.useForm();

  // 模拟获取角色数据
  const fetchRoleData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const mockData: RoleData[] = [
        {
          id: '1',
          roleName: '超级管理员',
          roleKey: 'admin',
          roleSort: 1,
          status: true,
          description: '系统超级管理员，拥有所有权限',
          createTime: '2023-11-01 00:00:00',
          permissions: ['*:*:*'],
        },
        {
          id: '2',
          roleName: '普通管理员',
          roleKey: 'manager',
          roleSort: 2,
          status: true,
          description: '普通管理员，拥有大部分权限',
          createTime: '2023-11-02 00:00:00',
          permissions: ['system:user:list', 'system:role:list', 'system:menu:list'],
        },
        {
          id: '3',
          roleName: '客服人员',
          roleKey: 'customer_service',
          roleSort: 3,
          status: true,
          description: '客服人员，负责回答用户问题',
          createTime: '2023-11-03 00:00:00',
          permissions: ['customer:service:list', 'customer:service:reply'],
        },
        {
          id: '4',
          roleName: '访客',
          roleKey: 'visitor',
          roleSort: 4,
          status: false,
          description: '访客角色，仅有查看权限',
          createTime: '2023-11-04 00:00:00',
          permissions: ['common:view'],
        },
      ];
      
      setRoleData(mockData);
      setPagination({
        ...pagination,
        total: mockData.length,
      });
    } catch (error) {
      message.error(t('system.role.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  // 模拟获取权限树
  const fetchPermissionTree = async () => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const mockPermissionTree: PermissionTreeData[] = [
        {
          key: 'system',
          title: '系统管理',
          children: [
            {
              key: 'system:user',
              title: '用户管理',
              children: [
                { key: 'system:user:list', title: '用户列表' },
                { key: 'system:user:add', title: '用户新增' },
                { key: 'system:user:edit', title: '用户编辑' },
                { key: 'system:user:delete', title: '用户删除' },
              ],
            },
            {
              key: 'system:role',
              title: '角色管理',
              children: [
                { key: 'system:role:list', title: '角色列表' },
                { key: 'system:role:add', title: '角色新增' },
                { key: 'system:role:edit', title: '角色编辑' },
                { key: 'system:role:delete', title: '角色删除' },
              ],
            },
            {
              key: 'system:menu',
              title: '菜单管理',
              children: [
                { key: 'system:menu:list', title: '菜单列表' },
                { key: 'system:menu:add', title: '菜单新增' },
                { key: 'system:menu:edit', title: '菜单编辑' },
                { key: 'system:menu:delete', title: '菜单删除' },
              ],
            },
          ],
        },
        {
          key: 'customer',
          title: '客服管理',
          children: [
            {
              key: 'customer:service',
              title: '客服功能',
              children: [
                { key: 'customer:service:list', title: '会话列表' },
                { key: 'customer:service:reply', title: '回复消息' },
                { key: 'customer:service:close', title: '关闭会话' },
              ],
            },
          ],
        },
      ];
      
      setPermissionTree(mockPermissionTree);
    } catch (error) {
      message.error(t('system.role.fetchPermissionsFailed'));
    }
  };

  useEffect(() => {
    fetchRoleData();
    fetchPermissionTree();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStatusChange = async (checked: boolean, record: RoleData) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const newData = roleData.map(item => {
        if (item.id === record.id) {
          return { ...item, status: checked };
        }
        return item;
      });
      
      setRoleData(newData);
      message.success(
        checked 
          ? t('system.role.enableSuccess', { roleName: record.roleName })
          : t('system.role.disableSuccess', { roleName: record.roleName })
      );
    } catch (error) {
      message.error(t('system.role.updateFailed'));
    }
  };

  const handleAddRole = () => {
    setModalTitle(t('system.role.addRole'));
    setCurrentRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditRole = (record: RoleData) => {
    setModalTitle(t('system.role.editRole'));
    setCurrentRole(record);
    form.setFieldsValue({
      roleName: record.roleName,
      roleKey: record.roleKey,
      roleSort: record.roleSort,
      description: record.description,
    });
    setModalVisible(true);
  };

  const handleDeleteRole = async (id: string) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const newData = roleData.filter(item => item.id !== id);
      setRoleData(newData);
      setPagination({
        ...pagination,
        total: newData.length,
      });
      
      message.success(t('system.role.deleteSuccess'));
    } catch (error) {
      message.error(t('system.role.deleteFailed'));
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (currentRole) {
        // 更新角色
        const newData = roleData.map(item => {
          if (item.id === currentRole.id) {
            return { 
              ...item, 
              roleName: values.roleName,
              roleKey: values.roleKey,
              roleSort: values.roleSort,
              description: values.description,
            };
          }
          return item;
        });
        
        setRoleData(newData);
        message.success(t('system.role.updateSuccess'));
      } else {
        // 添加角色
        const newRole: RoleData = {
          id: Math.random().toString(36).substring(2, 10),
          roleName: values.roleName,
          roleKey: values.roleKey,
          roleSort: values.roleSort,
          status: true,
          description: values.description,
          createTime: new Date().toLocaleString(),
          permissions: [],
        };
        
        setRoleData([...roleData, newRole]);
        setPagination({
          ...pagination,
          total: roleData.length + 1,
        });
        
        message.success(t('system.role.addSuccess'));
      }
      
      setModalVisible(false);
    } catch (error) {
      // 表单验证失败
    }
  };

  const handleConfigPermission = (record: RoleData) => {
    setCurrentRole(record);
    setSelectedPermissions(record.permissions);
    setPermissionModalVisible(true);
  };

  const handlePermissionModalOk = async () => {
    try {
      if (currentRole) {
        // 更新角色权限
        const newData = roleData.map(item => {
          if (item.id === currentRole.id) {
            return {
              ...item,
              permissions: selectedPermissions,
            };
          }
          return item;
        });
        
        setRoleData(newData);
        message.success(t('system.role.updatePermissionSuccess'));
        setPermissionModalVisible(false);
      }
    } catch (error) {
      message.error(t('system.role.updatePermissionFailed'));
    }
  };

  const columns = [
    {
      title: t('system.role.roleName'),
      dataIndex: 'roleName',
      key: 'roleName',
      sorter: (a: RoleData, b: RoleData) => a.roleName.localeCompare(b.roleName),
    },
    {
      title: t('system.role.roleKey'),
      dataIndex: 'roleKey',
      key: 'roleKey',
    },
    {
      title: t('system.role.roleSort'),
      dataIndex: 'roleSort',
      key: 'roleSort',
      sorter: (a: RoleData, b: RoleData) => a.roleSort - b.roleSort,
    },
    {
      title: t('system.role.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: boolean, record: RoleData) => (
        <Switch 
          checked={status} 
          onChange={(checked) => handleStatusChange(checked, record)}
          disabled={record.roleKey === 'admin'} // 不允许禁用超级管理员
        />
      ),
    },
    {
      title: t('system.role.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('system.role.createTime'),
      dataIndex: 'createTime',
      key: 'createTime',
      sorter: (a: RoleData, b: RoleData) => 
        new Date(a.createTime).getTime() - new Date(b.createTime).getTime(),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: any, record: RoleData) => (
        <Space size="small">
          <Button 
            type="primary" 
            icon={<KeyOutlined />} 
            size="small"
            onClick={() => handleConfigPermission(record)}
            disabled={record.roleKey === 'admin'} // 超级管理员默认拥有所有权限
          >
            {t('system.role.configPermission')}
          </Button>
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            onClick={() => handleEditRole(record)}
            disabled={record.roleKey === 'admin'} // 不允许编辑超级管理员
          >
            {t('common.edit')}
          </Button>
          <Popconfirm
            title={t('system.role.deleteConfirm')}
            onConfirm={() => handleDeleteRole(record.id)}
            okText={t('common.yes')}
            cancelText={t('common.no')}
            disabled={record.roleKey === 'admin'} // 不允许删除超级管理员
          >
            <Button 
              danger 
              icon={<DeleteOutlined />} 
              size="small"
              disabled={record.roleKey === 'admin'} // 不允许删除超级管理员
            >
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={t('system.role.title')}
      extra={
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAddRole}
          >
            {t('system.role.addRole')}
          </Button>
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => fetchRoleData()}
          >
            {t('common.refresh')}
          </Button>
        </Space>
      }
    >
      {/* 搜索表单 */}
      <Form layout="inline" style={{ marginBottom: 16 }}>
        <Row gutter={[8, 8]} style={{ width: '100%' }}>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Form.Item name="roleName" label={t('system.role.roleName')} style={{ marginBottom: 0 }}>
              <Input placeholder={t('system.role.inputRoleName')} allowClear />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Form.Item name="roleKey" label={t('system.role.roleKey')} style={{ marginBottom: 0 }}>
              <Input placeholder={t('system.role.inputRoleKey')} allowClear />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Form.Item name="status" label={t('system.role.status')} style={{ marginBottom: 0 }}>
              <Select
                placeholder={t('system.role.selectStatus')}
                allowClear
                options={[
                  { value: '1', label: t('system.role.enabled') },
                  { value: '0', label: t('system.role.disabled') },
                ]}
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" icon={<SearchOutlined />}>
                {t('common.search')}
              </Button>
              <Button style={{ margin: '0 8px' }}>
                {t('common.reset')}
              </Button>
            </Form.Item>
          </Col>
        </Row>
      </Form>

      <Table
        columns={columns}
        dataSource={roleData}
        rowKey="id"
        pagination={pagination}
        loading={loading}
        onChange={(tablePagination) => {
          setPagination({
            ...pagination,
            current: tablePagination.current || 1,
          });
        }}
      />

      {/* 添加/编辑角色对话框 */}
      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="roleName"
            label={t('system.role.roleName')}
            rules={[{ required: true, message: t('system.role.roleNameRequired') }]}
          >
            <Input placeholder={t('system.role.inputRoleName')} />
          </Form.Item>
          <Form.Item
            name="roleKey"
            label={t('system.role.roleKey')}
            rules={[{ required: true, message: t('system.role.roleKeyRequired') }]}
          >
            <Input placeholder={t('system.role.inputRoleKey')} />
          </Form.Item>
          <Form.Item
            name="roleSort"
            label={t('system.role.roleSort')}
            rules={[{ required: true, message: t('system.role.roleSortRequired') }]}
          >
            <Input type="number" placeholder={t('system.role.inputRoleSort')} />
          </Form.Item>
          <Form.Item
            name="description"
            label={t('system.role.description')}
          >
            <Input.TextArea rows={4} placeholder={t('system.role.inputDescription')} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配权限对话框 */}
      <Modal
        title={t('system.role.configPermission')}
        open={permissionModalVisible}
        onOk={handlePermissionModalOk}
        onCancel={() => setPermissionModalVisible(false)}
        width={600}
        destroyOnClose
      >
        {currentRole && (
          <>
            <p>{t('system.role.currentRole')}: {currentRole.roleName}</p>
            <Tree
              checkable
              checkStrictly
              defaultExpandAll
              checkedKeys={selectedPermissions}
              onCheck={(checkedKeys) => setSelectedPermissions(checkedKeys as string[])}
              treeData={permissionTree}
            />
          </>
        )}
      </Modal>
    </Card>
  );
};

export default RoleManagement; 