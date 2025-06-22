<template>
  <div class="p-6">
    <!-- 头部 -->
    <div class="mb-6">
      <div class="flex items-center gap-4 mb-4">
        <n-button text @click="$router.back()">
          <template #icon>
            <n-icon><ArrowBack /></n-icon>
          </template>
          返回
        </n-button>
        <h1 class="text-2xl font-bold text-gray-900">文档上传</h1>
      </div>
      <p class="text-gray-600">上传文档到知识库：{{ knowledgeBase?.name }}</p>
    </div>

    <!-- 上传区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 文件上传 -->
      <n-card title="文件上传" class="h-fit">
        <n-upload
          ref="uploadRef"
          multiple
          directory-dnd
          :max="20"
          :file-list="fileList"
          :custom-request="handleUpload"
          @update:file-list="handleFileListUpdate"
          @before-upload="handleBeforeUpload"
        >
          <n-upload-dragger>
            <div class="text-center">
              <n-icon size="48" class="text-gray-400 mb-4">
                <CloudUpload />
              </n-icon>
              <div class="text-lg font-medium mb-2">点击或拖拽文件到此区域上传</div>
              <div class="text-sm text-gray-500">
                支持单个或批量上传，支持 PDF、Word、PPT、TXT、Markdown 等格式
              </div>
              <div class="text-xs text-gray-400 mt-2">
                单个文件最大 100MB，最多同时上传 20 个文件
              </div>
            </div>
          </n-upload-dragger>
        </n-upload>

        <!-- 上传设置 -->
        <div class="mt-6">
          <h3 class="text-lg font-medium mb-4">上传设置</h3>
          <n-form :model="uploadSettings" label-placement="left" label-width="auto">
            <n-form-item label="自动处理">
              <n-switch v-model:value="uploadSettings.autoProcess" />
              <span class="ml-2 text-sm text-gray-500">上传后自动进行文档解析和向量化</span>
            </n-form-item>
            <n-form-item label="分块策略">
              <n-select
                v-model:value="uploadSettings.chunkStrategy"
                :options="chunkStrategyOptions"
                placeholder="选择分块策略"
              />
            </n-form-item>
            <n-form-item label="分块大小">
              <n-input-number
                v-model:value="uploadSettings.chunkSize"
                :min="100"
                :max="2000"
                :step="100"
                placeholder="字符数"
              />
            </n-form-item>
            <n-form-item label="重叠大小">
              <n-input-number
                v-model:value="uploadSettings.chunkOverlap"
                :min="0"
                :max="500"
                :step="50"
                placeholder="字符数"
              />
            </n-form-item>
            <n-form-item label="提取图谱">
              <n-switch v-model:value="uploadSettings.extractGraph" />
              <span class="ml-2 text-sm text-gray-500">提取实体和关系构建知识图谱</span>
            </n-form-item>
          </n-form>
        </div>

        <!-- 批量操作 -->
        <div class="mt-6 flex gap-2">
          <n-button
            type="primary"
            :disabled="fileList.length === 0"
            :loading="uploading"
            @click="handleBatchUpload"
          >
            <template #icon>
              <n-icon><Upload /></n-icon>
            </template>
            开始上传 ({{ fileList.length }})
          </n-button>
          <n-button @click="handleClearAll" :disabled="fileList.length === 0">
            清空列表
          </n-button>
        </div>
      </n-card>

      <!-- 上传进度 -->
      <n-card title="上传进度" class="h-fit">
        <div v-if="uploadTasks.length === 0" class="text-center text-gray-500 py-8">
          暂无上传任务
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="task in uploadTasks"
            :key="task.id"
            class="border rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="font-medium truncate flex-1 mr-4">{{ task.fileName }}</div>
              <n-tag :type="getTaskStatusType(task.status)" size="small">
                {{ getTaskStatusText(task.status) }}
              </n-tag>
            </div>
            
            <div class="mb-2">
              <n-progress
                :percentage="task.progress"
                :status="task.status === 'failed' ? 'error' : task.status === 'completed' ? 'success' : 'info'"
                :show-indicator="false"
              />
              <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>{{ task.progress }}%</span>
                <span>{{ formatFileSize(task.uploadedSize) }} / {{ formatFileSize(task.totalSize) }}</span>
              </div>
            </div>

            <div v-if="task.error" class="text-red-500 text-sm">
              错误：{{ task.error }}
            </div>

            <div v-if="task.status === 'completed'" class="text-green-600 text-sm">
              上传完成，{{ task.autoProcess ? '正在处理...' : '等待处理' }}
            </div>

            <div class="flex justify-end mt-2">
              <n-button
                v-if="task.status === 'failed'"
                size="small"
                type="primary"
                @click="handleRetryUpload(task)"
              >
                重试
              </n-button>
              <n-button
                v-if="task.status !== 'uploading'"
                size="small"
                @click="handleRemoveTask(task.id)"
              >
                移除
              </n-button>
            </div>
          </div>
        </div>
      </n-card>
    </div>

    <!-- 最近上传 -->
    <n-card title="最近上传" class="mt-6">
      <div class="mb-4 flex justify-between items-center">
        <div class="flex gap-4">
          <n-input
            v-model:value="recentSearch"
            placeholder="搜索文档"
            class="w-80"
          >
            <template #prefix>
              <n-icon><Search /></n-icon>
            </template>
          </n-input>
          <n-select
            v-model:value="recentStatusFilter"
            placeholder="状态筛选"
            :options="statusFilterOptions"
            class="w-40"
          />
        </div>
        <n-button @click="refreshRecentUploads">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </div>

      <n-data-table
        :columns="recentColumns"
        :data="filteredRecentUploads"
        :loading="recentLoading"
        :pagination="recentPagination"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, onUnmounted, reactive, ref} from 'vue'
