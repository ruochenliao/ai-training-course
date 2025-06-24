<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">文档管理</h1>
      <n-button type="primary" @click="showUploadModal = true">
        <template #icon>
          <n-icon><CloudUpload /></n-icon>
        </template>
        上传文档
      </n-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="mb-6 flex gap-4">
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索文档名称或内容"
        class="flex-1"
        @input="handleSearch"
      >
        <template #prefix>
          <n-icon><Search /></n-icon>
        </template>
      </n-input>
      <n-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        :options="statusOptions"
        class="w-40"
        @update:value="handleFilter"
      />
      <n-select
        v-model:value="knowledgeBaseFilter"
        placeholder="知识库筛选"
        :options="knowledgeBaseOptions"
        class="w-48"
        @update:value="handleFilter"
      />
      <n-button @click="refreshData">
        <template #icon>
          <n-icon><Refresh /></n-icon>
        </template>
        刷新
      </n-button>
    </div>

    <!-- 文档列表 -->
    <n-data-table
      :columns="columns"
      :data="filteredDocuments"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      @update:checked-row-keys="handleCheck"
    />

    <!-- 批量操作 -->
    <div v-if="checkedRowKeys.length > 0" class="mt-4 flex gap-2">
      <n-button type="error" @click="handleBatchDelete">
        批量删除 ({{ checkedRowKeys.length }})
      </n-button>
      <n-button @click="handleBatchReprocess">
        批量重新处理
      </n-button>
      <n-button @click="handleBatchDownload">
        批量下载
      </n-button>
    </div>

    <!-- 上传文档模态框 -->
    <n-modal v-model:show="showUploadModal" preset="dialog" title="上传文档">
      <div class="space-y-4">
        <n-form-item label="选择知识库">
          <n-select
            v-model:value="uploadForm.knowledgeBaseId"
            :options="knowledgeBaseOptions"
            placeholder="选择目标知识库"
          />
        </n-form-item>
        
        <n-upload
          ref="uploadRef"
          multiple
          :max="10"
          :file-list="uploadFileList"
          @update:file-list="handleUploadFileListUpdate"
          @before-upload="handleBeforeUpload"
        >
          <n-upload-dragger>
            <div class="text-center">
              <n-icon size="48" class="text-gray-400 mb-4">
                <CloudUpload />
              </n-icon>
              <div class="text-lg font-medium mb-2">点击或拖拽文件到此区域上传</div>
              <div class="text-sm text-gray-500">
                支持 PDF、Word、PPT、TXT、Markdown 等格式
              </div>
            </div>
          </n-upload-dragger>
        </n-upload>
      </div>
      
      <template #action>
        <n-button @click="showUploadModal = false">取消</n-button>
        <n-button 
          type="primary" 
          @click="handleUpload" 
          :loading="uploading"
          :disabled="!uploadForm.knowledgeBaseId || uploadFileList.length === 0"
        >
          开始上传
        </n-button>
      </template>
    </n-modal>

    <!-- 文档详情模态框 -->
    <n-modal v-model:show="showDetailModal" preset="dialog" title="文档详情" style="width: 800px">
      <div v-if="selectedDocument" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文档名称</label>
            <div class="text-sm text-gray-900">{{ selectedDocument.name }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文件类型</label>
            <n-tag size="small">{{ selectedDocument.type.toUpperCase() }}</n-tag>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文件大小</label>
            <div class="text-sm text-gray-900">{{ formatFileSize(selectedDocument.size) }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">处理状态</label>
            <n-tag :type="getStatusType(selectedDocument.status)">
              {{ getStatusText(selectedDocument.status) }}
            </n-tag>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">所属知识库</label>
            <div class="text-sm text-gray-900">{{ selectedDocument.knowledge_base_name }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">上传时间</label>
            <div class="text-sm text-gray-900">{{ new Date(selectedDocument.created_at).toLocaleString() }}</div>
          </div>
        </div>
        
        <div v-if="selectedDocument.chunks_count">
          <label class="block text-sm font-medium text-gray-700 mb-1">分块信息</label>
          <div class="text-sm text-gray-900">
            共 {{ selectedDocument.chunks_count }} 个分块，
            平均长度 {{ selectedDocument.avg_chunk_length }} 字符
          </div>
        </div>
        
        <div v-if="selectedDocument.processing_error">
          <label class="block text-sm font-medium text-gray-700 mb-1">错误信息</label>
          <div class="text-sm text-red-600 bg-red-50 p-2 rounded">
            {{ selectedDocument.processing_error }}
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NTag,
  NUpload,
  NUploadDragger,
  useMessage
} from 'naive-ui'
import {
  CloudUpload,
  Download,
  Eye,
  Refresh,
  Search,
  Trash as Delete
} from '@vicons/ionicons5'
import { useDocumentStore } from '~/stores/document'
import { useKnowledgeBaseStore } from '~/stores/knowledgeBase'

const message = useMessage()
const documentStore = useDocumentStore()
const knowledgeBaseStore = useKnowledgeBaseStore()

// 响应式数据
const loading = ref(false)
const uploading = ref(false)
const searchQuery = ref('')
const statusFilter = ref(null)
const knowledgeBaseFilter = ref(null)
const checkedRowKeys = ref([])
const showUploadModal = ref(false)
const showDetailModal = ref(false)
const selectedDocument = ref(null)
const uploadRef = ref()
const uploadFileList = ref([])

// 上传表单
const uploadForm = reactive({
  knowledgeBaseId: null
})

// 选项数据
const statusOptions = [
  { label: '全部', value: null },
  { label: '已处理', value: 'processed' },
  { label: '处理中', value: 'processing' },
  { label: '失败', value: 'failed' },
  { label: '等待处理', value: 'pending' }
]

// 知识库选项
const knowledgeBaseOptions = computed(() => [
  { label: '全部知识库', value: null },
  ...knowledgeBaseStore.knowledgeBases.map(kb => ({
    label: kb.name,
    value: kb.id
  }))
])

// 表格列配置
const columns = [
  { type: 'selection' },
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
    render: (row) => h(NTag, { type: getStatusType(row.status) }, { default: () => getStatusText(row.status) })
  },
  {
    title: '知识库',
    key: 'knowledge_base_name',
    ellipsis: { tooltip: true }
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
        onClick: () => handleViewDetail(row)
      }, { default: () => '详情', icon: () => h(NIcon, null, { default: () => h(Eye) }) }),
      h(NButton, {
        size: 'small',
        onClick: () => handleDownload(row)
      }, { default: () => '下载', icon: () => h(NIcon, null, { default: () => h(Download) }) }),
      h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => handleDelete(row)
      }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(Delete) }) })
    ])
  }
]

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 计算属性
const filteredDocuments = computed(() => {
  let result = documentStore.documents
  
  if (searchQuery.value) {
    result = result.filter(doc => 
      doc.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(doc => doc.status === statusFilter.value)
  }
  
  if (knowledgeBaseFilter.value) {
    result = result.filter(doc => doc.knowledge_base_id === knowledgeBaseFilter.value)
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

const getStatusType = (status) => {
  const statusMap = {
    processed: 'success',
    processing: 'warning',
    failed: 'error',
    pending: 'info'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    processed: '已处理',
    processing: '处理中',
    failed: '失败',
    pending: '等待处理'
  }
  return statusMap[status] || '未知'
}

// 事件处理函数
const handleSearch = () => {
  pagination.page = 1
}

const handleFilter = () => {
  pagination.page = 1
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      documentStore.fetchDocuments(),
      knowledgeBaseStore.fetchKnowledgeBases()
    ])
  } catch (error) {
    message.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const handleCheck = (keys: string[]) => {
  checkedRowKeys.value = keys
}

const handleViewDetail = (row: any) => {
  selectedDocument.value = row
  showDetailModal.value = true
}

const handleDownload = async (row: any) => {
  try {
    await documentStore.downloadDocument(row.id)
    message.success('下载开始')
  } catch (error) {
    message.error('下载失败')
  }
}

const handleDelete = async (row: any) => {
  const confirmed = await new Promise(resolve => {
    window.$dialog.warning({
      title: '确认删除',
      content: `确定要删除文档"${row.name}"吗？此操作不可恢复。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false)
    })
  })
  
  if (confirmed) {
    try {
      await documentStore.deleteDocument(row.id)
      message.success('删除成功')
    } catch (error) {
      message.error('删除失败')
    }
  }
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>
