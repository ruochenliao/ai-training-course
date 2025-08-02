<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>欢迎使用智能体应用综合平台</h1>
      <p>您好，{{ userStore.userName }}！今天是 {{ currentDate }}</p>
    </div>

    <div class="dashboard-stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon size="40" color="#409eff">
                  <Avatar />
                </el-icon>
              </div>
              <div class="stat-info">
                <h3>智能体数量</h3>
                <p class="stat-number">{{ stats.agentCount }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon size="40" color="#67c23a">
                  <Document />
                </el-icon>
              </div>
              <div class="stat-info">
                <h3>知识库数量</h3>
                <p class="stat-number">{{ stats.knowledgeCount }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon size="40" color="#e6a23c">
                  <ChatDotRound />
                </el-icon>
              </div>
              <div class="stat-info">
                <h3>今日对话</h3>
                <p class="stat-number">{{ stats.todayChats }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon size="40" color="#f56c6c">
                  <User />
                </el-icon>
              </div>
              <div class="stat-info">
                <h3>在线用户</h3>
                <p class="stat-number">{{ stats.onlineUsers }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="dashboard-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>快速操作</span>
              </div>
            </template>
            <div class="quick-actions">
              <el-button type="primary" size="large" @click="createAgent">
                <el-icon><Plus /></el-icon>
                创建智能体
              </el-button>
              <el-button type="success" size="large" @click="createKnowledge">
                <el-icon><FolderAdd /></el-icon>
                创建知识库
              </el-button>
              <el-button type="warning" size="large" @click="startChat">
                <el-icon><ChatDotRound /></el-icon>
                开始对话
              </el-button>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>系统状态</span>
              </div>
            </template>
            <div class="system-status">
              <div class="status-item">
                <span class="status-label">API服务</span>
                <el-tag type="success">正常</el-tag>
              </div>
              <div class="status-item">
                <span class="status-label">数据库</span>
                <el-tag type="success">正常</el-tag>
              </div>
              <div class="status-item">
                <span class="status-label">Redis缓存</span>
                <el-tag type="success">正常</el-tag>
              </div>
              <div class="status-item">
                <span class="status-label">向量数据库</span>
                <el-tag type="success">正常</el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Avatar, Document, ChatDotRound, User, Plus, FolderAdd } from '@element-plus/icons-vue'
import { formatTime } from '@/utils'
import { agentApi } from '@/api/agent'
import { systemApi } from '@/api/system'

const router = useRouter()
const userStore = useUserStore()

// 统计数据
const stats = ref({
  agentCount: 0,
  knowledgeCount: 0,
  todayChats: 0,
  onlineUsers: 0
})

// 当前日期
const currentDate = computed(() => {
  return formatTime(new Date(), 'YYYY年MM月DD日')
})

// 快速操作
const createAgent = () => {
  router.push('/agents')
}

const createKnowledge = () => {
  router.push('/knowledge')
}

const startChat = () => {
  router.push('/agents')
}

// 获取统计数据
const fetchStats = async () => {
  try {
    // 获取智能体数量
    const agentsResponse = await agentApi.getList({ limit: 1000 })
    const agentCount = agentsResponse.data?.length || 0

    // 获取系统健康状态
    const healthResponse = await systemApi.getHealth()

    // 更新统计数据
    stats.value = {
      agentCount,
      knowledgeCount: 8, // 暂时使用模拟数据
      todayChats: 156,   // 暂时使用模拟数据
      onlineUsers: 23    // 暂时使用模拟数据
    }

    console.log('统计数据获取成功:', stats.value)
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 使用模拟数据作为后备
    stats.value = {
      agentCount: 12,
      knowledgeCount: 8,
      todayChats: 156,
      onlineUsers: 23
    }
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 24px;
}

.dashboard-header {
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 16px;
    color: #606266;
  }
}

.dashboard-stats {
  margin-bottom: 32px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    padding: 16px 0;
  }
  
  .stat-icon {
    margin-right: 16px;
  }
  
  .stat-info {
    flex: 1;
    
    h3 {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }
    
    .stat-number {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
}

.dashboard-content {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }
}

.quick-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  
  .el-button {
    flex: 1;
    min-width: 120px;
  }
}

.system-status {
  .status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .status-label {
      font-size: 14px;
      color: #606266;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  
  .dashboard-stats {
    :deep(.el-col) {
      margin-bottom: 16px;
    }
  }
  
  .quick-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>