import {useRoute} from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NProgress,
  NSelect,
  NSwitch,
  NTag,
  NUpload,
  NUploadDragger,
  useMessage
} from 'naive-ui'
import {ArrowBack, CloudUpload, Trash as Delete, Download, Eye, Refresh, Search, CloudUpload as Upload} from '@vicons/ionicons5'
import {useKnowledgeBaseStore} from '~/stores/knowledgeBase'

const route = useRoute()
const message = useMessage()
const knowledgeBaseStore = useKnowledgeBaseStore()

// 响应式数据
const uploadRef = ref()
const fileList = ref([])
const uploading = ref(false)
const uploadTasks = ref([])
const recentUploads = ref([])
const recentLoading = ref(false)
const recentSearch = ref('')
const recentStatusFilter = ref(null)
const knowledgeBase = ref(null)

// 上传设置
const uploadSettings = reactive({
  autoProcess: true,
  chunkStrategy: 'semantic',
  chunkSize: 500,
  chunkOverlap: 50,
  extractGraph: true
})

// 选项数据
const chunkStrategyOptions = [
  { label: '语义分块', value: 'semantic' },
  { label: '固定长度', value: 'fixed' },
  { label: '段落分块', value: 'paragraph' },
  { label: '句子分块', value: 'sentence' }
]

const statusFilterOptions = [
  { label: '全部', value: null },
  { label: '已处理', value: 'processed' },
  { label: '处理中', value: 'processing' },
  { label: '失败', value: 'failed' },
  { label: '等待处理', value: 'pending' }
]

// 表格列配置
const recentColumns = [
  {
    title: '文档名称',
    key: 'name',
    render: (row) => h('div', { class: 'font-medium' }, row.name)
  },
  {
    title: '类型',
    key: 'type',
    render: (row) => h(NTag, { size: 'small' }, { default: () => row.type.toUpperCase() })
  },
  {
    title: '大小',
    key: 'size',
    render: (row) => formatFileSize(row.size)
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        processed: { color: 'success', text: '已处理' },
        processing: { color: 'warning', text: '处理中' },
        failed: { color: 'error', text: '失败' },
        pending: { color: 'info', text: '等待处理' }
      }
      const status = statusMap[row.status] || { color: 'default', text: '未知' }
      return h(NTag, { type: status.color }, { default: () => status.text })
    }
  },
  {
    title: '上传时间',
    key: 'created_at',
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h('div', { class: 'flex gap-2' }, [
      h(NButton, {
        size: 'small',
        onClick: () => handleViewDocument(row)
      }, { default: () => '查看', icon: () => h(NIcon, null, { default: () => h(Eye) }) }),
      h(NButton, {
        size: 'small',
        onClick: () => handleDownloadDocument(row)
      }, { default: () => '下载', icon: () => h(NIcon, null, { default: () => h(Download) }) }),
      h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => handleDeleteDocument(row)
      }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(Delete) }) })
    ])
  }
]

// 分页配置
const recentPagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 计算属性
const filteredRecentUploads = computed(() => {
  let result = recentUploads.value
  
  if (recentSearch.value) {
    result = result.filter(doc => 
      doc.name.toLowerCase().includes(recentSearch.value.toLowerCase())
    )
  }
  
  if (recentStatusFilter.value) {
    result = result.filter(doc => doc.status === recentStatusFilter.value)
  }
  
  return result
})

// 工具函数
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getTaskStatusType = (status) => {
  const statusMap = {
    uploading: 'info',
    completed: 'success',
    failed: 'error',
    processing: 'warning'
  }
  return statusMap[status] || 'default'
}

const getTaskStatusText = (status) => {
  const statusMap = {
    uploading: '上传中',
    completed: '已完成',
    failed: '失败',
    processing: '处理中'
  }
  return statusMap[status] || '未知'
}

// 事件处理函数
const handleFileListUpdate = (files) => {
  fileList.value = files
}

const handleBeforeUpload = (data) => {
  const { file } = data
  
  // 检查文件类型
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/markdown',
    'text/html',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json'
  ]
  
  if (!allowedTypes.includes(file.type) && !file.name.match(/\.(txt|md|html|csv|json)$/i)) {
    message.error(`不支持的文件类型：${file.name}`)
    return false
  }
  
  // 检查文件大小
  if (file.size > 100 * 1024 * 1024) {
    message.error(`文件过大：${file.name}，最大支持 100MB`)
    return false
  }
  
  return true
}

