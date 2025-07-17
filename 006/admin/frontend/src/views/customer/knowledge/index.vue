<template>
  <CommonPage show-footer title="知识库管理">
    <template #action>
      <div class="flex gap-2">
        <NButton v-permission="'post/api/v1/knowledge/create'" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建知识库
        </NButton>
        <NButton
          type="success"
          @click="handleQuickUpload"
        >
          <TheIcon icon="material-symbols:upload" :size="18" class="mr-5" />上传文件
        </NButton>
      </div>
    </template>
    <!-- 表格 -->

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getKnowledgeBaseList"
      @onChecked="handleRowKeysChange"
    >
      <template #queryBar>
        <QueryBarItem label="名称" :label-width="40">
          <NInput v-model:value="queryItems.name" clearable type="text" placeholder="请输入知识库名称" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="validateForm"
      >
        <NFormItem label="知识库名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入知识库名称" />
        </NFormItem>
        <NFormItem label="知识库描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            clearable
            type="textarea"
            placeholder="请输入知识库描述"
          />
        </NFormItem>
        <NFormItem label="知识库类型" path="knowledge_type">
          <NSelect v-model:value="modalForm.knowledge_type" :options="knowledgeTypeOptions" />
        </NFormItem>
        <NFormItem label="是否公开" path="is_public">
          <NSwitch v-model:value="modalForm.is_public" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 查看知识库文件 弹窗 -->
    <NModal
      v-model:show="filesModalVisible"
      style="width: 80%"
      preset="card"
      title="知识库文件"
      size="huge"
      :bordered="false"
      :mask-closable="false"
    >
      <div class="mb-4 flex gap-2">
        <NButton
          v-if="currentKnowledgeBase && userStore.userId === currentKnowledgeBase.owner_id"
          type="primary"
          @click="handleUpload"
        >
          <TheIcon icon="material-symbols:upload" :size="18" class="mr-5" />上传文件
        </NButton>
        <NButton @click="loadFiles" :loading="filesLoading">
          <TheIcon icon="material-symbols:refresh" :size="18" class="mr-5" />刷新
        </NButton>
      </div>

      <NDataTable
        remote
        :loading="filesLoading"
        :columns="fileColumns"
        :data="filesData"
        :pagination="filesPagination"
        @update:page="onFilesPageChange"
      />

      <template #footer>
        <div flex justify-end>
          <NButton @click="filesModalVisible = false">关闭</NButton>
        </div>
      </template>
    </NModal>

    <!-- 新增：文件上传 弹窗 -->
    <NModal
      v-model:show="uploadModalVisible"
      style="width: 500px"
      preset="card"
      title="上传文件"
      size="huge"
      :bordered="false"
      :mask-closable="false"
      @close="closeUploadModal"
    >
      <div v-if="selectedKnowledgeBase">
        <!-- 文件上传区域 -->
        <n-upload
          multiple
          directory-dnd
          :max="5"
          :default-upload="false"
          @change="handleFileChange"
          :file-list="fileList"
          :show-file-list="false"
          :before-upload="beforeUpload"
          class="upload-wrapper"
          ref="uploadRef"
          :disabled="isUploading"
        >
          <n-upload-dragger class="upload-dragger">
            <div class="upload-content">
              <n-button type="primary" class="upload-btn">
                <template #icon>
                  <TheIcon icon="material-symbols:upload" :size="18" />
                </template>
                选择文件
              </n-button>
              <div class="upload-tips">支持拖拽文件或点击上传（最多5个）</div>
            </div>
          </n-upload-dragger>
        </n-upload>

        <!-- 文件列表展示 -->
        <div v-if="fileList.length > 0" class="file-list mt-4">
          <n-tag
            v-for="(file, index) in fileList"
            :key="file.id"
            closable
            :type="file.status === 'success' ? 'success' : 'warning'"
            @close="removeFile(index)"
            class="file-tag mb-2"
            :disabled="isUploading"
          >
            <TheIcon :icon="getFileIcon(file.name)" class="file-icon" />
            {{ file.name }}
            <template #icon v-if="file.status === 'uploading'">
              <n-spin size="small" />
            </template>

            <n-progress
              v-if="file.status === 'uploading'"
              type="line"
              :percentage="file.progress || 0"
              :show-indicator="false"
              height="2px"
              class="upload-progress"
            />
          </n-tag>

          <div class="flex justify-between items-center mt-4">
            <n-button
              v-if="fileList.length > 1"
              text
              type="error"
              @click="clearFiles"
              :disabled="isUploading"
            >
              清除全部
            </n-button>
            <n-button
              type="primary"
              @click="handleUploadFiles"
              :loading="isUploading"
              :disabled="fileList.length === 0"
            >
              开始上传
            </n-button>
          </div>
        </div>
      </div>
      <div v-else style="text-align:center;padding:40px 0;">请先选择知识库</div>
    </NModal>

    <!-- 文件上传 弹窗 -->
    <NModal
      v-model:show="testModalVisible"
      style="width: 500px"
      preset="card"
      title="测试上传文件"
      size="huge"
      :bordered="false"
      :mask-closable="false"
    >
      <FileUpload
        :upload-url="`${window.location.origin}/api/v1/knowledge/upload`"
        :form-data="{ knowledge_base_id: selectedKnowledgeBase?.id || 1 }"
        @success="handleUploadSuccess"
        @cancel="closeTestModal"
      />
    </NModal>
  </CommonPage>
