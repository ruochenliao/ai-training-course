import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Input, Select, message, Spin, Modal, Form, Space, Tag, Statistic, Row, Col } from 'antd';
import { SearchOutlined, PlusOutlined, NodeIndexOutlined, LinkOutlined, BarChartOutlined } from '@ant-design/icons';
import * as d3 from 'd3';
import './KnowledgeGraph.css';

const { Option } = Select;
const { TextArea } = Input;

const KnowledgeGraph = () => {
  const [loading, setLoading] = useState(false);
  const [entities, setEntities] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState(null);
  const [extractModalVisible, setExtractModalVisible] = useState(false);
  const [entityModalVisible, setEntityModalVisible] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  
  const svgRef = useRef();
  const [form] = Form.useForm();
  const [entityForm] = Form.useForm();

  // 实体类型选项
  const entityTypes = [
    "人物", "组织", "地点", "产品", "技术", "概念", 
    "时间", "数量", "事件", "文档", "其他"
  ];

  // 关系类型选项
  const relationTypes = [
    "属于", "包含", "相关", "依赖", "产生", "使用",
    "位于", "发生在", "参与", "拥有", "创建", "修改"
  ];

  useEffect(() => {
    loadStatistics();
    loadEntities();
  }, [selectedKnowledgeBase]);

  useEffect(() => {
    if (entities.length > 0) {
      renderGraph();
    }
  }, [entities]);

  // 加载统计信息
  const loadStatistics = async () => {
    try {
      const params = selectedKnowledgeBase ? `?knowledge_base_id=${selectedKnowledgeBase}` : '';
      const response = await fetch(`/api/v1/knowledge-graph/statistics${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStatistics(data.statistics || {});
      }
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };

  // 加载实体列表
  const loadEntities = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedKnowledgeBase) {
        params.append('knowledge_base_id', selectedKnowledgeBase);
      }
      params.append('limit', '100');

      const response = await fetch(`/api/v1/knowledge-graph/entities?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEntities(data.entities || []);
        
        // 构建图数据
        await buildGraphData(data.entities || []);
      } else {
        message.error('加载实体失败');
      }
    } catch (error) {
      console.error('加载实体失败:', error);
      message.error('加载实体失败');
    } finally {
      setLoading(false);
    }
  };

  // 构建图数据
  const buildGraphData = async (entityList) => {
    const nodes = entityList.map(entity => ({
      id: entity.id,
      name: entity.name,
      type: entity.type,
      description: entity.description,
      group: entity.type
    }));

    const links = [];
    
    // 为每个实体获取相关实体
    for (const entity of entityList.slice(0, 20)) { // 限制数量避免过多请求
      try {
        const response = await fetch(`/api/v1/knowledge-graph/entities/${entity.id}/related?limit=5`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          data.related_entities?.forEach(relatedEntity => {
            if (entityList.find(e => e.id === relatedEntity.id)) {
              links.push({
                source: entity.id,
                target: relatedEntity.id,
                type: '相关',
                distance: relatedEntity.distance || 1
              });
            }
          });
        }
      } catch (error) {
        console.error(`获取实体 ${entity.id} 的相关实体失败:`, error);
      }
    }

    setGraphData({ nodes, links });
  };

  // 渲染图谱
  const renderGraph = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 600;
    
    svg.attr("width", width).attr("height", height);

    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // 创建连线
    const link = svg.append("g")
      .selectAll("line")
      .data(graphData.links)
      .enter().append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 2);

    // 创建节点
    const node = svg.append("g")
      .selectAll("circle")
      .data(graphData.nodes)
      .enter().append("circle")
      .attr("r", 8)
      .attr("fill", d => getNodeColor(d.type))
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // 添加节点标签
    const label = svg.append("g")
      .selectAll("text")
      .data(graphData.nodes)
      .enter().append("text")
      .text(d => d.name)
      .attr("font-size", "12px")
      .attr("dx", 12)
      .attr("dy", 4);

    // 添加工具提示
    node.append("title")
      .text(d => `${d.name}\n类型: ${d.type}\n描述: ${d.description || '无'}`);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      label
        .attr("x", d => d.x)
        .attr("y", d => d.y);
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  };

  // 获取节点颜色
  const getNodeColor = (type) => {
    const colors = {
      '人物': '#ff7875',
      '组织': '#40a9ff',
      '地点': '#73d13d',
      '产品': '#ffb347',
      '技术': '#b37feb',
      '概念': '#36cfc9',
      '时间': '#ffc069',
      '数量': '#ff85c0',
      '事件': '#95de64',
      '文档': '#87e8de',
      '其他': '#d9d9d9'
    };
    return colors[type] || '#d9d9d9';
  };

  // 从文本抽取实体和关系
  const handleExtractFromText = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/knowledge-graph/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text: values.text,
          knowledge_base_id: values.knowledge_base_id,
          auto_build: values.auto_build !== false
        })
      });

      if (response.ok) {
        const data = await response.json();
        message.success(data.message);
        setExtractModalVisible(false);
        form.resetFields();
        
        // 重新加载数据
        setTimeout(() => {
          loadEntities();
          loadStatistics();
        }, 2000); // 等待后台构建完成
      } else {
        const error = await response.json();
        message.error(error.detail || '抽取失败');
      }
    } catch (error) {
      console.error('抽取失败:', error);
      message.error('抽取失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建实体
  const handleCreateEntity = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/knowledge-graph/entities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: values.name,
          entity_type: values.entity_type,
          description: values.description,
          knowledge_base_id: values.knowledge_base_id,
          properties: values.properties ? JSON.parse(values.properties) : {}
        })
      });

      if (response.ok) {
        const data = await response.json();
        message.success(data.message);
        setEntityModalVisible(false);
        entityForm.resetFields();
        loadEntities();
        loadStatistics();
      } else {
        const error = await response.json();
        message.error(error.detail || '创建失败');
      }
    } catch (error) {
      console.error('创建实体失败:', error);
      message.error('创建实体失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索图谱
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/knowledge-graph/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: searchQuery,
          knowledge_base_id: selectedKnowledgeBase,
          max_results: 20
        })
      });

      if (response.ok) {
        const data = await response.json();
        const searchEntities = data.results.map(result => result.entity);
        setEntities(searchEntities);
        message.success(`找到 ${searchEntities.length} 个相关实体`);
      } else {
        const error = await response.json();
        message.error(error.detail || '搜索失败');
      }
    } catch (error) {
      console.error('搜索失败:', error);
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="knowledge-graph-container">
      <Card title="知识图谱管理" className="graph-card">
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="实体数量"
              value={statistics.entity_count || 0}
              prefix={<NodeIndexOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="关系数量"
              value={statistics.relationship_count || 0}
              prefix={<LinkOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="实体类型"
              value={statistics.entity_types?.length || 0}
              prefix={<BarChartOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="关系类型"
              value={statistics.relationship_types?.length || 0}
              prefix={<BarChartOutlined />}
            />
          </Col>
        </Row>

        {/* 操作栏 */}
        <Space style={{ marginBottom: 16, width: '100%' }} wrap>
          <Input.Search
            placeholder="搜索实体或关系..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 300 }}
            enterButton={<SearchOutlined />}
          />
          
          <Select
            placeholder="选择知识库"
            style={{ width: 200 }}
            value={selectedKnowledgeBase}
            onChange={setSelectedKnowledgeBase}
            allowClear
          >
            <Option value="kb_001">示例知识库1</Option>
            <Option value="kb_002">示例知识库2</Option>
            <Option value="manual_kb">手动知识库</Option>
          </Select>

          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setExtractModalVisible(true)}
          >
            文本抽取
          </Button>

          <Button
            icon={<PlusOutlined />}
            onClick={() => setEntityModalVisible(true)}
          >
            创建实体
          </Button>

          <Button onClick={loadEntities}>
            刷新
          </Button>
        </Space>

        {/* 图谱可视化 */}
        <div className="graph-visualization">
          <Spin spinning={loading}>
            <svg ref={svgRef} className="graph-svg"></svg>
          </Spin>
        </div>

        {/* 实体类型图例 */}
        <div style={{ marginTop: 16 }}>
          <strong>实体类型图例：</strong>
          <div style={{ marginTop: 8 }}>
            {entityTypes.map(type => (
              <Tag
                key={type}
                color={getNodeColor(type)}
                style={{ margin: '2px 4px' }}
              >
                {type}
              </Tag>
            ))}
          </div>
        </div>
      </Card>

      {/* 文本抽取模态框 */}
      <Modal
        title="从文本抽取实体和关系"
        open={extractModalVisible}
        onCancel={() => setExtractModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleExtractFromText}
        >
          <Form.Item
            name="text"
            label="输入文本"
            rules={[{ required: true, message: '请输入要分析的文本' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入要分析的文本内容..."
            />
          </Form.Item>

          <Form.Item
            name="knowledge_base_id"
            label="知识库ID"
          >
            <Input placeholder="可选，指定知识库ID" />
          </Form.Item>

          <Form.Item
            name="auto_build"
            label="自动构建图谱"
            valuePropName="checked"
            initialValue={true}
          >
            <input type="checkbox" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                开始抽取
              </Button>
              <Button onClick={() => setExtractModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建实体模态框 */}
      <Modal
        title="创建新实体"
        open={entityModalVisible}
        onCancel={() => setEntityModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form
          form={entityForm}
          layout="vertical"
          onFinish={handleCreateEntity}
        >
          <Form.Item
            name="name"
            label="实体名称"
            rules={[{ required: true, message: '请输入实体名称' }]}
          >
            <Input placeholder="输入实体名称" />
          </Form.Item>

          <Form.Item
            name="entity_type"
            label="实体类型"
            rules={[{ required: true, message: '请选择实体类型' }]}
          >
            <Select placeholder="选择实体类型">
              {entityTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="实体描述"
          >
            <TextArea rows={3} placeholder="输入实体描述" />
          </Form.Item>

          <Form.Item
            name="knowledge_base_id"
            label="知识库ID"
          >
            <Input placeholder="可选，指定知识库ID" />
          </Form.Item>

          <Form.Item
            name="properties"
            label="扩展属性 (JSON格式)"
          >
            <TextArea
              rows={3}
              placeholder='{"key": "value"}'
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建实体
              </Button>
              <Button onClick={() => setEntityModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KnowledgeGraph;