const handleUpload = async ({ file, onProgress, onFinish, onError }) => {
  const taskId = Date.now() + Math.random()
  const task = {
    id: taskId,
    fileName: file.name,
    status: 'uploading',
    progress: 0,
    uploadedSize: 0,
    totalSize: file.size,
    autoProcess: uploadSettings.autoProcess,
    error: null
  }
  
  uploadTasks.value.push(task)
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('knowledge_base_id', route.params.id)
    formData.append('auto_process', uploadSettings.autoProcess)
    formData.append('chunk_strategy', uploadSettings.chunkStrategy)
    formData.append('chunk_size', uploadSettings.chunkSize)
    formData.append('chunk_overlap', uploadSettings.chunkOverlap)
    formData.append('extract_graph', uploadSettings.extractGraph)
    
    const response = await knowledgeBaseStore.uploadDocument(formData, (progressEvent) => {
      const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      task.progress = progress
      task.uploadedSize = progressEvent.loaded
      onProgress({ percent: progress })
    })
    
    task.status = 'completed'
    task.progress = 100
    onFinish()
    message.success(`文件 ${file.name} 上传成功`)
    
    // 刷新最近上传列表
    await refreshRecentUploads()
    
  } catch (error) {
    task.status = 'failed'
    task.error = error.message || '上传失败'
    onError()
    message.error(`文件 ${file.name} 上传失败：${task.error}`)
  }
}

const handleBatchUpload = () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件')
    return
  }
  
  uploading.value = true
  uploadRef.value?.submit()
  
  // 监听所有上传任务完成
  const checkAllCompleted = () => {
    const allCompleted = uploadTasks.value.every(task => 
      task.status === 'completed' || task.status === 'failed'
    )
    
    if (allCompleted) {
      uploading.value = false
      const successCount = uploadTasks.value.filter(task => task.status === 'completed').length
      const failedCount = uploadTasks.value.filter(task => task.status === 'failed').length
      
      if (failedCount === 0) {
        message.success(`所有文件上传成功 (${successCount}/${uploadTasks.value.length})`)
      } else {
        message.warning(`上传完成：成功 ${successCount} 个，失败 ${failedCount} 个`)
      }
    } else {
      setTimeout(checkAllCompleted, 1000)
    }
  }
  
  setTimeout(checkAllCompleted, 1000)
}

const handleClearAll = () => {
  fileList.value = []
  uploadRef.value?.clear()
}

const handleRetryUpload = (task) => {
  // 重试上传逻辑
  const file = fileList.value.find(f => f.name === task.fileName)
  if (file) {
    task.status = 'uploading'
    task.progress = 0
    task.error = null
    // 重新触发上传
    handleUpload({
      file: file.file,
      onProgress: (progress) => {
        task.progress = progress.percent
      },
      onFinish: () => {
        task.status = 'completed'
      },
      onError: () => {
        task.status = 'failed'
      }
    })
  }
}

const handleRemoveTask = (taskId) => {
  const index = uploadTasks.value.findIndex(task => task.id === taskId)
  if (index > -1) {
    uploadTasks.value.splice(index, 1)
  }
}

const handleViewDocument = (document) => {
  window.open(`/api/documents/${document.id}/view`, '_blank')
}

const handleDownloadDocument = (document) => {
  window.open(`/api/documents/${document.id}/download`, '_blank')
}

const handleDeleteDocument = async (document) => {
  const confirmed = await new Promise(resolve => {
    const dialog = window.$dialog.warning({
      title: '确认删除',
      content: `确定要删除文档"${document.name}"吗？`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false)
    })
  })
  
  if (confirmed) {
    try {
      await knowledgeBaseStore.deleteDocument(document.id)
      message.success('删除成功')
      await refreshRecentUploads()
    } catch (error) {
      message.error('删除失败')
    }
  }
}

const refreshRecentUploads = async () => {
  recentLoading.value = true
  try {
    recentUploads.value = await knowledgeBaseStore.getRecentUploads(route.params.id)
  } catch (error) {
    message.error('加载最近上传失败')
  } finally {
    recentLoading.value = false
  }
}

// 数据加载
const loadKnowledgeBase = async () => {
  try {
    knowledgeBase.value = await knowledgeBaseStore.getKnowledgeBase(route.params.id)
  } catch (error) {
    message.error('加载知识库信息失败')
  }
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadKnowledgeBase(),
    refreshRecentUploads()
  ])
})

// 定期刷新上传任务状态
let statusInterval
onMounted(() => {
  statusInterval = setInterval(() => {
    if (uploadTasks.value.some(task => task.status === 'uploading' || task.status === 'processing')) {
      // 更新任务状态
    }
  }, 2000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.n-upload-dragger {
  padding: 2rem;
}
</style>