</template>

<script setup>
import { h, nextTick, onMounted, onBeforeUnmount, onUnmounted, ref, resolveDirective } from 'vue'
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NPopconfirm,
  NSelect,
  NSwitch,
  NTag,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import FileUpload from '@/components/upload/FileUpload.vue'

import { formatDate } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import { useUserStore } from '@/store'
import { uploadFile } from '@/api/modules/knowledge'

defineOptions({ name: '知识库管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()

// 知识库类型选项
const knowledgeTypeOptions = [
  { label: '智能客服知识库', value: 'customer_service' },
  { label: 'TextSQL知识库', value: 'text_sql' },
  { label: 'RAG知识库', value: 'rag' },
  { label: '文案创作知识库', value: 'content_creation' },
]

// 知识库表单验证规则
const validateForm = {
  name: [
    {
      required: true,
      message: '请输入知识库名称',
      trigger: ['input', 'blur'],
    },
  ],
}

// 知识库CRUD操作
const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '知识库',
  initForm: {
    is_public: false,
    knowledge_type: 'customer_service'
  },
  doCreate: api.createKnowledgeBase,
  doUpdate: api.updateKnowledgeBase,
  doDelete: api.deleteKnowledgeBase,
  refresh: () => $table.value?.handleSearch(),

})

// 知识库表格列定义
const columns = [
  { type: 'selection' },
  { title: 'ID', key: 'id', width: 60 },
  { title: '知识库名称', key: 'name', width: 200 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '知识库类型',
    key: 'knowledge_type',
    width: 150,
    render(row) {
      const typeMap = {
        customer_service: { text: '智能客服知识库', type: 'success' },
        text_sql: { text: 'TextSQL知识库', type: 'info' },
        rag: { text: 'RAG知识库', type: 'warning' },
        content_creation: { text: '文案创作知识库', type: 'error' }
      }
      const type = typeMap[row.knowledge_type] || { text: '未知类型', type: 'default' }

      return h(
        NTag,
        { type: type.type, size: 'small' },
        { default: () => type.text }
      )
    },
  },
  {
    title: '是否公开',
    key: 'is_public',
    width: 100,
    render(row) {
      return h(NSwitch, {
        size: 'small',
        value: row.is_public,
        disabled: true,
      })
    },
  },
  {
    title: '文件数量',
    key: 'files_count',
    width: 100,
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 360,
    fixed: 'right',
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleViewFiles(row),
          },
          { default: () => '查看文件' }
        ),
        // 直接在列表中添加上传文件按钮
        h(
          NButton,
          {
            size: 'small',
            type: 'success',
            onClick: () => handleDirectUpload(row),
            // 只有所有者可以上传
            disabled: row.owner_id !== userStore.userId,
          },
          { default: () => '上传文件' }
        ),
        h(
          NButton,
          {
            size: 'small',
            onClick: () => handleEdit(row),
            // 只有所有者可以编辑
            disabled: row.owner_id !== userStore.userId,
          },
          { default: () => '编辑' }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
          },
          {
            default: () => '确认删除？',
            trigger: () =>
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  // 只有所有者可以删除
                  disabled: row.owner_id !== userStore.userId,
                },
                { default: () => '删除' }
              ),
          }
        ),
      ])
    },
  },
]

