<template>
  <div class="knowledge-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="title-section">
          <h1>{{ knowledgeBase?.name || '知识库详情' }}</h1>
          <p>{{ knowledgeBase?.description || '暂无描述' }}</p>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="uploadFiles">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
        <el-button @click="editKnowledge">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </div>
    </div>

    <div class="knowledge-info" v-if="knowledgeBase">
      <el-row :gutter="24">
        <el-col :span="6">
          <div class="info-card">
            <div class="info-label">文档数量</div>
            <div class="info-value">{{ knowledgeBase.document_count || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-card">
            <div class="info-label">总大小</div>
            <div class="info-value">{{ formatFileSize(knowledgeBase.total_size || 0) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-card">
            <div class="info-label">创建时间</div>
            <div class="info-value">{{ formatTime(knowledgeBase.created_at) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-card">
            <div class="info-label">更新时间</div>
            <div class="info-value">{{ formatTime(knowledgeBase.updated_at) }}</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="documents-section">
      <div class="section-header">
        <h2>文档列表</h2>
        <el-input
          v-model="searchQuery"
          placeholder="搜索文档..."
          style="width: 300px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <el-table
        :data="documents"
        v-loading="loading"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="文档名称" min-width="200">
          <template #default="{ row }">
            <div class="document-name">
              <el-icon class="file-icon"><Document /></el-icon>
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getFileTypeColor(row.type)" size="small">
              {{ row.type?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewDocument(row)">
              查看
            </el-button>
            <el-button type="text" size="small" @click="downloadDocument(row)">
              下载
            </el-button>
            <el-button type="text" size="small" @click="deleteDocument(row)" class="danger">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <el-empty v-if="!loading && documents.length === 0" description="暂无文档" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Upload, Edit, Search, Document
} from '@element-plus/icons-vue'
import { formatTime } from '@/utils'

const route = useRoute()
const router = useRouter()

// 响应式数据
const knowledgeBase = ref<any>(null)
const documents = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedDocuments = ref<any[]>([])

// 获取知识库详情
const fetchKnowledgeBase = async () => {
  try {
    loading.value = true
    const id = route.params.id
    // TODO: 调用API获取知识库详情
    // const response = await knowledgeApi.getKnowledgeBase(id)
    // knowledgeBase.value = response.data
    
    // 模拟数据
    knowledgeBase.value = {
      id: id,
      name: '示例知识库',
      description: '这是一个示例知识库',
      document_count: 10,
      total_size: 1024 * 1024 * 50, // 50MB
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  } catch (error) {
    console.error('获取知识库详情失败:', error)
    ElMessage.error('获取知识库详情失败')
  } finally {
    loading.value = false
  }
}

// 获取文档列表
const fetchDocuments = async () => {
  try {
    loading.value = true
    // TODO: 调用API获取文档列表
    // const response = await knowledgeApi.getDocuments(route.params.id, {
    //   page: currentPage.value,
    //   size: pageSize.value,
    //   search: searchQuery.value
    // })
    // documents.value = response.data.items
    // total.value = response.data.total
    
    // 模拟数据
    documents.value = []
    total.value = 0
  } catch (error) {
    console.error('获取文档列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取文件类型颜色
const getFileTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    pdf: 'danger',
    doc: 'primary',
    docx: 'primary',
    txt: 'info',
    md: 'success'
  }
  return colors[type?.toLowerCase()] || 'info'
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return colors[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

// 事件处理
const goBack = () => {
  router.push('/knowledge')
}

const uploadFiles = () => {
  router.push(`/knowledge/${route.params.id}/upload`)
}

const editKnowledge = () => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中...')
}

const handleSearch = () => {
  currentPage.value = 1
  fetchDocuments()
}

const handleSelectionChange = (selection: any[]) => {
  selectedDocuments.value = selection
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchDocuments()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchDocuments()
}

const viewDocument = (document: any) => {
  // TODO: 实现查看文档功能
  ElMessage.info('查看文档功能开发中...')
}

const downloadDocument = (document: any) => {
  // TODO: 实现下载文档功能
  ElMessage.info('下载文档功能开发中...')
}

const deleteDocument = async (document: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '确认删除', {
      type: 'warning'
    })
    
    // TODO: 调用API删除文档
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error) {
    // 用户取消删除
  }
}

onMounted(() => {
  fetchKnowledgeBase()
  fetchDocuments()
})
</script>

<style lang="scss" scoped>
.knowledge-detail {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    
    .back-btn {
      margin-top: 4px;
    }
    
    .title-section {
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
  
  .header-right {
    display: flex;
    gap: 12px;
  }
}

.knowledge-info {
  margin-bottom: 32px;
  
  .info-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    
    .info-label {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }
    
    .info-value {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.documents-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h2 {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
}

.document-name {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .file-icon {
    color: #409eff;
  }
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.danger {
  color: #f56c6c !important;
}
</style>
