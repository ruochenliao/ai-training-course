'use client';

import {useEffect, useRef, useState} from 'react';
import {
    Alert,
    Button,
    Card,
    Col,
    Divider,
    Input,
    Row,
    Select,
    Slider,
    Space,
    Spin,
    Switch,
    Tag,
    Typography
} from 'antd';
import {
    CompressOutlined,
    DownloadOutlined,
    FullscreenOutlined,
    ReloadOutlined,
    SearchOutlined,
    ZoomInOutlined,
    ZoomOutOutlined
} from '@ant-design/icons';
import {useQuery} from '@tanstack/react-query';
import * as d3 from 'd3';
import type {KnowledgeBase} from '@/utils/api';
import {apiClient} from '@/utils/api';

const { Title, Text } = Typography;

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: any;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

interface GraphEdge {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  properties: any;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function KnowledgeGraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<number | null>(null);
  const [entityType, setEntityType] = useState<string>('');
  const [depth, setDepth] = useState(2);
  const [nodeLimit, setNodeLimit] = useState(100);
  const [searchTerm, setSearchTerm] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [simulation, setSimulation] = useState<d3.Simulation<GraphNode, GraphEdge> | null>(null);

  // 获取知识库列表
  const { data: kbData } = useQuery({
    queryKey: ['user-knowledge-bases'],
    queryFn: () => apiClient.getKnowledgeBases({ page: 1, size: 100 }),
  });

  // 获取图谱数据
  const { data: graphData, isLoading, refetch } = useQuery({
    queryKey: ['knowledge-graph', selectedKnowledgeBase, entityType, depth, nodeLimit],
    queryFn: () => apiClient.getKnowledgeGraph({
      knowledge_base_id: selectedKnowledgeBase || undefined,
      entity_type: entityType || undefined,
      depth,
      limit: nodeLimit
    }),
    enabled: !!selectedKnowledgeBase,
  });

  // 模拟图谱数据
  const mockGraphData: GraphData = {
    nodes: [
      { id: '1', label: 'Python', type: 'Technology', properties: { description: '编程语言' } },
      { id: '2', label: 'FastAPI', type: 'Framework', properties: { description: 'Web框架' } },
      { id: '3', label: 'React', type: 'Framework', properties: { description: '前端框架' } },
      { id: '4', label: 'TypeScript', type: 'Technology', properties: { description: '编程语言' } },
      { id: '5', label: 'Next.js', type: 'Framework', properties: { description: '全栈框架' } },
      { id: '6', label: 'Ant Design', type: 'Library', properties: { description: 'UI组件库' } },
      { id: '7', label: 'D3.js', type: 'Library', properties: { description: '数据可视化库' } },
      { id: '8', label: 'MySQL', type: 'Database', properties: { description: '关系数据库' } },
      { id: '9', label: 'Milvus', type: 'Database', properties: { description: '向量数据库' } },
      { id: '10', label: 'Neo4j', type: 'Database', properties: { description: '图数据库' } },
    ],
    edges: [
      { id: 'e1', source: '2', target: '1', type: 'BUILT_WITH', properties: {} },
      { id: 'e2', source: '5', target: '3', type: 'BASED_ON', properties: {} },
      { id: 'e3', source: '5', target: '4', type: 'SUPPORTS', properties: {} },
      { id: 'e4', source: '6', target: '3', type: 'COMPATIBLE_WITH', properties: {} },
      { id: 'e5', source: '7', target: '4', type: 'SUPPORTS', properties: {} },
      { id: 'e6', source: '2', target: '8', type: 'CONNECTS_TO', properties: {} },
      { id: 'e7', source: '2', target: '9', type: 'CONNECTS_TO', properties: {} },
      { id: 'e8', source: '2', target: '10', type: 'CONNECTS_TO', properties: {} },
    ]
  };

  const currentGraphData = graphData || mockGraphData;