// 文件列表相关
const filesModalVisible = ref(false)
const filesLoading = ref(false)
const filesData = ref([])
const filesPagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  pageSizes: [10, 20, 30, 40],
  showSizePicker: true,
  prefix({ itemCount }) {
    return `共 ${itemCount} 个文件`
  },
})
const currentKnowledgeBase = ref(null)

// 新增：记录最近上传的文件名称，用于高亮显示
const recentlyUploadedFiles = ref([])

// 新增：文件状态轮询相关
const pollingTimer = ref(null)
const isPolling = ref(false)
const pollingCount = ref(0) // 轮询次数计数器

// 文件表格列定义
const fileColumns = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '文件名称',
    key: 'name',
    width: 200,
    ellipsis: { tooltip: true },
    render(row) {
      // 判断是否是最近上传的文件，如果是则高亮显示
      const isRecentlyUploaded = recentlyUploadedFiles.value.includes(row.name)

      if (isRecentlyUploaded) {
        return h(
          'div',
          { class: 'flex items-center' },
          [
            h(
              'span',
              { class: 'text-primary font-bold flex items-center' },
              [
                h(TheIcon, { icon: 'material-symbols:new-releases', class: 'mr-1', size: 16 }),
                row.name
              ]
            )
          ]
        )
      }

      return row.name
    }
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 120,
    render(row) {
      return formatFileSize(row.file_size)
    },
  },
  { title: '文件类型', key: 'file_type', width: 150 },
  {
    title: '嵌入状态',
    key: 'embedding_status',
    width: 120,
    render(row) {
      const statusMap = {
        pending: { text: '待处理', type: 'warning' },
        processing: { text: '处理中', type: 'info' },
        completed: { text: '已完成', type: 'success' },
        failed: { text: '失败', type: 'error' }
      }
      const status = statusMap[row.embedding_status] || { text: '未知', type: 'default' }

      // 判断是否是最近上传的文件
      const isRecentlyUploaded = recentlyUploadedFiles.value.includes(row.name)
      const tagProps = {
        type: status.type,
        size: 'small',
        // 如果是最近上传的文件且正在处理中，添加动态效果
        class: isRecentlyUploaded && (row.embedding_status === 'pending' || row.embedding_status === 'processing') ? 'animate-pulse' : ''
      }

      // If status is failed and there's an error message, show it in a tooltip
      if (row.embedding_status === 'failed' && row.embedding_error) {
        return h(
          'div',
          { style: 'display: inline-block', title: row.embedding_error },
          [
            h(
              NTag,
              tagProps,
              { default: () => status.text }
            )
          ]
        )
      }

      return h(
        NTag,
        tagProps,
        { default: () => status.text }
      )
    },
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleDownloadFile(row),
          },
          { default: () => '下载' }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDeleteFile(row),
          },
          {
            default: () => '确认删除？',
            trigger: () =>
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  // 只有所有者可以删除文件
                  disabled: currentKnowledgeBase.value?.owner_id !== userStore.userId,
                },
                { default: () => '删除' }
              ),
          }
        ),
      ])
    },
  },
]

// 消息提示
const $message = useMessage()

// 文件上传相关
const uploadModalVisible = ref(false)
const testModalVisible = ref(false)
const selectedKnowledgeBase = ref(null)
const uploadRef = ref(null)
const fileList = ref([])
const isUploading = ref(false)

// 全局加载提示对象，用于在不同函数之间共享
let globalLoadingMessage = null

// 文件类型图标映射
const FILE_ICONS = {
  pdf: 'mdi:file-pdf',
  doc: 'mdi:file-word',
  docx: 'mdi:file-word',
  xls: 'mdi:file-excel',
  xlsx: 'mdi:file-excel',
  ppt: 'mdi:file-powerpoint',
  pptx: 'mdi:file-powerpoint',
  txt: 'mdi:file-document',
  default: 'mdi:file'
}

// 获取文件图标
const getFileIcon = (fileName) => {
  const extension = fileName.split('.').pop().toLowerCase()
  return FILE_ICONS[extension] || FILE_ICONS.default
}

