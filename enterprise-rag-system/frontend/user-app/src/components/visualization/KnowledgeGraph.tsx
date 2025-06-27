/**
 * 知识图谱可视化组件
 * 使用D3.js实现Neo4j知识图谱的交互式可视化
 */

'use client';

import React, {useEffect, useRef, useState} from 'react';
import * as d3 from 'd3';
import {Button, Card, Select, Slider, Space, Tooltip, Typography} from 'antd';
import {DownloadOutlined, ReloadOutlined, ZoomInOutlined, ZoomOutOutlined} from '@ant-design/icons';
import {useTheme} from '@/contexts/ThemeContext';

const { Text } = Typography;
const { Option } = Select;

interface GraphNode {
  id: string;
  label: string;
  type: 'document' | 'entity' | 'concept' | 'chunk';
  properties: Record<string, any>;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  weight: number;
  properties: Record<string, any>;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface KnowledgeGraphProps {
  data: GraphData;
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  onLinkClick?: (link: GraphLink) => void;
  className?: string;
}

export function KnowledgeGraph({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onLinkClick,
  className = ''
}: KnowledgeGraphProps) {
  const { theme, isDark } = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [linkDistance, setLinkDistance] = useState(100);
  const [chargeStrength, setChargeStrength] = useState(-300);
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 节点类型颜色映射
  const getNodeColor = (type: string) => {
    const colors = {
      document: theme.colors.primary,
      entity: theme.colors.success,
      concept: theme.colors.warning,
      chunk: theme.colors.info
    };
    return colors[type as keyof typeof colors] || theme.colors.secondary;
  };

  // 节点大小映射
  const getNodeSize = (node: GraphNode) => {
    const baseSizes = {
      document: 12,
      entity: 8,
      concept: 10,
      chunk: 6
    };
    const baseSize = baseSizes[node.type] || 8;
    
    // 根据连接数调整大小
    const connections = data.links.filter(
      link => link.source === node.id || link.target === node.id
    ).length;
    
    return baseSize + Math.min(connections * 2, 20);
  };

  // 初始化和更新图谱
  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 创建容器组
    const container = svg.append('g').attr('class', 'graph-container');

    // 设置缩放行为
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // 过滤数据
    const filteredNodes = selectedNodeType === 'all' 
      ? data.nodes 
      : data.nodes.filter(node => node.type === selectedNodeType);
    
    const filteredLinks = data.links.filter(link => {
      const sourceNode = data.nodes.find(n => n.id === (typeof link.source === 'string' ? link.source : link.source.id));
      const targetNode = data.nodes.find(n => n.id === (typeof link.target === 'string' ? link.target : link.target.id));
      return filteredNodes.includes(sourceNode!) && filteredNodes.includes(targetNode!);
    });

    // 创建力导向图模拟
    const simulation = d3.forceSimulation<GraphNode>(filteredNodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(filteredLinks)
        .id(d => d.id)
        .distance(linkDistance)
        .strength(0.1))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 5));

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
      .attr('fill', theme.colors.onSurfaceVariant);

    // 创建连接线
    const links = container.selectAll('.link')
      .data(filteredLinks)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', theme.colors.outline)
      .attr('stroke-width', d => Math.sqrt(d.weight) * 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)')
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        onLinkClick?.(d);
      });

    // 创建节点组
    const nodeGroups = container.selectAll('.node')
      .data(filteredNodes)
      .enter().append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // 添加节点圆圈
    nodeGroups.append('circle')
      .attr('r', getNodeSize)
      .attr('fill', d => getNodeColor(d.type))
      .attr('stroke', theme.colors.background)
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        onNodeClick?.(d);
      })
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', getNodeSize(d) * 1.2)
          .attr('stroke-width', 3);
        
        // 显示工具提示
        const tooltip = d3.select('body').append('div')
          .attr('class', 'graph-tooltip')
          .style('position', 'absolute')
          .style('background', theme.colors.surface)
          .style('border', `1px solid ${theme.colors.outline}`)
          .style('border-radius', '4px')
          .style('padding', '8px')
          .style('font-size', '12px')
          .style('color', theme.colors.onSurface)
          .style('pointer-events', 'none')
          .style('opacity', 0);

        tooltip.transition()
          .duration(200)
          .style('opacity', 1);

        tooltip.html(`
          <div><strong>${d.label}</strong></div>
          <div>类型: ${d.type}</div>
          <div>ID: ${d.id}</div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', getNodeSize(d))
          .attr('stroke-width', 2);
        
        d3.selectAll('.graph-tooltip').remove();
      });

    // 添加节点标签
    nodeGroups.append('text')
      .text(d => d.label.length > 15 ? d.label.substring(0, 15) + '...' : d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', d => getNodeSize(d) + 15)
      .attr('font-size', '10px')
      .attr('fill', theme.colors.onSurface)
      .style('pointer-events', 'none');

    // 更新位置
    simulation.on('tick', () => {
      links
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);

      nodeGroups
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // 清理函数
    return () => {
      simulation.stop();
    };
  }, [data, theme, selectedNodeType, linkDistance, chargeStrength, width, height]);

  // 缩放控制
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

  // 导出图片
  const handleExport = () => {
    const svg = svgRef.current;
    if (!svg) return;

    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    canvas.width = width;
    canvas.height = height;

    img.onload = () => {
      ctx?.drawImage(img, 0, 0);
      const link = document.createElement('a');
      link.download = 'knowledge-graph.png';
      link.href = canvas.toDataURL();
      link.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
  };

  return (
    <Card 
      className={className}
      style={{ backgroundColor: theme.colors.surface }}
      title={
        <div className="flex items-center justify-between">
          <Text strong style={{ color: theme.colors.onSurface }}>
            知识图谱可视化
          </Text>
          <Space>
            <Text style={{ color: theme.colors.onSurfaceVariant }}>
              节点: {data.nodes.length} | 关系: {data.links.length}
            </Text>
          </Space>
        </div>
      }
      extra={
        <Space>
          <Select
            value={selectedNodeType}
            onChange={setSelectedNodeType}
            style={{ width: 120 }}
            size="small"
          >
            <Option value="all">所有类型</Option>
            <Option value="document">文档</Option>
            <Option value="entity">实体</Option>
            <Option value="concept">概念</Option>
            <Option value="chunk">分块</Option>
          </Select>
          
          <Tooltip title="放大">
            <Button size="small" icon={<ZoomInOutlined />} onClick={handleZoomIn} />
          </Tooltip>
          
          <Tooltip title="缩小">
            <Button size="small" icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
          </Tooltip>
          
          <Tooltip title="重置">
            <Button size="small" icon={<ReloadOutlined />} onClick={handleReset} />
          </Tooltip>
          
          <Tooltip title="导出">
            <Button size="small" icon={<DownloadOutlined />} onClick={handleExport} />
          </Tooltip>
        </Space>
      }
    >
      <div className="space-y-4">
        {/* 控制面板 */}
        <div className="flex items-center gap-4 p-3 rounded-lg" style={{ backgroundColor: theme.colors.surfaceVariant }}>
          <div className="flex items-center gap-2">
            <Text style={{ color: theme.colors.onSurfaceVariant }}>连接距离:</Text>
            <Slider
              min={50}
              max={200}
              value={linkDistance}
              onChange={setLinkDistance}
              style={{ width: 100 }}
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Text style={{ color: theme.colors.onSurfaceVariant }}>排斥力:</Text>
            <Slider
              min={-500}
              max={-100}
              value={chargeStrength}
              onChange={setChargeStrength}
              style={{ width: 100 }}
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Text style={{ color: theme.colors.onSurfaceVariant }}>缩放:</Text>
            <Text style={{ color: theme.colors.onSurface }}>{(zoom * 100).toFixed(0)}%</Text>
          </div>
        </div>

        {/* 图谱容器 */}
        <div 
          className="border rounded-lg overflow-hidden"
          style={{ 
            borderColor: theme.colors.outline,
            backgroundColor: theme.colors.background 
          }}
        >
          <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{ display: 'block' }}
          />
        </div>

        {/* 图例 */}
        <div className="flex items-center gap-4 p-3 rounded-lg" style={{ backgroundColor: theme.colors.surfaceVariant }}>
          <Text style={{ color: theme.colors.onSurfaceVariant }}>图例:</Text>
          {[
            { type: 'document', label: '文档' },
            { type: 'entity', label: '实体' },
            { type: 'concept', label: '概念' },
            { type: 'chunk', label: '分块' }
          ].map(({ type, label }) => (
            <div key={type} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getNodeColor(type) }}
              />
              <Text style={{ color: theme.colors.onSurfaceVariant }}>{label}</Text>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
