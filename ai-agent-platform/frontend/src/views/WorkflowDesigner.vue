<template>
  <div class="workflow-designer">
    <div class="designer-header">
      <div class="header-left">
        <h1>工作流设计器</h1>
        <div class="workflow-info">
          <el-input 
            v-model="workflowName" 
            placeholder="工作流名称"
            style="width: 200px; margin-right: 12px;"
          />
          <el-tag v-if="currentWorkflow.status" :type="getStatusType(currentWorkflow.status)">
            {{ getStatusText(currentWorkflow.status) }}
          </el-tag>
        </div>
      </div>
      
      <div class="header-actions">
        <el-button @click="showTemplateDialog = true">
          <el-icon><Document /></el-icon>
          模板
        </el-button>
        <el-button @click="validateWorkflow">
          <el-icon><Check /></el-icon>
          验证
        </el-button>
        <el-button type="primary" @click="saveWorkflow" :loading="saving">
          <el-icon><DocumentAdd /></el-icon>
          保存
        </el-button>
        <el-button type="success" @click="deployWorkflow" :loading="deploying">
          <el-icon><Upload /></el-icon>
          部署
        </el-button>
      </div>
    </div>

    <div class="designer-content">
      <!-- 工具面板 -->
      <div class="tool-panel">
        <div class="panel-header">
          <h3>组件库</h3>
        </div>
        
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="智能体" name="agents">
            <div class="tool-group">
              <div 
                v-for="agent in agentNodes" 
                :key="agent.type"
                class="tool-item"
                draggable="true"
                @dragstart="handleDragStart($event, agent)"
              >
                <div class="tool-icon">
                  <el-icon>{{ agent.icon }}</el-icon>
                </div>
                <span class="tool-name">{{ agent.name }}</span>
              </div>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="控制流" name="control">
            <div class="tool-group">
              <div 
                v-for="control in controlNodes" 
                :key="control.type"
                class="tool-item"
                draggable="true"
                @dragstart="handleDragStart($event, control)"
              >
                <div class="tool-icon">
                  <el-icon>{{ control.icon }}</el-icon>
                </div>
                <span class="tool-name">{{ control.name }}</span>
              </div>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="工具" name="tools">
            <div class="tool-group">
              <div 
                v-for="tool in toolNodes" 
                :key="tool.type"
                class="tool-item"
                draggable="true"
                @dragstart="handleDragStart($event, tool)"
              >
                <div class="tool-icon">
                  <el-icon>{{ tool.icon }}</el-icon>
                </div>
                <span class="tool-name">{{ tool.name }}</span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 设计画布 -->
      <div class="design-canvas">
        <div class="canvas-toolbar">
          <el-button-group>
            <el-button :type="canvasMode === 'select' ? 'primary' : ''" @click="setCanvasMode('select')">
              <el-icon><Pointer /></el-icon>
            </el-button>
            <el-button :type="canvasMode === 'connect' ? 'primary' : ''" @click="setCanvasMode('connect')">
              <el-icon><Connection /></el-icon>
            </el-button>
          </el-button-group>
          
          <div class="canvas-actions">
            <el-button @click="zoomIn">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <el-button @click="zoomOut">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button @click="resetZoom">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div 
          ref="canvasContainer"
          class="canvas-container"
          @drop="handleDrop"
          @dragover.prevent
          @click="handleCanvasClick"
        >
          <svg 
            ref="svgCanvas"
            class="canvas-svg"
            :style="{ transform: `scale(${zoomLevel})` }"
          >
            <!-- 网格背景 -->
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            <!-- 连接线 -->
            <g class="connections">
              <path 
                v-for="connection in connections" 
                :key="connection.id"
                :d="getConnectionPath(connection)"
                class="connection-path"
                :class="{ selected: selectedConnection === connection.id }"
                @click="selectConnection(connection.id)"
              />
            </g>
            
            <!-- 临时连接线 -->
            <path 
              v-if="tempConnection"
              :d="tempConnection.path"
              class="temp-connection"
            />
          </svg>
          
          <!-- 工作流节点 -->
          <div class="canvas-nodes">
            <WorkflowNode
              v-for="node in nodes"
              :key="node.id"
              :node="node"
              :selected="selectedNode === node.id"
              :zoom-level="zoomLevel"
              @select="selectNode"
              @move="moveNode"
              @connect="startConnection"
              @configure="configureNode"
            />
          </div>
        </div>
      </div>

      <!-- 属性面板 -->
      <div class="property-panel">
        <div class="panel-header">
          <h3>属性配置</h3>
        </div>
        
        <div class="property-content">
          <div v-if="!selectedNode && !selectedConnection" class="empty-selection">
            <el-empty description="选择节点或连接线进行配置" />
          </div>
          
          <NodeProperties 
            v-if="selectedNode"
            :node="getSelectedNode()"
            @update="updateNodeProperties"
          />
          
          <ConnectionProperties 
            v-if="selectedConnection"
            :connection="getSelectedConnection()"
            @update="updateConnectionProperties"
          />
        </div>
      </div>
    </div>

    <!-- 工作流模板对话框 -->
    <el-dialog v-model="showTemplateDialog" title="选择工作流模板" width="800px">
      <WorkflowTemplates @select="loadTemplate" @close="showTemplateDialog = false" />
    </el-dialog>

    <!-- 验证结果对话框 -->
    <el-dialog v-model="showValidationDialog" title="验证结果" width="600px">
      <ValidationResults :results="validationResults" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Check, DocumentAdd, Upload, Pointer, Connection,
  ZoomIn, ZoomOut, Refresh
} from '@element-plus/icons-vue'
import WorkflowNode from '@/components/Workflow/WorkflowNode.vue'
import NodeProperties from '@/components/Workflow/NodeProperties.vue'
import ConnectionProperties from '@/components/Workflow/ConnectionProperties.vue'
import WorkflowTemplates from '@/components/Workflow/WorkflowTemplates.vue'
import ValidationResults from '@/components/Workflow/ValidationResults.vue'
import { useWorkflowDesigner } from '@/composables/useWorkflowDesigner'

