import React, {useEffect, useState} from 'react';
import {Button, Card, Col, DatePicker, Form, Input, message, Popover, Row, Select, Space, Table, Tag} from 'antd';
import {EyeOutlined, SearchOutlined} from '@ant-design/icons';
import {type AuditLog, auditLogApi, type AuditLogQueryParams} from '@/api/auditlog';
import dayjs from 'dayjs';

// 查询参数接口
interface QueryParams extends AuditLogQueryParams {
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs] | null;
}

const AuditLog: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [logList, setLogList] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [current, setCurrent] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [queryParams, setQueryParams] = useState<QueryParams>({});
  const [form] = Form.useForm();

  // 格式化JSON数据
  const formatJSON = (data: any): string => {
    try {
      return typeof data === 'string' 
        ? JSON.stringify(JSON.parse(data), null, 2)
        : JSON.stringify(data, null, 2);
    } catch (e) {
      return data || '无数据';
    }
  };

  // 获取当天的开始和结束时间
  const getDefaultDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] => {
    const today = dayjs();
    return [
      today.startOf('day'),
      today.endOf('day')
    ];
  };

  // 初始化查询参数
  useEffect(() => {
    const defaultRange = getDefaultDateRange();
    const initialParams = {
      dateRange: defaultRange,
      start_time: defaultRange[0].format('YYYY-MM-DD HH:mm:ss'),
      end_time: defaultRange[1].format('YYYY-MM-DD HH:mm:ss')
    };
    setQueryParams(initialParams);
    form.setFieldsValue({ dateRange: defaultRange });
  }, [form]);

  // 加载审计日志数据
  useEffect(() => {
    if (queryParams.start_time && queryParams.end_time) {
      fetchLogList();
    }
  }, [queryParams, current, pageSize]);

  // 获取日志列表
  const fetchLogList = async () => {
    setLoading(true);
    try {
      const params = {
        ...queryParams,
        page: current,
        page_size: pageSize,
      };
      // 移除dateRange字段，因为API不需要这个字段
      delete params.dateRange;
      
      const response = await auditLogApi.list(params);
      if (response.data) {
        setLogList(response.data);
        setTotal(response.total);
      }
    } catch (error) {
      message.error('获取审计日志失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索
  const handleSearch = async () => {
    try {
      const values = await form.validateFields();
      const newParams: QueryParams = { ...values };
      
      // 处理时间范围
      if (values.dateRange) {
        newParams.start_time = values.dateRange[0].format('YYYY-MM-DD HH:mm:ss');
        newParams.end_time = values.dateRange[1].format('YYYY-MM-DD HH:mm:ss');
      } else {
        newParams.start_time = undefined;
        newParams.end_time = undefined;
      }
      
      setQueryParams(newParams);
      setCurrent(1); // 重置到第一页
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    const defaultRange = getDefaultDateRange();
    const resetParams = {
      dateRange: defaultRange,
      start_time: defaultRange[0].format('YYYY-MM-DD HH:mm:ss'),
      end_time: defaultRange[1].format('YYYY-MM-DD HH:mm:ss')
    };
    setQueryParams(resetParams);
    form.setFieldsValue({ dateRange: defaultRange });
    setCurrent(1);
  };

  // 处理分页变化
  const handleTableChange = (page: number, size: number) => {
    setCurrent(page);
    setPageSize(size);
  };

  // 表格列配置
  const columns = [
    {
      title: '用户名称',
      dataIndex: 'username',
      key: 'username',
      width: 'auto',
      align: 'center' as const,
      ellipsis: { tooltip: true },
    },
    {
      title: '接口概要',
      dataIndex: 'summary',
      key: 'summary',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '功能模块',
      dataIndex: 'module',
      key: 'module',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '请求方法',
      dataIndex: 'method',
      key: 'method',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '请求路径',
      dataIndex: 'path',
      key: 'path',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '状态码',
      dataIndex: 'status',
      key: 'status',
      align: 'center' as const,
      width: 'auto',
      render: (status: number) => {
        const color = status >= 200 && status < 300 ? 'green' : 'red';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: '请求体',
      dataIndex: 'request_args',
      key: 'request_args',
      align: 'center' as const,
      width: 80,
      render: (params: any) => (
        <Popover
          trigger="hover"
          placement="right"
          content={
            <pre
              style={{
                maxHeight: '400px',
                overflow: 'auto',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px',
                margin: 0,
              }}
            >
              {formatJSON(params)}
            </pre>
          }
        >
          <div style={{ cursor: 'pointer' }}>
            <EyeOutlined />
          </div>
        </Popover>
      ),
    },
    {
      title: '响应体',
      dataIndex: 'response_body',
      key: 'response_body',
      align: 'center' as const,
      width: 80,
      render: (response: any) => (
        <Popover
          trigger="hover"
          placement="right"
          content={
            <pre
              style={{
                maxHeight: '400px',
                overflow: 'auto',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px',
                margin: 0,
              }}
            >
              {formatJSON(response)}
            </pre>
          }
        >
          <div style={{ cursor: 'pointer' }}>
            <EyeOutlined />
          </div>
        </Popover>
      ),
    },
    {
      title: '响应时间(ms)',
      dataIndex: 'response_time',
      key: 'response_time',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
  ];

  return (
    <div className="audit-log">
      <Card title="审计日志">
        <Form
          form={form}
          layout="horizontal"
          className="mb-5"
        >
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="username" label="用户名称" labelCol={{ span: 8 }}>
                <Input 
                  placeholder="请输入用户名称" 
                  onPressEnter={handleSearch}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="module" label="功能模块" labelCol={{ span: 8 }}>
                <Input 
                  placeholder="请输入功能模块" 
                  onPressEnter={handleSearch}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="summary" label="接口概要" labelCol={{ span: 8 }}>
                <Input 
                  placeholder="请输入接口概要" 
                  onPressEnter={handleSearch}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="method" label="请求方法" labelCol={{ span: 8 }}>
                <Select placeholder="请选择请求方法" allowClear>
                  <Select.Option value="GET">GET</Select.Option>
                  <Select.Option value="POST">POST</Select.Option>
                  <Select.Option value="DELETE">DELETE</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="path" label="请求路径" labelCol={{ span: 8 }}>
                <Input 
                  placeholder="请输入请求路径" 
                  onPressEnter={handleSearch}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="status" label="状态码" labelCol={{ span: 8 }}>
                <Input 
                  placeholder="请输入状态码" 
                  onPressEnter={handleSearch}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="dateRange" label="操作时间" labelCol={{ span: 6 }}>
                <DatePicker.RangePicker 
                  showTime 
                  style={{ width: '100%' }} 
                  placeholder={['开始时间', '结束时间']}
                />
              </Form.Item>
            </Col>
            <Col span={4} style={{ textAlign: 'right' }}>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  搜索
                </Button>
                <Button onClick={handleReset}>重置</Button>
              </Space>
            </Col>
          </Row>
        </Form>

        <Table
          columns={columns}
          dataSource={logList}
          rowKey="id"
          loading={loading}
          pagination={{
            current,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/总共 ${total} 条`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange,
          }}
          scroll={{ x: 1400 }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default AuditLog;