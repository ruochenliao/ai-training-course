<template>
  <div 
    class="workflow-node"
    :class="{ 
      selected, 
      dragging,
      [`node-${node.type}`]: true 
    }"
    :style="nodeStyle"
    @mousedown="handleMouseDown"
    @click="handleClick"
  >
    <!-- 节点头部 -->
    <div class="node-header">
      <div class="node-icon">
        <el-icon>{{ getNodeIcon(node.type) }}</el-icon>
      </div>
      <div class="node-title">
        <span class="node-name">{{ node.name }}</span>
        <span class="node-type">{{ getNodeTypeName(node.type) }}</span>
      </div>
      <div class="node-actions">
        <el-dropdown @command="handleAction" trigger="click" @click.stop>
          <el-button size="small" text>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="configure">
                <el-icon><Setting /></el-icon>
                配置
              </el-dropdown-item>
              <el-dropdown-item command="duplicate">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 节点内容 -->
    <div class="node-content">
      <div v-if="node.config.description" class="node-description">
        {{ node.config.description }}
      </div>
      
      <!-- 根据节点类型显示不同内容 -->
      <div class="node-details">
        <template v-if="node.type === 'http_request'">
          <div class="config-item">
            <span class="label">URL:</span>
            <span class="value">{{ node.config.url || '未配置' }}</span>
          </div>
          <div class="config-item">
            <span class="label">方法:</span>
            <span class="value">{{ node.config.method || 'GET' }}</span>
          </div>
        </template>
        
        <template v-else-if="node.type === 'condition'">
          <div class="config-item">
            <span class="label">条件:</span>
            <span class="value">{{ node.config.condition || '未配置' }}</span>
          </div>
        </template>
        
        <template v-else-if="node.type === 'database_query'">
          <div class="config-item">
            <span class="label">数据库:</span>
            <span class="value">{{ node.config.database || '未配置' }}</span>
          </div>
        </template>
        
        <template v-else-if="isAgentNode(node.type)">
          <div class="config-item">
            <span class="label">模型:</span>
            <span class="value">{{ node.config.model || 'gpt-4' }}</span>
          </div>
          <div class="config-item">
            <span class="label">温度:</span>
            <span class="value">{{ node.config.temperature || 0.7 }}</span>
          </div>
        </template>
      </div>
    </div>

    <!-- 输入端口 -->
    <div class="input-ports">
      <div 
        v-for="input in node.inputs" 
        :key="input.name"
        class="port input-port"
        :class="{ required: input.required }"
        @mousedown.stop="handlePortMouseDown('input', input.name)"
      >
        <div class="port-dot"></div>
        <span class="port-label">{{ input.name }}</span>
      </div>
    </div>

    <!-- 输出端口 -->
    <div class="output-ports">
      <div 
        v-for="output in node.outputs" 
        :key="output.name"
        class="port output-port"
        @mousedown.stop="handlePortMouseDown('output', output.name)"
      >
        <span class="port-label">{{ output.name }}</span>
        <div class="port-dot"></div>
      </div>
    </div>

    <!-- 状态指示器 -->
    <div v-if="node.status" class="node-status" :class="`status-${node.status}`">
      <el-icon v-if="node.status === 'running'"><Loading /></el-icon>
      <el-icon v-else-if="node.status === 'success'"><Check /></el-icon>
      <el-icon v-else-if="node.status === 'error'"><Close /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  MoreFilled, Setting, CopyDocument, Delete, Loading, Check, Close 
} from '@element-plus/icons-vue'
import type { WorkflowNode } from '@/composables/useWorkflowDesigner'

// Props
interface Props {
  node: WorkflowNode
  selected: boolean
  zoomLevel: number
}

const props = defineProps<Props>()
const emit = defineEmits(['select', 'move', 'connect', 'configure', 'duplicate', 'delete'])

// 响应式数据
const dragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const nodeStart = ref({ x: 0, y: 0 })

// 计算属性
const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  width: `${props.node.width || 200}px`,
  minHeight: `${props.node.height || 100}px`,
  transform: `scale(${props.zoomLevel})`,
  transformOrigin: 'top left',
  pointerEvents: 'auto'
}))

// 方法
const handleClick = (event: MouseEvent) => {
  event.stopPropagation()
  emit('select', props.node.id)
}

const handleMouseDown = (event: MouseEvent) => {
  if (event.button !== 0) return // 只处理左键

  dragging.value = true
  dragStart.value = { x: event.clientX, y: event.clientY }
  nodeStart.value = { x: props.node.x, y: props.node.y }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  
  event.preventDefault()
}

