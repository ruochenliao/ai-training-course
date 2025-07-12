<template>
  <n-modal 
    v-model:show="visible" 
    preset="card" 
    :title="`文件管理 - ${knowledgeBase?.name || '知识库'}`"
    style="width: 90%; max-width: 1200px;"
    :mask-closable="false"
  >
    <template #header-extra>
      <n-space>
        <n-button @click="loadStatistics">
          <template #icon>
            <TheIcon icon="material-symbols:analytics" />
          </template>
          统计信息
        </n-button>
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
      </n-space>
    </template>

    <!-- 统计信息 -->
    <div v-if="statistics" class="mb-4">
      <n-card size="small">
        <n-grid :cols="4" :x-gap="16">
          <n-grid-item>
            <n-statistic label="总文件数" :value="statistics.total_files" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="总大小" :value="formatFileSize(statistics.total_size)" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="处理中" :value="statistics.processing_files" />
          </n-grid-item>
          <n-grid-item>
            <n-statistic label="处理完成" :value="statistics.completed_files" />
          </n-grid-item>
        </n-grid>
      </n-card>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadList.length > 0" class="mb-4">
      <n-card size="small" title="上传进度">
        <div v-for="item in uploadList" :key="item.filename" class="upload-item">
          <div class="upload-info">
            <span>{{ item.filename }}</span>
            <span class="upload-status">{{ item.status }}</span>
          </div>
          <n-progress 
            :percentage="item.progress" 
            :status="item.status === '上传失败' ? 'error' : 'info'"
          />
        </div>
      </n-card>
    </div>

    <!-- 文件列表 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getData"
      :scroll-x="1200"
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
  </n-modal>
</template>

<script setup>
import {computed, h, ref, watch} from 'vue'
import {
  NButton,
  NCard,
  NGrid,
  NGridItem,
  NInput,
  NModal,
  NPopconfirm,
  NProgress,
  NSelect,
  NSpace,
  NStatistic,
  NTag,
  NUpload,
  useMessage
} from 'naive-ui'

import CrudTable from '@/components/table/CrudTable.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import {formatDate, formatFileSize, getToken} from '@/utils'
import api from '@/api'

defineOptions({ name: 'FileManagementModal' })

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  knowledgeBase: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:show'])

const visible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const message = useMessage()
const $table = ref(null)
const queryItems = ref({})
const uploadRef = ref()
const uploadList = ref([])
const statistics = ref(null)

// 上传配置
const uploadUrl = computed(() => {
  if (!props.knowledgeBase?.id) return ''
  const baseURL = import.meta.env.VITE_BASE_API || '/api/v1'
  return `${baseURL}/knowledge/${props.knowledgeBase.id}/files`
})

const uploadHeaders = computed(() => ({
  'token': getToken()
}))

// 文件类型选项
const fileTypeOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word文档', value: 'docx' },
  { label: '文本文件', value: 'txt' },
  { label: 'Markdown', value: 'md' },
  { label: '图片', value: 'image' }
]

// 状态选项
const statusOptions = [
  { label: '等待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '处理完成', value: 'completed' },
  { label: '处理失败', value: 'failed' }
]

// 表格列定义
const columns = [
  {
    title: '文件名',
    key: 'name',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '文件类型',
    key: 'file_type',
    width: 100,
    render(row) {
      const typeMap = {
        pdf: 'PDF',
        docx: 'Word',
        txt: '文本',
        md: 'Markdown',
        jpg: '图片',
        png: '图片'
      }
      return typeMap[row.file_type] || row.file_type
    }
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 100,
    render(row) {
      return formatFileSize(row.file_size)
    }
  },
  {
    title: '处理状态',
    key: 'embedding_status',
    width: 120,
    render(row) {
      const statusMap = {
        pending: { text: '等待处理', type: 'default' },
        processing: { text: '处理中', type: 'info' },
        completed: { text: '处理完成', type: 'success' },
        failed: { text: '处理失败', type: 'error' }
      }
      const status = statusMap[row.embedding_status] || { text: row.embedding_status, type: 'default' }
      return h(NTag, { type: status.type }, { default: () => status.text })
    }
  },
  {
    title: '分块数量',
    key: 'chunk_count',
    width: 100
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 160,
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
  if (!props.knowledgeBase?.id) return Promise.resolve({ data: [], total: 0 })
  return api.getKnowledgeFileList(props.knowledgeBase.id, params)
}

// 加载统计信息
const loadStatistics = async () => {
  if (!props.knowledgeBase?.id) return
  
  try {
    const response = await api.getKnowledgeFileStatistics(props.knowledgeBase.id)
    if (response.code === 200) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
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
    progress: 0,
    status: '准备上传'
  })

  return true
}

// 上传进度
const handleUploadProgress = (event) => {
  const progress = Math.round((event.loaded / event.total) * 100)
  const item = uploadList.value.find(item => item.filename === event.file?.name)
  if (item) {
    item.progress = progress
    item.status = '上传中'
  }
}

// 上传成功
const handleUploadSuccess = (response) => {
  const filename = response.file?.name
  const item = uploadList.value.find(item => item.filename === filename)
  
  if (item) {
    if (response.response?.code === 200) {
      item.progress = 100
      item.status = '上传成功'
      message.success(`文件 ${filename} 上传成功`)
    } else {
      item.status = '上传失败'
      message.error(`文件 ${filename} 上传失败: ${response.response?.msg || '未知错误'}`)
    }
  }

  // 刷新列表和统计
  $table.value?.handleSearch()
  loadStatistics()

  // 3秒后清除上传记录
  setTimeout(() => {
    const index = uploadList.value.findIndex(item => item.filename === filename)
    if (index > -1) {
      uploadList.value.splice(index, 1)
    }
  }, 3000)
}

// 上传失败
const handleUploadError = (error) => {
  const filename = error.file?.name
  const item = uploadList.value.find(item => item.filename === filename)
  
  if (item) {
    item.status = '上传失败'
    message.error(`文件 ${filename} 上传失败`)
  }
}

// 重试处理
const retryProcessing = async (file) => {
  try {
    // TODO: 实现重试处理API
    message.info('重试功能暂未实现')
  } catch (error) {
    message.error('重试失败')
  }
}

// 删除文件
const deleteFile = async (file) => {
  try {
    const response = await api.deleteKnowledgeFile(file.id)
    if (response.code === 200) {
      message.success('删除成功')
      $table.value?.handleSearch()
      loadStatistics()
    }
  } catch (error) {
    message.error('删除失败')
  }
}

// 监听弹窗显示状态
watch(() => props.show, (show) => {
  if (show && props.knowledgeBase?.id) {
    // 重置查询条件
    queryItems.value = {}
    // 加载统计信息
    loadStatistics()
    // 刷新表格
    setTimeout(() => {
      $table.value?.handleSearch()
    }, 100)
  }
})
</script>

<style scoped>
.upload-item {
  margin-bottom: 12px;
}

.upload-item:last-child {
  margin-bottom: 0;
}

.upload-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.upload-status {
  font-size: 12px;
  color: #666;
}
</style>
