<template>
  <CommonPage show-footer title="知识库管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建知识库
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getKnowledgeBaseList"
    >
      <template #queryBar>
        <QueryBarItem label="知识库名称" :label-width="80">
          <NInput
            v-model:value="queryItems.search"
            clearable
            type="text"
            placeholder="请输入知识库名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="知识库类型" :label-width="80">
          <NSelect
            v-model:value="queryItems.knowledge_type"
            clearable
            placeholder="请选择知识库类型"
            :options="knowledgeTypeOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="访问权限" :label-width="80">
          <NSelect
            v-model:value="queryItems.is_public"
            clearable
            placeholder="请选择访问权限"
            :options="publicOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

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
        :label-width="120"
        :model="modalForm"
        :rules="modalRules"
        :disabled="modalAction === 'view'"
      >
        <NGrid :cols="2" :x-gap="16">
          <NGi>
            <NFormItem label="知识库名称" path="name">
              <NInput v-model:value="modalForm.name" placeholder="请输入知识库名称" />
            </NFormItem>
          </NGi>
          <NGi>
            <NFormItem label="知识库类型" path="knowledge_type">
              <NSelect
                v-model:value="modalForm.knowledge_type"
                placeholder="请选择知识库类型"
                :options="knowledgeTypeOptions"
              />
            </NFormItem>
          </NGi>
        </NGrid>

        <NFormItem label="知识库描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            placeholder="请输入知识库描述"
            :rows="3"
          />
        </NFormItem>

        <NGrid :cols="2" :x-gap="16">
          <NGi>
            <NFormItem label="访问权限" path="is_public">
              <NSelect
                v-model:value="modalForm.is_public"
                placeholder="请选择访问权限"
                :options="publicOptions"
              />
            </NFormItem>
          </NGi>
          <NGi>
            <NFormItem label="嵌入模型" path="embedding_model">
              <NInput v-model:value="modalForm.embedding_model" placeholder="嵌入模型" />
            </NFormItem>
          </NGi>
        </NGrid>

        <NGrid :cols="3" :x-gap="16">
          <NGi>
            <NFormItem label="分块大小" path="chunk_size">
              <NInputNumber
                v-model:value="modalForm.chunk_size"
                placeholder="分块大小"
                :min="100"
                :max="5000"
                class="w-full"
              />
            </NFormItem>
          </NGi>
          <NGi>
            <NFormItem label="分块重叠" path="chunk_overlap">
              <NInputNumber
                v-model:value="modalForm.chunk_overlap"
                placeholder="分块重叠"
                :min="0"
                :max="1000"
                class="w-full"
              />
            </NFormItem>
          </NGi>
          <NGi>
            <NFormItem label="最大文件大小(MB)" path="max_file_size_mb">
              <NInputNumber
                v-model:value="modalForm.max_file_size_mb"
                placeholder="最大文件大小"
                :min="1"
                :max="1000"
                class="w-full"
              />
            </NFormItem>
          </NGi>
        </NGrid>

        <NFormItem label="允许的文件类型" path="allowed_file_types">
          <NSelect
            v-model:value="modalForm.allowed_file_types"
            multiple
            placeholder="请选择允许的文件类型"
            :options="fileTypeOptions"
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 文件管理模态框 -->
    <NModal
      v-model:show="fileModalVisible"
      preset="card"
      title="文件管理"
      class="w-1200px"
      :mask-closable="false"
    >
      <div class="file-management">
        <!-- 文件上传区域 -->
        <div class="upload-section mb-4">
          <NUpload
            ref="uploadRef"
            multiple
            directory-dnd
            :action="`/api/v1/knowledge/files/${currentKnowledgeBase?.id}/upload`"
            :headers="{ token: getToken() }"
            :file-list="fileList"
            @update:file-list="handleFileListChange"
            @finish="handleUploadFinish"
            @error="handleUploadError"
          >
            <NUploadDragger>
              <div style="margin-bottom: 12px">
                <TheIcon icon="material-symbols:cloud-upload" :size="48" />
              </div>
              <NText style="font-size: 16px">
                点击或者拖动文件到该区域来上传
              </NText>
              <NP depth="3" style="margin: 8px 0 0 0">
                支持单个或批量上传。支持的文件类型：{{ currentKnowledgeBase?.allowed_file_types?.join(', ') }}
              </NP>
            </NUploadDragger>
          </NUpload>
        </div>

        <!-- 文件列表 -->
        <div class="file-list">
          <NDataTable
            :columns="fileColumns"
            :data="knowledgeFiles"
            :loading="fileLoading"
            :pagination="filePagination"
            :row-key="(row) => row.id"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <NButton @click="fileModalVisible = false">关闭</NButton>
        </div>
      </template>
    </NModal>
  </CommonPage>
