<template>
  <CommonPage show-footer title="文件管理">
    <!-- 面包屑导航 -->
    <template #header>
      <div class="page-header">
        <div class="header-content">
          <n-breadcrumb>
            <n-breadcrumb-item @click="$router.push({ name: 'AiServiceKnowledge' })">
              <n-button text>知识库管理</n-button>
            </n-breadcrumb-item>
            <n-breadcrumb-item>{{ knowledgeBaseName }}</n-breadcrumb-item>
          </n-breadcrumb>
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
          <n-upload
            ref="uploadRef"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-before-upload="beforeUpload"
            :on-finish="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-progress="handleUploadProgress"
            :show-file-list="false"
            multiple
          >
            <n-button type="primary">
              <template #icon>
                <TheIcon icon="material-symbols:upload" />
              </template>
              上传文件
            </n-button>
          </n-upload>
        </div>
      </div>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getData"
    >
      <template #queryBar>
        <QueryBarItem label="搜索" :label-width="50">
          <n-input
            v-model:value="queryItems.search"
            clearable
            type="text"
            placeholder="搜索文件名"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="文件类型" :label-width="60">
          <n-select
            v-model:value="queryItems.file_type"
            clearable
            placeholder="选择类型"
            :options="fileTypeOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="处理状态" :label-width="60">
          <n-select
            v-model:value="queryItems.status"
            clearable
            placeholder="选择状态"
            :options="statusOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 上传进度对话框 -->
    <n-modal
      v-model:show="uploadDialogVisible"
      title="文件上传"
      preset="dialog"
      style="width: 500px"
      :mask-closable="false"
    >
      <div v-for="(upload, index) in uploadList" :key="index" class="upload-item">
        <div class="upload-info">
          <span class="filename">{{ upload.filename }}</span>
          <n-tag :type="getUploadStatusType(upload.status)" size="small">
            {{ upload.statusText }}
          </n-tag>
        </div>
        <n-progress
          v-if="upload.status === 'uploading'"
          :percentage="upload.progress"
          :height="6"
          style="margin-top: 8px"
        />
      </div>

      <template #action>
        <n-button @click="uploadDialogVisible = false">关闭</n-button>
      </template>
    </n-modal>
  </CommonPage>
</template>

<script setup>
import { h, ref, reactive, onMounted, computed, resolveDirective, withDirectives } from 'vue'
import { useRoute } from 'vue-router'
import {
  NButton,
  NTag,
  NSpace,
  NPopconfirm,
  NModal,
  NProgress,
  NUpload,
  NBreadcrumb,
  NBreadcrumbItem,
  useMessage,
  useDialog
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon, formatDate } from '@/utils'
import api from '@/api'

defineOptions({ name: '文件管理' })

const route = useRoute()
const message = useMessage()
const dialog = useDialog()
const $table = ref(null)
const queryItems = ref({})

// 知识库信息
const kbId = computed(() => route.params.kbId)
const knowledgeBaseName = computed(() => route.query.name || '知识库')

// 上传相关
const uploadRef = ref()
const uploadDialogVisible = ref(false)
const uploadList = ref([])
const statistics = ref(null)

