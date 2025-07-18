import React, { useEffect, useRef, useState } from 'react'
import { Card, Button, Space, Select, Slider, Switch, Tooltip, message } from 'antd'
import {
  FullscreenOutlined,
  ReloadOutlined,
  DownloadOutlined,
  SettingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  DragOutlined
} from '@ant-design/icons'
import * as d3 from 'd3'
import './KnowledgeGraphVisualization.css'

const { Option } = Select

interface Node {
  id: string
  name: string
  type: string
  properties: Record<string, any>
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface Link {
  source: string | Node
  target: string | Node
  type: string
  properties: Record<string, any>
}

interface GraphData {
  nodes: Node[]
  links: Link[]
}

interface KnowledgeGraphVisualizationProps {
  data?: GraphData
  width?: number
  height?: number
  onNodeClick?: (node: Node) => void
  onLinkClick?: (link: Link) => void
}

const KnowledgeGraphVisualization: React.FC<KnowledgeGraphVisualizationProps> = ({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onLinkClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [simulation, setSimulation] = useState<d3.Simulation<Node, Link> | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [nodeSize, setNodeSize] = useState(8)
  const [linkDistance, setLinkDistance] = useState(100)
  const [chargeStrength, setChargeStrength] = useState(-300)
  const [showLabels, setShowLabels] = useState(true)
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all')
  const [isDragging, setIsDragging] = useState(false)

  // 节点类型颜色映射
  const nodeTypeColors = {
    'PERSON': '#ff7875',
    'ORGANIZATION': '#40a9ff',
    'LOCATION': '#73d13d',
    'CONCEPT': '#b37feb',
    'TECHNOLOGY': '#ffa940',
    'DOCUMENT': '#36cfc9',
    'EVENT': '#ff9c6e',
    'default': '#d9d9d9'
  }

  // 关系类型样式映射
  const linkTypeStyles = {
    'WORKS_FOR': { stroke: '#1890ff', strokeWidth: 2, strokeDasharray: 'none' },
    'LOCATED_IN': { stroke: '#52c41a', strokeWidth: 2, strokeDasharray: 'none' },
    'PART_OF': { stroke: '#722ed1', strokeWidth: 1.5, strokeDasharray: '5,5' },
    'RELATED_TO': { stroke: '#fa8c16', strokeWidth: 1, strokeDasharray: '3,3' },
    'default': { stroke: '#d9d9d9', strokeWidth: 1, strokeDasharray: 'none' }
  }

  useEffect(() => {
    if (!data || !svgRef.current) return

    initializeGraph()
  }, [data, width, height, nodeSize, linkDistance, chargeStrength])

  const initializeGraph = () => {
    if (!data || !svgRef.current) return

    // 清除之前的内容
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
    const container = svg.append('g')

    // 添加缩放和拖拽功能
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform)
      })

    svg.call(zoom)

    // 创建力导向图仿真
    const sim = d3.forceSimulation<Node>(data.nodes)
      .force('link', d3.forceLink<Node, Link>(data.links)
        .id(d => d.id)
        .distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(nodeSize + 2))

    setSimulation(sim)

    // 创建箭头标记
    const defs = svg.append('defs')
    
    Object.entries(linkTypeStyles).forEach(([type, style]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', style.stroke)
    })

