<template>
  <div class="knowledge-upload">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/knowledge' }">知识库管理</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: `/knowledge/${knowledgeId}` }">
          {{ knowledgeName }}
        </el-breadcrumb-item>
        <el-breadcrumb-item>文件上传</el-breadcrumb-item>
      </el-breadcrumb>
      <h2>文件上传</h2>
    </div>

    <el-row :gutter="24">
      <!-- 文件上传区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>上传文件</span>
            </div>
          </template>
          
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            multiple
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 txt、md、pdf、doc、docx、ppt、pptx、xls、xlsx 格式文件，单个文件不超过 10MB
              </div>
            </template>
          </el-upload>

          <div class="upload-actions" v-if="fileList.length > 0">
            <el-button type="primary" @click="handleUpload" :loading="uploading">
              开始上传
            </el-button>
            <el-button @click="clearFiles">清空列表</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 上传进度 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>上传进度</span>
            </div>
          </template>
          
          <div v-if="uploadProgress.length === 0" class="empty-progress">
            <el-empty description="暂无上传任务" :image-size="80" />
          </div>
          
          <div v-else class="progress-list">
            <div
              v-for="(progress, index) in uploadProgress"
              :key="index"
              class="progress-item"
            >
              <div class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span class="file-name">{{ progress.name }}</span>
                <el-tag
                  :type="getStatusType(progress.status)"
                  size="small"
                  class="status-tag"
                >
                  {{ getStatusText(progress.status) }}
                </el-tag>
              </div>
              
              <el-progress
                :percentage="progress.percentage"
                :status="progress.status === 'failed' ? 'exception' : 
                         progress.status === 'completed' ? 'success' : undefined"
                :show-text="false"
                class="progress-bar"
              />
              
              <div class="progress-text">
                {{ progress.percentage }}% 
                <span v-if="progress.status === 'failed'" class="error-text">
                  - {{ progress.error }}
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 已上传文件列表 -->
    <el-card class="file-list-card">
      <template #header>
        <div class="card-header">
          <span>已上传文件</span>
          <el-button type="text" @click="refreshFileList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table v-loading="fileListLoading" :data="uploadedFiles" style="width: 100%">
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'failed'"
              type="text"
              size="small"
              @click="reprocessFile(row.id)"
            >
              重新处理
            </el-button>
            <el-button type="text" size="small" @click="deleteFile(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Document, Refresh } from '@element-plus/icons-vue'
import type { UploadFile, UploadFiles } from 'element-plus'
import { knowledgeApi, type KnowledgeFile } from '@/api/knowledge'
import { formatTime, formatFileSize } from '@/utils'

const router = useRouter()
const route = useRoute()

const knowledgeId = Number(route.params.id)
const knowledgeName = ref('')
const uploadRef = ref()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const fileListLoading = ref(false)
const uploadedFiles = ref<KnowledgeFile[]>([])

// 上传进度
interface UploadProgress {
  name: string
  percentage: number
  status: 'uploading' | 'completed' | 'failed'
  error?: string
}

const uploadProgress = ref<UploadProgress[]>([])

// 文件变化处理
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  // 检查文件大小
  if (file.raw && file.raw.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    files.splice(files.indexOf(file), 1)
    return
  }
  
  fileList.value = files
}

// 文件移除处理
const handleFileRemove = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
}

// 清空文件列表
const clearFiles = () => {
  fileList.value = []
  uploadProgress.value = []
}

// 开始上传
const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }
  
  uploading.value = true
  uploadProgress.value = fileList.value.map(file => ({
    name: file.name,
    percentage: 0,
    status: 'uploading' as const
  }))
  
  try {
    const files = fileList.value.map(file => file.raw!).filter(Boolean)
    
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      uploadProgress.value.forEach(progress => {
        if (progress.status === 'uploading' && progress.percentage < 90) {
          progress.percentage += Math.random() * 20
        }
      })
    }, 500)
    
    await knowledgeApi.uploadFiles(knowledgeId, files)
    
    clearInterval(progressInterval)
    
    // 完成上传
    uploadProgress.value.forEach(progress => {
      progress.percentage = 100
      progress.status = 'completed'
    })
    
    ElMessage.success('文件上传成功')
    fileList.value = []
    refreshFileList()
    
  } catch (error) {
    console.error('文件上传失败:', error)
    uploadProgress.value.forEach(progress => {
      if (progress.status === 'uploading') {
        progress.status = 'failed'
        progress.error = '上传失败'
      }
    })
    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
  }
}

// 获取已上传文件列表
const refreshFileList = async () => {
  fileListLoading.value = true
  try {
    const response = await knowledgeApi.getFiles(knowledgeId)
    uploadedFiles.value = response.data
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  } finally {
    fileListLoading.value = false
  }
}

// 重新处理文件
const reprocessFile = async (fileId: number) => {
  try {
    await knowledgeApi.reprocessFile(knowledgeId, fileId)
    ElMessage.success('重新处理任务已提交')
    refreshFileList()
  } catch (error) {
    console.error('重新处理失败:', error)
    ElMessage.error('重新处理失败')
  }
}

// 删除文件
const deleteFile = async (fileId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文件吗？', '确认删除', {
      type: 'warning'
    })
    
    await knowledgeApi.deleteFile(knowledgeId, fileId)
    ElMessage.success('文件删除成功')
    refreshFileList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error)
      ElMessage.error('删除文件失败')
    }
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    uploading: 'warning',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    uploading: '上传中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  refreshFileList()
})
</script>

<style lang="scss" scoped>
.knowledge-upload {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  h2 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 16px 0 0 0;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-demo {
  width: 100%;
  
  .el-upload-dragger {
    width: 100%;
  }
}

.upload-actions {
  margin-top: 16px;
  text-align: center;
}

.empty-progress {
  text-align: center;
  padding: 40px 0;
}

.progress-list {
  .progress-item {
    margin-bottom: 16px;
    
    .file-info {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      
      .file-icon {
        color: #409eff;
        margin-right: 8px;
      }
      
      .file-name {
        flex: 1;
        font-size: 14px;
      }
      
      .status-tag {
        margin-left: 8px;
      }
    }
    
    .progress-bar {
      margin-bottom: 4px;
    }
    
    .progress-text {
      font-size: 12px;
      color: #909399;
      
      .error-text {
        color: #f56c6c;
      }
    }
  }
}

.file-list-card {
  margin-top: 24px;
}
</style>
