import React from 'react';
import {Avatar, Button, Card, Col, Progress, Row, Space, Statistic, Table, Tag, Typography} from 'antd';
import {
    AppstoreOutlined,
    BellOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    FileTextOutlined,
    LineChartOutlined,
    TeamOutlined,
    UserOutlined
} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';
import {useTheme} from '../../contexts/ThemeContext';
import {cn} from '../../utils';

const { Title, Text } = Typography;

// 模拟用户数据
const mockUser = {
  name: '管理员',
  avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=1'
};

// 模拟统计数据
const statisticData = [
  {
    id: 1,
    title: '项目数量',
    value: 25,
    icon: <AppstoreOutlined />,
    color: '#1890ff',
  },
  {
    id: 2,
    title: '待办事项',
    value: 8,
    icon: <FileTextOutlined />,
    color: '#52c41a',
  },
  {
    id: 3,
    title: '消息通知',
    value: 12,
    icon: <BellOutlined />,
    color: '#faad14',
  },
  {
    id: 4,
    title: '团队成员',
    value: 18,
    icon: <TeamOutlined />,
    color: '#722ed1',
  },
];

// 模拟项目数据
const projectData = [
  {
    id: 1,
    name: '智能客服系统',
    desc: '基于FastAPI和React的智能客服系统',
    progress: 85,
    status: 'active',
  },
  {
    id: 2,
    name: 'Vue FastAPI Admin',
    desc: '一个基于Vue3.0、FastAPI的轻量级后台管理模板',
    progress: 65,
    status: 'active',
  },
  {
    id: 3,
    name: '数据分析平台',
    desc: '企业级数据分析和可视化平台',
    progress: 32,
    status: 'pending',
  },
  {
    id: 4,
    name: '内容管理系统',
    desc: '高性能的内容管理系统，支持多语言',
    progress: 100,
    status: 'complete',
  },
  {
    id: 5,
    name: '电子商务平台',
    desc: '全功能电子商务平台，包含订单管理、库存管理等',
    progress: 76,
    status: 'active',
  },
  {
    id: 6,
    name: '客户关系管理系统',
    desc: '企业级CRM系统，帮助企业管理客户关系',
    progress: 54,
    status: 'active',
  },
];

// 模拟待办事项
const todoData = [
  {
    id: 1,
    title: '完成用户管理模块',
    status: 'in-progress',
    priority: 'high',
    deadline: '2024-12-20',
  },
  {
    id: 2,
    title: '优化登录页面UI',
    status: 'done',
    priority: 'medium',
    deadline: '2024-12-15',
  },
  {
    id: 3,
    title: '修复权限控制Bug',
    status: 'pending',
    priority: 'urgent',
    deadline: '2024-12-18',
  },
  {
    id: 4,
    title: '更新API文档',
    status: 'in-progress',
    priority: 'low',
    deadline: '2024-12-25',
  },
  {
    id: 5,
    title: '部署生产环境',
    status: 'pending',
    priority: 'high',
    deadline: '2024-12-28',
  },
];

