<template>
  <div class="agent-list">
    <div class="page-header">
      <div class="header-left">
        <h1>智能体管理</h1>
        <p>创建和管理您的智能体</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createAgent">
          <el-icon><Plus /></el-icon>
          创建智能体
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索智能体..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="类型筛选" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="聊天助手" value="chat" />
            <el-option label="工作流" value="workflow" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterPublic" placeholder="可见性" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="公开" :value="true" />
            <el-option label="私有" :value="false" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <div class="agent-grid">
      <el-row :gutter="20">
        <el-col :span="6" v-for="agent in agents" :key="agent.id">
          <el-card class="agent-card" @click="viewAgent(agent.id)">
            <div class="agent-avatar">
              <el-avatar :size="60" :src="agent.avatar_url">
                <el-icon size="30"><User /></el-icon>
              </el-avatar>
            </div>
            <div class="agent-info">
              <h3>{{ agent.name }}</h3>
              <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
              <div class="agent-meta">
                <el-tag :type="getTypeColor(agent.type)" size="small">
                  {{ getTypeLabel(agent.type) }}
                </el-tag>
                <el-tag v-if="agent.is_public" type="success" size="small">公开</el-tag>
              </div>
              <div class="agent-stats">
                <span><el-icon><ChatDotRound /></el-icon> {{ agent.chat_count }}</span>
                <span><el-icon><Star /></el-icon> {{ agent.like_count }}</span>
              </div>
            </div>
            <div class="agent-actions" @click.stop>
              <el-dropdown @command="handleCommand">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`edit-${agent.id}`">编辑</el-dropdown-item>
                    <el-dropdown-item :command="`clone-${agent.id}`">克隆</el-dropdown-item>
                    <el-dropdown-item :command="`chat-${agent.id}`">开始对话</el-dropdown-item>
                    <el-dropdown-item :command="`delete-${agent.id}`" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 48]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="6" animated />
    </div>

    <el-empty v-if="!loading && agents.length === 0" description="暂无智能体" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, User, ChatDotRound, Star, MoreFilled
} from '@element-plus/icons-vue'
import { agentApi, type Agent } from '@/api/agent'
import { formatTime } from '@/utils'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const router = useRouter()

// 响应式数据
const agents = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const filterPublic = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 计算属性
const searchParams = computed(() => ({
  skip: (currentPage.value - 1) * pageSize.value,
  limit: pageSize.value,
  search: searchQuery.value || undefined,
  type: filterType.value || undefined,
  is_public: filterPublic.value !== '' ? filterPublic.value : undefined
}))

// 方法
const fetchAgents = async () => {
  loading.value = true
  try {
    const response = await agentApi.getAgents(searchParams.value)
    agents.value = response.data
    total.value = response.total || response.data.length
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchAgents()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchAgents()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchAgents()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchAgents()
}

const createAgent = () => {
  router.push('/agents/create')
}

const viewAgent = (id: number) => {
  router.push(`/agents/${id}`)
}

const handleCommand = async (command: string) => {
  const [action, id] = command.split('-')
  const agentId = parseInt(id)
  
  switch (action) {
    case 'edit':
      router.push(`/agents/${agentId}/edit`)
      break
    case 'clone':
      await cloneAgent(agentId)
      break
    case 'chat':
      router.push(`/chat?agent=${agentId}`)
      break
    case 'delete':
      await deleteAgent(agentId)
      break
  }
}

const cloneAgent = async (id: number) => {
  try {
    await agentApi.clone(id)
    ElMessage.success('智能体克隆成功')
    fetchAgents()
  } catch (error) {
    console.error('克隆智能体失败:', error)
    ElMessage.error('克隆智能体失败')
  }
}

const deleteAgent = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个智能体吗？', '确认删除', {
      type: 'warning'
    })

    await agentApi.delete(id)
    ElMessage.success('智能体删除成功')
    fetchAgents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除智能体失败:', error)
      ElMessage.error('删除智能体失败')
    }
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

onMounted(() => {
  fetchAgents()
})
</script>

<style lang="scss" scoped>
.agent-list {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    h1 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }
    
    p {
      color: #606266;
      margin: 0;
    }
  }
}

.filter-bar {
  margin-bottom: 24px;
}

.agent-grid {
  margin-bottom: 24px;
}

.agent-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 280px;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
  
  :deep(.el-card__body) {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
}

.agent-avatar {
  text-align: center;
  margin-bottom: 16px;
}

.agent-info {
  flex: 1;
  
  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .agent-description {
    font-size: 14px;
    color: #606266;
    line-height: 1.5;
    margin-bottom: 12px;
    height: 42px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .agent-meta {
    margin-bottom: 12px;
    
    .el-tag {
      margin-right: 8px;
    }
  }
  
  .agent-stats {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #909399;
    
    span {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
}

.agent-actions {
  position: absolute;
  top: 12px;
  right: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.loading-wrapper {
  padding: 24px;
}

// 响应式设计
@media (max-width: 1200px) {
  .agent-grid {
    :deep(.el-col) {
      width: 33.333%;
    }
  }
}

@media (max-width: 768px) {
  .agent-list {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    
    .header-right {
      width: 100%;
    }
  }
  
  .filter-bar {
    :deep(.el-col) {
      margin-bottom: 12px;
    }
  }
  
  .agent-grid {
    :deep(.el-col) {
      width: 50%;
    }
  }
}

@media (max-width: 480px) {
  .agent-grid {
    :deep(.el-col) {
      width: 100%;
    }
  }
}
</style>