const uploadUrl = computed(() => `/api/v1/knowledge/files/${kbId.value}/upload`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

// 选项数据
const fileTypeOptions = ref([])
const statusOptions = [
  { label: '等待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '处理失败', value: 'failed' }
]

// 表格列定义
const columns = [
  {
    title: '文件名',
    key: 'original_name',
    width: 250,
    render(row) {
      return h('div', { class: 'file-info' }, [
        h(TheIcon, {
          icon: getFileIcon(row.file_type),
          size: 20,
          style: { marginRight: '8px', color: getFileIconColor(row.file_type) }
        }),
        h('div', { class: 'file-details' }, [
          h('div', { class: 'file-name' }, row.original_name),
          h('div', { class: 'file-meta' }, formatFileSize(row.file_size))
        ])
      ])
    }
  },
  {
    title: '类型',
    key: 'file_type',
    width: 80,
    render(row) {
      return h(NTag, { size: 'small' }, { default: () => row.file_type.toUpperCase() })
    }
  },
  {
    title: '处理状态',
    key: 'embedding_status',
    width: 120,
    render(row) {
      return h(NTag, {
        type: getStatusType(row.embedding_status),
        size: 'small'
      }, { default: () => getStatusText(row.embedding_status) })
    }
  },
  {
    title: '分块数',
    key: 'chunk_count',
    width: 80,
    render(row) {
      return row.chunk_count || '-'
    }
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 150,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    render(row) {
      const actions = []

      if (row.embedding_status === 'failed') {
        actions.push(
          h(NButton, {
            size: 'small',
            type: 'warning',
            style: 'margin-right: 8px;',
            onClick: () => retryProcessing(row)
          }, { default: () => '重试' })
        )
      }

      actions.push(
        h(NPopconfirm, {
          onPositiveClick: () => deleteFile(row)
        }, {
          trigger: () => h(NButton, {
            size: 'small',
            type: 'error'
          }, { default: () => '删除' }),
          default: () => '确定要删除这个文件吗？'
        })
      )

      return h(NSpace, {}, { default: () => actions })
    }
  }
]

// 获取数据的函数
const getData = (params) => {
  return api.knowledgeFile.getList(kbId.value, params)
}

// 上传前检查
const beforeUpload = (file) => {
  // 检查文件大小（50MB）
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    message.error('文件大小不能超过50MB')
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
const handleUploadProgress = (event) => {
  const uploadItem = uploadList.value[uploadList.value.length - 1]
  if (uploadItem) {
    uploadItem.progress = Math.round(event.percent || 0)
  }
}

// 上传成功
const handleUploadSuccess = (response) => {
  const uploadItem = uploadList.value[uploadList.value.length - 1]
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
  $table.value?.handleSearch()
  loadStatistics()
}

// 上传失败
const handleUploadError = (error) => {
  const uploadItem = uploadList.value[uploadList.value.length - 1]
  if (uploadItem) {
    uploadItem.status = 'error'
    uploadItem.statusText = '上传失败'
  }
  message.error('文件上传失败')
}

// 重试处理
const retryProcessing = async (file) => {
  try {
    const response = await api.knowledgeFile.retry(file.id)
    if (response.code === 200) {
      message.success('已重新提交处理')
      $table.value?.handleSearch()
    }
  } catch (error) {
    message.error('重试失败')
  }
}

// 删除文件
const deleteFile = async (file) => {
  try {
    const response = await api.knowledgeFile.delete(file.id)
    if (response.code === 200) {
      message.success('删除成功')
      $table.value?.handleSearch()
      loadStatistics()
    }
  } catch (error) {
    message.error('删除失败')
}

// 加载文件类型
const loadFileTypes = async () => {
  try {
    const response = await api.knowledgeFile.getTypes()
    if (response.code === 200) {
      fileTypeOptions.value = response.data.map(type => ({
        label: type.label,
        value: type.value
      }))
    }
  } catch (error) {
    console.error('加载文件类型失败:', error)
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await api.knowledgeFile.getStatistics(kbId.value)
    if (response.code === 200) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 工具函数
const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'error'
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

const getUploadStatusType = (status) => {
  const typeMap = {
    uploading: 'info',
    success: 'success',
    error: 'error'
  }
  return typeMap[status] || 'info'
}

const getFileIcon = (fileType) => {
  const iconMap = {
    pdf: 'material-symbols:picture-as-pdf',
    docx: 'material-symbols:description',
    txt: 'material-symbols:text-snippet',
    md: 'material-symbols:markdown',
    jpg: 'material-symbols:image',
    png: 'material-symbols:image',
    jpeg: 'material-symbols:image'
  }
  return iconMap[fileType] || 'material-symbols:insert-drive-file'
}

const getFileIconColor = (fileType) => {
  const colorMap = {
    pdf: '#ff4757',
    docx: '#2f5bea',
    txt: '#5f27cd',
    md: '#00d2d3',
    jpg: '#ff9ff3',
    png: '#ff9ff3',
    jpeg: '#ff9ff3'
  }
  return colorMap[fileType] || '#666'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 生命周期
onMounted(() => {
  loadFileTypes()
  loadStatistics()
})
</script>

<style scoped>
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
  color: #18a058;
}

.file-info {
  display: flex;
  align-items: center;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.file-meta {
  font-size: 12px;
  color: #666;
}

.upload-item {
  margin-bottom: 16px;
}

.upload-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.filename {
  font-weight: 500;
}
</style>