</template>

<script setup lang="ts">
import {h, onMounted, ref, resolveDirective, withDirectives} from 'vue'
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NP,
  NPopconfirm,
  NSelect,
  NTag,
  NText,
  NUpload,
  NUploadDragger,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import {formatDate, renderIcon} from '@/utils'
import {useCRUD} from '@/composables'
import api from '@/api'

defineOptions({ name: '知识库管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

// 文件管理相关
const fileModalVisible = ref(false)
const currentKnowledgeBase = ref(null)
const knowledgeFiles = ref([])
const fileLoading = ref(false)
const fileList = ref([])
const uploadRef = ref(null)

// 文件分页
const filePagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    filePagination.page = page
    loadKnowledgeFiles()
  },
  onUpdatePageSize: (pageSize: number) => {
    filePagination.pageSize = pageSize
    filePagination.page = 1
    loadKnowledgeFiles()
  }
})

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '知识库',
  initForm: {
    name: '',
    description: '',
    knowledge_type: 'general',
    is_public: false,
    max_file_size_mb: 50,
    allowed_file_types: ['pdf', 'docx', 'txt', 'md'],
    embedding_model: 'BAAI/bge-small-zh-v1.5',
    chunk_size: 1024,
    chunk_overlap: 100
  },
  doCreate: api.createKnowledgeBase,
  doUpdate: (data) => api.updateKnowledgeBase(data.id, data),
  doDelete: (data) => api.deleteKnowledgeBase(data.id),
  refresh: () => $table.value?.handleSearch(),
})

// 选项数据
const knowledgeTypeOptions = ref([
  { label: '智能客服知识库', value: 'customer_service' },
  { label: 'TextSQL知识库', value: 'text_sql' },
  { label: 'RAG知识库', value: 'rag' },
  { label: '文案创作知识库', value: 'content_creation' },
  { label: '通用知识库', value: 'general' },
  { label: '技术文档', value: 'technical_docs' },
  { label: '常见问题', value: 'faq' },
  { label: '政策文档', value: 'policy_docs' },
  { label: '产品文档', value: 'product_docs' }
])

const publicOptions = [
  { label: '公开', value: true },
  { label: '私有', value: false }
]

const fileTypeOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word文档', value: 'docx' },
  { label: '文本文件', value: 'txt' },
  { label: 'Markdown', value: 'md' },
  { label: 'Excel', value: 'xlsx' },
  { label: 'PowerPoint', value: 'pptx' }
]

// 获取知识库类型选项
const loadKnowledgeTypes = async () => {
  try {
    const response = await api.getKnowledgeTypes()
    if (response.code === 200) {
      knowledgeTypeOptions.value = response.data
    }
  } catch (error) {
    console.error('获取知识库类型失败:', error)
    // 如果API失败，使用默认选项
  }
}

// 文件管理相关方法
const handleManageFiles = (row) => {
  currentKnowledgeBase.value = row
  fileModalVisible.value = true
  loadKnowledgeFiles()
}

