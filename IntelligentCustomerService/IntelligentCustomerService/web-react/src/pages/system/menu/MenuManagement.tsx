import React, {useCallback, useEffect, useState} from 'react'
import {
    App,
    Button,
    Card,
    Form,
    Input,
    InputNumber,
    Modal,
    Popconfirm,
    Radio,
    Space,
    Switch,
    Table,
    Tag,
    Tooltip,
    TreeSelect,
    Typography,
} from 'antd'
import {DeleteOutlined, EditOutlined, FileOutlined, FolderOutlined, PlusOutlined} from '@ant-design/icons'
import {type Menu, menuApi} from '@/api/menu'

const { Title } = Typography

// 菜单项接口已从API模块导入

const MenuManagement: React.FC = () => {
  const { message } = App.useApp()
  const [loading, setLoading] = useState<boolean>(false)
  const [menuList, setMenuList] = useState<Menu[]>([])
  const [modalVisible, setModalVisible] = useState<boolean>(false)
  const [currentMenu, setCurrentMenu] = useState<Menu | null>(null)
  const [menuOptions, setMenuOptions] = useState<any[]>([])
  const [form] = Form.useForm()

  // 菜单数据将从API获取

  // 加载菜单数据
  useEffect(() => {
    fetchMenuList()
  }, [])

  // 当菜单列表更新时，更新树形选择器选项
  useEffect(() => {
    getTreeSelectOptions()
  }, [menuList])

  // 获取菜单列表
  const fetchMenuList = useCallback(async () => {
    setLoading(true)
    try {
      const response = await menuApi.getMenuList()
      // 处理分页响应或直接数组响应
      const menuData = response.data?.items || response.data || []
      setMenuList(menuData)
    } catch (error) {
      console.error('获取菜单列表失败:', error)
      message.error('获取菜单列表失败')
      setMenuList([])
    } finally {
      setLoading(false)
    }
  }, [message])

  // 获取树形选择器选项
  const getTreeSelectOptions = () => {
    const buildTreeOptions = (items: Menu[]): any[] => {
      return items.map((item) => ({
        value: item.id,
        title: item.name,
        children: item.children ? buildTreeOptions(item.children) : [],
      }))
    }

    const rootOption = {
      value: 0,
      title: '根目录',
      children: buildTreeOptions(menuList),
    }
    setMenuOptions([rootOption])
  }

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
        const type = menu_type || (record.parent_id === 0 ? 'catalog' : 'menu')
        return (
          <Tag
            color={type === 'catalog' ? 'blue' : 'green'}
            style={{
              borderRadius: '2px',
              padding: '2px 8px',
            }}
          >
            {type === 'catalog' ? '目录' : '菜单'}
          </Tag>
        )
      },
    },
    {
      title: '图标',
      dataIndex: 'icon',
      key: 'icon',
      width: 60,
      align: 'center' as const,
      render: (icon: string, record: Menu) => {
        // 根据菜单类型显示不同图标
        const type = record.menu_type || (record.parent_id === 0 ? 'catalog' : 'menu')
        if (type === 'catalog') {
          return <FolderOutlined style={{ fontSize: '16px', color: '#1890ff' }} />
        } else {
          return <FileOutlined style={{ fontSize: '16px', color: '#52c41a' }} />
        }
      },
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
      render: (path: string) => (
        <Tooltip title={path}>
          <span className='ellipsis-text'>{path || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '跳转路径',
      dataIndex: 'redirect',
      key: 'redirect',
      width: 120,
      align: 'center' as const,
      render: (redirect: string) => (
        <Tooltip title={redirect}>
          <span className='ellipsis-text'>{redirect || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '组件路径',
      dataIndex: 'component',
      key: 'component',
      width: 120,
      align: 'center' as const,
      render: (component: string) => (
        <Tooltip title={component}>
          <span className='ellipsis-text'>{component || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '保活',
      dataIndex: 'keepalive',
      key: 'keepalive',
      width: 60,
      align: 'center' as const,
      render: (keepalive: boolean, record: Menu) => (
        <Switch size='small' checked={keepalive || false} onChange={(checked) => handleUpdateKeepAlive(record, checked)} className='custom-switch' />
      ),
    },
    {
      title: '隐藏',
      dataIndex: 'is_hidden',
      key: 'is_hidden',
      width: 60,
      align: 'center' as const,
      render: (is_hidden: boolean, record: Menu) => (
        <Switch size='small' checked={is_hidden || false} onChange={(checked) => handleUpdateVisible(record, checked)} className='custom-switch' />
      ),
    },
    {
      title: '创建日期',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      align: 'center' as const,
      render: (created_at: string) => {
        if (created_at) {
          return new Date(created_at).toLocaleDateString('zh-CN')
        }
        return '-'
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      align: 'center' as const,
      fixed: 'right' as const,
      render: (text: string, record: Menu) => {
        const hasChildren = record.children && record.children.length > 0
        const menuType = record.menu_type || (record.parent_id === 0 ? 'catalog' : 'menu')

        return (
          <Space>
            {/* 目录类型显示子菜单和编辑按钮 */}
            {menuType === 'catalog' && (
              <>
                <Button size='small' type='link' onClick={() => handleAddSubMenu(record)} className='action-button'>
                  子菜单
                </Button>
                <Button size='small' type='link' icon={<EditOutlined />} onClick={() => handleEdit(record)} className='action-button'>
                  编辑
                </Button>
              </>
            )}

            {/* 菜单类型显示编辑和删除按钮 */}
            {menuType === 'menu' && (
              <>
                <Button size='small' type='link' icon={<EditOutlined />} onClick={() => handleEdit(record)} className='action-button'>
                  编辑
                </Button>
                <Popconfirm title='确定删除该菜单吗？' onConfirm={() => handleDelete(record.id)} disabled={hasChildren || false}>
                  <Button
                    size='small'
                    type='link'
                    danger
                    icon={<DeleteOutlined />}
                    disabled={hasChildren || false}
                    className='action-button delete-button'
                  >
                    删除
                  </Button>
                </Popconfirm>
              </>
            )}
          </Space>
        )
      },
    },
  ]

  // 更新可见状态
  const handleUpdateVisible = async (record: Menu, checked: boolean) => {
    try {
      const updateData = {
        id: record.id,
        name: record.name,
        path: record.path,
        component: record.component || '',
        redirect: record.redirect || '',
        parent_id: record.parent_id,
        icon: record.icon || '',
        order: record.order,
        menu_type: record.menu_type || (record.parent_id === 0 ? 'catalog' : 'menu'),
        keepalive: record.keepalive || false,
        is_hidden: checked,
      }
      await menuApi.updateMenu(updateData)
      message.success('更新成功')
      fetchMenuList()
    } catch (error) {
      message.error('更新失败')
    }
  }

  // 更新KeepAlive状态
  const handleUpdateKeepAlive = async (record: Menu, checked: boolean) => {
    try {
      const updateData = {
        id: record.id,
        name: record.name,
        path: record.path,
        component: record.component || '',
        redirect: record.redirect || '',
        parent_id: record.parent_id,
        icon: record.icon || '',
        order: record.order,
        menu_type: record.menu_type || (record.parent_id === 0 ? 'catalog' : 'menu'),
        keepalive: checked,
        is_hidden: record.is_hidden || false,
      }
      await menuApi.updateMenu(updateData)
      message.success('更新成功')
      fetchMenuList()
    } catch (error) {
      message.error('更新失败')
    }
  }

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
      updated_at: '',
    })
    form.resetFields()
    setModalVisible(true)
  }

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
      updated_at: '',
    })
    form.resetFields()
    form.setFieldsValue({
      parent_id: parentMenu.id,
      menu_type: 'menu', // 子菜单默认类型为菜单
    })
    setModalVisible(true)
  }

  // 处理编辑
  const handleEdit = (menu: Menu) => {
    setCurrentMenu(menu)
    form.setFieldsValue(menu)
    setModalVisible(true)
  }

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      await menuApi.deleteMenu(id)
      message.success('删除成功')
      fetchMenuList()
    } catch (error) {
      console.error('删除菜单失败:', error)
      message.error('删除失败')
    }
  }

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      if (currentMenu && currentMenu.id) {
        // 更新菜单
        await menuApi.updateMenu({ id: currentMenu.id, ...values })
        message.success('更新成功')
      } else {
        // 创建菜单
        await menuApi.createMenu(values)
        message.success('创建成功')
      }

      setModalVisible(false)
      form.resetFields()
      fetchMenuList()
    } catch (error) {
      console.error('菜单操作失败:', error)
      message.error('操作失败')
    }
  }

  return (
    <div className='menu-management' style={{ padding: '24px' }}>
      <Card
        title={<Title level={4}>菜单管理</Title>}
        extra={
          <Button type='primary' icon={<PlusOutlined />} onClick={handleAdd} className='add-button'>
            新建根菜单
          </Button>
        }
        style={{ borderRadius: '4px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
        className='system-card'
      >
        <Table
          columns={columns}
          dataSource={menuList}
          rowKey='id'
          loading={loading}
          pagination={false}
          scroll={{ x: 1200 }}
          size='middle'
          bordered
          className='system-table'
        />
      </Card>

      {/* 菜单表单对话框 */}
      <Modal
        title={currentMenu && currentMenu.id ? '编辑菜单' : '新增菜单'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={600}
        destroyOnClose
        className='system-modal'
      >
        <Form
          form={form}
          layout='vertical'
          initialValues={{ menu_type: 'catalog', order: 1, is_hidden: false, keepalive: false, ...currentMenu }}
          onFinish={handleSubmit}
          className='system-form'
        >
          <Form.Item label='菜单类型' name='menu_type' rules={[{ required: true, message: '请选择菜单类型' }]}>
            <Radio.Group>
              <Radio value='catalog'>目录</Radio>
              <Radio value='menu'>菜单</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item label='上级菜单' name='parent_id' rules={[{ required: true, message: '请选择上级菜单' }]}>
            <TreeSelect placeholder='请选择上级菜单' treeData={menuOptions} allowClear />
          </Form.Item>

          <Form.Item label='菜单名称' name='name' rules={[{ required: true, message: '请输入菜单名称' }]}>
            <Input placeholder='请输入唯一菜单名称' />
          </Form.Item>

          <Form.Item label='访问路径' name='path' rules={[{ required: true, message: '请输入访问路径' }]}>
            <Input placeholder='请输入访问路径' />
          </Form.Item>

          <Form.Item label='跳转路径' name='redirect'>
            <Input placeholder='请输入跳转路径' />
          </Form.Item>

          <Form.Item label='组件路径' name='component' rules={[{ required: true, message: '请输入组件路径' }]}>
            <Input placeholder='请输入组件路径' />
          </Form.Item>

          <Form.Item label='菜单图标' name='icon'>
            <Input placeholder='请输入图标名称' />
          </Form.Item>

          <Form.Item label='显示排序' name='order' rules={[{ required: true, message: '请输入排序' }]}>
            <InputNumber min={1} placeholder='1' style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label='是否隐藏' name='is_hidden' valuePropName='checked'>
            <Switch className='custom-switch' />
          </Form.Item>

          <Form.Item label='KeepAlive' name='keepalive' valuePropName='checked'>
            <Switch className='custom-switch' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MenuManagement
