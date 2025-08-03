/**
 * 工作流设计器组合式函数
 */

import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { workflowApi } from '@/api/workflow'

export interface WorkflowNode {
  id: string
  type: string
  name: string
  x: number
  y: number
  width?: number
  height?: number
  config: Record<string, any>
  inputs?: Array<{
    name: string
    type: string
    required: boolean
  }>
  outputs?: Array<{
    name: string
    type: string
  }>
}

export interface WorkflowConnection {
  id: string
  from: string
  to: string
  fromPort?: string
  toPort?: string
  condition?: string
  config?: Record<string, any>
}

export interface Workflow {
  id?: string
  name: string
  description?: string
  status: 'draft' | 'active' | 'inactive' | 'error'
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
  config?: Record<string, any>
  createdAt?: string
  updatedAt?: string
}

export function useWorkflowDesigner() {
  // 响应式数据
  const currentWorkflow = ref<Workflow>({
    name: '新工作流',
    status: 'draft',
    nodes: [],
    connections: []
  })

  const nodes = ref<WorkflowNode[]>([])
  const connections = ref<WorkflowConnection[]>([])
  const selectedNodes = ref<string[]>([])
  const selectedConnections = ref<string[]>([])
  const clipboard = ref<any>(null)
  const history = ref<any[]>([])
  const historyIndex = ref(-1)

  // 临时连接状态
  const tempConnection = ref<{
    from: string
    fromPort: string
    path: string
  } | null>(null)

  // 计算属性
  const hasUnsavedChanges = computed(() => {
    return history.value.length > 0 && historyIndex.value !== -1
  })

  const canUndo = computed(() => {
    return historyIndex.value > 0
  })

  const canRedo = computed(() => {
    return historyIndex.value < history.value.length - 1
  })

  // 节点操作
  const addNode = (nodeData: Partial<WorkflowNode>) => {
    const node: WorkflowNode = {
      id: generateId(),
      type: nodeData.type || 'unknown',
      name: nodeData.name || '新节点',
      x: nodeData.x || 100,
      y: nodeData.y || 100,
      width: nodeData.width || 200,
      height: nodeData.height || 100,
      config: nodeData.config || {},
      inputs: getNodeInputs(nodeData.type || 'unknown'),
      outputs: getNodeOutputs(nodeData.type || 'unknown')
    }

    nodes.value.push(node)
    saveToHistory('添加节点')
    
    return node
  }

  const removeNode = (nodeId: string) => {
    const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
    if (nodeIndex > -1) {
      nodes.value.splice(nodeIndex, 1)
      
      // 删除相关连接
      connections.value = connections.value.filter(
        conn => conn.from !== nodeId && conn.to !== nodeId
      )
      
      saveToHistory('删除节点')
    }
  }

  const updateNode = (nodeId: string, updates: Partial<WorkflowNode>) => {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      Object.assign(node, updates)
      saveToHistory('更新节点')
    }
  }

  const duplicateNode = (nodeId: string) => {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      const newNode = {
        ...node,
        id: generateId(),
        name: `${node.name} 副本`,
        x: node.x + 20,
        y: node.y + 20
      }
      nodes.value.push(newNode)
      saveToHistory('复制节点')
      return newNode
    }
  }

  // 连接操作
  const addConnection = (connectionData: Partial<WorkflowConnection>) => {
    // 验证连接是否有效
    if (!isValidConnection(connectionData.from!, connectionData.to!)) {
      ElMessage.error('无效的连接')
      return null
    }

    const connection: WorkflowConnection = {
      id: generateId(),
      from: connectionData.from!,
      to: connectionData.to!,
      fromPort: connectionData.fromPort || 'output',
      toPort: connectionData.toPort || 'input',
      condition: connectionData.condition,
      config: connectionData.config || {}
    }

    connections.value.push(connection)
    saveToHistory('添加连接')
    
    return connection
  }

  const removeConnection = (connectionId: string) => {
    const connectionIndex = connections.value.findIndex(c => c.id === connectionId)
    if (connectionIndex > -1) {
      connections.value.splice(connectionIndex, 1)
      saveToHistory('删除连接')
    }
  }

  const updateConnection = (connectionId: string, updates: Partial<WorkflowConnection>) => {
    const connection = connections.value.find(c => c.id === connectionId)
    if (connection) {
      Object.assign(connection, updates)
      saveToHistory('更新连接')
    }
  }

  // 验证工作流
  const validateWorkflow = async () => {
    const results = []

    // 检查是否有开始节点
    const startNodes = nodes.value.filter(n => n.type === 'start')
    if (startNodes.length === 0) {
      results.push({
        type: 'error',
        message: '工作流必须包含至少一个开始节点'
      })
    } else if (startNodes.length > 1) {
      results.push({
        type: 'warning',
        message: '工作流包含多个开始节点'
      })
    }

    // 检查是否有结束节点
    const endNodes = nodes.value.filter(n => n.type === 'end')
    if (endNodes.length === 0) {
      results.push({
        type: 'warning',
        message: '建议添加结束节点'
      })
    }

    // 检查孤立节点
    const orphanNodes = nodes.value.filter(node => {
      const hasIncoming = connections.value.some(conn => conn.to === node.id)
      const hasOutgoing = connections.value.some(conn => conn.from === node.id)
      return !hasIncoming && !hasOutgoing && node.type !== 'start'
    })

    if (orphanNodes.length > 0) {
      results.push({
        type: 'warning',
        message: `发现 ${orphanNodes.length} 个孤立节点`
      })
    }

    // 检查循环依赖
    if (hasCircularDependency()) {
      results.push({
        type: 'error',
        message: '工作流存在循环依赖'
      })
    }

    // 检查节点配置
    for (const node of nodes.value) {
      const nodeValidation = validateNodeConfig(node)
      results.push(...nodeValidation)
    }

    return results
  }

  // 保存工作流
  const saveWorkflow = async (workflowData?: Partial<Workflow>) => {
    try {
      const workflow: Workflow = {
        ...currentWorkflow.value,
        ...workflowData,
        nodes: nodes.value,
        connections: connections.value
      }

      let result
      if (workflow.id) {
        result = await workflowApi.update(workflow.id, workflow)
      } else {
        result = await workflowApi.create(workflow)
      }

      currentWorkflow.value = result.data
      clearHistory()
      
      return result.data
    } catch (error) {
      console.error('保存工作流失败:', error)
      throw error
    }
  }

  // 加载工作流
  const loadWorkflow = (workflow: Workflow) => {
    currentWorkflow.value = workflow
    nodes.value = [...workflow.nodes]
    connections.value = [...workflow.connections]
    clearHistory()
  }

  // 导出工作流
  const exportWorkflow = () => {
    const workflow = {
      ...currentWorkflow.value,
      nodes: nodes.value,
      connections: connections.value
    }
    
    const dataStr = JSON.stringify(workflow, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `${workflow.name}.json`
    link.click()
  }

  // 导入工作流
  const importWorkflow = (file: File) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const workflow = JSON.parse(e.target?.result as string)
          loadWorkflow(workflow)
          resolve(workflow)
        } catch (error) {
          reject(new Error('无效的工作流文件'))
        }
      }
      reader.readAsText(file)
    })
  }

  // 历史记录管理
  const saveToHistory = (action: string) => {
    const state = {
      action,
      nodes: JSON.parse(JSON.stringify(nodes.value)),
      connections: JSON.parse(JSON.stringify(connections.value)),
      timestamp: Date.now()
    }

    // 如果当前不在历史记录的末尾，删除后面的记录
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }

    history.value.push(state)
    historyIndex.value = history.value.length - 1

    // 限制历史记录数量
    if (history.value.length > 50) {
      history.value.shift()
      historyIndex.value--
    }
  }

  const undo = () => {
    if (canUndo.value) {
      historyIndex.value--
      const state = history.value[historyIndex.value]
      nodes.value = JSON.parse(JSON.stringify(state.nodes))
      connections.value = JSON.parse(JSON.stringify(state.connections))
    }
  }

  const redo = () => {
    if (canRedo.value) {
      historyIndex.value++
      const state = history.value[historyIndex.value]
      nodes.value = JSON.parse(JSON.stringify(state.nodes))
      connections.value = JSON.parse(JSON.stringify(state.connections))
    }
  }

  const clearHistory = () => {
    history.value = []
    historyIndex.value = -1
  }

  // 辅助函数
  const generateId = () => {
    return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const isValidConnection = (fromNodeId: string, toNodeId: string) => {
    // 不能连接到自己
    if (fromNodeId === toNodeId) return false

    // 检查是否已存在连接
    const existingConnection = connections.value.find(
      conn => conn.from === fromNodeId && conn.to === toNodeId
    )
    if (existingConnection) return false

    // 检查是否会形成循环
    return !wouldCreateCycle(fromNodeId, toNodeId)
  }

  const wouldCreateCycle = (fromNodeId: string, toNodeId: string) => {
    const visited = new Set<string>()
    const stack = [toNodeId]

    while (stack.length > 0) {
      const currentNode = stack.pop()!
      if (currentNode === fromNodeId) return true
      if (visited.has(currentNode)) continue

      visited.add(currentNode)
      
      const outgoingConnections = connections.value.filter(conn => conn.from === currentNode)
      for (const conn of outgoingConnections) {
        stack.push(conn.to)
      }
    }

    return false
  }

  const hasCircularDependency = () => {
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    const dfs = (nodeId: string): boolean => {
      visited.add(nodeId)
      recursionStack.add(nodeId)

      const outgoingConnections = connections.value.filter(conn => conn.from === nodeId)
      for (const conn of outgoingConnections) {
        if (!visited.has(conn.to)) {
          if (dfs(conn.to)) return true
        } else if (recursionStack.has(conn.to)) {
          return true
        }
      }

      recursionStack.delete(nodeId)
      return false
    }

    for (const node of nodes.value) {
      if (!visited.has(node.id)) {
        if (dfs(node.id)) return true
      }
    }

    return false
  }

  const validateNodeConfig = (node: WorkflowNode) => {
    const results = []

    // 根据节点类型验证配置
    switch (node.type) {
      case 'http_request':
        if (!node.config.url) {
          results.push({
            type: 'error',
            message: `节点 "${node.name}" 缺少URL配置`
          })
        }
        break
      case 'condition':
        if (!node.config.condition) {
          results.push({
            type: 'error',
            message: `节点 "${node.name}" 缺少条件配置`
          })
        }
        break
      // 添加更多节点类型的验证
    }

    return results
  }

  const getNodeInputs = (nodeType: string) => {
    const inputConfigs = {
      start: [],
      end: [{ name: 'input', type: 'any', required: false }],
      condition: [{ name: 'input', type: 'any', required: true }],
      http_request: [{ name: 'input', type: 'any', required: false }],
      // 添加更多节点类型的输入配置
    }
    return inputConfigs[nodeType] || [{ name: 'input', type: 'any', required: false }]
  }

  const getNodeOutputs = (nodeType: string) => {
    const outputConfigs = {
      start: [{ name: 'output', type: 'any' }],
      end: [],
      condition: [
        { name: 'true', type: 'any' },
        { name: 'false', type: 'any' }
      ],
      http_request: [
        { name: 'success', type: 'any' },
        { name: 'error', type: 'any' }
      ],
      // 添加更多节点类型的输出配置
    }
    return outputConfigs[nodeType] || [{ name: 'output', type: 'any' }]
  }

  return {
    // 状态
    currentWorkflow,
    nodes,
    connections,
    selectedNodes,
    selectedConnections,
    tempConnection,
    hasUnsavedChanges,
    canUndo,
    canRedo,

    // 节点操作
    addNode,
    removeNode,
    updateNode,
    duplicateNode,

    // 连接操作
    addConnection,
    removeConnection,
    updateConnection,

    // 工作流操作
    validateWorkflow,
    saveWorkflow,
    loadWorkflow,
    exportWorkflow,
    importWorkflow,

    // 历史记录
    undo,
    redo,
    clearHistory,

    // 辅助函数
    isValidConnection
  }
}
