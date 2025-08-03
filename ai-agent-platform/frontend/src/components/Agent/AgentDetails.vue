<template>
  <div class="agent-details">
    <!-- 基本信息 -->
    <el-card class="info-card" shadow="never">
      <template #header>
        <span>基本信息</span>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="智能体名称">
          {{ agent.name }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag>{{ agent.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(agent.status)">
            {{ getStatusText(agent.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模型">
          {{ agent.model }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ agent.description }}
        </el-descriptions-item>
        <el-descriptions-item label="能力" :span="2">
          <el-tag 
            v-for="capability in agent.capabilities" 
            :key="capability"
            size="small"
            style="margin-right: 8px;"
          >
            {{ capability }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 性能指标 -->
    <el-card class="metrics-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>性能指标</span>
          <el-button size="small" @click="refreshMetrics">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-value">{{ metrics.totalConversations }}</div>
            <div class="metric-label">总对话数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-value">{{ metrics.successRate }}%</div>
            <div class="metric-label">成功率</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-value">{{ metrics.avgResponseTime }}ms</div>
            <div class="metric-label">平均响应时间</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-value">{{ metrics.errorRate }}%</div>
            <div class="metric-label">错误率</div>
          </div>
        </el-col>
      </el-row>

      <!-- 性能图表 -->
      <div class="charts-container">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-wrapper">
              <h4>对话趋势</h4>
              <div ref="conversationChart" class="chart"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-wrapper">
              <h4>响应时间趋势</h4>
              <div ref="responseTimeChart" class="chart"></div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 最近对话 -->
    <el-card class="conversations-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>最近对话</span>
          <el-button size="small" @click="viewAllConversations">
            查看全部
          </el-button>
        </div>
      </template>

      <el-table :data="recentConversations" stripe>
        <el-table-column prop="id" label="对话ID" width="120" />
        <el-table-column prop="user" label="用户" width="100" />
        <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="response" label="回复" min-width="200" show-overflow-tooltip />
        <el-table-column prop="responseTime" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.responseTime }}ms
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 配置信息 -->
    <el-card class="config-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>配置信息</span>
          <el-button size="small" type="primary" @click="editConfig">
            编辑配置
          </el-button>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="温度参数">
          {{ agent.config?.temperature || 0.7 }}
        </el-descriptions-item>
        <el-descriptions-item label="最大Token数">
          {{ agent.config?.maxTokens || 2000 }}
        </el-descriptions-item>
        <el-descriptions-item label="系统提示词">
          <div class="system-prompt">
            {{ agent.config?.systemPrompt || '暂无配置' }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="其他配置">
          <pre class="config-json">{{ JSON.stringify(agent.config || {}, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

// Props
interface Props {
  agent: {
    id: string
    name: string
    type: string
    description: string
    status: string
    model: string
    capabilities: string[]
    config?: any
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['refresh', 'edit-config'])

// 响应式数据
const conversationChart = ref<HTMLElement>()
const responseTimeChart = ref<HTMLElement>()

const metrics = reactive({
  totalConversations: 1250,
  successRate: 95.8,
  avgResponseTime: 850,
  errorRate: 4.2
})

const recentConversations = ref([
  {
    id: 'conv_001',
    user: 'user123',
    message: '你好，我想了解产品信息',
    response: '您好！很高兴为您介绍我们的产品...',
    responseTime: 650,
    status: 'success',
    timestamp: new Date(Date.now() - 1000 * 60 * 5)
  },
  {
    id: 'conv_002',
    user: 'user456',
    message: '如何使用这个功能？',
    response: '这个功能的使用方法如下...',
    responseTime: 920,
    status: 'success',
    timestamp: new Date(Date.now() - 1000 * 60 * 15)
  },
  {
    id: 'conv_003',
    user: 'user789',
    message: '系统出现错误了',
    response: '抱歉，系统遇到了问题...',
    responseTime: 1200,
    status: 'error',
    timestamp: new Date(Date.now() - 1000 * 60 * 30)
  }
])

// 方法
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

const refreshMetrics = async () => {
  try {
    // 这里应该调用API获取最新指标
    ElMessage.success('指标已刷新')
    emit('refresh')
  } catch (error) {
    ElMessage.error('刷新指标失败')
  }
}

const viewAllConversations = () => {
  // 跳转到对话列表页面
  ElMessage.info('跳转到对话列表页面')
}

const editConfig = () => {
  emit('edit-config')
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleString('zh-CN')
}

const initCharts = () => {
  // 这里应该使用图表库（如ECharts）初始化图表
  // 暂时用占位符
  if (conversationChart.value) {
    conversationChart.value.innerHTML = '<div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #909399;">对话趋势图表</div>'
  }
  
  if (responseTimeChart.value) {
    responseTimeChart.value.innerHTML = '<div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #909399;">响应时间图表</div>'
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initCharts()
  })
})
</script>

<style scoped>
.agent-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.charts-container {
  margin-top: 20px;
}

.chart-wrapper {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.chart-wrapper h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.chart {
  height: 200px;
  background: white;
  border-radius: 4px;
}

.system-prompt {
  max-height: 100px;
  overflow-y: auto;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
}

.config-json {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}
</style>