const handleMouseMove = (event: MouseEvent) => {
  if (!dragging.value) return

  const deltaX = (event.clientX - dragStart.value.x) / props.zoomLevel
  const deltaY = (event.clientY - dragStart.value.y) / props.zoomLevel

  const newX = Math.max(0, nodeStart.value.x + deltaX)
  const newY = Math.max(0, nodeStart.value.y + deltaY)

  emit('move', props.node.id, newX, newY)
}

const handleMouseUp = () => {
  dragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

const handlePortMouseDown = (portType: 'input' | 'output', portName: string) => {
  if (portType === 'output') {
    emit('connect', props.node.id, portName)
  }
}

const handleAction = (command: string) => {
  switch (command) {
    case 'configure':
      emit('configure', props.node.id)
      break
    case 'duplicate':
      emit('duplicate', props.node.id)
      break
    case 'delete':
      emit('delete', props.node.id)
      break
  }
}

const getNodeIcon = (nodeType: string) => {
  const icons = {
    start: 'video-play',
    end: 'video-pause',
    condition: 'switch',
    parallel: 'copy-document',
    loop: 'refresh',
    http_request: 'link',
    database_query: 'coin',
    file_operation: 'folder',
    email_send: 'message',
    webhook: 'bell',
    router_agent: 'guide',
    planning_agent: 'list',
    customer_service_agent: 'service',
    knowledge_qa_agent: 'question',
    text2sql_agent: 'data-analysis',
    content_creation_agent: 'edit'
  }
  return icons[nodeType] || 'box'
}

const getNodeTypeName = (nodeType: string) => {
  const names = {
    start: '开始',
    end: '结束',
    condition: '条件判断',
    parallel: '并行执行',
    loop: '循环',
    http_request: 'HTTP请求',
    database_query: '数据库查询',
    file_operation: '文件操作',
    email_send: '发送邮件',
    webhook: 'Webhook',
    router_agent: '路由智能体',
    planning_agent: '规划智能体',
    customer_service_agent: '客服智能体',
    knowledge_qa_agent: '知识问答',
    text2sql_agent: '数据分析',
    content_creation_agent: '内容创作'
  }
  return names[nodeType] || nodeType
}

const isAgentNode = (nodeType: string) => {
  return nodeType.endsWith('_agent')
}

// 生命周期
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
.workflow-node {
  position: absolute;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  transition: all 0.2s ease;
  user-select: none;
}

.workflow-node:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.workflow-node.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.workflow-node.dragging {
  z-index: 1000;
  transform: rotate(2deg);
}

/* 节点类型样式 */
.node-start .node-header {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
}

.node-end .node-header {
  background: linear-gradient(135deg, #f56c6c, #f78989);
  color: white;
}

.node-condition .node-header {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
  color: white;
}

.node-http_request .node-header {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: white;
}

.node-database_query .node-header {
  background: linear-gradient(135deg, #909399, #a6a9ad);
  color: white;
}

.workflow-node[class*="agent"] .node-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px 6px 0 0;
  border-bottom: 1px solid #e4e7ed;
}

.node-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  font-size: 16px;
}

.node-title {
  flex: 1;
  min-width: 0;
}

.node-name {
  display: block;
  font-weight: 500;
  font-size: 14px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-type {
  display: block;
  font-size: 12px;
  opacity: 0.8;
  line-height: 1.2;
}

.node-actions {
  margin-left: 8px;
}

.node-content {
  padding: 12px;
}

.node-description {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
}

.node-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.config-item .label {
  color: #909399;
  margin-right: 8px;
}

.config-item .value {
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100px;
}

.input-ports,
.output-ports {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-ports {
  left: -8px;
}

.output-ports {
  right: -8px;
}

.port {
  display: flex;
  align-items: center;
  font-size: 10px;
  color: #606266;
  cursor: pointer;
}

.input-port {
  flex-direction: row;
}

.output-port {
  flex-direction: row-reverse;
}

.port-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e4e7ed;
  border: 2px solid white;
  transition: all 0.2s;
}

.port:hover .port-dot {
  background: #409eff;
  transform: scale(1.2);
}

.port.required .port-dot {
  background: #f56c6c;
}

.port-label {
  margin: 0 6px;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 4px;
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.port:hover .port-label {
  opacity: 1;
}

.node-status {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
}

.status-running {
  background: #409eff;
  animation: pulse 1.5s infinite;
}

.status-success {
  background: #67c23a;
}

.status-error {
  background: #f56c6c;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
</style>
