import React, {useEffect, useState} from 'react';
import {Button, Card, Col, DatePicker, Form, Input, message, Row, Select, Space, Table, Tag, Tooltip,} from 'antd';
import {ExportOutlined, SearchOutlined} from '@ant-design/icons';

// 审计日志接口
interface AuditLogItem {
  id: number;
  username: string;
  operation: string;
  method: string;
  params?: string;
  ip: string;
  location?: string;
  browser: string;
  os: string;
  status: 'success' | 'fail';
  errorMsg?: string;
  time: string;
  duration: number;
}

const AuditLog: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [logList, setLogList] = useState<AuditLogItem[]>([]);
  const [form] = Form.useForm();
  
  // 模拟审计日志数据
  const mockLogData: AuditLogItem[] = [
    {
      id: 1,
      username: 'admin',
      operation: '用户登录',
      method: 'POST /api/auth/login',
      params: '{"username": "admin", "password": "******"}',
      ip: '192.168.1.100',
      location: '中国 北京',
      browser: 'Chrome 91.0.4472.124',
      os: 'Windows 10',
      status: 'success',
      time: '2023-06-10 08:30:25',
      duration: 124,
    },
    {
      id: 2,
      username: 'admin',
      operation: '查询用户列表',
      method: 'GET /api/users',
      params: '{"page": 1, "size": 10}',
      ip: '192.168.1.100',
      location: '中国 北京',
      browser: 'Chrome 91.0.4472.124',
      os: 'Windows 10',
      status: 'success',
      time: '2023-06-10 08:35:12',
      duration: 56,
    },
    {
      id: 3,
      username: 'zhangsan',
      operation: '用户登录',
      method: 'POST /api/auth/login',
      params: '{"username": "zhangsan", "password": "******"}',
      ip: '192.168.1.101',
      location: '中国 上海',
      browser: 'Firefox 89.0',
      os: 'macOS 11.4',
      status: 'fail',
      errorMsg: '密码错误',
      time: '2023-06-10 09:15:33',
      duration: 89,
    },
    {
      id: 4,
      username: 'zhangsan',
      operation: '用户登录',
      method: 'POST /api/auth/login',
      params: '{"username": "zhangsan", "password": "******"}',
      ip: '192.168.1.101',
      location: '中国 上海',
      browser: 'Firefox 89.0',
      os: 'macOS 11.4',
      status: 'success',
      time: '2023-06-10 09:16:02',
      duration: 105,
    },
    {
      id: 5,
      username: 'zhangsan',
      operation: '新增用户',
      method: 'POST /api/users',
      params: '{"username": "lisi", "realname": "李四", "email": "lisi@example.com", "phone": "13800138001"}',
      ip: '192.168.1.101',
      location: '中国 上海',
      browser: 'Firefox 89.0',
      os: 'macOS 11.4',
      status: 'success',
      time: '2023-06-10 09:25:18',
      duration: 152,
    },
  ];

  // 加载审计日志数据
  useEffect(() => {
    fetchLogList();
  }, []);

  // 获取日志列表
  const fetchLogList = async () => {
    setLoading(true);
    try {
      // 这里应该是从API获取数据
      // const response = await api.getAuditLogList();
      // setLogList(response.data);
      
      // 使用模拟数据
      setTimeout(() => {
        setLogList(mockLogData);
        setLoading(false);
      }, 500);
    } catch (error) {
      message.error('获取审计日志失败');
      setLoading(false);
    }
  };

  // 处理表单提交
  const handleSearch = async () => {
    const values = await form.validateFields();
    console.log('搜索条件:', values);
    
    // 这里应该是根据条件从API获取数据
    // 但现在我们只是模拟一下
    message.success('搜索成功');
    fetchLogList();
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
  };

  // 导出日志
  const handleExport = () => {
    message.success('导出成功');
  };

  // 表格列配置
  const columns = [
    {
      title: '序号',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 100,
    },
    {
      title: '操作',
      dataIndex: 'operation',
      key: 'operation',
      width: 150,
    },
    {
      title: '请求方法',
      dataIndex: 'method',
      key: 'method',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 120,
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 120,
    },
    {
      title: '浏览器',
      dataIndex: 'browser',
      key: 'browser',
      width: 150,
      ellipsis: true,
    },
    {
      title: '操作系统',
      dataIndex: 'os',
      key: 'os',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        if (status === 'success') {
          return <Tag color="green">成功</Tag>;
        }
        return <Tag color="red">失败</Tag>;
      },
    },
    {
      title: '操作时间',
      dataIndex: 'time',
      key: 'time',
      width: 180,
    },
    {
      title: '耗时(ms)',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      sorter: (a: AuditLogItem, b: AuditLogItem) => a.duration - b.duration,
    },
    {
      title: '操作参数',
      dataIndex: 'params',
      key: 'params',
      width: 150,
      render: (params: string) => (
        <Tooltip title={params}>
          <span className="ellipsis">{params}</span>
        </Tooltip>
      ),
    },
    {
      title: '异常信息',
      dataIndex: 'errorMsg',
      key: 'errorMsg',
      width: 150,
      render: (errorMsg: string) => (
        errorMsg ? (
          <Tooltip title={errorMsg}>
            <span className="text-red-500 ellipsis">{errorMsg}</span>
          </Tooltip>
        ) : null
      ),
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
              <Form.Item name="username" label="用户名">
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="operation" label="操作">
                <Input placeholder="请输入操作" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="status" label="状态">
                <Select placeholder="请选择状态" allowClear>
                  <Select.Option value="success">成功</Select.Option>
                  <Select.Option value="fail">失败</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="ip" label="IP地址">
                <Input placeholder="请输入IP地址" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="dateRange" label="时间范围">
                <DatePicker.RangePicker showTime style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12} style={{ textAlign: 'right' }}>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  搜索
                </Button>
                <Button onClick={handleReset}>重置</Button>
                <Button type="primary" icon={<ExportOutlined />} onClick={handleExport}>
                  导出
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>

        <Table
          columns={columns}
          dataSource={logList}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1800 }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default AuditLog; 