const Workbench: React.FC = () => {
  const { t } = useTranslation();
  const { isDark, primaryColor } = useTheme();

  // 状态标签映射
  const statusMap = {
    'pending': { color: 'orange', text: '待处理', icon: <ClockCircleOutlined /> },
    'in-progress': { color: 'blue', text: '进行中', icon: <LineChartOutlined /> },
    'done': { color: 'green', text: '已完成', icon: <CheckCircleOutlined /> },
  };

  // 优先级标签映射
  const priorityMap = {
    'low': { color: 'green', text: '低' },
    'medium': { color: 'blue', text: '中' },
    'high': { color: 'orange', text: '高' },
    'urgent': { color: 'red', text: '紧急' },
  };

  // 表格列配置
  const todoColumns = [
    {
      title: '任务名称',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag icon={statusMap[status as keyof typeof statusMap]?.icon} color={statusMap[status as keyof typeof statusMap]?.color}>
          {statusMap[status as keyof typeof statusMap]?.text}
        </Tag>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={priorityMap[priority as keyof typeof priorityMap]?.color}>
          {priorityMap[priority as keyof typeof priorityMap]?.text}
        </Tag>
      ),
    },
    {
      title: '截止日期',
      dataIndex: 'deadline',
      key: 'deadline',
    },
    {
      title: '操作',
      key: 'action',
      render: () => (
        <Space size="small">
          <Button type="link" size="small">查看</Button>
          <Button type="link" size="small">编辑</Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="workbench">
      {/* 欢迎卡片 */}
      <Card 
        bordered={false}
        className={cn(
          "mb-6 overflow-hidden",
          isDark ? "bg-gray-800" : "bg-white"
        )}
        style={{ borderRadius: '8px' }}
      >
        <div className="flex items-center justify-between flex-wrap">
          <div className="flex items-center gap-4">
            <Avatar 
              size={64} 
              src={mockUser.avatar}
              icon={<UserOutlined />}
              style={{ backgroundColor: primaryColor }}
            />
            <div>
              <Title level={4} className={cn(
                "!mb-1",
                isDark ? "text-white" : "text-gray-800"
              )}>
                欢迎回来，{mockUser.name}
              </Title>
              <Text className={cn(
                isDark ? "text-gray-300" : "text-gray-500"
              )}>
                今天是 {new Date().toLocaleDateString()} {['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][new Date().getDay()]}，祝您工作愉快！
              </Text>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 mt-4 sm:mt-0">
            <Card 
              size="small" 
              className={cn(
                "!border-0",
                isDark ? "bg-gray-700" : "bg-gray-50"
              )}
              style={{ borderRadius: '6px' }}
            >
              <Statistic 
                title={<span className={isDark ? "text-gray-300" : "text-gray-500"}>今日工单</span>}
                value={28}
                valueStyle={{ color: primaryColor }}
              />
            </Card>
            <Card 
              size="small" 
              className={cn(
                "!border-0",
                isDark ? "bg-gray-700" : "bg-gray-50"
              )}
              style={{ borderRadius: '6px' }}
            >
              <Statistic 
                title={<span className={isDark ? "text-gray-300" : "text-gray-500"}>待处理</span>}
                value={12}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
            <Card 
              size="small" 
              className={cn(
                "!border-0",
                isDark ? "bg-gray-700" : "bg-gray-50"
              )}
              style={{ borderRadius: '6px' }}
            >
              <Statistic 
                title={<span className={isDark ? "text-gray-300" : "text-gray-500"}>已完成</span>}
                value={16}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </div>
        </div>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        {statisticData.map(item => (
          <Col xs={24} sm={12} md={6} key={item.id}>
            <Card 
              bordered={false}
              className={cn(
                "h-full",
                isDark ? "bg-gray-800" : "bg-white"
              )}
              style={{ borderRadius: '8px' }}
            >
              <div className="flex items-center gap-4">
                <div 
                  className="w-12 h-12 rounded-full flex-center"
                  style={{ backgroundColor: item.color + '15' }}
                >
                  <span style={{ color: item.color, fontSize: '20px' }}>
                    {item.icon}
                  </span>
                </div>
                <div>
                  <div className={cn(
                    "text-sm mb-1",
                    isDark ? "text-gray-300" : "text-gray-500"
                  )}>
                    {item.title}
                  </div>
                  <div className="text-2xl font-semibold" style={{ color: item.color }}>
                    {item.value}
                  </div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 项目和待办任务 */}
      <Row gutter={[16, 16]}>
        {/* 项目列表 */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div className="flex items-center gap-2">
                <AppstoreOutlined className="text-lg" style={{ color: primaryColor }} />
                <span>项目列表</span>
              </div>
            }
            bordered={false}
            className={cn(
              "h-full",
              isDark ? "bg-gray-800" : "bg-white"
            )}
            style={{ borderRadius: '8px' }}
            extra={
              <Button type="link" icon={<AppstoreOutlined />}>
                查看全部
              </Button>
            }
          >
            <div className="grid gap-4">
              {projectData.slice(0, 4).map(project => (
                <Card 
                  key={project.id}
                  size="small"
                  className={cn(
                    "cursor-pointer hover:shadow-md transition-shadow",
                    isDark ? "bg-gray-700 border-gray-600" : "bg-white"
                  )}
                  style={{ borderRadius: '6px' }}
                >
                  <div className="flex flex-col">
                    <div className="flex justify-between items-center mb-2">
                      <Text strong className={isDark ? "text-white" : ""}>
                        {project.name}
                      </Text>
                      <Tag color={
                        project.status === 'complete' ? 'success' : 
                        project.status === 'active' ? 'processing' : 'warning'
                      }>
                        {project.status === 'complete' ? '已完成' : 
                         project.status === 'active' ? '进行中' : '待开始'}
                      </Tag>
                    </div>
                    <Text type="secondary" className="mb-2 text-xs">
                      {project.desc}
                    </Text>
                    <div className="flex justify-between items-center">
                      <Progress 
                        percent={project.progress} 
                        size="small" 
                        status={
                          project.progress === 100 ? 'success' : 
                          project.status === 'active' ? 'active' : 'normal'
                        }
                        className="w-3/4" 
                      />
                      <Text type="secondary" className="text-xs">
                        {project.progress}%
                      </Text>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </Card>
        </Col>

        {/* 待办任务 */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div className="flex items-center gap-2">
                <FileTextOutlined className="text-lg" style={{ color: primaryColor }} />
                <span>待办任务</span>
              </div>
            }
            bordered={false}
            className={cn(
              "h-full",
              isDark ? "bg-gray-800" : "bg-white"
            )}
            style={{ borderRadius: '8px' }}
            extra={
              <Button type="link" icon={<FileTextOutlined />}>
                添加任务
              </Button>
            }
          >
            <Table 
              dataSource={todoData} 
              columns={todoColumns} 
              rowKey="id"
              size="small"
              pagination={false}
              className={isDark ? "ant-table-dark" : ""}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Workbench;