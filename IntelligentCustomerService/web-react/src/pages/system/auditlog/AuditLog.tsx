import React, {useEffect, useState} from 'react'
import {App, Button, Card, Col, DatePicker, Form, Input, Popover, Row, Select, Table, Tag, Typography} from 'antd'
import type {ColumnsType} from 'antd/es/table'
import {EyeOutlined, ReloadOutlined, SearchOutlined} from '@ant-design/icons'
import {type AuditLog, auditLogApi, type AuditLogQueryParams} from '@/api/auditlog.ts'
import dayjs from 'dayjs'
import CommonPagination from '@/components/CommonPagination.tsx'

const { Title } = Typography
const { RangePicker } = DatePicker

// 查询参数接口
interface QueryParams extends AuditLogQueryParams {
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs] | null
  start_time?: string
  end_time?: string
}

const AuditLog: React.FC = () => {
  const { message } = App.useApp()
  const [loading, setLoading] = useState<boolean>(false)
  const [logList, setLogList] = useState<AuditLog[]>([])
  const [total, setTotal] = useState<number>(0)
  const [current, setCurrent] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [queryParams, setQueryParams] = useState<QueryParams>({})
  const [form] = Form.useForm()

  // 格式化JSON数据
  const formatJSON = (data: any): string => {
    try {
      return typeof data === 'string' ? JSON.stringify(JSON.parse(data), null, 2) : JSON.stringify(data, null, 2)
    } catch (e) {
      return data || '无数据'
    }
  }

  // 获取当天的开始和结束时间
  const getDefaultDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] => {
    const today = dayjs()
    return [today.startOf('day'), today.endOf('day')]
  }

  // 初始化查询参数
  useEffect(() => {
    const defaultRange = getDefaultDateRange()
    const initialParams = {
      dateRange: defaultRange,
      start_time: defaultRange[0].format('YYYY-MM-DD HH:mm:ss'),
      end_time: defaultRange[1].format('YYYY-MM-DD HH:mm:ss'),
    }
    setQueryParams(initialParams)
    form.setFieldsValue({ dateRange: defaultRange })
  }, [form])

  // 加载审计日志数据
  useEffect(() => {
    if (queryParams.start_time && queryParams.end_time) {
      fetchLogList()
    }
  }, [queryParams, current, pageSize])

  // 获取日志列表
  const fetchLogList = async () => {
    setLoading(true)
    try {
      const params = {
        ...queryParams,
        page: current,
        page_size: pageSize,
      }
      // 移除dateRange字段，因为API不需要这个字段
      delete params.dateRange

      const response = await auditLogApi.list(params)

      // 根据API响应结构处理数据
      if (response && response.data) {
        // 如果返回的是分页数据
        if (Array.isArray(response.data.items)) {
          setLogList(response.data.items)
          setTotal(response.data.total || response.data.items.length)
        }
        // 如果直接返回数组数据
        else if (Array.isArray(response.data)) {
          setLogList(response.data)
          setTotal(response.data.length)
        }
      }
    } catch (error) {
      message.error('获取审计日志失败')
    } finally {
      setLoading(false)
    }
  }

  // 处理搜索
  const handleSearch = async () => {
    try {
      const values = await form.validateFields()
      const newParams: QueryParams = { ...values }

      // 处理时间范围
      if (values.dateRange) {
        newParams.start_time = values.dateRange[0].format('YYYY-MM-DD HH:mm:ss')
        newParams.end_time = values.dateRange[1].format('YYYY-MM-DD HH:mm:ss')
      } else {
        // 使用空字符串代替undefined
        newParams.start_time = ''
        newParams.end_time = ''
      }

      setQueryParams(newParams)
      setCurrent(1) // 重置到第一页
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  // 重置表单
  const handleReset = () => {
    form.resetFields()
    const defaultRange = getDefaultDateRange()
    const resetParams = {
      dateRange: defaultRange,
      start_time: defaultRange[0].format('YYYY-MM-DD HH:mm:ss'),
      end_time: defaultRange[1].format('YYYY-MM-DD HH:mm:ss'),
    }
    setQueryParams(resetParams)
    form.setFieldsValue({ dateRange: defaultRange })
    setCurrent(1)
  }

  // 处理分页变化
  const handleTableChange = (page: number, size: number) => {
    setCurrent(page)
    setPageSize(size)
  }

  // 表格列配置
  const columns: ColumnsType<AuditLog> = [
    {
      title: '用户名称',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      align: 'center',
      ellipsis: true,
    },
    {
      title: '接口概要',
      dataIndex: 'summary',
      key: 'summary',
      align: 'center',
      width: 150,
      ellipsis: true,
    },
    {
      title: '功能模块',
      dataIndex: 'module',
      key: 'module',
      align: 'center',
      width: 120,
      ellipsis: true,
    },
    {
      title: '请求方法',
      dataIndex: 'method',
      key: 'method',
      align: 'center',
      width: 90,
      render: (method: string) => {
        let color = 'default'
        switch (method) {
          case 'GET':
            color = 'blue'
            break
          case 'POST':
            color = 'green'
            break
          case 'DELETE':
            color = 'red'
            break
          case 'PUT':
            color = 'orange'
            break
          case 'PATCH':
            color = 'purple'
            break
          default:
            color = 'default'
        }
        return <Tag color={color}>{method}</Tag>
      },
    },
    {
      title: '请求路径',
      dataIndex: 'path',
      key: 'path',
      align: 'center',
      width: 200,
      ellipsis: true,
    },
    {
      title: '状态码',
      dataIndex: 'status',
      key: 'status',
      align: 'center',
      width: 80,
      render: (status: number) => {
        let color = 'green'
        if (status >= 400) {
          color = 'red'
        } else if (status >= 300) {
          color = 'orange'
        }
        return <Tag color={color}>{status}</Tag>
      },
    },
    {
      title: '请求体',
      dataIndex: 'request_args',
      key: 'request_args',
      align: 'center',
      width: 80,
      render: (params: any) => (
        <Popover
          trigger='hover'
          placement='right'
          content={
            <pre
              style={{
                maxHeight: '400px',
                overflow: 'auto',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px',
                margin: 0,
                fontSize: '12px',
              }}
            >
              {formatJSON(params)}
            </pre>
          }
        >
          <Button type='link' size='small' icon={<EyeOutlined />} className='action-button' />
        </Popover>
      ),
    },
    {
      title: '响应体',
      dataIndex: 'response_body',
      key: 'response_body',
      align: 'center',
      width: 80,
      render: (response: any) => (
        <Popover
          trigger='hover'
          placement='right'
          content={
            <pre
              style={{
                maxHeight: '400px',
                overflow: 'auto',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px',
                margin: 0,
                fontSize: '12px',
              }}
            >
              {formatJSON(response)}
            </pre>
          }
        >
          <Button type='link' size='small' icon={<EyeOutlined />} className='action-button' />
        </Popover>
      ),
    },
    {
      title: '响应时间(ms)',
      dataIndex: 'response_time',
      key: 'response_time',
      align: 'center',
      width: 100,
      ellipsis: true,
    },
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      align: 'center',
      width: 160,
      ellipsis: true,
    },
  ]

  return (
    <div className='audit-log-container'>
      <Card title={<Title level={4}>审计日志</Title>} className='system-card'>
        <Form form={form} layout='horizontal' className='system-form mb-4'>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name='username' label='用户名称' labelCol={{ span: 8 }}>
                <Input placeholder='请输入用户名称' onPressEnter={handleSearch} allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name='module' label='功能模块' labelCol={{ span: 8 }}>
                <Input placeholder='请输入功能模块' onPressEnter={handleSearch} allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name='summary' label='接口概要' labelCol={{ span: 8 }}>
                <Input placeholder='请输入接口概要' onPressEnter={handleSearch} allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name='method' label='请求方法' labelCol={{ span: 8 }}>
                <Select
                  placeholder='请选择方法'
                  allowClear
                  options={[
                    { value: 'GET', label: 'GET' },
                    { value: 'POST', label: 'POST' },
                    { value: 'PUT', label: 'PUT' },
                    { value: 'DELETE', label: 'DELETE' },
                    { value: 'PATCH', label: 'PATCH' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name='dateRange' label='时间范围' labelCol={{ span: 4 }}>
                <RangePicker showTime style={{ width: '100%' }} format='YYYY-MM-DD HH:mm:ss' />
              </Form.Item>
            </Col>
            <Col span={12} style={{ textAlign: 'right' }}>
              <Button type='primary' icon={<SearchOutlined />} onClick={handleSearch} className='search-button mr-2'>
                搜索
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset} className='reset-button'>
                重置
              </Button>
            </Col>
          </Row>
        </Form>

        <Table
          className='system-table'
          dataSource={logList}
          columns={columns}
          rowKey='id'
          loading={loading}
          pagination={CommonPagination({
            current,
            pageSize,
            total,
            onChange: handleTableChange,
          })}
          scroll={{ x: 1200 }}
          size='middle'
        />
      </Card>
    </div>
  )
}

export default AuditLog