// 响应式数据
const workflowName = ref('新工作流')
const saving = ref(false)
const deploying = ref(false)
const showTemplateDialog = ref(false)
const showValidationDialog = ref(false)
const activeCollapse = ref(['agents', 'control', 'tools'])
const canvasMode = ref('select')
const zoomLevel = ref(1)
const selectedNode = ref<string>('')
const selectedConnection = ref<string>('')
const validationResults = ref([])

const canvasContainer = ref<HTMLElement>()
const svgCanvas = ref<SVGElement>()

// 使用工作流设计器组合式函数
const {
  currentWorkflow,
  nodes,
  connections,
  tempConnection,
  addNode,
  removeNode,
  updateNode,
  addConnection,
  removeConnection,
  updateConnection,
  validateWorkflow: validate,
  saveWorkflow: save,
  loadWorkflow
} = useWorkflowDesigner()

// 节点类型定义
const agentNodes = [
  { type: 'router_agent', name: '路由智能体', icon: 'guide' },
  { type: 'planning_agent', name: '规划智能体', icon: 'list' },
  { type: 'customer_service_agent', name: '客服智能体', icon: 'service' },
  { type: 'knowledge_qa_agent', name: '知识问答', icon: 'question' },
  { type: 'text2sql_agent', name: '数据分析', icon: 'data-analysis' },
  { type: 'content_creation_agent', name: '内容创作', icon: 'edit' }
]

const controlNodes = [
  { type: 'start', name: '开始', icon: 'video-play' },
  { type: 'end', name: '结束', icon: 'video-pause' },
  { type: 'condition', name: '条件判断', icon: 'switch' },
  { type: 'parallel', name: '并行执行', icon: 'copy-document' },
  { type: 'loop', name: '循环', icon: 'refresh' }
]

const toolNodes = [
  { type: 'http_request', name: 'HTTP请求', icon: 'link' },
  { type: 'database_query', name: '数据库查询', icon: 'coin' },
  { type: 'file_operation', name: '文件操作', icon: 'folder' },
  { type: 'email_send', name: '发送邮件', icon: 'message' },
  { type: 'webhook', name: 'Webhook', icon: 'bell' }
]

// 方法
const handleDragStart = (event: DragEvent, nodeType: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(nodeType))
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  
  if (event.dataTransfer) {
    try {
      const nodeType = JSON.parse(event.dataTransfer.getData('application/json'))
      const rect = canvasContainer.value!.getBoundingClientRect()
      
      const x = (event.clientX - rect.left) / zoomLevel.value
      const y = (event.clientY - rect.top) / zoomLevel.value
      
      addNode({
        type: nodeType.type,
        name: nodeType.name,
        x,
        y,
        config: {}
      })
    } catch (error) {
      console.error('拖拽处理失败:', error)
    }
  }
}