// 文件大小格式化
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 文件上传前验证
const beforeUpload = ({ file }) => {
  const MAX_SIZE = 10 * 1024 * 1024 // 10MB
  const ALLOWED_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]

  if (file.file.size > MAX_SIZE) {
    window.$message?.error(`${file.name} 超过大小限制（10MB）`)
    return false
  }

  if (!ALLOWED_TYPES.includes(file.file.type)) {
    window.$message?.error(`${file.name} 不支持的文件类型`)
    return false
  }

  return true
}

// 处理文件变化
const handleFileChange = async ({ fileList: newFileList }) => {
  try {
    const updatedList = [...newFileList].slice(0, 5)
    fileList.value = updatedList.map(file => ({
      ...file,
      status: 'pending',
      progress: 0
    }))
  } catch (error) {
    console.error('文件处理失败:', error)
    window.$message?.error('文件处理失败')
  }
}

// 上传单个文件
const uploadSingleFile = async (file) => {
  const formData = new FormData()
  // Check if file.file exists (from naive-ui upload) or fall back to file.raw
  const fileToUpload = file.file || file.raw

  if (!fileToUpload) {
    console.error('No file data found:', file)
    throw new Error('文件数据无效')
  }

  formData.append('file', fileToUpload)
  formData.append('knowledge_base_id', currentKnowledgeBase.value.id)

  console.log('Uploading file:', fileToUpload.name, 'Size:', fileToUpload.size)

  try {
    // 不再为每个文件单独创建加载提示，使用全局提示
    // 更新全局加载提示的文本
    if (globalLoadingMessage && typeof globalLoadingMessage.update === 'function') {
      globalLoadingMessage.update(`正在上传文件 ${file.name}...`)
    }

    const response = await uploadFile(formData, {
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        file.progress = progress
      }
    })

    if (response.code === 200) {
      file.status = 'success'
      // Success message will be shown once all files are uploaded
    } else {
      file.status = 'error'
      $message.error(`文件 ${file.name} 上传失败：${response.msg}`)
    }
  } catch (error) {
    file.status = 'error'

    // 提供更详细的错误信息
    let errorMessage = error.message

    // 处理超时错误
    if (errorMessage.includes('timeout')) {
      errorMessage = '上传超时，请检查文件大小或网络连接'
    }
    // 处理网络错误
    else if (errorMessage.includes('Network Error')) {
      errorMessage = '网络错误，请检查您的网络连接'
    }

    console.error(`文件上传错误:`, error)
    $message.error(`文件 ${file.name} 上传失败：${errorMessage}`)
  }
}

// 开始上传文件
const handleUploadFiles = async () => {
  if (isUploading.value) return
  if (!currentKnowledgeBase.value?.id) {
    $message.warning('请先选择知识库')
    return
  }

  // 显示全局加载提示，并存储到全局变量
  // 先关闭可能存在的之前的提示
  if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
    globalLoadingMessage.destroy()
  }

  // 创建新的加载提示
  globalLoadingMessage = $message.loading('正在准备上传文件...', {
    duration: 0, // 不自动关闭
  })

  isUploading.value = true
  const pendingFiles = fileList.value.filter(f => f.status === 'pending')
  // 记录上传的文件名称，用于后续在文件列表中高亮显示
  const uploadedFileNames = []

  try {
    for (const file of pendingFiles) {
      const index = fileList.value.findIndex(f => f.id === file.id)
      if (index === -1) continue

      // Set initial status and progress
      fileList.value[index].status = 'uploading'
      fileList.value[index].progress = 0

      try {
        await uploadSingleFile(file)
        if (file.status === 'success') {
          uploadedFileNames.push(file.name)
        }
      } catch (error) {
        fileList.value[index].status = 'error'
        $message.error(`文件 ${file.name} 上传失败`)
      }
    }

    const successCount = fileList.value.filter(f => f.status === 'success').length
    const totalCount = fileList.value.length

    if (successCount > 0) {
      // 关闭全局加载提示 - 立即关闭，不等待后台处理
      if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
        globalLoadingMessage.destroy()
        globalLoadingMessage = null
      }

      // 关闭上传窗口
      uploadModalVisible.value = false
      fileList.value = []

      // 记录新上传的文件名称，用于高亮显示
      recentlyUploadedFiles.value = uploadedFileNames

      // 显示成功提示，并说明文件已交由后台处理
      if (successCount === totalCount) {
        $message.success('所有文件上传成功，已交由后台转换处理', {
          duration: 5000, // 显示5秒
        })
      } else {
        $message.success(`成功上传 ${successCount}/${totalCount} 个文件，已交由后台转换处理`, {
          duration: 5000, // 显示5秒
        })
      }

      // 在后台静默加载文件列表，不打开文件列表窗口
      // 这样用户可以继续操作其他模块
      // 使用 setTimeout 延迟执行，确保不阻塞主线程
      setTimeout(() => {
        // 先加载文件列表
        loadFiles(false).then(() => {
          // 启动定时刷新，监控文件处理状态，但不显示给用户
          startFileStatusPolling()

          // 刷新知识库列表，更新文件数量
          $table.value?.handleSearch()
        })
      }, 100) // 延迟 100 毫秒执行，确保不阻塞主线程
    }
  } catch (error) {
    console.error('文件上传过程出错:', error)
    $message.error('上传过程出现错误')
  } finally {
    // 关闭全局加载提示
    if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
      globalLoadingMessage.destroy()
      globalLoadingMessage = null // 清空全局变量
    }
    isUploading.value = false
  }
}