const loadKnowledgeFiles = async () => {
  if (!currentKnowledgeBase.value) return

  fileLoading.value = true
  try {
    const response = await api.getKnowledgeFileList(currentKnowledgeBase.value.id, {
      page: filePagination.page,
      page_size: filePagination.pageSize
    })

    if (response.code === 200) {
      knowledgeFiles.value = response.data
      filePagination.itemCount = response.total
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
    window.$message?.error('获取文件列表失败')
  } finally {
    fileLoading.value = false
  }
}

const handleFileListChange = (files) => {
  fileList.value = files
}

const handleUploadFinish = ({ file, event }) => {
  try {
    const response = JSON.parse(event.target.response)
    if (response.code === 200) {
      window.$message?.success(`文件 ${file.name} 上传成功`)
      loadKnowledgeFiles() // 重新加载文件列表
    } else {
      window.$message?.error(`文件 ${file.name} 上传失败: ${response.msg}`)
    }
  } catch (error) {
    console.error('Upload finish error:', error)
    window.$message?.error(`文件 ${file.name} 上传失败`)
  }
}

const handleUploadError = ({ file, event }) => {
  try {
    if (event?.target?.response) {
      const response = JSON.parse(event.target.response)
      window.$message?.error(`文件 ${file.name} 上传失败: ${response.msg || '未知错误'}`)
    } else {
      window.$message?.error(`文件 ${file.name} 上传失败`)
    }
  } catch (error) {
    console.error('Upload error:', error)
    window.$message?.error(`文件 ${file.name} 上传失败`)
  }
}

const handleDeleteFile = async (file) => {
  try {
    const response = await api.deleteKnowledgeFile(file.id)
    if (response.code === 200) {
      window.$message?.success('文件删除成功')
      loadKnowledgeFiles() // 重新加载文件列表
    } else {
      window.$message?.error(response.msg || '文件删除失败')
    }
  } catch (error) {
    console.error('删除文件失败:', error)
    window.$message?.error('文件删除失败')
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getToken = () => {
  const tokenData = localStorage.getItem('ACCESS_TOKEN')
  if (tokenData) {
    try {
      const parsed = JSON.parse(tokenData)
      return parsed.value || ''
    } catch (e) {
      return ''
    }
  }
  return ''
}

// 文件列表列定义
const fileColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: '文件名',
    key: 'name',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '文件类型',
    key: 'file_type',
    width: 120,
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 100,
    render: (row) => formatFileSize(row.file_size),
  },
  {
    title: '处理状态',
    key: 'embedding_status',
    width: 120,
    render: (row) => {
      const statusMap = {
        pending: { type: 'warning', text: '待处理' },
        processing: { type: 'info', text: '处理中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '处理失败' }
      }
      const status = statusMap[row.embedding_status] || { type: 'default', text: '未知' }
      return h(NTag, { type: status.type }, { default: () => status.text })
    }
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 180,
    render: (row) => formatDate(row.created_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center',
    render: (row) => [
      h(
        NButton,
        {
          size: 'small',
          type: 'error',
          onClick: () => handleDeleteFile(row),
        },
        {
          default: () => '删除',
          icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
        }
      ),
    ],
  },
]

onMounted(() => {
  loadKnowledgeTypes()
  $table.value?.handleSearch()
})

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: '知识库名称',
    key: 'name',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '描述',
    key: 'description',
    width: 250,
    ellipsis: { tooltip: true },
  },
  {
    title: '类型',
    key: 'knowledge_type',
    width: 120,
    render: (row) => {
      const typeOption = knowledgeTypeOptions.value.find(opt => opt.value === row.knowledge_type)
      return typeOption?.label || row.knowledge_type
    }
  },
  {
    title: '访问权限',
    key: 'is_public',
    width: 100,
    align: 'center',
    render: (row) => h(NTag,
      { type: row.is_public ? 'success' : 'warning' },
      { default: () => row.is_public ? '公开' : '私有' }
    )
  },
  {
    title: '文件数量',
    key: 'file_count',
    width: 100,
    align: 'center',
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => formatDate(row.created_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    render: (row) => [
      withDirectives(
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            style: 'margin-right: 8px;',
            onClick: () => handleManageFiles(row),
          },
          {
            default: () => '管理文件',
            icon: renderIcon('material-symbols:folder-open', { size: 16 }),
          }
        ),
        [[vPermission, 'get/api/v1/knowledge/files']]
      ),
      withDirectives(
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => handleEdit(row),
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
          }
        ),
        [[vPermission, 'put/api/v1/knowledge/bases']]
      ),
      h(
        NPopconfirm,
        {
          onPositiveClick: () => handleDelete(row),
          onNegativeClick: () => {},
        },
        {
          trigger: () =>
            withDirectives(
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  style: 'margin-right: 8px;',
                },
                {
                  default: () => '删除',
                  icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                }
              ),
              [[vPermission, 'delete/api/v1/knowledge/bases']]
            ),
          default: () => h('div', {}, '确定删除该知识库吗?'),
        }
      ),
    ],
  },
]

// 表单验证规则
const modalRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' }
  ],
  knowledge_type: [
    { required: true, message: '请选择知识库类型', trigger: 'change' }
  ]
}
</script>
