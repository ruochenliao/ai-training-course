import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Modal,
  Descriptions,
  message,
  Spin,
  Empty,
  Tabs
} from 'antd'
import {
  NodeIndexOutlined,
  SearchOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons'
import KnowledgeGraphVisualization from '@/components/KnowledgeGraph/KnowledgeGraphVisualization'
import './KnowledgeGraphPage.css'

const { Search } = Input
const { Option } = Select
const { TabPane } = Tabs

interface Entity {
  id: string
  name: string
  type: string
  properties: Record<string, any>
  createdAt: string
  updatedAt: string
}

interface Relationship {
  id: string
  source: string
  target: string
  type: string
  properties: Record<string, any>
  createdAt: string
}

interface GraphStats {
  totalNodes: number
  totalRelationships: number
  nodeTypes: Record<string, number>
  relationshipTypes: Record<string, number>
}

const KnowledgeGraphPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [graphData, setGraphData] = useState<any>(null)
  const [entities, setEntities] = useState<Entity[]>([])
  const [relationships, setRelationships] = useState<Relationship[]>([])
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
  const [selectedRelationship, setSelectedRelationship] = useState<Relationship | null>(null)
  const [entityModalVisible, setEntityModalVisible] = useState(false)
  const [relationshipModalVisible, setRelationshipModalVisible] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all')
  const [selectedRelationType, setSelectedRelationType] = useState<string>('all')

  useEffect(() => {
    loadGraphData()
    loadEntities()
    loadRelationships()
    loadStats()
  }, [])

  const loadGraphData = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      const mockData = {
        nodes: [
          { id: '1', name: '人工智能', type: 'CONCEPT', properties: { description: 'AI技术概念' } },
          { id: '2', name: '机器学习', type: 'CONCEPT', properties: { description: 'ML技术' } },
          { id: '3', name: '深度学习', type: 'CONCEPT', properties: { description: 'DL技术' } },
          { id: '4', name: '神经网络', type: 'TECHNOLOGY', properties: { description: '神经网络技术' } },
          { id: '5', name: 'OpenAI', type: 'ORGANIZATION', properties: { description: 'AI公司' } },
          { id: '6', name: 'GPT', type: 'TECHNOLOGY', properties: { description: '生成式预训练模型' } },
          { id: '7', name: '自然语言处理', type: 'CONCEPT', properties: { description: 'NLP技术' } },
          { id: '8', name: '计算机视觉', type: 'CONCEPT', properties: { description: 'CV技术' } }
        ],
        links: [
          { source: '1', target: '2', type: 'CONTAINS', properties: {} },
          { source: '2', target: '3', type: 'CONTAINS', properties: {} },
          { source: '3', target: '4', type: 'USES', properties: {} },
          { source: '5', target: '6', type: 'DEVELOPS', properties: {} },
          { source: '1', target: '7', type: 'INCLUDES', properties: {} },
          { source: '1', target: '8', type: 'INCLUDES', properties: {} },
          { source: '6', target: '7', type: 'APPLIES_TO', properties: {} }
        ]
      }
      
      setGraphData(mockData)
    } catch (error) {
      message.error('加载知识图谱数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadEntities = async () => {
    try {
      // 模拟API调用
      const mockEntities: Entity[] = [
        {
          id: '1',
          name: '人工智能',
          type: 'CONCEPT',
          properties: { description: 'AI技术概念', confidence: 0.95 },
          createdAt: '2024-01-15',
          updatedAt: '2024-01-15'
        },
        {
          id: '2',
          name: '机器学习',
          type: 'CONCEPT',
          properties: { description: 'ML技术', confidence: 0.92 },
          createdAt: '2024-01-15',
          updatedAt: '2024-01-15'
        }
      ]
      
      setEntities(mockEntities)
    } catch (error) {
      message.error('加载实体数据失败')
    }
  }

  const loadRelationships = async () => {
    try {
      // 模拟API调用
      const mockRelationships: Relationship[] = [
        {
          id: '1',
          source: '人工智能',
          target: '机器学习',
          type: 'CONTAINS',
          properties: { confidence: 0.9 },
          createdAt: '2024-01-15'
        }
      ]
      
      setRelationships(mockRelationships)
    } catch (error) {
      message.error('加载关系数据失败')
    }
  }

  const loadStats = async () => {
    try {
      // 模拟API调用
      const mockStats: GraphStats = {
        totalNodes: 8,
        totalRelationships: 7,
        nodeTypes: {
          'CONCEPT': 5,
          'TECHNOLOGY': 2,
          'ORGANIZATION': 1
        },
        relationshipTypes: {
          'CONTAINS': 2,
          'USES': 1,
          'DEVELOPS': 1,
          'INCLUDES': 2,
          'APPLIES_TO': 1
        }
      }
      
      setStats(mockStats)
    } catch (error) {
      message.error('加载统计数据失败')
    }
  }

  const handleNodeClick = (node: any) => {
    const entity = entities.find(e => e.id === node.id)
    if (entity) {
      setSelectedEntity(entity)
      setEntityModalVisible(true)
    }
  }

  const handleLinkClick = (link: any) => {
    const relationship = relationships.find(r => 
      r.source === link.source.name && r.target === link.target.name
    )
    if (relationship) {
      setSelectedRelationship(relationship)
      setRelationshipModalVisible(true)
    }
  }

  const entityColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      filteredValue: searchKeyword ? [searchKeyword] : null,
      onFilter: (value: any, record: Entity) =>
        record.name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      ),
      filters: [
        { text: 'CONCEPT', value: 'CONCEPT' },
        { text: 'TECHNOLOGY', value: 'TECHNOLOGY' },
        { text: 'ORGANIZATION', value: 'ORGANIZATION' },
        { text: 'PERSON', value: 'PERSON' },
        { text: 'LOCATION', value: 'LOCATION' }
      ],
      onFilter: (value: any, record: Entity) => record.type === value,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: (a: Entity, b: Entity) => 
        new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Entity) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedEntity(record)
              setEntityModalVisible(true)
            }}
          />
          <Button type="text" icon={<EditOutlined />} />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ]

  const relationshipColumns = [
    {
      title: '源实体',
      dataIndex: 'source',
      key: 'source',
    },
    {
      title: '关系类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getRelationTypeColor(type)}>{type}</Tag>
      ),
    },
    {
      title: '目标实体',
      dataIndex: 'target',
      key: 'target',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Relationship) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedRelationship(record)
              setRelationshipModalVisible(true)
            }}
          />
          <Button type="text" icon={<EditOutlined />} />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ]

  const getTypeColor = (type: string) => {
    const colors = {
      'CONCEPT': 'blue',
      'TECHNOLOGY': 'green',
      'ORGANIZATION': 'orange',
      'PERSON': 'red',
      'LOCATION': 'purple'
    }
    return colors[type] || 'default'
  }

  const getRelationTypeColor = (type: string) => {
    const colors = {
      'CONTAINS': 'blue',
      'USES': 'green',
      'DEVELOPS': 'orange',
      'INCLUDES': 'purple',
      'APPLIES_TO': 'cyan'
    }
    return colors[type] || 'default'
  }

  return (
    <div className="knowledge-graph-page">
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总节点数"
              value={stats?.totalNodes || 0}
              prefix={<NodeIndexOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总关系数"
              value={stats?.totalRelationships || 0}
              prefix={<NodeIndexOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="节点类型"
              value={Object.keys(stats?.nodeTypes || {}).length}
              prefix={<NodeIndexOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="关系类型"
              value={Object.keys(stats?.relationshipTypes || {}).length}
              prefix={<NodeIndexOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Tabs defaultActiveKey="visualization">
        <TabPane tab="图谱可视化" key="visualization">
          <Card
            title="知识图谱可视化"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadGraphData}>
                  刷新
                </Button>
                <Button icon={<DownloadOutlined />}>
                  导出
                </Button>
                <Button icon={<UploadOutlined />}>
                  导入
                </Button>
              </Space>
            }
          >
            {loading ? (
              <div style={{ textAlign: 'center', padding: '100px 0' }}>
                <Spin size="large" />
              </div>
            ) : graphData ? (
              <KnowledgeGraphVisualization
                data={graphData}
                width={1000}
                height={600}
                onNodeClick={handleNodeClick}
                onLinkClick={handleLinkClick}
              />
            ) : (
              <Empty description="暂无图谱数据" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="实体管理" key="entities">
          <Card
            title="实体管理"
            extra={
              <Space>
                <Search
                  placeholder="搜索实体"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  style={{ width: 200 }}
                />
                <Button type="primary" icon={<PlusOutlined />}>
                  添加实体
                </Button>
              </Space>
            }
          >
            <Table
              columns={entityColumns}
              dataSource={entities}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="关系管理" key="relationships">
          <Card
            title="关系管理"
            extra={
              <Button type="primary" icon={<PlusOutlined />}>
                添加关系
              </Button>
            }
          >
            <Table
              columns={relationshipColumns}
              dataSource={relationships}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 实体详情模态框 */}
      <Modal
        title="实体详情"
        open={entityModalVisible}
        onCancel={() => setEntityModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedEntity && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="ID">{selectedEntity.id}</Descriptions.Item>
            <Descriptions.Item label="名称">{selectedEntity.name}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={getTypeColor(selectedEntity.type)}>
                {selectedEntity.type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="属性">
              <pre>{JSON.stringify(selectedEntity.properties, null, 2)}</pre>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedEntity.createdAt}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{selectedEntity.updatedAt}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 关系详情模态框 */}
      <Modal
        title="关系详情"
        open={relationshipModalVisible}
        onCancel={() => setRelationshipModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedRelationship && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="ID">{selectedRelationship.id}</Descriptions.Item>
            <Descriptions.Item label="源实体">{selectedRelationship.source}</Descriptions.Item>
            <Descriptions.Item label="关系类型">
              <Tag color={getRelationTypeColor(selectedRelationship.type)}>
                {selectedRelationship.type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="目标实体">{selectedRelationship.target}</Descriptions.Item>
            <Descriptions.Item label="属性">
              <pre>{JSON.stringify(selectedRelationship.properties, null, 2)}</pre>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedRelationship.createdAt}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default KnowledgeGraphPage
