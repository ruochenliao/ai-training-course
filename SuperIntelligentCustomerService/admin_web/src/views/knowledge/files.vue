<template>
  <div class="knowledge-files">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ name: 'Knowledge' }">知识库管理</el-breadcrumb-item>
          <el-breadcrumb-item>{{ knowledgeBaseName }}</el-breadcrumb-item>
        </el-breadcrumb>
        <h1>文件管理</h1>
        
        <!-- 统计信息 -->
        <div class="statistics" v-if="statistics">
          <div class="stat-item">
            <span class="label">总文件</span>
            <span class="value">{{ statistics.total }}</span>
          </div>
          <div class="stat-item">
            <span class="label">已完成</span>
            <span class="value">{{ statistics.by_status.completed || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="label">处理中</span>
            <span class="value">{{ statistics.by_status.processing || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="label">失败</span>
            <span class="value">{{ statistics.by_status.failed || 0 }}</span>
          </div>
        </div>
      </div>
      
      <div class="header-actions">
        <el-upload
          ref="uploadRef"
          :action="uploadUrl"
          :headers="uploadHeaders"
          :before-upload="beforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :on-progress="handleUploadProgress"
          :show-file-list="false"
          multiple
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传文件
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 查询条件 -->
    <div class="query-bar">
      <el-form :model="queryForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="queryForm.search"
            placeholder="搜索文件名"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="文件类型">
          <el-select v-model="queryForm.file_type" placeholder="选择类型" clearable>
            <el-option
              v-for="type in fileTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="queryForm.status" placeholder="选择状态" clearable>
            <el-option label="等待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="处理失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <el-table
        v-loading="loading"
        :data="files"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon class="file-icon" :class="`file-${row.file_type}`">
                <Document />
              </el-icon>
              <div class="file-details">
                <div class="file-name">{{ row.original_name }}</div>
                <div class="file-meta">{{ formatFileSize(row.file_size) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="处理状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.embedding_status)"
              size="small"
            >
              {{ getStatusText(row.embedding_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="分块数" width="80">
          <template #default="{ row }">
            {{ row.chunk_count || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="上传时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.embedding_status === 'failed'"
              size="small"
              type="warning"
              @click="retryProcessing(row)"
            >
              重试
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteFile(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- 上传进度对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="文件上传"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-for="(upload, index) in uploadList" :key="index" class="upload-item">
        <div class="upload-info">
          <span class="filename">{{ upload.filename }}</span>
          <span class="status" :class="upload.status">{{ upload.statusText }}</span>
        </div>
        <el-progress
          v-if="upload.status === 'uploading'"
          :percentage="upload.progress"
          :stroke-width="6"
        />
      </div>
      
      <template #footer>
        <el-button @click="uploadDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document } from '@element-plus/icons-vue'
import { knowledgeFileApi } from '@/api/knowledge'
import { getToken } from '@/utils/auth'

const route = useRoute()

// 响应式数据
const loading = ref(false)
const files = ref([])
const fileTypes = ref([])
const statistics = ref(null)
const total = ref(0)
const selectedFiles = ref([])

// 知识库信息
const kbId = computed(() => route.params.kbId)
const knowledgeBaseName = computed(() => route.query.name || '知识库')

// 查询表单
const queryForm = reactive({
  search: '',
  file_type: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 上传相关
const uploadRef = ref()
const uploadDialogVisible = ref(false)
const uploadList = ref([])

const uploadUrl = computed(() => `/api/v1/knowledge/files/${kbId.value}/upload`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${getToken()}`
}))

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryForm
    }
    
    const response = await knowledgeFileApi.getList(kbId.value, params)
    if (response.code === 200) {
      files.value = response.data.items
      total.value = response.data.total
    }
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

// 加载文件类型
const loadFileTypes = async () => {
  try {
    const response = await knowledgeFileApi.getTypes()
    if (response.code === 200) {
      fileTypes.value = response.data
    }
  } catch (error) {
    console.error('加载文件类型失败:', error)
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await knowledgeFileApi.getStatistics(kbId.value)
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
    file_type: '',
    status: ''
  })
  pagination.page = 1
  loadData()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

// 上传前检查
const beforeUpload = (file) => {
  // 检查文件大小（50MB）
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  
  // 添加到上传列表
  uploadList.value.push({
    filename: file.name,
    status: 'uploading',
    statusText: '上传中...',
    progress: 0
  })
  
  uploadDialogVisible.value = true
  return true
}

// 上传进度
const handleUploadProgress = (event, file) => {
  const uploadItem = uploadList.value.find(item => item.filename === file.name)
  if (uploadItem) {
    uploadItem.progress = Math.round(event.percent)
  }
}

// 上传成功
const handleUploadSuccess = (response, file) => {
  const uploadItem = uploadList.value.find(item => item.filename === file.name)
  if (uploadItem) {
    if (response.code === 200) {
      uploadItem.status = 'success'
      uploadItem.statusText = '上传成功'
      uploadItem.progress = 100
    } else {
      uploadItem.status = 'error'
      uploadItem.statusText = response.msg || '上传失败'
    }
  }
  
  // 刷新列表
  loadData()
  loadStatistics()
}

// 上传失败
const handleUploadError = (error, file) => {
  const uploadItem = uploadList.value.find(item => item.filename === file.name)
  if (uploadItem) {
    uploadItem.status = 'error'
    uploadItem.statusText = '上传失败'
  }
  ElMessage.error('文件上传失败')
}

// 重试处理
const retryProcessing = async (file) => {
  try {
    const response = await knowledgeFileApi.retry(file.id)
    if (response.code === 200) {
      ElMessage.success('已重新提交处理')
      loadData()
    }
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

// 删除文件
const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件"${file.original_name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await knowledgeFileApi.delete(file.id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      loadData()
      loadStatistics()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 工具函数
const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '等待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '处理失败'
  }
  return textMap[status] || status
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatTime = (time) => {
  return new Date(time).toLocaleString()
}

// 生命周期
onMounted(() => {
  loadFileTypes()
  loadStatistics()
  loadData()
})
</script>

<style scoped>
.knowledge-files {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-content h1 {
  margin: 10px 0;
  font-size: 24px;
  font-weight: 600;
}

.statistics {
  display: flex;
  gap: 20px;
  margin-top: 10px;
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

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 20px;
  color: #409eff;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #303133;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.upload-item {
  margin-bottom: 15px;
}

.upload-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.filename {
  font-weight: 500;
}

.status.success {
  color: #67c23a;
}

.status.error {
  color: #f56c6c;
}

.status.uploading {
  color: #409eff;
}
</style>