  // 节点类型颜色映射
  const nodeColors = {
    'Technology': '#1890ff',
    'Framework': '#52c41a',
    'Library': '#722ed1',
    'Database': '#fa541c',
    'Entity': '#faad14',
    'Concept': '#13c2c2',
    'Person': '#eb2f96',
    'Organization': '#f5222d',
    'default': '#666666'
  };

  // 初始化D3图谱
  useEffect(() => {
    if (!svgRef.current || !currentGraphData.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800;
    const height = 600;

    // 创建缩放行为
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    const container = svg.append('g');

    // 创建力导向布局
    const sim = d3.forceSimulation<GraphNode>(currentGraphData.nodes)
      .force('link', d3.forceLink<GraphNode, GraphEdge>(currentGraphData.edges)
        .id(d => d.id)
        .distance(100)
        .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    setSimulation(sim);

    // 创建箭头标记
    const defs = container.append('defs');
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#999')
      .style('stroke', 'none');

    // 创建边
    const links = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(currentGraphData.edges)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // 创建边标签
    const linkLabels = container.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(currentGraphData.edges)
      .enter().append('text')
      .attr('class', 'link-label')
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .style('display', showEdgeLabels ? 'block' : 'none')
      .text(d => d.type);

    // 创建节点组
    const nodeGroups = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(currentGraphData.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) sim.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // 添加节点圆圈
    nodeGroups.append('circle')
      .attr('r', 20)
      .attr('fill', d => nodeColors[d.type as keyof typeof nodeColors] || nodeColors.default)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        setSelectedNode(d);
      })
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', 25);
        
        // 显示tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'graph-tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', 1000)
          .html(`
            <strong>${d.label}</strong><br/>
            类型: ${d.type}<br/>
            ${d.properties.description || ''}
          `);
        
        tooltip.style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('r', 20);
        d3.selectAll('.graph-tooltip').remove();
      });

    // 添加节点标签
    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', 'white')
      .style('pointer-events', 'none')
      .style('display', showLabels ? 'block' : 'none')
      .text(d => d.label.length > 8 ? d.label.substring(0, 8) + '...' : d.label);

    // 更新位置
    sim.on('tick', () => {
      links
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);

      linkLabels
        .attr('x', d => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
        .attr('y', d => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2);

      nodeGroups
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => {
      sim.stop();
    };
  }, [currentGraphData, showLabels, showEdgeLabels]);

  // 更新标签显示
  useEffect(() => {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('.node text')
      .style('display', showLabels ? 'block' : 'none');
    
    svg.selectAll('.link-label')
      .style('display', showEdgeLabels ? 'block' : 'none');
  }, [showLabels, showEdgeLabels]);

