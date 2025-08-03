<template>
  <div class="agent-management">
    <div class="page-header">
      <h1>智能体管理</h1>
      <p>管理和监控所有智能体的状态和性能</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon active">
                <el-icon><Robot /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.activeAgents }}</h3>
                <p>活跃智能体</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon conversations">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.totalConversations }}</h3>
                <p>总对话数</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon success">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.successRate }}%</h3>
                <p>成功率</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon response">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.avgResponseTime }}s</h3>
                <p>平均响应时间</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 智能体列表 -->
    <el-card class="agents-card">
      <template #header>
        <div class="card-header">
          <span>智能体列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="refreshAgents">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="success" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              添加智能体
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="agents" v-loading="loading" stripe>
        <el-table-column prop="name" label="智能体名称" min-width="150">
          <template #default="{ row }">
            <div class="agent-name">
              <el-avatar :size="32" class="agent-avatar">
                <el-icon>{{ getAgentIcon(row.type) }}</el-icon>
              </el-avatar>
              <div>
                <div class="name">{{ row.name }}</div>
                <div class="type">{{ row.type }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="model" label="模型" width="120" />
        
        <el-table-column label="性能指标" width="200">
          <template #default="{ row }">
            <div class="performance-metrics">
              <div class="metric">
                <span class="label">对话数:</span>
                <span class="value">{{ row.metrics?.conversations || 0 }}</span>
              </div>
              <div class="metric">
                <span class="label">成功率:</span>
                <span class="value">{{ row.metrics?.successRate || 0 }}%</span>
              </div>
              <div class="metric">
                <span class="label">响应时间:</span>
                <span class="value">{{ row.metrics?.avgResponseTime || 0 }}ms</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewAgentDetails(row)"
            >
              详情
            </el-button>
            <el-button 
              size="small" 
              :type="row.status === 'active' ? 'warning' : 'success'"
              @click="toggleAgentStatus(row)"
            >
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="configureAgent(row)"
            >
              配置
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 智能体详情对话框 -->
    <el-dialog 
      v-model="showDetailsDialog" 
      title="智能体详情" 
      width="800px"
      destroy-on-close
    >
      <AgentDetails 
        v-if="selectedAgent" 
        :agent="selectedAgent" 
        @refresh="refreshAgentDetails"
      />
    </el-dialog>

    <!-- 智能体配置对话框 -->
    <el-dialog 
      v-model="showConfigDialog" 
      title="智能体配置" 
      width="600px"
      destroy-on-close
    >
      <AgentConfig 
        v-if="selectedAgent" 
        :agent="selectedAgent" 
        @save="handleConfigSave"
        @cancel="showConfigDialog = false"
      />
    </el-dialog>

    <!-- 创建智能体对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="创建智能体" 
      width="600px"
      destroy-on-close
    >
      <CreateAgent 
        @create="handleAgentCreate"
        @cancel="showCreateDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Robot, ChatDotRound, SuccessFilled, Timer, Refresh, Plus 
} from '@element-plus/icons-vue'
import AgentDetails from '@/components/Agent/AgentDetails.vue'
import AgentConfig from '@/components/Agent/AgentConfig.vue'
import CreateAgent from '@/components/Agent/CreateAgent.vue'
import { agentApi } from '@/api/agent'

// 接口定义
interface Agent {
  id: string
  name: string
  type: string
  description: string
  status: 'active' | 'inactive' | 'error'
  model: string
  capabilities: string[]
  metrics?: {
    conversations: number
    successRate: number
    avgResponseTime: number
  }
  config?: any
}

interface Stats {
  activeAgents: number
  totalConversations: number
  successRate: number
  avgResponseTime: number
}

// 响应式数据
const loading = ref(false)
const agents = ref<Agent[]>([])
const selectedAgent = ref<Agent | null>(null)
const showDetailsDialog = ref(false)
const showConfigDialog = ref(false)
const showCreateDialog = ref(false)