const handleCanvasClick = (event: MouseEvent) => {
  if (event.target === canvasContainer.value || event.target === svgCanvas.value) {
    selectedNode.value = ''
    selectedConnection.value = ''
  }
}

const setCanvasMode = (mode: string) => {
  canvasMode.value = mode
}

const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value * 1.2, 3)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.2)
}

const resetZoom = () => {
  zoomLevel.value = 1
}

const selectNode = (nodeId: string) => {
  selectedNode.value = nodeId
  selectedConnection.value = ''
}

const selectConnection = (connectionId: string) => {
  selectedConnection.value = connectionId
  selectedNode.value = ''
}

const moveNode = (nodeId: string, x: number, y: number) => {
  updateNode(nodeId, { x, y })
}

const startConnection = (fromNodeId: string, fromPort: string) => {
  // 开始连接逻辑
  console.log('开始连接:', fromNodeId, fromPort)
}

const configureNode = (nodeId: string) => {
  selectNode(nodeId)
}

const getSelectedNode = () => {
  return nodes.value.find(node => node.id === selectedNode.value)
}

const getSelectedConnection = () => {
  return connections.value.find(conn => conn.id === selectedConnection.value)
}

const updateNodeProperties = (properties: any) => {
  if (selectedNode.value) {
    updateNode(selectedNode.value, properties)
  }
}

const updateConnectionProperties = (properties: any) => {
  if (selectedConnection.value) {
    updateConnection(selectedConnection.value, properties)
  }
}

const getConnectionPath = (connection: any) => {
  // 生成连接线的SVG路径
  const fromNode = nodes.value.find(n => n.id === connection.from)
  const toNode = nodes.value.find(n => n.id === connection.to)
  
  if (!fromNode || !toNode) return ''
  
  const x1 = fromNode.x + 100 // 节点宽度的一半
  const y1 = fromNode.y + 50  // 节点高度的一半
  const x2 = toNode.x + 100
  const y2 = toNode.y + 50
  
  // 贝塞尔曲线
  const cx1 = x1 + (x2 - x1) / 3
  const cy1 = y1
  const cx2 = x2 - (x2 - x1) / 3
  const cy2 = y2
  
  return `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`
}

const validateWorkflow = async () => {
  try {
    const results = await validate()
    validationResults.value = results
    showValidationDialog.value = true
  } catch (error) {
    ElMessage.error('验证失败')
  }
}

const saveWorkflow = async () => {
  saving.value = true
  try {
    await save({
      name: workflowName.value,
      nodes: nodes.value,
      connections: connections.value
    })
    ElMessage.success('工作流保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const deployWorkflow = async () => {
  deploying.value = true
  try {
    // 部署工作流逻辑
    ElMessage.success('工作流部署成功')
  } catch (error) {
    ElMessage.error('部署失败')
  } finally {
    deploying.value = false
  }
}

const loadTemplate = (template: any) => {
  loadWorkflow(template)
  workflowName.value = template.name
  showTemplateDialog.value = false
  ElMessage.success('模板加载成功')
}

const getStatusType = (status: string) => {
  const types = {
    draft: 'info',
    active: 'success',
    inactive: 'warning',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts = {
    draft: '草稿',
    active: '运行中',
    inactive: '已停用',
    error: '错误'
  }
  return texts[status] || '未知'
}

// 生命周期
onMounted(() => {
  // 初始化画布
  nextTick(() => {
    // 设置画布大小等初始化操作
  })
})
</script>

<style scoped>
.workflow-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.designer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.workflow-info {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.designer-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.tool-panel {
  width: 280px;
  background: white;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.tool-group {
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.tool-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.3s;
  background: white;
}

.tool-item:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.15);
}

.tool-item:active {
  cursor: grabbing;
}

.tool-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  color: #606266;
}

.tool-name {
  font-size: 12px;
  color: #303133;
  text-align: center;
  line-height: 1.2;
}

.design-canvas {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.canvas-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-level {
  font-size: 14px;
  color: #606266;
  min-width: 50px;
  text-align: center;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: default;
}

.canvas-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transform-origin: 0 0;
}

.connection-path {
  fill: none;
  stroke: #606266;
  stroke-width: 2;
  cursor: pointer;
}

.connection-path:hover,
.connection-path.selected {
  stroke: #409eff;
  stroke-width: 3;
}

.temp-connection {
  fill: none;
  stroke: #409eff;
  stroke-width: 2;
  stroke-dasharray: 5,5;
}

.canvas-nodes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.property-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
}

.property-content {
  padding: 16px;
}

.empty-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}
</style>
