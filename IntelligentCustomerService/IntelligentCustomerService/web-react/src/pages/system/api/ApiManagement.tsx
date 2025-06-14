import React, {useCallback, useEffect, useState} from 'react'
import {App, Button, Card, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag, Typography} from 'antd'
import {
    ApiOutlined,
    DeleteOutlined,
    EditOutlined,
    PlusOutlined,
    ReloadOutlined,
    SearchOutlined
} from '@ant-design/icons'
import {apiApi, ApiItem, ApiQueryParams} from '@/api/api'
import {useTheme} from '@/contexts/ThemeContext'
import {cn} from '@/utils'
import CommonPagination from '@/components/CommonPagination'

const { Option } = Select
const { Title } = Typography

const ApiManagement: React.FC = () => {
  const { message } = App.useApp()
  const { isDark, primaryColor } = useTheme()
  const [loading, setLoading] = useState<boolean>(false)
  const [apiList, setApiList] = useState<ApiItem[]>([])
  const [modalVisible, setModalVisible] = useState<boolean>(false)
  const [currentApi, setCurrentApi] = useState<ApiItem | null>(null)
  const [form] = Form.useForm()
  const [searchForm] = Form.useForm()
  const [total, setTotal] = useState<number>(0)
  const [current, setCurrent] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [queryParams, setQueryParams] = useState<ApiQueryParams>({
    page: 1,
    page_size: 10,
  })

  // 获取API列表
  const fetchApiList = useCallback(async () => {
    setLoading(true)
    try {
      const values = searchForm.getFieldsValue()
      const params = {
        ...queryParams,
        ...values,
      }

      const response = await apiApi.getApis(params)
      if (response.code === 200 && response.data) {
        setApiList(response.data || [])
        setTotal(response.total || 0)
        setCurrent(response.page || 1)
        setPageSize(response.page_size || 10)
      } else {
        message.error(response.msg || '获取API列表失败')
        setApiList([])
      }
    } catch (error) {
      message.error('获取API列表失败')
      console.error('API列表获取错误:', error)
      setApiList([])
    } finally {
      setLoading(false)
    }
  }, [queryParams, searchForm, message])

  // 加载API数据
  useEffect(() => {
    fetchApiList()
  }, [fetchApiList])

  // 搜索处理
  const handleSearch = useCallback(() => {
    const values = searchForm.getFieldsValue()
    setQueryParams((prev) => ({
      ...prev,
      ...values,
      page: 1,
    }))
    setCurrent(1) // 重置到第一页
  }, [searchForm])

  // 重置搜索
  const handleReset = useCallback(() => {
    searchForm.resetFields()
    setQueryParams({
      page: 1,
      page_size: 10,
    })
    setCurrent(1) // 重置到第一页
  }, [searchForm])

  // 分页处理
  const handleTableChange = (page: number, size: number) => {
    setCurrent(page)
    setPageSize(size)
    setQueryParams((prev) => ({
      ...prev,
      page: page,
      page_size: size,
    }))
  }

  // 表格列配置
  const columns = [
    {
      title: 'API路径',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
      render: (path: string) => (
        <div className='flex items-center'>
          <ApiOutlined className='mr-2 text-blue-500' />
          <span className='font-medium'>{path}</span>
        </div>
      ),
    },
    {
      title: '请求方式',
      dataIndex: 'method',
      key: 'method',
      width: 120,
      render: (method: string) => {
        const colorMap: Record<string, string> = {
          GET: 'green',
          POST: 'blue',
          PUT: 'orange',
          DELETE: 'red',
          PATCH: 'purple',
        }
        return (
          <Tag color={colorMap[method] || 'default'} className='rounded-md py-1 px-2 uppercase font-medium'>
            {method}
          </Tag>
        )
      },
    },
    {
      title: 'API简介',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
      render: (summary: string) => <div className='text-gray-600'>{summary}</div>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags: string) => {
        if (!tags) return '-'
        return (
          <Tag className='rounded-md' color='blue'>
            {tags}
          </Tag>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: ApiItem) => (
        <Space>
          <Button type='link' icon={<EditOutlined />} size='small' onClick={() => handleEdit(record)} className='action-button'>
            编辑
          </Button>
          <Popconfirm
            title='确定删除此API吗？'
            description={
              <>
                删除后不可恢复，确认删除<b>{record.path}</b>吗？
              </>
            }
            onConfirm={() => handleDelete(record.id)}
            okButtonProps={{ danger: true }}
            okText='删除'
            cancelText='取消'
          >
            <Button type='link' danger icon={<DeleteOutlined />} size='small' className='action-button delete-button'>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 处理新增
  const handleAdd = () => {
    setCurrentApi(null)
    form.resetFields()
    setModalVisible(true)
  }

  // 处理编辑
  const handleEdit = (api: ApiItem) => {
    setCurrentApi(api)
    form.setFieldsValue(api)
    setModalVisible(true)
  }

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      const response = await apiApi.deleteApi(id)

      if (response.code === 200) {
        message.success('删除API成功')
        fetchApiList()
      } else {
        // 使用类型断言处理错误信息
        const errorMsg = (response as any).msg || (response as any).message || '删除API失败'
        message.error(errorMsg)
      }
    } catch (error) {
      console.error('删除API失败:', error)
      message.error('删除API失败')
    }
  }

  // 处理刷新API
  const handleRefreshApi = async () => {
    try {
      const response = await apiApi.refreshApi()

      if (response.code === 200) {
        message.success('刷新API成功')
        fetchApiList()
      } else {
        // 使用类型断言处理错误信息
        const errorMsg = (response as any).msg || (response as any).message || '刷新API失败'
        message.error(errorMsg)
      }
    } catch (error) {
      console.error('刷新API失败:', error)
      message.error('刷新API失败')
    }
  }

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      let response

      if (currentApi) {
        // 编辑
        response = await apiApi.updateApi({ id: currentApi.id, ...values })
      } else {
        // 新增
        response = await apiApi.createApi(values)
      }

      if (response.code === 200) {
        message.success(currentApi ? '更新API成功' : '添加API成功')
        setModalVisible(false)
        fetchApiList()
      } else {
        // 使用类型断言处理错误信息
        const errorMsg = (response as any).msg || (response as any).message || (currentApi ? '更新API失败' : '添加API失败')
        message.error(errorMsg)
      }
    } catch (error) {
      console.error(currentApi ? '更新API失败' : '添加API失败', error)
      message.error(currentApi ? '更新API失败' : '添加API失败')
    }
  }

  return (
    <div className='api-management' style={{ padding: '24px' }}>
      <Card
        title={<Title level={4}>API管理</Title>}
        style={{ borderRadius: '4px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
        className={cn('system-card', isDark ? 'bg-gray-800 border-gray-700' : 'bg-white')}
        bordered={false}
      >
        {/* 搜索表单 */}
        <div className='mb-4'>
          <Form form={searchForm} layout='inline' onFinish={handleSearch} className='gap-4 flex-wrap system-form' style={{ rowGap: '12px' }}>
            <Form.Item name='path' label='API路径'>
              <Input placeholder='请输入API路径' allowClear />
            </Form.Item>
            <Form.Item name='method' label='请求方式'>
              <Select placeholder='请选择请求方式' allowClear style={{ width: 120 }}>
                <Option value='GET'>GET</Option>
                <Option value='POST'>POST</Option>
                <Option value='PUT'>PUT</Option>
                <Option value='DELETE'>DELETE</Option>
                <Option value='PATCH'>PATCH</Option>
              </Select>
            </Form.Item>
            <Form.Item name='tags' label='标签'>
              <Input placeholder='请输入标签' allowClear />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button
                  type='primary'
                  htmlType='submit'
                  icon={<SearchOutlined />}
                  className='search-button'
                  style={{ backgroundColor: primaryColor }}
                >
                  搜索
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset} className='reset-button'>
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>

        {/* 工具栏 */}
        <div className='mb-4 flex justify-between'>
          <div className={cn(isDark ? 'text-white' : 'text-gray-800')}>API列表</div>
          <Space>
            <Button type='primary' icon={<PlusOutlined />} onClick={handleAdd} className='add-button' style={{ backgroundColor: primaryColor }}>
              新增API
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleRefreshApi}>
              刷新
            </Button>
          </Space>
        </div>

        {/* API表格 */}
        <Table
          columns={columns}
          dataSource={apiList}
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

      {/* API表单弹窗 */}
      <Modal
        title={currentApi ? '编辑API' : '新增API'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={550}
        className='system-modal'
      >
        <Form form={form} layout='vertical' requiredMark={false} className='system-form'>
          <Form.Item name='path' label='API路径' rules={[{ required: true, message: '请输入API路径' }]}>
            <Input placeholder='请输入API路径，例如：/api/v1/user/list' />
          </Form.Item>

          <Form.Item name='method' label='请求方式' rules={[{ required: true, message: '请选择请求方式' }]}>
            <Select placeholder='请选择请求方式'>
              <Option value='GET'>GET</Option>
              <Option value='POST'>POST</Option>
              <Option value='PUT'>PUT</Option>
              <Option value='DELETE'>DELETE</Option>
              <Option value='PATCH'>PATCH</Option>
            </Select>
          </Form.Item>

          <Form.Item name='summary' label='API简介' rules={[{ required: true, message: '请输入API简介' }]}>
            <Input placeholder='请输入API简介' />
          </Form.Item>

          <Form.Item name='tags' label='标签' rules={[{ required: true, message: '请输入标签' }]}>
            <Input placeholder='请输入标签，例如：user' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ApiManagement