// 移除文件
const removeFile = (index) => {
  if (isUploading.value) return
  fileList.value.splice(index, 1)
}

// 清除所有文件
const clearFiles = () => {
  if (isUploading.value) return
  fileList.value = []
}

// 关闭上传模态框
const closeUploadModal = () => {
  if (isUploading.value) {
    $message.warning('文件正在上传中，请等待上传完成')
    return
  }

  // 关闭全局加载提示
  if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
    globalLoadingMessage.destroy()
    globalLoadingMessage = null
  }

  uploadModalVisible.value = false
  fileList.value = []
}

// 查看知识库文件
async function handleViewFiles(row) {
  currentKnowledgeBase.value = row
  filesModalVisible.value = true
  filesPagination.value.page = 1
  await loadFiles()
}

// 加载文件列表
async function loadFiles(showLoading = true) {
  if (!currentKnowledgeBase.value) return

  if (showLoading) {
    filesLoading.value = true
  }

  try {
    const res = await api.getKnowledgeFiles({
      knowledge_base_id: currentKnowledgeBase.value.id,
      page: filesPagination.value.page,
      page_size: filesPagination.value.pageSize,
    })
    filesData.value = res.data
    filesPagination.value.itemCount = res.total

    // 检查是否有文件正在处理中
    const hasProcessingFiles = res.data.some(file =>
      file.embedding_status === 'pending' || file.embedding_status === 'processing'
    )

    // 如果有文件正在处理中，继续轮询
    if (hasProcessingFiles && !isPolling.value) {
      startFileStatusPolling()
    } else if (!hasProcessingFiles && isPolling.value) {
      stopFileStatusPolling()
    }

    return res.data
  } catch (error) {
    console.error('Failed to load files:', error)
    return []
  } finally {
    if (showLoading) {
      filesLoading.value = false
    }
  }
}

// 启动文件状态轮询
function startFileStatusPolling() {
  if (isPolling.value) return

  isPolling.value = true
  console.log('启动文件状态轮询')

  // 每5秒轮询一次，不显示加载状态
  pollingTimer.value = setInterval(async () => {
    // 即使文件列表窗口关闭，也继续在后台轮询
    // 这样当用户再次打开文件列表时，可以看到最新状态

    // 不显示加载状态，防止闪烁
    const updatedFiles = await loadFiles(false)

    // 检查是否所有文件处理完成
    const allCompleted = updatedFiles.every(file =>
      file.embedding_status === 'completed' || file.embedding_status === 'failed'
    )

    if (allCompleted) {
      console.log('所有文件处理完成，停止轮询')
      stopFileStatusPolling() // 这会自动刷新知识库列表

      // 显示文件处理完成的提示
      $message.success('文件处理完成', { duration: 3000 })
    }

    // 设置最大轮询次数，防止无限轮询
    // 如果轮询超过 10 分钟，则停止轮询
    if (pollingCount.value >= 120) { // 5秒一次，120次大约是10分钟
      console.log('轮询超时，停止轮询')
      stopFileStatusPolling()
      return
    }

    pollingCount.value++
  }, 5000) // 每5秒轮询一次
}

