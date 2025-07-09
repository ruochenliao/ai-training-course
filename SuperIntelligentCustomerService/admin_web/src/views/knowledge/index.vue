<template>
  <div class="knowledge-base-management">
    <!-- 页面标题和统计 -->
    <div class="page-header">
      <div class="header-content">
        <h1>知识库管理</h1>
        <div class="statistics" v-if="statistics">
          <div class="stat-item">
            <span class="label">我的知识库</span>
            <span class="value">{{ statistics.owned_count }}</span>
          </div>
          <div class="stat-item">
            <span class="label">可访问</span>
            <span class="value">{{ statistics.accessible_count }}</span>
          </div>
          <div class="stat-item">
            <span class="label">总文件数</span>
            <span class="value">{{ statistics.total_files }}</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建知识库
        </el-button>
      </div>
    </div>

    <!-- 查询条件 -->
    <div class="query-bar">
      <el-form :model="queryForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="queryForm.search"
            placeholder="搜索知识库名称或描述"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryForm.knowledge_type" placeholder="选择类型" clearable>
            <el-option
              v-for="type in knowledgeTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.is_public" placeholder="选择状态" clearable>
            <el-option label="公开" :value="true" />
            <el-option label="私有" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 知识库列表 -->
    <div class="knowledge-list">
      <el-row :gutter="20">
        <el-col
          v-for="kb in knowledgeBases"
          :key="kb.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
        >
          <div class="knowledge-card">
            <div class="card-header">
              <div class="title">{{ kb.name }}</div>
              <div class="type-badge" :class="`type-${kb.knowledge_type}`">
                {{ getTypeLabel(kb.knowledge_type) }}
              </div>
            </div>
            
            <div class="card-content">
              <p class="description">{{ kb.description || '暂无描述' }}</p>
              
              <div class="stats">
                <div class="stat">
                  <span class="label">文件数</span>
                  <span class="value">{{ kb.file_count || 0 }}</span>
                </div>
                <div class="stat">
                  <span class="label">大小</span>
                  <span class="value">{{ formatFileSize(kb.total_size || 0) }}</span>
                </div>
              </div>
              
              <div class="meta">
                <div class="visibility">
                  <el-tag :type="kb.is_public ? 'success' : 'info'" size="small">
                    {{ kb.is_public ? '公开' : '私有' }}
                  </el-tag>
                </div>
                <div class="time">
                  {{ formatTime(kb.created_at) }}
                </div>
              </div>
            </div>
            
            <div class="card-actions">
              <el-button size="small" @click="viewFiles(kb)">
                <el-icon><Document /></el-icon>
                文件管理
              </el-button>
              <el-dropdown v-if="kb.can_modify" @command="handleCommand">
                <el-button size="small" type="text">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`edit-${kb.id}`">编辑</el-dropdown-item>
                    <el-dropdown-item :command="`delete-${kb.id}`" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 空状态 -->
      <div v-if="!loading && knowledgeBases.length === 0" class="empty-state">
        <el-empty description="暂无知识库">
          <el-button type="primary" @click="showCreateDialog">创建第一个知识库</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <KnowledgeBaseDialog
      v-model="dialogVisible"
      :knowledge-base="currentKnowledgeBase"
      :knowledge-types="knowledgeTypes"
      @success="handleDialogSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import {
  NButton,
  NCard,
  NSpace,
  NTag,
  NPopconfirm,
  NDataTable,
  NInput,
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NTextarea,
  useMessage,
  useDialog
} from 'naive-ui'
import { useRouter } from 'vue-router'
import { knowledgeBaseApi } from '@/api/knowledge'
import KnowledgeBaseDialog from './components/KnowledgeBaseDialog.vue'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// 响应式数据
const loading = ref(false)
const knowledgeBases = ref([])
const knowledgeTypes = ref([])
const statistics = ref(null)
const total = ref(0)

// 查询表单
const queryForm = reactive({
  search: '',
  knowledge_type: '',
  is_public: null
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 12
})

// 对话框
const dialogVisible = ref(false)
const currentKnowledgeBase = ref(null)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryForm
    }
    
    const response = await knowledgeBaseApi.getList(params)
    if (response.code === 200) {
      knowledgeBases.value = response.data.items
      total.value = response.data.total
    }
  } catch (error) {
    message.error('加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

// 加载知识库类型
const loadKnowledgeTypes = async () => {
  try {
    const response = await knowledgeBaseApi.getTypes()
    if (response.code === 200) {
      knowledgeTypes.value = response.data
    }
  } catch (error) {
    console.error('加载知识库类型失败:', error)
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await knowledgeBaseApi.getStatistics()
    if (response.code === 200) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 重置查询
const resetQuery = () => {
  Object.assign(queryForm, {
    search: '',
    knowledge_type: '',
    is_public: null
  })
  pagination.page = 1
  loadData()
}

// 显示创建对话框
const showCreateDialog = () => {
  currentKnowledgeBase.value = null
  dialogVisible.value = true
}

// 查看文件
const viewFiles = (kb) => {
  router.push({
    name: 'KnowledgeFiles',
    params: { kbId: kb.id },
    query: { name: kb.name }
  })
}

// 处理下拉菜单命令
const handleCommand = (command) => {
  const [action, id] = command.split('-')
  const kb = knowledgeBases.value.find(item => item.id == id)
  
  if (action === 'edit') {
    currentKnowledgeBase.value = kb
    dialogVisible.value = true
  } else if (action === 'delete') {
    handleDelete(kb)
  }
}

// 删除知识库
const handleDelete = async (kb) => {
  try {
    await new Promise((resolve, reject) => {
      dialog.warning({
        title: '确认删除',
        content: `确定要删除知识库"${kb.name}"吗？此操作不可恢复。`,
        positiveText: '确定',
        negativeText: '取消',
        onPositiveClick: () => resolve(),
        onNegativeClick: () => reject('cancel')
      })
    })
    
    const response = await knowledgeBaseApi.delete(kb.id)
    if (response.code === 200) {
      message.success('删除成功')
      loadData()
      loadStatistics()
    }
  } catch (error) {
    if (error !== 'cancel') {
      message.error('删除失败')
    }
  }
}

// 对话框成功回调
const handleDialogSuccess = () => {
  loadData()
  loadStatistics()
}

// 工具函数
const getTypeLabel = (type) => {
  const typeItem = knowledgeTypes.value.find(item => item.value === type)
  return typeItem ? typeItem.label : type
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatTime = (time) => {
  return new Date(time).toLocaleDateString()
}

// 生命周期
onMounted(() => {
  loadKnowledgeTypes()
  loadStatistics()
  loadData()
})
</script>

<style scoped>
.knowledge-base-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-content h1 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
}

.statistics {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-item .label {
  font-size: 12px;
  color: #666;
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.query-bar {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.knowledge-list {
  margin-bottom: 20px;
}

.knowledge-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  transition: all 0.3s;
  height: 280px;
  display: flex;
  flex-direction: column;
}

.knowledge-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  margin-right: 8px;
}

.type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
  background: #909399;
}

.type-badge.type-technical { background: #409eff; }
.type-badge.type-faq { background: #67c23a; }
.type-badge.type-policy { background: #e6a23c; }
.type-badge.type-product { background: #f56c6c; }

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.description {
  color: #606266;
  font-size: 14px;
  margin: 0 0 12px 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat .label {
  font-size: 12px;
  color: #909399;
}

.stat .value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.time {
  font-size: 12px;
  color: #909399;
}

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}
</style>
