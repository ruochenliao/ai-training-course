import React, {useEffect, useState} from 'react';
import {Button, Card, Form, Input, message, Modal, Popconfirm, Select, Space, Switch, Table,} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined} from '@ant-design/icons';

// 菜单项接口
interface MenuItemType {
  id: number;
  name: string;
  icon?: string;
  path?: string;
  component?: string;
  parentId: number | null;
  type: 'menu' | 'button';
  permission?: string;
  sort: number;
  status: boolean;
  children?: MenuItemType[];
}

const MenuManagement: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [menuList, setMenuList] = useState<MenuItemType[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentMenu, setCurrentMenu] = useState<MenuItemType | null>(null);
  const [form] = Form.useForm();

  // 模拟菜单数据
  const mockMenuData: MenuItemType[] = [
    {
      id: 1,
      name: '系统管理',
      icon: 'SettingOutlined',
      path: '/system',
      component: 'Layout',
      parentId: null,
      type: 'menu',
      sort: 1,
      status: true,
      children: [
        {
          id: 2,
          name: '用户管理',
          icon: 'UserOutlined',
          path: '/system/user',
          component: 'system/user/UserManagement',
          parentId: 1,
          type: 'menu',
          sort: 1,
          status: true,
        },
        {
          id: 3,
          name: '角色管理',
          icon: 'TeamOutlined',
          path: '/system/role',
          component: 'system/role/RoleManagement',
          parentId: 1,
          type: 'menu',
          sort: 2,
          status: true,
        },
        {
          id: 4,
          name: '菜单管理',
          icon: 'MenuOutlined',
          path: '/system/menu',
          component: 'system/menu/MenuManagement',
          parentId: 1,
          type: 'menu',
          sort: 3,
          status: true,
        },
      ],
    },
  ];

  // 加载菜单数据
  useEffect(() => {
    fetchMenuList();
  }, []);

  // 获取菜单列表
  const fetchMenuList = async () => {
    setLoading(true);
    try {
      // 这里应该是从API获取数据
      // const response = await api.getMenuList();
      // setMenuList(response.data);
      
      // 使用模拟数据
      setTimeout(() => {
        setMenuList(mockMenuData);
        setLoading(false);
      }, 500);
    } catch (error) {
      message.error('获取菜单列表失败');
      setLoading(false);
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '菜单名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '图标',
      dataIndex: 'icon',
      key: 'icon',
    },
    {
      title: '排序',
      dataIndex: 'sort',
      key: 'sort',
    },
    {
      title: '权限标识',
      dataIndex: 'permission',
      key: 'permission',
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: boolean) => (
        <Switch checked={status} disabled />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (text: string, record: MenuItemType) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该菜单吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="primary" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 处理新增
  const handleAdd = () => {
    setCurrentMenu(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (menu: MenuItemType) => {
    setCurrentMenu(menu);
    form.setFieldsValue(menu);
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = (id: number) => {
    // 这里应该调用API删除菜单
    message.success('删除成功');
    fetchMenuList();
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 这里应该调用API保存数据
      if (currentMenu) {
        // 编辑
        message.success('更新成功');
      } else {
        // 新增
        message.success('添加成功');
      }
      
      setModalVisible(false);
      fetchMenuList();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <div className="menu-management">
      <Card
        title="菜单管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新增菜单
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={menuList}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 菜单表单对话框 */}
      <Modal
        title={currentMenu ? '编辑菜单' : '新增菜单'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="菜单名称"
            rules={[{ required: true, message: '请输入菜单名称' }]}
          >
            <Input placeholder="请输入菜单名称" />
          </Form.Item>

          <Form.Item
            name="parentId"
            label="上级菜单"
          >
            <Select placeholder="请选择上级菜单">
              <Select.Option value={null}>无</Select.Option>
              {menuList.map(menu => (
                <Select.Option key={menu.id} value={menu.id}>
                  {menu.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="type"
            label="菜单类型"
            rules={[{ required: true, message: '请选择菜单类型' }]}
          >
            <Select placeholder="请选择菜单类型">
              <Select.Option value="menu">菜单</Select.Option>
              <Select.Option value="button">按钮</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="icon"
            label="菜单图标"
          >
            <Input placeholder="请输入菜单图标" />
          </Form.Item>

          <Form.Item
            name="path"
            label="路由路径"
          >
            <Input placeholder="请输入路由路径" />
          </Form.Item>

          <Form.Item
            name="component"
            label="组件路径"
          >
            <Input placeholder="请输入组件路径" />
          </Form.Item>

          <Form.Item
            name="permission"
            label="权限标识"
          >
            <Input placeholder="请输入权限标识" />
          </Form.Item>

          <Form.Item
            name="sort"
            label="排序号"
            rules={[{ required: true, message: '请输入排序号' }]}
          >
            <Input type="number" placeholder="请输入排序号" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MenuManagement; 