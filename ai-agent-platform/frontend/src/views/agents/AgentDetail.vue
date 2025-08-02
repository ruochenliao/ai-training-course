<template>
  <div class="agent-detail">
    <div class="page-header">
      <el-button @click="goBack" type="text">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="agent" class="agent-content">
      <div class="agent-header">
        <div class="agent-avatar">
          <el-avatar :size="80" :src="agent.avatar_url">
            <el-icon size="40"><Robot /></el-icon>
          </el-avatar>
        </div>
        <div class="agent-info">
          <h1>{{ agent.name }}</h1>
          <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
          <div class="agent-meta">
            <el-tag :type="getTypeColor(agent.type)">{{ getTypeLabel(agent.type) }}</el-tag>
            <el-tag v-if="agent.is_public" type="success">公开</el-tag>
            <el-tag :type="agent.status === 'active' ? 'success' : 'danger'">
              {{ agent.status === 'active' ? '活跃' : '非活跃' }}
            </el-tag>
          </div>
          <div class="agent-stats">
            <span><el-icon><ChatDotRound /></el-icon> {{ agent.chat_count }} 次对话</span>
            <span><el-icon><Star /></el-icon> {{ agent.like_count }} 个赞</span>
            <span><el-icon><Calendar /></el-icon> 创建于 {{ formatDate(agent.created_at) }}</span>
          </div>
        </div>
        <div class="agent-actions">
          <el-button type="primary" @click="startChat">
            <el-icon><ChatDotRound /></el-icon>
            开始对话
          </el-button>
          <el-button v-if="canEdit" @click="editAgent">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button @click="cloneAgent">
            <el-icon><CopyDocument /></el-icon>
            克隆
          </el-button>
          <el-button @click="likeAgent" :disabled="liked">
            <el-icon><Star /></el-icon>
            {{ liked ? '已点赞' : '点赞' }}
          </el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="agent-tabs">
        <el-tab-pane label="基本信息" name="basic">
          <div class="tab-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="智能体名称">{{ agent.name }}</el-descriptions-item>
              <el-descriptions-item label="类型">{{ getTypeLabel(agent.type) }}</el-descriptions-item>
              <el-descriptions-item label="模型">{{ agent.model_name || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="温度参数">{{ agent.temperature }}</el-descriptions-item>
              <el-descriptions-item label="最大Token">{{ agent.max_tokens }}</el-descriptions-item>
              <el-descriptions-item label="可见性">{{ agent.is_public ? '公开' : '私有' }}</el-descriptions-item>
              <el-descriptions-item label="创建时间" :span="2">{{ formatDateTime(agent.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间" :span="2">{{ formatDateTime(agent.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <el-tab-pane label="提示词" name="prompt">
          <div class="tab-content">
            <el-card>
              <template #header>
                <span>提示词模板</span>
              </template>
              <div class="prompt-content">
                <pre v-if="agent.prompt_template">{{ agent.prompt_template }}</pre>
                <el-empty v-else description="暂无提示词模板" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="配置信息" name="config">
          <div class="tab-content">
            <el-card>
              <template #header>
                <span>智能体配置</span>
              </template>
              <div class="config-content">
                <pre v-if="agent.config">{{ JSON.stringify(agent.config, null, 2) }}</pre>
                <el-empty v-else description="暂无配置信息" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="知识库" name="knowledge">
          <div class="tab-content">
            <el-card>
              <template #header>
                <span>关联知识库</span>
              </template>
              <div class="knowledge-list">
                <div v-if="agent.knowledge_base_ids && agent.knowledge_base_ids.length > 0">
                  <el-tag 
                    v-for="kbId in agent.knowledge_base_ids" 
                    :key="kbId" 
                    class="knowledge-tag"
                  >
                    知识库 #{{ kbId }}
                  </el-tag>
                </div>
                <el-empty v-else description="暂无关联知识库" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="对话历史" name="conversations">
          <div class="tab-content">
            <el-card>
              <template #header>
                <span>最近对话</span>
              </template>
              <div class="conversation-list">
                <el-empty description="暂无对话历史" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-empty v-else description="智能体不存在" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, Robot, ChatDotRound, Star, Calendar, Edit, CopyDocument 
} from '@element-plus/icons-vue'
import { agentApi } from '@/api/agent'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const agent = ref(null)
const loading = ref(false)
const activeTab = ref('basic')
const liked = ref(false)

// 计算属性
const agentId = computed(() => parseInt(route.params.id as string))
const canEdit = computed(() => {
  return agent.value && agent.value.owner_id === userStore.userId
})

// 方法
const fetchAgent = async () => {
  loading.value = true
  try {
    const response = await agentApi.getAgent(agentId.value)
    agent.value = response.data
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    ElMessage.error('获取智能体详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const startChat = () => {
  router.push(`/chat?agent=${agentId.value}`)
}

const editAgent = () => {
  router.push(`/agents/${agentId.value}/edit`)
}

const cloneAgent = async () => {
  try {
    await agentApi.cloneAgent(agentId.value)
    ElMessage.success('智能体克隆成功')
  } catch (error) {
    console.error('克隆智能体失败:', error)
    ElMessage.error('克隆智能体失败')
  }
}

const likeAgent = async () => {
  try {
    await agentApi.likeAgent(agentId.value)
    liked.value = true
    if (agent.value) {
      agent.value.like_count = String(parseInt(agent.value.like_count) + 1)
    }
    ElMessage.success('点赞成功')
  } catch (error) {
    console.error('点赞失败:', error)
    ElMessage.error('点赞失败')
  }
}

const getTypeLabel = (type: string) => {
  const labels = {
    chat: '聊天助手',
    assistant: '智能助手',
    workflow: '工作流',
    custom: '自定义'
  }
  return labels[type] || type
}

const getTypeColor = (type: string) => {
  const colors = {
    chat: 'primary',
    assistant: 'success',
    workflow: 'warning',
    custom: 'info'
  }
  return colors[type] || 'info'
}

const formatDate = (dateString: string) => {
  return formatTime(new Date(dateString), 'YYYY-MM-DD')
}

const formatDateTime = (dateString: string) => {
  return formatTime(new Date(dateString), 'YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  fetchAgent()
})
</script>

<style lang="scss" scoped>
.agent-detail {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.loading-wrapper {
  padding: 24px;
}

.agent-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 32px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agent-info {
  flex: 1;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
  }
  
  .agent-description {
    font-size: 16px;
    color: #606266;
    line-height: 1.5;
    margin-bottom: 16px;
  }
  
  .agent-meta {
    margin-bottom: 16px;
    
    .el-tag {
      margin-right: 8px;
    }
  }
  
  .agent-stats {
    display: flex;
    gap: 24px;
    font-size: 14px;
    color: #909399;
    
    span {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
}

.agent-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .el-button {
    width: 120px;
  }
}

.agent-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 24px;
  }
}

.tab-content {
  .el-descriptions {
    :deep(.el-descriptions__label) {
      font-weight: 600;
    }
  }
  
  .prompt-content,
  .config-content {
    pre {
      background: #f5f7fa;
      padding: 16px;
      border-radius: 4px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 14px;
      line-height: 1.5;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
  
  .knowledge-list {
    .knowledge-tag {
      margin-right: 8px;
      margin-bottom: 8px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .agent-detail {
    padding: 16px;
  }
  
  .agent-header {
    flex-direction: column;
    text-align: center;
    
    .agent-actions {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: center;
      
      .el-button {
        width: auto;
        min-width: 100px;
      }
    }
  }
  
  .agent-stats {
    flex-direction: column;
    gap: 8px !important;
  }
}
</style>
