import React, {useEffect, useState} from 'react';
import {Button, Card, Form, Input, message, Modal, Popconfirm, Select, Space, Switch, Table, Tabs, Tag,} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined} from '@ant-design/icons';

// API项接口
interface ApiItem {
  id: number;
  name: string;
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  module: string;
  description?: string;
  status: boolean;
}

const ApiManagement: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [apiList, setApiList] = useState<ApiItem[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentApi, setCurrentApi] = useState<ApiItem | null>(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState<string>('all');
  const { TabPane } = Tabs;

  // 模拟API数据
  const mockApiData: ApiItem[] = [
    {
      id: 1,
      name: '获取用户列表',
      url: '/api/users',
      method: 'GET',
      module: '用户管理',
      description: '获取所有用户的列表数据',
      status: true,
    },
    {
      id: 2,
      name: '创建用户',
      url: '/api/users',
      method: 'POST',
      module: '用户管理',
      description: '创建新用户',
      status: true,
    },
    {
      id: 3,
      name: '更新用户',
      url: '/api/users/{id}',
      method: 'PUT',
      module: '用户管理',
      description: '更新指定用户信息',
      status: true,
    },
    {
      id: 4,
      name: '删除用户',
      url: '/api/users/{id}',
      method: 'DELETE',
      module: '用户管理',
      description: '删除指定用户',
      status: false,
    },
    {
      id: 5,
      name: '获取角色列表',
      url: '/api/roles',
      method: 'GET',
      module: '角色管理',
      description: '获取所有角色的列表数据',
      status: true,
    },
    {
      id: 6,
      name: '创建角色',
      url: '/api/roles',
      method: 'POST',
      module: '角色管理',
      description: '创建新角色',
      status: true,
    },
  ];

  // 获取唯一的模块列表
  const modules = Array.from(new Set(mockApiData.map(api => api.module)));

  // 加载API数据
  useEffect(() => {
    fetchApiList();
  }, []);

  // 获取API列表
  const fetchApiList = async () => {
    setLoading(true);
    try {
      // 这里应该是从API获取数据
      // const response = await api.getApiList();
      // setApiList(response.data);
      
      // 使用模拟数据
      setTimeout(() => {
        setApiList(mockApiData);
        setLoading(false);
      }, 500);
    } catch (error) {
      message.error('获取API列表失败');
      setLoading(false);
    }
  };

  // 过滤API列表
  const getFilteredApiList = () => {
    if (activeTab === 'all') {
      return apiList;
    }
    return apiList.filter(api => api.module === activeTab);
  };

  // 表格列配置
  const columns = [
    {
      title: 'API名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
    },
    {
      title: '请求方式',
      dataIndex: 'method',
      key: 'method',
      render: (method: string) => {
        const colorMap: Record<string, string> = {
          GET: 'green',
          POST: 'blue',
          PUT: 'orange',
          DELETE: 'red',
        };
        return <Tag color={colorMap[method]}>{method}</Tag>;
      },
    },
    {
      title: '所属模块',
      dataIndex: 'module',
      key: 'module',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
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
      render: (text: string, record: ApiItem) => (
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
            title="确定删除该API吗？"
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
    setCurrentApi(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (api: ApiItem) => {
    setCurrentApi(api);
    form.setFieldsValue(api);
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = (id: number) => {
    // 这里应该调用API删除数据
    message.success('删除成功');
    fetchApiList();
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 这里应该调用API保存数据
      if (currentApi) {
        // 编辑
        message.success('更新成功');
      } else {
        // 新增
        message.success('添加成功');
      }
      
      setModalVisible(false);
      fetchApiList();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <div className="api-management">
      <Card
        title="API管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新增API
          </Button>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="全部" key="all" />
          {modules.map(module => (
            <TabPane tab={module} key={module} />
          ))}
        </Tabs>
        
        <Table
          columns={columns}
          dataSource={getFilteredApiList()}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* API表单对话框 */}
      <Modal
        title={currentApi ? '编辑API' : '新增API'}
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
            label="API名称"
            rules={[{ required: true, message: '请输入API名称' }]}
          >
            <Input placeholder="请输入API名称" />
          </Form.Item>

          <Form.Item
            name="url"
            label="请求URL"
            rules={[{ required: true, message: '请输入请求URL' }]}
          >
            <Input placeholder="请输入请求URL" />
          </Form.Item>

          <Form.Item
            name="method"
            label="请求方式"
            rules={[{ required: true, message: '请选择请求方式' }]}
          >
            <Select placeholder="请选择请求方式">
              <Select.Option value="GET">GET</Select.Option>
              <Select.Option value="POST">POST</Select.Option>
              <Select.Option value="PUT">PUT</Select.Option>
              <Select.Option value="DELETE">DELETE</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="module"
            label="所属模块"
            rules={[{ required: true, message: '请输入所属模块' }]}
          >
            <Input placeholder="请输入所属模块" />
          </Form.Item>

          <Form.Item
            name="description"
            label="API描述"
          >
            <Input.TextArea rows={3} placeholder="请输入API描述" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiManagement; 