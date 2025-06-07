import React, {useEffect, useState} from 'react';
import {
    App,
    Button,
    Card,
    Form,
    Input,
    InputNumber,
    Modal,
    Popconfirm,
    Space,
    Switch,
    Table,
    Tag,
    TreeSelect,
} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined, SettingOutlined} from '@ant-design/icons';
import {Menu, menuApi} from '../../../api/menu';

// 菜单项接口已从API模块导入

const MenuManagement: React.FC = () => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState<boolean>(false);
  const [menuList, setMenuList] = useState<Menu[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentMenu, setCurrentMenu] = useState<Menu | null>(null);
  const [menuOptions, setMenuOptions] = useState<any[]>([]);
  const [form] = Form.useForm();

  // 菜单数据将从API获取

  // 加载菜单数据
  useEffect(() => {
    fetchMenuList();
    getTreeSelectOptions();
  }, []);

  // 获取菜单列表
  const fetchMenuList = async () => {
    setLoading(true);
    try {
      const response = await menuApi.getMenuList();
      setMenuList(response.data);
      setLoading(false);
    } catch (error) {
      message.error('获取菜单列表失败');
      setLoading(false);
    }
  };

  // 获取树形选择器选项
  const getTreeSelectOptions = () => {
    const buildTreeOptions = (items: Menu[]): any[] => {
      return items.map(item => ({
        value: item.id,
        title: item.name,
        children: item.children ? buildTreeOptions(item.children) : []
      }));
    };

    const rootOption = {
      value: 0,
      title: '根目录',
      children: buildTreeOptions(menuList)
    };
    setMenuOptions([rootOption]);
  };

  // 表格列配置
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 50,
      align: 'center' as const,
    },
    {
      title: '菜单名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
      align: 'center' as const,
    },
    {
      title: '菜单类型',
      dataIndex: 'menu_type',
      key: 'menu_type',
      width: 80,
      align: 'center' as const,
      render: (menu_type: string, record: Menu) => {
        // 根据parent_id判断类型，如果没有menu_type字段
        const type = menu_type || (record.parent_id === 0 ? 'catalog' : 'menu');
        return (
          <Tag
            color={type === 'catalog' ? 'blue' : 'green'}
            style={{
              borderRadius: type === 'catalog' ? '2px' : '10px',
              border: type === 'catalog' ? '1px solid #1890ff' : 'none'
            }}
          >
            {type === 'catalog' ? '目录' : '菜单'}
          </Tag>
        );
      },
    },
    {
      title: '图标',
      dataIndex: 'icon',
      key: 'icon',
      width: 60,
      align: 'center' as const,
      render: (icon: string) => (
        icon ? <SettingOutlined style={{ fontSize: '16px' }} /> : '-'
      ),
    },
    {
      title: '排序',
      dataIndex: 'order',
      key: 'order',
      width: 60,
      align: 'center' as const,
    },
    {
      title: '访问路径',
      dataIndex: 'path',
      key: 'path',
      width: 120,
      align: 'center' as const,
    },
    {
      title: '跳转路径',
      dataIndex: 'redirect',
      key: 'redirect',
      width: 120,
      align: 'center' as const,
      render: (redirect: string) => redirect || '-',
    },
    {
      title: '组件路径',
      dataIndex: 'component',
      key: 'component',
      width: 120,
      align: 'center' as const,
    },
    {
      title: '可见',
      dataIndex: 'is_hidden',
      key: 'is_hidden',
      width: 60,
      align: 'center' as const,
      render: (is_hidden: boolean, record: Menu) => (
        <Switch
          size="small"
          checked={!is_hidden}
          onChange={() => handleUpdateVisible(record)}
        />
      ),
    },
    {
      title: '创建日期',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      align: 'center' as const,
      render: (created_at: string) => created_at || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      align: 'center' as const,
      fixed: 'right' as const,
      render: (text: string, record: Menu) => {
        const hasChildren = record.children && record.children.length > 0;
        const isTopLevel = record.parent_id === 0;
        return (
          <Space>
            {isTopLevel && (
              <Button
                size="small"
                type="link"
                onClick={() => handleAddSubMenu(record)}
              >
                子菜单
              </Button>
            )}
            <Button
              size="small"
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            >
              编辑
            </Button>
            <Popconfirm
              title="确定删除该菜单吗？"
              onConfirm={() => handleDelete(record.id)}
              disabled={hasChildren}
            >
              <Button
                size="small"
                type="link"
                danger
                icon={<DeleteOutlined />}
                disabled={hasChildren}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  // 更新可见状态
  const handleUpdateVisible = async (record: Menu) => {
    try {
      await menuApi.updateMenu({ id: record.id, is_hidden: !record.is_hidden });
      message.success('更新成功');
      fetchMenuList();
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 处理新增根菜单
  const handleAdd = () => {
    setCurrentMenu({
      id: 0,
      name: '',
      path: '',
      component: '',
      redirect: '',
      parent_id: 0,
      icon: '',
      order: 1,
      is_hidden: false,
      created_at: '',
      updated_at: ''
    });
    setModalVisible(true);
  };

  // 处理添加子菜单
  const handleAddSubMenu = (parentMenu: Menu) => {
    setCurrentMenu({
      id: 0,
      name: '',
      path: '',
      component: '',
      redirect: '',
      parent_id: parentMenu.id,
      icon: '',
      order: 1,
      is_hidden: false,
      created_at: '',
      updated_at: ''
    });
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (menu: Menu) => {
    setCurrentMenu(menu);
    form.setFieldsValue(menu);
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      await menuApi.deleteMenu(id);
      message.success('删除成功');
      fetchMenuList();
      getTreeSelectOptions();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      if (currentMenu && currentMenu.id) {
        // 更新菜单
        await menuApi.updateMenu({ id: currentMenu.id, ...values });
        message.success('更新成功');
      } else {
        // 创建菜单
        await menuApi.createMenu(values);
        message.success('创建成功');
      }
      
      setModalVisible(false);
      fetchMenuList();
      getTreeSelectOptions();
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <div className="menu-management" style={{ padding: '24px' }}>
      <Card
        title="菜单列表"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新建根菜单
          </Button>
        }
        style={{ marginBottom: '16px' }}
      >
        <Table
          columns={columns}
          dataSource={menuList}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 菜单表单对话框 */}
      <Modal
          title={currentMenu && currentMenu.id ? '编辑菜单' : '新增菜单'}
          open={modalVisible}
          onOk={() => form.submit()}
          onCancel={() => setModalVisible(false)}
          width={600}
          destroyOnHidden
        >
        <Form
            form={form}
            layout="vertical"
            initialValues={currentMenu || {}}
            onFinish={handleSubmit}
          >
          <Form.Item
            label="上级菜单"
            name="parent_id"
            rules={[{ required: true, message: '请选择上级菜单' }]}
          >
            <TreeSelect
              placeholder="请选择上级菜单"
              treeData={menuOptions}
              allowClear
            />
          </Form.Item>

          <Form.Item
            label="菜单名称"
            name="name"
            rules={[{ required: true, message: '请输入菜单名称' }]}
          >
            <Input placeholder="请输入菜单名称" />
          </Form.Item>

          <Form.Item
            label="访问路径"
            name="path"
            rules={[{ required: true, message: '请输入访问路径' }]}
          >
            <Input placeholder="请输入访问路径" />
          </Form.Item>

          <Form.Item
            label="组件路径"
            name="component"
          >
            <Input placeholder="请输入组件路径" />
          </Form.Item>

          <Form.Item
            label="重定向路径"
            name="redirect"
          >
            <Input placeholder="请输入重定向路径" />
          </Form.Item>

          <Form.Item
            label="图标"
            name="icon"
          >
            <Input placeholder="请输入图标" />
          </Form.Item>

          <Form.Item
            label="排序"
            name="order"
            rules={[{ required: true, message: '请输入排序' }]}
          >
            <InputNumber min={1} placeholder="请输入排序" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="可见"
            name="is_hidden"
            valuePropName="checked"
            getValueFromEvent={(checked) => !checked}
            getValueProps={(value) => ({ checked: !value })}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MenuManagement;