    // 绘制连接线
    const links = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(data.links)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', d => linkTypeStyles[d.type]?.stroke || linkTypeStyles.default.stroke)
      .attr('stroke-width', d => linkTypeStyles[d.type]?.strokeWidth || linkTypeStyles.default.strokeWidth)
      .attr('stroke-dasharray', d => linkTypeStyles[d.type]?.strokeDasharray || linkTypeStyles.default.strokeDasharray)
      .attr('marker-end', d => `url(#arrow-${d.type})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        onLinkClick?.(d)
      })

    // 绘制节点
    const nodes = container.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(data.nodes)
      .enter().append('circle')
      .attr('class', 'node')
      .attr('r', nodeSize)
      .attr('fill', d => nodeTypeColors[d.type] || nodeTypeColors.default)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeClick?.(d)
      })
      .on('mouseover', function(event, d) {
        d3.select(this).attr('stroke-width', 3)
        
        // 显示tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'graph-tooltip')
          .style('opacity', 0)
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', 1000)

        tooltip.transition().duration(200).style('opacity', 1)
        tooltip.html(`
          <strong>${d.name}</strong><br/>
          类型: ${d.type}<br/>
          ID: ${d.id}
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke-width', 2)
        d3.selectAll('.graph-tooltip').remove()
      })

    // 添加节点标签
    const labels = container.append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(data.nodes)
      .enter().append('text')
      .attr('class', 'label')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .attr('pointer-events', 'none')
      .style('display', showLabels ? 'block' : 'none')
      .text(d => d.name.length > 10 ? d.name.substring(0, 10) + '...' : d.name)

    // 更新位置
    sim.on('tick', () => {
      links
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!)

      nodes
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!)

      labels
        .attr('x', d => d.x!)
        .attr('y', d => d.y! + nodeSize + 12)
    })

    function dragstarted(event: d3.D3DragEvent<SVGCircleElement, Node, Node>, d: Node) {
      setIsDragging(true)
      if (!event.active) sim.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: d3.D3DragEvent<SVGCircleElement, Node, Node>, d: Node) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: d3.D3DragEvent<SVGCircleElement, Node, Node>, d: Node) {
      setIsDragging(false)
      if (!event.active) sim.alphaTarget(0)
      d.fx = null
      d.fy = null
    }
  }

  const handleRestart = () => {
    if (simulation) {
      simulation.alpha(1).restart()
    }
  }

  const handleZoomIn = () => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1.5
      )
    }
  }

  const handleZoomOut = () => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1 / 1.5
      )
    }
  }

  const handleDownload = () => {
    if (!svgRef.current) return

    const svgElement = svgRef.current
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svgElement)
    
    const blob = new Blob([svgString], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = 'knowledge-graph.svg'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    message.success('知识图谱已下载')
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const getNodeTypes = () => {
    if (!data) return []
    const types = new Set(data.nodes.map(node => node.type))
    return Array.from(types)
  }

  return (
    <Card 
      className={`knowledge-graph-container ${isFullscreen ? 'fullscreen' : ''}`}
      title="知识图谱可视化"
      extra={
        <Space>
          <Tooltip title="重新布局">
            <Button icon={<ReloadOutlined />} onClick={handleRestart} />
          </Tooltip>
          <Tooltip title="放大">
            <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
          </Tooltip>
          <Tooltip title="缩小">
            <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
          </Tooltip>
          <Tooltip title="下载">
            <Button icon={<DownloadOutlined />} onClick={handleDownload} />
          </Tooltip>
          <Tooltip title="全屏">
            <Button icon={<FullscreenOutlined />} onClick={toggleFullscreen} />
          </Tooltip>
        </Space>
      }
    >
      <div className="graph-controls">
        <Space wrap>
          <div className="control-item">
            <span>节点类型:</span>
            <Select
              value={selectedNodeType}
              onChange={setSelectedNodeType}
              style={{ width: 120 }}
            >
              <Option value="all">全部</Option>
              {getNodeTypes().map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </div>
          
          <div className="control-item">
            <span>节点大小:</span>
            <Slider
              min={4}
              max={20}
              value={nodeSize}
              onChange={setNodeSize}
              style={{ width: 100 }}
            />
          </div>
          
          <div className="control-item">
            <span>连接距离:</span>
            <Slider
              min={50}
              max={200}
              value={linkDistance}
              onChange={setLinkDistance}
              style={{ width: 100 }}
            />
          </div>
          
          <div className="control-item">
            <span>显示标签:</span>
            <Switch
              checked={showLabels}
              onChange={setShowLabels}
            />
          </div>
        </Space>
      </div>

      <div className="graph-canvas">
        <svg
          ref={svgRef}
          width={isFullscreen ? '100vw' : width}
          height={isFullscreen ? '100vh' : height}
          style={{ border: '1px solid #d9d9d9', borderRadius: '6px' }}
        />
      </div>

      {isDragging && (
        <div className="drag-hint">
          <DragOutlined /> 拖拽节点调整位置
        </div>
      )}
    </Card>
  )
}

export default KnowledgeGraphVisualization