const stats = reactive<Stats>({
  activeAgents: 0,
  totalConversations: 0,
  successRate: 0,
  avgResponseTime: 0
})

// 方法
const refreshAgents = async () => {
  loading.value = true
  try {
    const response = await agentApi.getList()
    agents.value = response.data.map(agent => ({
      ...agent,
      metrics: {
        conversations: Math.floor(Math.random() * 1000),
        successRate: Math.floor(Math.random() * 100),
        avgResponseTime: Math.floor(Math.random() * 2000)
      }
    }))
    
    // 更新统计数据
    updateStats()
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.activeAgents = agents.value.filter(a => a.status === 'active').length
  stats.totalConversations = agents.value.reduce((sum, a) => sum + (a.metrics?.conversations || 0), 0)
  
  const successRates = agents.value.map(a => a.metrics?.successRate || 0)
  stats.successRate = successRates.length > 0 
    ? Math.round(successRates.reduce((sum, rate) => sum + rate, 0) / successRates.length)
    : 0
  
  const responseTimes = agents.value.map(a => a.metrics?.avgResponseTime || 0)
  stats.avgResponseTime = responseTimes.length > 0
    ? Math.round(responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length / 1000)
    : 0
}

const viewAgentDetails = (agent: Agent) => {
  selectedAgent.value = agent
  showDetailsDialog.value = true
}

const configureAgent = (agent: Agent) => {
  selectedAgent.value = agent
  showConfigDialog.value = true
}

const toggleAgentStatus = async (agent: Agent) => {
  try {
    const action = agent.status === 'active' ? '停用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}智能体 "${agent.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里应该调用API更新状态
    agent.status = agent.status === 'active' ? 'inactive' : 'active'
    ElMessage.success(`智能体已${action}`)
    updateStats()
  } catch (error) {
    // 用户取消操作
  }
}

const refreshAgentDetails = () => {
  // 刷新选中智能体的详情
  if (selectedAgent.value) {
    const agent = agents.value.find(a => a.id === selectedAgent.value!.id)
    if (agent) {
      selectedAgent.value = { ...agent }
    }
  }
}

const handleConfigSave = (config: any) => {
  if (selectedAgent.value) {
    selectedAgent.value.config = config
    ElMessage.success('配置已保存')
    showConfigDialog.value = false
  }
}

const handleAgentCreate = (agentData: any) => {
  // 这里应该调用API创建智能体
  const newAgent: Agent = {
    id: `agent_${Date.now()}`,
    ...agentData,
    status: 'inactive',
    metrics: {
      conversations: 0,
      successRate: 0,
      avgResponseTime: 0
    }
  }
  
  agents.value.push(newAgent)
  ElMessage.success('智能体创建成功')
  showCreateDialog.value = false
  updateStats()
}

const getAgentIcon = (type: string) => {
  const icons = {
    customer_service: 'service',
    knowledge_qa: 'question',
    text2sql: 'data-analysis',
    content_creation: 'edit',
    router: 'guide',
    planning: 'list',
    tool_calling: 'tools',
    summarizing: 'document'
  }
  return icons[type] || 'robot'
}

const getStatusType = (status: string) => {
  const types = {
    active: 'success',
    inactive: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts = {
    active: '运行中',
    inactive: '已停用',
    error: '错误'
  }
  return texts[status] || '未知'
}

// 生命周期
onMounted(() => {
  refreshAgents()
})
</script>

<style scoped>
.agent-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stat-icon.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.conversations {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.success {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.response {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info h3 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-info p {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.agents-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-avatar {
  background: #f0f2f5;
  color: #606266;
}

.name {
  font-weight: 500;
  color: #303133;
}

.type {
  font-size: 12px;
  color: #909399;
}

.performance-metrics {
  font-size: 12px;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2px;
}

.metric .label {
  color: #909399;
}

.metric .value {
  color: #303133;
  font-weight: 500;
}
</style>
