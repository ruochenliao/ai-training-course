'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, Button, Slider, Select, Space, Typography, Tooltip } from 'antd';
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import * as d3 from 'd3';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;
const { Option } = Select;

interface Node {
  id: string;
  name: string;
  type: 'document' | 'concept' | 'entity' | 'keyword';
  size: number;
  color: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Link {
  source: string | Node;
  target: string | Node;
  value: number;
  type: 'related' | 'contains' | 'references';
}

interface KnowledgeGraphProps {
  data?: {
    nodes: Node[];
    links: Link[];
  };
  width?: number;
  height?: number;
  className?: string;
}

export default function KnowledgeGraph({
  data,
  width = 800,
  height = 600,
  className = '',
}: KnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [linkDistance, setLinkDistance] = useState(100);
  const [chargeStrength, setChargeStrength] = useState(-300);
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 模拟数据
  const mockData = data || {
    nodes: [
      { id: '1', name: '企业架构文档', type: 'document', size: 20, color: '#1890ff' },
      { id: '2', name: '微服务', type: 'concept', size: 15, color: '#52c41a' },
      { id: '3', name: 'Docker', type: 'entity', size: 12, color: '#fa8c16' },
      { id: '4', name: 'Kubernetes', type: 'entity', size: 18, color: '#fa8c16' },
      { id: '5', name: '容器化', type: 'keyword', size: 10, color: '#eb2f96' },
      { id: '6', name: 'API网关', type: 'concept', size: 14, color: '#52c41a' },
      { id: '7', name: '负载均衡', type: 'concept', size: 13, color: '#52c41a' },
      { id: '8', name: '技术规范', type: 'document', size: 16, color: '#1890ff' },
      { id: '9', name: '部署指南', type: 'document', size: 14, color: '#1890ff' },
      { id: '10', name: 'DevOps', type: 'keyword', size: 11, color: '#eb2f96' },
    ],
    links: [
      { source: '1', target: '2', value: 5, type: 'contains' },
      { source: '2', target: '3', value: 3, type: 'related' },
      { source: '2', target: '4', value: 4, type: 'related' },
      { source: '3', target: '5', value: 2, type: 'references' },
      { source: '4', target: '5', value: 3, type: 'references' },
      { source: '2', target: '6', value: 4, type: 'related' },
      { source: '6', target: '7', value: 3, type: 'related' },
      { source: '8', target: '2', value: 3, type: 'contains' },
      { source: '9', target: '4', value: 4, type: 'contains' },
      { source: '5', target: '10', value: 2, type: 'related' },
    ],
  };

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const container = svg
      .append('g')
      .attr('class', 'graph-container');

    // 创建缩放行为
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // 过滤节点
    const filteredNodes = selectedNodeType === 'all' 
      ? mockData.nodes 
      : mockData.nodes.filter(node => node.type === selectedNodeType);
    
    const filteredNodeIds = new Set(filteredNodes.map(node => node.id));
    const filteredLinks = mockData.links.filter(
      link => filteredNodeIds.has(typeof link.source === 'string' ? link.source : link.source.id) &&
              filteredNodeIds.has(typeof link.target === 'string' ? link.target : link.target.id)
    );

    // 创建力导向图
    const simulation = d3.forceSimulation(filteredNodes as any)
      .force('link', d3.forceLink(filteredLinks).id((d: any) => d.id).distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => d.size + 5));

