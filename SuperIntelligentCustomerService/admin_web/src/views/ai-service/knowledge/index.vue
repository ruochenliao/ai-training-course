<template>
  <div class="knowledge-base-management">
    <n-card title="知识库管理" :bordered="false" size="small" class="rounded-16px shadow-sm">
      <!-- 操作栏 -->
      <template #header-extra>
        <n-button type="primary" @click="handleAdd">
          <icon-ic-round-plus class="mr-4px text-16px" />
          新建知识库
        </n-button>
      </template>

      <!-- 搜索栏 -->
      <n-space class="pb-12px" justify="space-between">
        <n-space>
          <n-input
            v-model:value="searchParams.search"
            placeholder="搜索知识库名称或描述"
            clearable
            class="w-240px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <icon-ic-round-search class="text-16px" />
            </template>
          </n-input>
          <n-select
            v-model:value="searchParams.knowledge_type"
            placeholder="选择知识库类型"
            clearable
            class="w-160px"
            :options="knowledgeTypeOptions"
            @update:value="handleSearch"
          />
          <n-select
            v-model:value="searchParams.is_public"
            placeholder="访问权限"
            clearable
            class="w-120px"
            :options="publicOptions"
            @update:value="handleSearch"
          />
        </n-space>
        <n-button @click="handleSearch">
          <icon-ic-round-search class="mr-4px text-16px" />
          搜索
        </n-button>
      </n-space>

      <!-- 表格 -->
      <n-data-table
        ref="tableRef"
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.id"
        flex-height
        class="sm:h-320px"
      />
    </n-card>

    <!-- 新建/编辑弹窗 -->
    <n-modal
      v-model:show="modalVisible"
      :title="modalTitle"
      preset="card"
      class="w-700px"
    >
      <n-form
        ref="modalFormRef"
        :model="modalForm"
        :rules="modalRules"
        label-placement="left"
        label-width="120px"
      >
        <n-grid :cols="2" :x-gap="16">
          <n-form-item-gi label="知识库名称" path="name">
            <n-input v-model:value="modalForm.name" placeholder="请输入知识库名称" />
          </n-form-item-gi>
          <n-form-item-gi label="知识库类型" path="knowledge_type">
            <n-select
              v-model:value="modalForm.knowledge_type"
              placeholder="请选择知识库类型"
              :options="knowledgeTypeOptions"
            />
          </n-form-item-gi>
        </n-grid>
        
        <n-form-item label="知识库描述" path="description">
          <n-input
            v-model:value="modalForm.description"
            type="textarea"
            placeholder="请输入知识库描述"
            :rows="3"
          />
        </n-form-item>

        <n-grid :cols="2" :x-gap="16">
          <n-form-item-gi label="访问权限" path="is_public">
            <n-select
              v-model:value="modalForm.is_public"
              placeholder="请选择访问权限"
              :options="publicOptions"
            />
          </n-form-item-gi>
          <n-form-item-gi label="嵌入模型" path="embedding_model">
            <n-input v-model:value="modalForm.embedding_model" placeholder="嵌入模型" />
          </n-form-item-gi>
        </n-grid>

        <n-grid :cols="3" :x-gap="16">
          <n-form-item-gi label="分块大小" path="chunk_size">
            <n-input-number
              v-model:value="modalForm.chunk_size"
              placeholder="分块大小"
              :min="100"
              :max="5000"
              class="w-full"
            />
          </n-form-item-gi>
          <n-form-item-gi label="分块重叠" path="chunk_overlap">
            <n-input-number
              v-model:value="modalForm.chunk_overlap"
              placeholder="分块重叠"
              :min="0"
              :max="1000"
              class="w-full"
            />
          </n-form-item-gi>
          <n-form-item-gi label="最大文件大小(MB)" path="max_file_size_mb">
            <n-input-number
              v-model:value="modalForm.max_file_size_mb"
              placeholder="最大文件大小"
              :min="1"
              :max="1000"
              class="w-full"
            />
          </n-form-item-gi>
        </n-grid>

        <n-form-item label="允许的文件类型" path="allowed_file_types">
          <n-select
            v-model:value="modalForm.allowed_file_types"
            multiple
            placeholder="请选择允许的文件类型"
            :options="fileTypeOptions"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" :loading="modalLoading" @click="handleSave">
            确定
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { Ref } from 'vue'
import { NButton, NTag, NSpace, NPopconfirm } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useCRUD } from '@/hooks/common/crud'
import { useLoading } from '@/hooks/common/loading'
import { $t } from '@/locales'
import api from '@/service/api'

