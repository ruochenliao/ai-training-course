import React from 'react';
import {Avatar, Card, Col, List, Row, Space, Statistic, Tag, Typography} from 'antd';
import {
    CheckCircleOutlined,
    ClockCircleOutlined,
    MessageOutlined,
    SolutionOutlined,
    UserOutlined
} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';

const { Title, Text } = Typography;

interface StatisticItemProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

const StatisticItem: React.FC<StatisticItemProps> = ({ title, value, icon, color }) => (
  <Card className="hover:shadow-md transition-shadow duration-300">
    <Statistic 
      title={
        <Space>
          <span style={{ color }}>{icon}</span>
          <span>{title}</span>
        </Space>
      }
      value={value}
      valueStyle={{ color }}
    />
  </Card>
);

const recentTickets = [
  {
    id: '1',
    title: '产品无法登录',
    status: 'open',
    priority: 'high',
    time: '10分钟前',
    user: 'user1',
  },
  {
    id: '2',
    title: '如何重置密码',
    status: 'closed',
    priority: 'medium',
    time: '30分钟前',
    user: 'user2',
  },
  {
    id: '3',
    title: '订单支付失败',
    status: 'processing',
    priority: 'high',
    time: '1小时前',
    user: 'user3',
  },
  {
    id: '4',
    title: '产品功能咨询',
    status: 'open',
    priority: 'low',
    time: '2小时前',
    user: 'user4',
  },
  {
    id: '5',
    title: '账号异常登录',
    status: 'processing',
    priority: 'high',
    time: '3小时前',
    user: 'user5',
  },
];

const getStatusTag = (status: string) => {
  const statusMap = {
    open: { color: 'blue', text: '待处理', icon: <ClockCircleOutlined /> },
    processing: { color: 'orange', text: '处理中', icon: <SolutionOutlined /> },
    closed: { color: 'green', text: '已解决', icon: <CheckCircleOutlined /> },
  };
  const currentStatus = statusMap[status as keyof typeof statusMap];
  return (
    <Tag color={currentStatus.color} icon={currentStatus.icon}>
      {currentStatus.text}
    </Tag>
  );
};

const getPriorityTag = (priority: string) => {
  const priorityMap = {
    high: { color: 'red', text: '高' },
    medium: { color: 'orange', text: '中' },
    low: { color: 'green', text: '低' },
  };
  const currentPriority = priorityMap[priority as keyof typeof priorityMap];
  return <Tag color={currentPriority.color}>{currentPriority.text}</Tag>;
};

const Workbench: React.FC = () => {
  const { t } = useTranslation();

  const statistics = [
    {
      title: t('workbench.totalUsers'),
      value: 1285,
      icon: <UserOutlined />,
      color: '#1890ff',
    },
    {
      title: t('workbench.onlineUsers'),
      value: 428,
      icon: <UserOutlined />,
      color: '#52c41a',
    },
    {
      title: t('workbench.totalTickets'),
      value: 3254,
      icon: <MessageOutlined />,
      color: '#722ed1',
    },
    {
      title: t('workbench.pendingTickets'),
      value: 42,
      icon: <SolutionOutlined />,
      color: '#faad14',
    },
  ];

  return (
    <div className="p-6">
      <Title level={4} className="mb-6">{t('workbench.title')}</Title>
      
      <Row gutter={[16, 16]} className="mb-6">
        {statistics.map((stat, index) => (
          <Col xs={24} sm={12} md={12} lg={6} key={index}>
            <StatisticItem {...stat} />
          </Col>
        ))}
      </Row>

      <Card 
        title={t('workbench.recentTickets')} 
        className="mb-6"
        extra={<a href="#">{t('workbench.viewAll')}</a>}
      >
        <List
          itemLayout="horizontal"
          dataSource={recentTickets}
          renderItem={(item) => (
            <List.Item
              actions={[
                <a key="view" href={`#/ticket/${item.id}`}>
                  {t('workbench.view')}
                </a>,
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<UserOutlined />} />}
                title={<a href={`#/ticket/${item.id}`}>{item.title}</a>}
                description={
                  <Space>
                    {getStatusTag(item.status)}
                    {getPriorityTag(item.priority)}
                    <Text type="secondary">
                      <ClockCircleOutlined /> {item.time}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default Workbench; 