<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">知识库管理</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <n-icon><Plus /></n-icon>
        </template>
        创建知识库
      </n-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="mb-6 flex gap-4">
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索知识库名称或描述"
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
      <n-button @click="refreshData">
        <template #icon>
          <n-icon><Refresh /></n-icon>
        </template>
        刷新
      </n-button>
    </div>

    <!-- 知识库列表 -->
    <n-data-table
      :columns="columns"
      :data="filteredKnowledgeBases"
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
      <n-button @click="handleBatchExport">
        批量导出
      </n-button>
    </div>

    <!-- 创建知识库模态框 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="创建知识库">
      <n-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="知识库名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="请输入知识库名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="createForm.description"
            type="textarea"
            placeholder="请输入知识库描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="访问权限" path="access_level">
          <n-select
            v-model:value="createForm.access_level"
            :options="accessLevelOptions"
            placeholder="选择访问权限"
          />
        </n-form-item>
        <n-form-item label="标签" path="tags">
          <n-dynamic-tags v-model:value="createForm.tags" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </n-button>
      </template>
    </n-modal>

    <!-- 编辑知识库模态框 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑知识库">
      <n-form
        ref="editFormRef"
        :model="editForm"
        :rules="createRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="知识库名称" path="name">
          <n-input v-model:value="editForm.name" placeholder="请输入知识库名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="editForm.description"
            type="textarea"
            placeholder="请输入知识库描述"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="访问权限" path="access_level">
          <n-select
            v-model:value="editForm.access_level"
            :options="accessLevelOptions"
            placeholder="选择访问权限"
          />
        </n-form-item>
        <n-form-item label="标签" path="tags">
          <n-dynamic-tags v-model:value="editForm.tags" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="handleUpdate" :loading="updating">
          更新
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {computed, h, onMounted, reactive, ref} from 'vue'
import {NButton, NDataTable, NDynamicTags, NForm, NFormItem, NIcon, NInput, NModal, NSelect, NTag, useMessage} from 'naive-ui'
import {Trash as Delete, Create as Edit, Eye, Add as Plus, Refresh, Search, CloudUpload as Upload} from '@vicons/ionicons5'
import {useKnowledgeBaseStore} from '~/stores/knowledgeBase'

const message = useMessage()
const knowledgeBaseStore = useKnowledgeBaseStore()

// 响应式数据
const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const searchQuery = ref('')
const statusFilter = ref(null)
const checkedRowKeys = ref([])
const showCreateModal = ref(false)
const showEditModal = ref(false)
const createFormRef = ref()
const editFormRef = ref()

// 表单数据
const createForm = reactive({
  name: '',
  description: '',
  access_level: 'private',
  tags: []
})

const editForm = reactive({
  id: '',
  name: '',
  description: '',
  access_level: 'private',
  tags: []
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度应在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ],
  access_level: [
    { required: true, message: '请选择访问权限', trigger: 'change' }
  ]
}

// 选项数据
const statusOptions = [
  { label: '全部', value: null },
  { label: '活跃', value: 'active' },
  { label: '已禁用', value: 'disabled' },
  { label: '处理中', value: 'processing' }
]

const accessLevelOptions = [
  { label: '私有', value: 'private' },
  { label: '团队', value: 'team' },
  { label: '公开', value: 'public' }
]

// 表格列配置
const columns = [
  { type: 'selection' },
  {
    title: '知识库名称',
    key: 'name',
    render: (row) => h('div', { class: 'font-medium' }, row.name)
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: { tooltip: true }
  },
  {
    title: '文档数量',
    key: 'document_count',
    render: (row) => h('span', { class: 'text-blue-600' }, row.document_count || 0)
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        active: { color: 'success', text: '活跃' },
        disabled: { color: 'error', text: '已禁用' },
        processing: { color: 'warning', text: '处理中' }
      }
      const status = statusMap[row.status] || { color: 'default', text: '未知' }
      return h(NTag, { type: status.color }, { default: () => status.text })
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h('div', { class: 'flex gap-2' }, [
      h(NButton, {
        size: 'small',
        onClick: () => handleView(row)
      }, { default: () => '查看', icon: () => h(NIcon, null, { default: () => h(Eye) }) }),
      h(NButton, {
        size: 'small',
        type: 'primary',
        onClick: () => handleEdit(row)
      }, { default: () => '编辑', icon: () => h(NIcon, null, { default: () => h(Edit) }) }),
      h(NButton, {
        size: 'small',
        onClick: () => handleUpload(row)
      }, { default: () => '上传', icon: () => h(NIcon, null, { default: () => h(Upload) }) }),
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
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
  }
})

// 计算属性
const filteredKnowledgeBases = computed(() => {
  let result = knowledgeBaseStore.knowledgeBases
  
  if (searchQuery.value) {
    result = result.filter(kb => 
      kb.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      kb.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(kb => kb.status === statusFilter.value)
  }
  
  return result
})

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
    await knowledgeBaseStore.fetchKnowledgeBases()
  } catch (error) {
    message.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const handleCheck = (keys: string[]) => {
  checkedRowKeys.value = keys
}

const handleCreate = async () => {
  try {
    await createFormRef.value?.validate()
    creating.value = true
    await knowledgeBaseStore.createKnowledgeBase(createForm)
    message.success('知识库创建成功')
    showCreateModal.value = false
    Object.assign(createForm, { name: '', description: '', access_level: 'private', tags: [] })
  } catch (error) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

const handleEdit = (row: any) => {
  Object.assign(editForm, row)
  showEditModal.value = true
}

const handleUpdate = async () => {
  try {
    await editFormRef.value?.validate()
    updating.value = true
    await knowledgeBaseStore.updateKnowledgeBase(editForm.id, editForm)
    message.success('知识库更新成功')
    showEditModal.value = false
  } catch (error) {
    message.error('更新失败')
  } finally {
    updating.value = false
  }
}

const handleView = (row: any) => {
  navigateTo(`/knowledge-bases/${row.id}`)
}

const handleUpload = (row: any) => {
  navigateTo(`/knowledge-bases/${row.id}/upload`)
}

const handleDelete = async (row: any) => {
  const confirmed = await new Promise(resolve => {
    const dialog = window.$dialog.warning({
      title: '确认删除',
      content: `确定要删除知识库"${row.name}"吗？此操作不可恢复。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false)
    })
  })
  
  if (confirmed) {
    try {
      await knowledgeBaseStore.deleteKnowledgeBase(row.id)
      message.success('删除成功')
    } catch (error) {
      message.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  const confirmed = await new Promise(resolve => {
    const dialog = window.$dialog.warning({
      title: '确认批量删除',
      content: `确定要删除选中的${checkedRowKeys.value.length}个知识库吗？此操作不可恢复。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false)
    })
  })
  
  if (confirmed) {
    try {
      await knowledgeBaseStore.batchDeleteKnowledgeBases(checkedRowKeys.value)
      message.success('批量删除成功')
      checkedRowKeys.value = []
    } catch (error) {
      message.error('批量删除失败')
    }
  }
}

const handleBatchExport = async () => {
  try {
    await knowledgeBaseStore.batchExportKnowledgeBases(checkedRowKeys.value)
    message.success('导出任务已启动')
  } catch (error) {
    message.error('导出失败')
  }
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.n-data-table {
  --n-th-color: #f8fafc;
}
</style>
