import React, {useCallback, useEffect, useState} from 'react';
import {App, Button, Card, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag,} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined} from '@ant-design/icons';
import {apiApi, ApiItem, ApiQueryParams} from '@/api/api';

const ApiManagement: React.FC = () => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState<boolean>(false);
  const [apiList, setApiList] = useState<ApiItem[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentApi, setCurrentApi] = useState<ApiItem | null>(null);
  const [form] = Form.useForm();
  const [queryParams, setQueryParams] = useState<ApiQueryParams>({
    page: 1,
    page_size: 10,
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 获取API列表
  const fetchApiList = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiApi.getApis(queryParams);
      if (response.code === 200 && response.data) {
        // 根据实际接口返回结构调整数据解析
        setApiList(response.data || []);
        setPagination({
          current: response.page || 1,
          pageSize: response.page_size || 10,
          total: response.total || 0,
        });
      }
    } catch (error) {
      message.error('获取API列表失败');
      console.error('API列表获取错误:', error);
    } finally {
      setLoading(false);
    }
  }, [queryParams, message]);

  // 加载API数据
  useEffect(() => {
    fetchApiList();
  }, [fetchApiList]);

  // 搜索处理
  const handleSearch = useCallback(() => {
    setQueryParams(prev => ({
      ...prev,
      page: 1,
    }));
  }, []);

  // 重置搜索
  const handleReset = useCallback(() => {
    setQueryParams({
      page: 1,
      page_size: 10,
    });
  }, []);

  // 分页处理
  const handleTableChange = useCallback((page: number, pageSize: number) => {
    setQueryParams(prev => ({
      ...prev,
      page,
      page_size: pageSize,
    }));
  }, []);

  // 表格列配置
  const columns = [
    {
      title: 'API路径',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
    },
    {
      title: '请求方式',
      dataIndex: 'method',
      key: 'method',
      width: 100,
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
      title: 'API简介',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      width: 120,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
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
  const handleDelete = async (id: number) => {
    try {
      await apiApi.deleteApi(id);
      message.success('删除成功');
      fetchApiList();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 处理刷新API
  const handleRefreshApi = async () => {
    try {
      await apiApi.refreshApi();
      message.success('刷新完成');
      fetchApiList();
    } catch (error) {
      message.error('刷新失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (currentApi) {
        // 编辑
        await apiApi.updateApi({ id: currentApi.id, ...values });
        message.success('更新成功');
      } else {
        // 新增
        await apiApi.createApi(values);
        message.success('添加成功');
      }
      
      setModalVisible(false);
      fetchApiList();
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <div className="api-management">
      <Card
        title="API列表"
        extra={
          <Space>
            <Button
              type="warning"
              icon={<ReloadOutlined />}
              onClick={handleRefreshApi}
            >
              刷新API
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              新建API
            </Button>
          </Space>
        }
      >
        {/* 搜索栏 */}
        <div style={{ marginBottom: 16 }}>
          <Form layout="inline">
            <Form.Item label="路径">
              <Input
                placeholder="请输入API路径"
                value={queryParams.path}
                onChange={(e) => setQueryParams({ ...queryParams, path: e.target.value })}
                onPressEnter={handleSearch}
                allowClear
                style={{ width: 200 }}
              />
            </Form.Item>
            <Form.Item label="API简介">
              <Input
                placeholder="请输入API简介"
                value={queryParams.summary}
                onChange={(e) => setQueryParams({ ...queryParams, summary: e.target.value })}
                onPressEnter={handleSearch}
                allowClear
                style={{ width: 200 }}
              />
            </Form.Item>
            <Form.Item label="Tags">
              <Input
                placeholder="请输入API模块"
                value={queryParams.tags}
                onChange={(e) => setQueryParams({ ...queryParams, tags: e.target.value })}
                onPressEnter={handleSearch}
                allowClear
                style={{ width: 200 }}
              />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" onClick={handleSearch}>
                  搜索
                </Button>
                <Button onClick={handleReset}>
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>
        
        <Table
          columns={columns}
          dataSource={apiList}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange,
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* API表单对话框 */}
      <Modal
        title={currentApi ? '编辑API' : '新增API'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          preserve={false}
        >
          <Form.Item
            name="path"
            label="API路径"
            rules={[{ required: true, message: '请输入API路径' }]}
          >
            <Input placeholder="请输入API路径" />
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
              <Select.Option value="PATCH">PATCH</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="summary"
            label="API简介"
            rules={[{ required: true, message: '请输入API简介' }]}
          >
            <Input placeholder="请输入API简介" />
          </Form.Item>

          <Form.Item
            name="tags"
            label="Tags"
            rules={[{ required: true, message: '请输入Tags' }]}
          >
            <Input placeholder="请输入Tags" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiManagement;