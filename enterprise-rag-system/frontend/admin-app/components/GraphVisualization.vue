<template>
  <div class="graph-visualization">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <n-space>
          <n-select
            v-model:value="selectedKnowledgeBase"
            :options="knowledgeBaseOptions"
            placeholder="选择知识库"
            style="width: 200px"
            @update:value="handleKnowledgeBaseChange"
          />
          
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索实体或关系"
            style="width: 250px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <Icon name="heroicons:magnifying-glass" />
            </template>
          </n-input>
          
          <n-button type="primary" @click="handleSearch">
            搜索
          </n-button>
        </n-space>
      </div>
      
      <div class="toolbar-right">
        <n-space>
          <n-button-group>
            <n-button @click="zoomIn">
              <Icon name="heroicons:plus" />
            </n-button>
            <n-button @click="zoomOut">
              <Icon name="heroicons:minus" />
            </n-button>
            <n-button @click="resetZoom">
              <Icon name="heroicons:arrow-path" />
            </n-button>
          </n-button-group>
          
          <n-dropdown :options="layoutOptions" @select="handleLayoutChange">
            <n-button>
              布局: {{ currentLayout }}
              <Icon name="heroicons:chevron-down" />
            </n-button>
          </n-dropdown>
          
          <n-button @click="exportGraph">
            <Icon name="heroicons:arrow-down-tray" />
            导出
          </n-button>
        </n-space>
      </div>
    </div>
    
    <!-- 图谱容器 -->
    <div class="graph-container">
      <div ref="chartRef" class="chart" />
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <n-spin size="large">
          <template #description>
            加载图谱数据中...
          </template>
        </n-spin>
      </div>
      
      <!-- 空状态 -->
      <div v-if="!loading && !hasData" class="empty-state">
        <n-empty description="暂无图谱数据">
          <template #extra>
            <n-button @click="refreshData">
              刷新数据
            </n-button>
          </template>
        </n-empty>
      </div>
    </div>
    
    <!-- 侧边面板 -->
    <div v-if="selectedNode" class="side-panel">
      <div class="panel-header">
        <h3>{{ selectedNode.name }}</h3>
        <n-button quaternary circle @click="closeSidePanel">
          <Icon name="heroicons:x-mark" />
        </n-button>
      </div>
      
      <div class="panel-content">
        <n-descriptions :column="1" bordered>
          <n-descriptions-item label="类型">
            {{ selectedNode.category }}
          </n-descriptions-item>
          <n-descriptions-item label="度数">
            {{ selectedNode.degree }}
          </n-descriptions-item>
          <n-descriptions-item label="描述">
            {{ selectedNode.description || '暂无描述' }}
          </n-descriptions-item>
        </n-descriptions>
        
        <n-divider />
        
        <h4>相关关系</h4>
        <n-list>
          <n-list-item
            v-for="relation in selectedNodeRelations"
            :key="relation.id"
          >
            <div class="relation-item">
              <span class="relation-type">{{ relation.type }}</span>
              <span class="relation-target">{{ relation.target }}</span>
            </div>
          </n-list-item>
        </n-list>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'

interface GraphNode {
  id: string
  name: string
  category: string
  value: number
  degree: number
  description?: string
  x?: number
  y?: number
}

interface GraphLink {
  id: string
  source: string
  target: string
  type: string
  weight: number
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  categories: Array<{ name: string; color: string }>
}

// 响应式数据
const chartRef = ref<HTMLElement>()
const chart = ref<ECharts>()
const loading = ref(false)
const hasData = ref(false)
const searchQuery = ref('')
const selectedKnowledgeBase = ref<number>()
const selectedNode = ref<GraphNode>()
const selectedNodeRelations = ref<Array<{ id: string; type: string; target: string }>>([])

// 图谱数据
const graphData = ref<GraphData>({
  nodes: [],
  links: [],
  categories: []
})

// 布局选项
const currentLayout = ref('force')
const layoutOptions = [
  { label: '力导向布局', key: 'force' },
  { label: '圆形布局', key: 'circular' },
  { label: '网格布局', key: 'grid' }
]

// 知识库选项
const knowledgeBaseOptions = ref([
  { label: '全部知识库', value: 0 },
  { label: '技术文档', value: 1 },
  { label: '产品手册', value: 2 },
  { label: '业务流程', value: 3 }
])

// 生命周期
onMounted(() => {
  initChart()
  loadGraphData()
})

onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
  }
})

// 初始化图表
function initChart() {
  if (!chartRef.value) return
  
  chart.value = echarts.init(chartRef.value)
  
  // 监听节点点击事件
  chart.value.on('click', (params: any) => {
    if (params.dataType === 'node') {
      handleNodeClick(params.data)
    }
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    chart.value?.resize()
  })
}

// 加载图谱数据
async function loadGraphData() {
  loading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟数据
    const mockData: GraphData = {
      nodes: [
        { id: '1', name: 'Python', category: '编程语言', value: 100, degree: 15 },
        { id: '2', name: 'FastAPI', category: '框架', value: 80, degree: 12 },
        { id: '3', name: 'Vue.js', category: '框架', value: 90, degree: 18 },
        { id: '4', name: 'TypeScript', category: '编程语言', value: 70, degree: 10 },
        { id: '5', name: 'Docker', category: '工具', value: 85, degree: 14 },
        { id: '6', name: 'Redis', category: '数据库', value: 75, degree: 8 },
        { id: '7', name: 'MySQL', category: '数据库', value: 95, degree: 20 },
        { id: '8', name: 'Milvus', category: '向量数据库', value: 60, degree: 6 },
        { id: '9', name: 'Neo4j', category: '图数据库', value: 65, degree: 7 }
      ],
      links: [
        { id: 'l1', source: '1', target: '2', type: '使用', weight: 0.8 },
        { id: 'l2', source: '3', target: '4', type: '基于', weight: 0.9 },
        { id: 'l3', source: '2', target: '6', type: '集成', weight: 0.7 },
        { id: 'l4', source: '2', target: '7', type: '连接', weight: 0.8 },
        { id: 'l5', source: '1', target: '8', type: '操作', weight: 0.6 },
        { id: 'l6', source: '1', target: '9', type: '查询', weight: 0.7 },
        { id: 'l7', source: '5', target: '2', type: '部署', weight: 0.9 },
        { id: 'l8', source: '5', target: '3', type: '容器化', weight: 0.8 }
      ],
      categories: [
        { name: '编程语言', color: '#5470c6' },
        { name: '框架', color: '#91cc75' },
        { name: '工具', color: '#fac858' },
        { name: '数据库', color: '#ee6666' },
        { name: '向量数据库', color: '#73c0de' },
        { name: '图数据库', color: '#3ba272' }
      ]
    }
    
    graphData.value = mockData
    hasData.value = mockData.nodes.length > 0
    updateChart()
    
  } catch (error) {
    console.error('加载图谱数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 更新图表
function updateChart() {
  if (!chart.value || !hasData.value) return
  
  const option = {
    title: {
      text: '知识图谱',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `
            <div>
              <strong>${params.data.name}</strong><br/>
              类型: ${params.data.category}<br/>
              度数: ${params.data.degree}<br/>
              权重: ${params.data.value}
            </div>
          `
        } else if (params.dataType === 'edge') {
          return `
            <div>
              关系: ${params.data.type}<br/>
              权重: ${params.data.weight}
            </div>
          `
        }
      }
    },
    legend: {
      data: graphData.value.categories.map(cat => cat.name),
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        type: 'graph',
        layout: currentLayout.value,
        data: graphData.value.nodes.map(node => ({
          ...node,
          symbolSize: Math.sqrt(node.value) * 2,
          itemStyle: {
            color: graphData.value.categories.find(cat => cat.name === node.category)?.color
          }
        })),
        links: graphData.value.links.map(link => ({
          ...link,
          lineStyle: {
            width: link.weight * 3,
            opacity: 0.7
          }
        })),
        categories: graphData.value.categories,
        roam: true,
        focusNodeAdjacency: true,
        draggable: true,
        force: {
          repulsion: 1000,
          gravity: 0.1,
          edgeLength: 200,
          layoutAnimation: true
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{b}'
        },
        lineStyle: {
          color: 'source',
          curveness: 0.1
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 5
          }
        }
      }
    ]
  }
  
  chart.value.setOption(option, true)
}

// 节点点击处理
function handleNodeClick(node: GraphNode) {
  selectedNode.value = node
  
  // 获取相关关系
  selectedNodeRelations.value = graphData.value.links
    .filter(link => link.source === node.id || link.target === node.id)
    .map(link => ({
      id: link.id,
      type: link.type,
      target: link.source === node.id 
        ? graphData.value.nodes.find(n => n.id === link.target)?.name || ''
        : graphData.value.nodes.find(n => n.id === link.source)?.name || ''
    }))
}

// 关闭侧边面板
function closeSidePanel() {
  selectedNode.value = undefined
  selectedNodeRelations.value = []
}

// 搜索处理
function handleSearch() {
  if (!searchQuery.value.trim()) {
    updateChart()
    return
  }
  
  // 过滤节点和边
  const filteredNodes = graphData.value.nodes.filter(node =>
    node.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    node.category.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
  
  const filteredNodeIds = new Set(filteredNodes.map(node => node.id))
  const filteredLinks = graphData.value.links.filter(link =>
    filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target)
  )
  
  // 更新图表
  const option = chart.value?.getOption()
  if (option && option.series) {
    option.series[0].data = filteredNodes
    option.series[0].links = filteredLinks
    chart.value?.setOption(option, true)
  }
}

// 知识库变更处理
function handleKnowledgeBaseChange(value: number) {
  loadGraphData()
}

// 布局变更处理
function handleLayoutChange(key: string) {
  currentLayout.value = key
  updateChart()
}

// 缩放控制
function zoomIn() {
  chart.value?.dispatchAction({
    type: 'dataZoom',
    start: 0,
    end: 50
  })
}

function zoomOut() {
  chart.value?.dispatchAction({
    type: 'dataZoom',
    start: 0,
    end: 100
  })
}

function resetZoom() {
  chart.value?.dispatchAction({
    type: 'restore'
  })
}

// 导出图谱
function exportGraph() {
  if (!chart.value) return
  
  const url = chart.value.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `knowledge-graph-${Date.now()}.png`
  link.href = url
  link.click()
}

// 刷新数据
function refreshData() {
  loadGraphData()
}
</script>

<style scoped>
.graph-visualization {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--n-card-color);
  border-bottom: 1px solid var(--n-border-color);
}

.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.chart {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 10;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.side-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background: var(--n-card-color);
  border-left: 1px solid var(--n-border-color);
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--n-border-color);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.relation-type {
  font-weight: 500;
  color: var(--n-primary-color);
}

.relation-target {
  color: var(--n-text-color-2);
}
</style>