// 停止文件状态轮询
function stopFileStatusPolling() {
  if (!isPolling.value) return

  console.log('停止文件状态轮询')
  clearInterval(pollingTimer.value)
  pollingTimer.value = null
  isPolling.value = false
  pollingCount.value = 0 // 重置轮询计数器

  // 在轮询结束时刷新知识库列表，确保文件数量是最新的
  $table.value?.handleSearch()
}

// 文件列表分页变化
async function onFilesPageChange(page) {
  filesPagination.value.page = page
  await loadFiles()
}

// 下载文件
function handleDownloadFile(file) {
  if (file.download_url) {
    window.open(file.download_url, '_blank')
  } else {
    $message.error('下载链接不可用')
  }
}

// 删除文件
async function handleDeleteFile(file) {
  try {
    await api.deleteKnowledgeFile({ id: file.id })
    $message.success('文件删除成功')
    await loadFiles()
  } catch (error) {
    console.error('Failed to delete file:', error)
    $message.error('文件删除失败')
  }
}

// 打开上传文件弹窗
function handleUpload() {
  if (!currentKnowledgeBase.value) {
    $message.warning('请先选择知识库')
    return
  }
  selectedKnowledgeBase.value = currentKnowledgeBase.value
  uploadModalVisible.value = true
}

// 直接从列表打开上传文件弹窗
function handleDirectUpload(row) {
  selectedKnowledgeBase.value = row
  currentKnowledgeBase.value = row
  uploadModalVisible.value = true
}

// 从顶部按钮打开上传文件弹窗
function handleQuickUpload() {
  if (!selectedKnowledgeBase.value) {
    $message.warning('请先选择知识库')
    return
  }
  currentKnowledgeBase.value = selectedKnowledgeBase.value
  uploadModalVisible.value = true
}

// 上传成功回调
async function handleUploadSuccess() {
  // 立即关闭所有相关窗口
  uploadModalVisible.value = false
  testModalVisible.value = false
  fileList.value = []

  // 关闭全局加载提示
  if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
    globalLoadingMessage.destroy()
    globalLoadingMessage = null // 清空全局变量
  }

  // 显示成功提示，并说明文件已交由后台处理
  $message.success('文件上传成功，已交由后台转换处理', {
    duration: 5000, // 显示5秒
  })

  // 在后台静默加载文件列表，不打开文件列表窗口
  // 这样用户可以继续操作其他模块
  // 使用 setTimeout 延迟执行，确保不阻塞主线程
  setTimeout(() => {
    // 先加载文件列表
    loadFiles(false).then(() => {
      // 启动定时刷新，监控文件处理状态，但不显示给用户
      startFileStatusPolling()

      // 刷新知识库列表，更新文件数量
      $table.value?.handleSearch()
    })
  }, 100) // 延迟 100 毫秒执行，确保不阻塞主线程
}

// 关闭测试模态框
function closeTestModal() {
  testModalVisible.value = false
}

// 处理表格行选中变化
function handleRowKeysChange(keys) {
  console.log('Selected row keys:', keys)
  if (keys && keys.length > 0) {
    // 获取选中的知识库
    const selectedId = keys[0]
    const tableDataArr = $table.value?.tableData?.value || []
    const selectedRow = tableDataArr.find(row => row.id === selectedId)
    if (selectedRow) {
      selectedKnowledgeBase.value = selectedRow
      console.log('Selected knowledge base:', selectedKnowledgeBase.value)
    }
  } else {
    selectedKnowledgeBase.value = null
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

// 清理轮询定时器

onBeforeUnmount(() => {
  stopFileStatusPolling()

  // 清理全局加载提示
  if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
    globalLoadingMessage.destroy()
    globalLoadingMessage = null
  }
})

onUnmounted(() => {
  stopFileStatusPolling()

  // 清理全局加载提示
  if (globalLoadingMessage && typeof globalLoadingMessage.destroy === 'function') {
    globalLoadingMessage.destroy()
    globalLoadingMessage = null
  }
})
</script>

<style scoped>
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
