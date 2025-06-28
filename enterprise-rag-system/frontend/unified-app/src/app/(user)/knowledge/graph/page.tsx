'use client';

import { useState } from 'react';
import { Card, Select, Button, Space, Typography, Tabs, Statistic, Row, Col } from 'antd';
import { 
  ShareAltOutlined, 
  DownloadOutlined, 
  SettingOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  ClusterOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import KnowledgeGraph from '@/components/visualization/KnowledgeGraph';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

export default function KnowledgeGraphPage() {
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<string>('all');
  const [graphType, setGraphType] = useState<string>('concept');

  // 模拟知识库数据
  const knowledgeBases = [
    { id: 'all', name: '全部知识库' },
    { id: '1', name: '技术文档' },
    { id: '2', name: '产品手册' },
    { id: '3', name: '业务流程' },
  ];

  // 模拟统计数据
  const graphStats = {
    nodes: 156,
    edges: 342,
    clusters: 12,
    depth: 6,
  };

  const handleExport = () => {
    // 导出图谱逻辑
    console.log('导出知识图谱');
  };

  const handleShare = () => {
    // 分享图谱逻辑
    console.log('分享知识图谱');
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* 页面头部 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <Title level={2} className="!mb-2">
              知识图谱
            </Title>
            <Text type="secondary">
              可视化展示知识库中的概念关系和知识结构
            </Text>
          </div>
          
          <Space>
            <Button icon={<ShareAltOutlined />} onClick={handleShare}>
              分享
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出
            </Button>
            <Button icon={<SettingOutlined />}>
              设置
            </Button>
          </Space>
        </div>
        
        {/* 控制选项 */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Text>知识库:</Text>
            <Select
              value={selectedKnowledgeBase}
              onChange={setSelectedKnowledgeBase}
              style={{ width: 200 }}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>{kb.name}</Option>
              ))}
            </Select>
          </div>
          
          <div className="flex items-center space-x-2">
            <Text>图谱类型:</Text>
            <Select
              value={graphType}
              onChange={setGraphType}
              style={{ width: 150 }}
            >
              <Option value="concept">概念图谱</Option>
              <Option value="document">文档关系</Option>
              <Option value="entity">实体关系</Option>
              <Option value="topic">主题聚类</Option>
            </Select>
          </div>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="h-full grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左侧统计面板 */}
          <div className="lg:col-span-1 space-y-4">
            {/* 图谱统计 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card title="图谱统计" className="shadow-sm">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Statistic
                      title="节点数"
                      value={graphStats.nodes}
                      prefix={<NodeIndexOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="连接数"
                      value={graphStats.edges}
                      prefix={<BranchesOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="聚类数"
                      value={graphStats.clusters}
                      prefix={<ClusterOutlined />}
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="最大深度"
                      value={graphStats.depth}
                      valueStyle={{ color: '#eb2f96' }}
                    />
                  </Col>
                </Row>
              </Card>
            </motion.div>

            {/* 图谱分析 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <Card title="图谱分析" className="shadow-sm">
                <Tabs defaultActiveKey="centrality" size="small">
                  <TabPane tab="中心性" key="centrality">
                    <div className="space-y-3">
                      {[
                        { name: '微服务架构', score: 0.95 },
                        { name: 'Docker容器', score: 0.87 },
                        { name: 'API网关', score: 0.76 },
                        { name: '负载均衡', score: 0.68 },
                      ].map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <Text className="text-sm truncate">{item.name}</Text>
                          <Text className="text-xs text-blue-600">{item.score}</Text>
                        </div>
                      ))}
                    </div>
                  </TabPane>
                  
                  <TabPane tab="聚类" key="clusters">
                    <div className="space-y-3">
                      {[
                        { name: '容器技术', count: 12 },
                        { name: '微服务', count: 8 },
                        { name: '数据库', count: 6 },
                        { name: '监控运维', count: 5 },
                      ].map((item, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <Text className="text-sm truncate">{item.name}</Text>
                          <Text className="text-xs text-green-600">{item.count}</Text>
                        </div>
                      ))}
                    </div>
                  </TabPane>
                  
                  <TabPane tab="路径" key="paths">
                    <div className="space-y-2">
                      <Text className="text-xs text-gray-500">最短路径分析</Text>
                      <div className="space-y-2">
                        {[
                          '微服务 → API网关 → 负载均衡',
                          'Docker → Kubernetes → 容器编排',
                          '数据库 → 缓存 → 性能优化',
                        ].map((path, index) => (
                          <div key={index} className="text-xs p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            {path}
                          </div>
                        ))}
                      </div>
                    </div>
                  </TabPane>
                </Tabs>
              </Card>
            </motion.div>

            {/* 操作面板 */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              <Card title="图谱操作" className="shadow-sm">
                <div className="space-y-3">
                  <Button block size="small">
                    查找最短路径
                  </Button>
                  <Button block size="small">
                    社区检测
                  </Button>
                  <Button block size="small">
                    影响力分析
                  </Button>
                  <Button block size="small">
                    相似性计算
                  </Button>
                </div>
              </Card>
            </motion.div>
          </div>

          {/* 右侧图谱展示 */}
          <div className="lg:col-span-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="h-full"
            >
              <KnowledgeGraph
                width={800}
                height={600}
                className="h-full"
              />
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