    // 创建箭头标记
    const defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // 创建连线
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredLinks)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.value))
      .attr('marker-end', 'url(#arrowhead)');

    // 创建节点
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(filteredNodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // 添加节点圆圈
    node.append('circle')
      .attr('r', (d: any) => d.size)
      .attr('fill', (d: any) => d.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer');

    // 添加节点标签
    node.append('text')
      .text((d: any) => d.name)
      .attr('x', 0)
      .attr('y', (d: any) => d.size + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#333')
      .style('pointer-events', 'none');

    // 添加悬停效果
    node
      .on('mouseover', function(event, d: any) {
        d3.select(this).select('circle')
          .transition()
          .duration(200)
          .attr('r', d.size * 1.2)
          .attr('stroke-width', 3);
      })
      .on('mouseout', function(event, d: any) {
        d3.select(this).select('circle')
          .transition()
          .duration(200)
          .attr('r', d.size)
          .attr('stroke-width', 2);
      })
      .on('click', function(event, d: any) {
        console.log('点击节点:', d);
      });

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // 拖拽函数
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 清理函数
    return () => {
      simulation.stop();
    };
  }, [width, height, linkDistance, chargeStrength, selectedNodeType]);

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.5
    );
  };

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1 / 1.5
    );
  };

  const handleReset = () => {
    const svg = d3.select(svgRef.current);
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity
    );
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`${className} ${isFullscreen ? 'fixed inset-0 z-50 bg-white dark:bg-gray-900' : ''}`}
    >
      <Card
        title={
          <div className="flex items-center justify-between">
            <Title level={4} className="!mb-0">知识图谱</Title>
            <Space>
              <Text type="secondary">缩放: {(zoom * 100).toFixed(0)}%</Text>
            </Space>
          </div>
        }
        extra={
          <Space>
            <Tooltip title="放大">
              <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
            </Tooltip>
            <Tooltip title="缩小">
              <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
            </Tooltip>
            <Tooltip title="重置">
              <Button icon={<ReloadOutlined />} onClick={handleReset} />
            </Tooltip>
            <Tooltip title={isFullscreen ? '退出全屏' : '全屏'}>
              <Button icon={<FullscreenOutlined />} onClick={toggleFullscreen} />
            </Tooltip>
          </Space>
        }
        className={`${isFullscreen ? 'h-full' : ''} shadow-lg`}
        bodyStyle={{ padding: 0 }}
      >
        {/* 控制面板 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Text strong className="block mb-2">节点类型</Text>
              <Select
                value={selectedNodeType}
                onChange={setSelectedNodeType}
                style={{ width: '100%' }}
              >
                <Option value="all">全部</Option>
                <Option value="document">文档</Option>
                <Option value="concept">概念</Option>
                <Option value="entity">实体</Option>
                <Option value="keyword">关键词</Option>
              </Select>
            </div>
            
            <div>
              <Text strong className="block mb-2">连线距离</Text>
              <Slider
                min={50}
                max={200}
                value={linkDistance}
                onChange={setLinkDistance}
              />
            </div>
            
            <div>
              <Text strong className="block mb-2">排斥力</Text>
              <Slider
                min={-500}
                max={-100}
                value={chargeStrength}
                onChange={setChargeStrength}
              />
            </div>
            
            <div className="flex items-end">
              <Button icon={<SettingOutlined />} block>
                高级设置
              </Button>
            </div>
          </div>
        </div>

        {/* 图谱容器 */}
        <div className="relative" style={{ height: isFullscreen ? 'calc(100vh - 200px)' : height }}>
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            className="border-0"
            style={{ background: 'linear-gradient(45deg, #f8f9fa 25%, transparent 25%), linear-gradient(-45deg, #f8f9fa 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f8f9fa 75%), linear-gradient(-45deg, transparent 75%, #f8f9fa 75%)', backgroundSize: '20px 20px', backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px' }}
          />
          
          {/* 图例 */}
          <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3">
            <Text strong className="block mb-2">图例</Text>
            <div className="space-y-2">
              {[
                { type: 'document', color: '#1890ff', label: '文档' },
                { type: 'concept', color: '#52c41a', label: '概念' },
                { type: 'entity', color: '#fa8c16', label: '实体' },
                { type: 'keyword', color: '#eb2f96', label: '关键词' },
              ].map(item => (
                <div key={item.type} className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <Text className="text-sm">{item.label}</Text>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