  const handleZoomIn = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1.5
    );
  };

  const handleZoomOut = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1 / 1.5
    );
  };

  const handleResetZoom = () => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity
    );
  };

  const handleDownload = () => {
    if (!svgRef.current) return;
    
    const svgElement = svgRef.current;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'knowledge-graph.svg';
    a.click();
  };

  const filteredNodes = currentGraphData.nodes.filter(node =>
    !searchTerm || node.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
              可视化探索知识库中的实体关系
            </Text>
          </div>
          
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownload}
            >
              导出图谱
            </Button>
            <Button
              icon={<FullscreenOutlined />}
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? '退出全屏' : '全屏显示'}
            </Button>
          </Space>
        </div>

        {/* 控制面板 */}
        <Row gutter={16}>
          <Col span={6}>
            <Select
              placeholder="选择知识库"
              value={selectedKnowledgeBase}
              onChange={setSelectedKnowledgeBase}
              style={{ width: '100%' }}
              allowClear
            >
              {kbData?.items?.map((kb: KnowledgeBase) => (
                <Select.Option key={kb.id} value={kb.id}>
                  {kb.name}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="实体类型"
              value={entityType}
              onChange={setEntityType}
              style={{ width: '100%' }}
              allowClear
            >
              <Select.Option value="Technology">技术</Select.Option>
              <Select.Option value="Framework">框架</Select.Option>
              <Select.Option value="Library">库</Select.Option>
              <Select.Option value="Database">数据库</Select.Option>
              <Select.Option value="Concept">概念</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <Input
              placeholder="搜索节点"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col span={4}>
            <Space>
              <Switch
                checked={showLabels}
                onChange={setShowLabels}
                size="small"
              />
              <Text>显示标签</Text>
            </Space>
          </Col>
          <Col span={6}>
            <Space>
              <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} size="small" />
              <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} size="small" />
              <Button icon={<CompressOutlined />} onClick={handleResetZoom} size="small" />
              <Button icon={<ReloadOutlined />} onClick={() => refetch()} size="small" loading={isLoading} />
            </Space>
          </Col>
        </Row>
      </div>

      {/* 图谱显示区域 */}
      <div className="flex-1 flex">
        <div className="flex-1 p-6">
          <Card className="h-full">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Spin size="large" tip="加载知识图谱中..." />
              </div>
            ) : currentGraphData.nodes.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <Alert
                  message="暂无图谱数据"
                  description="请选择知识库或调整筛选条件"
                  type="info"
                  showIcon
                />
              </div>
            ) : (
              <div className="relative h-full">
                <svg
                  ref={svgRef}
                  width="100%"
                  height="100%"
                  style={{ border: '1px solid #f0f0f0', borderRadius: '6px' }}
                />
                
                {/* 图例 */}
                <div className="absolute top-4 right-4 bg-white p-3 rounded shadow-lg">
                  <Text strong className="block mb-2">图例</Text>
                  {Object.entries(nodeColors).filter(([key]) => key !== 'default').map(([type, color]) => (
                    <div key={type} className="flex items-center mb-1">
                      <div
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: color }}
                      />
                      <Text style={{ fontSize: '12px' }}>{type}</Text>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* 侧边栏 */}
        <div className="w-80 p-6 pl-0">
          <Card title="图谱信息" size="small" className="mb-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Text>节点数量:</Text>
                <Tag color="blue">{currentGraphData.nodes.length}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>关系数量:</Text>
                <Tag color="green">{currentGraphData.edges.length}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>图谱深度:</Text>
                <Tag color="orange">{depth}</Tag>
              </div>
            </div>
          </Card>

          <Card title="参数设置" size="small" className="mb-4">
            <div className="space-y-4">
              <div>
                <Text>图谱深度: {depth}</Text>
                <Slider
                  min={1}
                  max={5}
                  value={depth}
                  onChange={setDepth}
                  marks={{ 1: '1', 3: '3', 5: '5' }}
                />
              </div>
              <div>
                <Text>节点限制: {nodeLimit}</Text>
                <Slider
                  min={50}
                  max={500}
                  step={50}
                  value={nodeLimit}
                  onChange={setNodeLimit}
                  marks={{ 50: '50', 250: '250', 500: '500' }}
                />
              </div>
              <div>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div className="flex justify-between">
                    <Text>显示节点标签</Text>
                    <Switch checked={showLabels} onChange={setShowLabels} size="small" />
                  </div>
                  <div className="flex justify-between">
                    <Text>显示关系标签</Text>
                    <Switch checked={showEdgeLabels} onChange={setShowEdgeLabels} size="small" />
                  </div>
                </Space>
              </div>
            </div>
          </Card>

          {selectedNode && (
            <Card title="节点详情" size="small">
              <div className="space-y-2">
                <div>
                  <Text strong>名称:</Text>
                  <Text className="ml-2">{selectedNode.label}</Text>
                </div>
                <div>
                  <Text strong>类型:</Text>
                  <Tag color={nodeColors[selectedNode.type as keyof typeof nodeColors]} className="ml-2">
                    {selectedNode.type}
                  </Tag>
                </div>
                {selectedNode.properties.description && (
                  <div>
                    <Text strong>描述:</Text>
                    <Text className="ml-2">{selectedNode.properties.description}</Text>
                  </div>
                )}
                <Divider />
                <Button
                  type="link"
                  size="small"
                  onClick={() => setSelectedNode(null)}
                >
                  关闭详情
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