defineOptions({
  name: 'KnowledgeBaseManagement'
})

interface KnowledgeBase {
  id: number
  name: string
  description: string
  knowledge_type: string
  is_public: boolean
  owner_id: number
  file_count: number
  total_size: number
  status: string
  created_at: string
  updated_at: string
}

interface SearchParams {
  search: string
  knowledge_type: string | null
  is_public: boolean | null
}

const { loading, startLoading, endLoading } = useLoading()

// 搜索参数
const searchParams: SearchParams = reactive({
  search: '',
  knowledge_type: null,
  is_public: null
})

// 表格数据
const tableData = ref<KnowledgeBase[]>([])
const tableRef = ref()

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page: number) => {
    pagination.page = page
    handleSearch()
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    handleSearch()
  }
})

// 表格列定义
const columns: Ref<DataTableColumns<KnowledgeBase>> = ref([
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center'
  },
  {
    title: '知识库名称',
    key: 'name',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '描述',
    key: 'description',
    width: 250,
    ellipsis: {
      tooltip: true
    }
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
    render: (row) => (
      <NTag type={row.is_public ? 'success' : 'warning'}>
        {row.is_public ? '公开' : '私有'}
      </NTag>
    )
  },
  {
    title: '文件数量',
    key: 'file_count',
    width: 100,
    align: 'center'
  },
  {
    title: '总大小',
    key: 'total_size',
    width: 120,
    align: 'center',
    render: (row) => formatFileSize(row.total_size)
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center',
    render: (row) => (
      <NTag type={row.status === 'active' ? 'success' : 'error'}>
        {row.status === 'active' ? '正常' : '禁用'}
      </NTag>
    )
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    fixed: 'right',
    render: (row) => (
      <NSpace justify="center">
        <NButton size="small" onClick={() => handleView(row)}>
          查看
        </NButton>
        <NButton size="small" type="primary" onClick={() => handleEdit(row)}>
          编辑
        </NButton>
        <NPopconfirm onPositiveClick={() => handleDelete(row)}>
          {{
            default: () => '确定删除这个知识库吗？',
            trigger: () => (
              <NButton size="small" type="error">
                删除
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
]) as Ref<DataTableColumns<KnowledgeBase>>

// CRUD相关
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
    name: '',
    description: '',
    knowledge_type: null,
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
  refresh: () => handleSearch(),
})

// 表单验证规则
const modalRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' }
  ],
  knowledge_type: [
    { required: true, message: '请选择知识库类型', trigger: 'change' }
  ]
}

// 选项数据
const knowledgeTypeOptions = ref([])
const publicOptions = [
  { label: '公开', value: true },
  { label: '私有', value: false }
]
const fileTypeOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word文档', value: 'docx' },
  { label: '文本文件', value: 'txt' },
  { label: 'Markdown', value: 'md' }
]

// 方法
const handleSearch = async () => {
  startLoading()
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchParams
    }
    
    const response = await api.getKnowledgeBases(params)
    if (response.success) {
      tableData.value = response.data
      pagination.itemCount = response.total
    }
  } catch (error) {
    console.error('获取知识库列表失败:', error)
  } finally {
    endLoading()
  }
}

const handleView = (row: KnowledgeBase) => {
  // 跳转到知识库详情页面
  // router.push(`/ai-service/knowledge/${row.id}`)
  console.log('查看知识库:', row)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取知识库类型选项
const loadKnowledgeTypes = async () => {
  try {
    const response = await api.getKnowledgeTypes()
    if (response.success) {
      knowledgeTypeOptions.value = response.data
    }
  } catch (error) {
    console.error('获取知识库类型失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadKnowledgeTypes()
  handleSearch()
})
</script>

<style scoped>
.knowledge-base-management {
  padding: 16px;
}
</style>
