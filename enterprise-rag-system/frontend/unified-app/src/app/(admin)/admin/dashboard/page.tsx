'use client';

import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag, Typography, Space, Button } from 'antd';
import {
  UserOutlined,
  BookOutlined,
  FileTextOutlined,
  MessageOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/utils/api';
import { formatNumber, formatDate } from '@/utils';
import ReactECharts from 'echarts-for-react';

const { Title, Text } = Typography;

export default function AdminDashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  // 获取系统统计数据
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats', refreshKey],
    queryFn: () => apiClient.getSystemStats(),
  });

  // 模拟数据（实际应该从API获取）
  const mockStats = {
    users: {
      total: 1248,
      active: 892,
      new_today: 23,
      growth_rate: 12.5,
    },
    knowledge_bases: {
      total: 156,
      public: 89,
      private: 67,
      growth_rate: 8.3,
    },
    documents: {
      total: 12847,
      processing: 45,
      completed: 12756,
      failed: 46,
      total_size: 2.4, // GB
      growth_rate: 15.7,
    },
    conversations: {
      total: 8934,
      today: 234,
      this_week: 1567,
      growth_rate: 22.1,
    },
    system: {
      uptime: 99.8,
      memory_usage: 68.5,
      cpu_usage: 45.2,
      disk_usage: 72.3,
    },
  };

  const currentStats = stats || mockStats;

  // 统计卡片数据
  const statCards = [
    {
      title: '总用户数',
      value: currentStats.users.total,
      icon: <UserOutlined className="text-blue-500" />,
      color: 'blue',
      growth: currentStats.users.growth_rate,
      suffix: '人',
    },
    {
      title: '知识库数量',
      value: currentStats.knowledge_bases.total,
      icon: <BookOutlined className="text-green-500" />,
      color: 'green',
      growth: currentStats.knowledge_bases.growth_rate,
      suffix: '个',
    },
    {
      title: '文档总数',
      value: currentStats.documents.total,
      icon: <FileTextOutlined className="text-purple-500" />,
      color: 'purple',
      growth: currentStats.documents.growth_rate,
      suffix: '份',
    },
    {
      title: '对话总数',
      value: currentStats.conversations.total,
      icon: <MessageOutlined className="text-orange-500" />,
      color: 'orange',
      growth: currentStats.conversations.growth_rate,
      suffix: '次',
    },
  ];

  // 最近活动数据
  const recentActivities = [
    {
      key: '1',
      user: '张三',
      action: '上传文档',
      target: '技术规范.pdf',
      time: '2分钟前',
      status: 'success',
    },
    {
      key: '2',
      user: '李四',
      action: '创建知识库',
      target: '产品手册',
      time: '5分钟前',
      status: 'success',
    },
    {
      key: '3',
      user: '王五',
      action: '发起对话',
      target: '关于API使用',
      time: '8分钟前',
      status: 'processing',
    },
    {
      key: '4',
      user: '赵六',
      action: '文档处理失败',
      target: '大型文件.docx',
      time: '12分钟前',
      status: 'error',
    },
  ];

  const activityColumns = [
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '目标',
      dataIndex: 'target',
      key: 'target',
      render: (text: string) => (
        <Text className="text-blue-600 cursor-pointer hover:underline">
          {text}
        </Text>
      ),
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          success: { color: 'green', text: '成功' },
          processing: { color: 'blue', text: '处理中' },
          error: { color: 'red', text: '失败' },
        };
        const config = statusMap[status as keyof typeof statusMap];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
  ];

  // 图表配置
  const chartOption = {
    title: {
      text: '过去7天用户活跃度',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal',
      },
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '活跃用户',
        type: 'line',
        smooth: true,
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        itemStyle: {
          color: '#1890ff',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
            ],
          },
        },
      },
    ],
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-2">
            系统仪表板
          </Title>
          <Text type="secondary">
            实时监控系统运行状态和关键指标
          </Text>
        </div>
        
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRefresh}
          loading={statsLoading}
        >
          刷新数据
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        {statCards.map((card, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card className="hover:shadow-lg transition-shadow duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <Text type="secondary" className="text-sm">
                      {card.title}
                    </Text>
                    <div className="flex items-center space-x-2 mt-1">
                      <Statistic
                        value={card.value}
                        suffix={card.suffix}
                        valueStyle={{ fontSize: '24px', fontWeight: 'bold' }}
                      />
                    </div>
                    <div className="flex items-center space-x-1 mt-2">
                      {card.growth > 0 ? (
                        <ArrowUpOutlined className="text-green-500 text-xs" />
                      ) : (
                        <ArrowDownOutlined className="text-red-500 text-xs" />
                      )}
                      <Text
                        className={`text-xs ${
                          card.growth > 0 ? 'text-green-500' : 'text-red-500'
                        }`}
                      >
                        {Math.abs(card.growth)}%
                      </Text>
                      <Text type="secondary" className="text-xs">
                        较上月
                      </Text>
                    </div>
                  </div>
                  <div className="text-3xl">{card.icon}</div>
                </div>
              </Card>
            </motion.div>
          </Col>
        ))}
      </Row>

      {/* 图表和系统状态 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <Card title="用户活跃度趋势" className="h-96">
              <ReactECharts option={chartOption} style={{ height: '300px' }} />
            </Card>
          </motion.div>
        </Col>
        
        <Col xs={24} lg={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.5 }}
          >
            <Card title="系统资源" className="h-96">
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <Text>CPU使用率</Text>
                    <Text>{currentStats.system.cpu_usage}%</Text>
                  </div>
                  <Progress
                    percent={currentStats.system.cpu_usage}
                    strokeColor="#52c41a"
                    size="small"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <Text>内存使用率</Text>
                    <Text>{currentStats.system.memory_usage}%</Text>
                  </div>
                  <Progress
                    percent={currentStats.system.memory_usage}
                    strokeColor="#1890ff"
                    size="small"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <Text>磁盘使用率</Text>
                    <Text>{currentStats.system.disk_usage}%</Text>
                  </div>
                  <Progress
                    percent={currentStats.system.disk_usage}
                    strokeColor="#faad14"
                    size="small"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <Text>系统正常运行时间</Text>
                    <Text>{currentStats.system.uptime}%</Text>
                  </div>
                  <Progress
                    percent={currentStats.system.uptime}
                    strokeColor="#722ed1"
                    size="small"
                  />
                </div>
              </div>
            </Card>
          </motion.div>
        </Col>
      </Row>

      {/* 最近活动 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.6 }}
      >
        <Card
          title="最近活动"
          extra={
            <Button type="link" icon={<EyeOutlined />}>
              查看全部
            </Button>
          }
        >
          <Table
            columns={activityColumns}
            dataSource={recentActivities}
            pagination={false}
            size="small"
          />
        </Card>
      </motion.div>
    </div>
  );
}
