<template>
  <div class="p-6">
    <!-- 头部信息 -->
    <div class="mb-6">
      <div class="flex items-center gap-4 mb-4">
        <n-button text @click="$router.back()">
          <template #icon>
            <n-icon><ArrowBack /></n-icon>
          </template>
          返回
        </n-button>
        <h1 class="text-2xl font-bold text-gray-900">{{ knowledgeBase?.name }}</h1>
        <n-tag :type="getStatusType(knowledgeBase?.status)">
          {{ getStatusText(knowledgeBase?.status) }}
        </n-tag>
      </div>
      <p class="text-gray-600">{{ knowledgeBase?.description }}</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
      <n-card>
        <n-statistic label="文档总数" :value="stats.documentCount">
          <template #prefix>
            <n-icon color="#18a058"><Document /></n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="向量数量" :value="stats.vectorCount">
          <template #prefix>
            <n-icon color="#2080f0"><Analytics /></n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="图谱节点" :value="stats.nodeCount">
          <template #prefix>
            <n-icon color="#f0a020"><GitNetwork /></n-icon>
          </template>
        </n-statistic>
      </n-card>
      <n-card>
        <n-statistic label="存储大小" :value="formatFileSize(stats.storageSize)">
          <template #prefix>
            <n-icon color="#d03050"><Server /></n-icon>
          </template>
        </n-statistic>
      </n-card>
    </div>

    <!-- 标签页 -->
    <n-tabs v-model:value="activeTab" type="line" animated>
      <!-- 文档管理 -->
      <n-tab-pane name="documents" tab="文档管理">
        <div class="mb-4 flex justify-between items-center">
          <div class="flex gap-4">
            <n-input
              v-model:value="documentSearch"
              placeholder="搜索文档"
              class="w-80"
            >
              <template #prefix>
                <n-icon><Search /></n-icon>
              </template>
            </n-input>
            <n-select
              v-model:value="documentStatusFilter"
              placeholder="状态筛选"
              :options="documentStatusOptions"
              class="w-40"
            />
          </div>
          <n-button type="primary" @click="$router.push(`/knowledge-bases/${route.params.id}/upload`)">
            <template #icon>
              <n-icon><Upload /></n-icon>
            </template>
            上传文档
          </n-button>
        </div>

        <n-data-table
          :columns="documentColumns"
          :data="filteredDocuments"
          :loading="documentsLoading"
          :pagination="documentPagination"
        />
      </n-tab-pane>

      <!-- 图谱视图 -->
      <n-tab-pane name="graph" tab="知识图谱">
        <div class="mb-4 flex gap-4">
          <n-input
            v-model:value="graphSearch"
            placeholder="搜索实体或关系"
            class="w-80"
          >
            <template #prefix>
              <n-icon><Search /></n-icon>
            </template>
          </n-input>
          <n-select
            v-model:value="graphTypeFilter"
            placeholder="类型筛选"
            :options="graphTypeOptions"
            class="w-40"
          />
          <n-button @click="refreshGraph">
            <template #icon>
              <n-icon><Refresh /></n-icon>
            </template>
            刷新
          </n-button>
        </div>

        <GraphVisualization
          :knowledge-base-id="route.params.id"
          :search-query="graphSearch"
          :type-filter="graphTypeFilter"
          class="h-96"
        />
      </n-tab-pane>

      <!-- 处理任务 -->
      <n-tab-pane name="tasks" tab="处理任务">
        <div class="mb-4 flex gap-4">
          <n-select
            v-model:value="taskStatusFilter"
            placeholder="任务状态"
            :options="taskStatusOptions"
            class="w-40"
          />
          <n-button @click="refreshTasks">
            <template #icon>
              <n-icon><Refresh /></n-icon>
            </template>
            刷新
          </n-button>
        </div>

        <n-data-table
          :columns="taskColumns"
          :data="filteredTasks"
          :loading="tasksLoading"
          :pagination="taskPagination"
        />
      </n-tab-pane>

      <!-- 设置 -->
      <n-tab-pane name="settings" tab="设置">
        <n-form
          ref="settingsFormRef"
          :model="settingsForm"
          label-placement="left"
          label-width="auto"
          class="max-w-2xl"
        >
          <n-form-item label="知识库名称" path="name">
            <n-input v-model:value="settingsForm.name" />
          </n-form-item>
          <n-form-item label="描述" path="description">
            <n-input
              v-model:value="settingsForm.description"
              type="textarea"
              :rows="3"
            />
          </n-form-item>
          <n-form-item label="访问权限" path="access_level">
            <n-select
              v-model:value="settingsForm.access_level"
              :options="accessLevelOptions"
            />
          </n-form-item>
          <n-form-item label="标签" path="tags">
            <n-dynamic-tags v-model:value="settingsForm.tags" />
          </n-form-item>
          <n-form-item label="自动处理" path="auto_process">
            <n-switch v-model:value="settingsForm.auto_process" />
          </n-form-item>
          <n-form-item label="向量化模型" path="embedding_model">
            <n-select
              v-model:value="settingsForm.embedding_model"
              :options="embeddingModelOptions"
            />
          </n-form-item>
          <n-form-item>
            <n-button type="primary" @click="handleUpdateSettings" :loading="settingsLoading">
              保存设置
            </n-button>
          </n-form-item>
        </n-form>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, reactive, ref} from 'vue'
import {useRoute} from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NDynamicTags,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NSelect,
  NStatistic,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  useMessage
} from 'naive-ui'
import {
  Analytics,
  ArrowBack,
  CheckmarkCircle,
  CloseCircle,
  Trash as Delete,
  Document,
  Download,
  Eye,
  GitNetwork,
  Refresh,
  Search,
  Server,
  Time,
  CloudUpload as Upload
} from '@vicons/ionicons5'
import {useKnowledgeBaseStore} from '~/stores/knowledgeBase'
import GraphVisualization from '~/components/GraphVisualization.vue'

const route = useRoute()
const message = useMessage()
const knowledgeBaseStore = useKnowledgeBaseStore()

// 响应式数据
const activeTab = ref('documents')
const documentsLoading = ref(false)
const tasksLoading = ref(false)
const settingsLoading = ref(false)
const documentSearch = ref('')
const documentStatusFilter = ref(null)
const graphSearch = ref('')
const graphTypeFilter = ref(null)
const taskStatusFilter = ref(null)

// 知识库数据
const knowledgeBase = ref(null)
const stats = reactive({
  documentCount: 0,
  vectorCount: 0,
  nodeCount: 0,
  storageSize: 0
})

// 文档数据
const documents = ref([])
const tasks = ref([])

// 设置表单
const settingsForm = reactive({
  name: '',
  description: '',
  access_level: 'private',
  tags: [],
  auto_process: true,
  embedding_model: 'qwen-embedding'
})

// 选项数据
const documentStatusOptions = [
  { label: '全部', value: null },
  { label: '已处理', value: 'processed' },
  { label: '处理中', value: 'processing' },
  { label: '失败', value: 'failed' }
]

const graphTypeOptions = [
  { label: '全部', value: null },
  { label: '实体', value: 'entity' },
  { label: '关系', value: 'relation' }
]

const taskStatusOptions = [
  { label: '全部', value: null },
  { label: '进行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

const accessLevelOptions = [
  { label: '私有', value: 'private' },
  { label: '团队', value: 'team' },
  { label: '公开', value: 'public' }
]

const embeddingModelOptions = [
  { label: '通义千问3-8B', value: 'qwen-embedding' },
  { label: 'BGE-Large-ZH', value: 'bge-large-zh' },
  { label: 'Text-Embedding-Ada-002', value: 'ada-002' }
]

// 表格列配置
const documentColumns = [
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
        failed: { color: 'error', text: '失败' }
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

const taskColumns = [
  {
    title: '任务ID',
    key: 'id',
    render: (row) => h('code', { class: 'text-xs' }, row.id.slice(0, 8))
  },
  {
    title: '任务类型',
    key: 'type',
    render: (row) => h(NTag, { size: 'small' }, { default: () => row.type })
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        running: { color: 'warning', text: '进行中', icon: Time },
        completed: { color: 'success', text: '已完成', icon: CheckmarkCircle },
        failed: { color: 'error', text: '失败', icon: CloseCircle }
      }
      const status = statusMap[row.status] || { color: 'default', text: '未知', icon: Time }
      return h('div', { class: 'flex items-center gap-2' }, [
        h(NIcon, { color: status.color === 'success' ? '#18a058' : status.color === 'error' ? '#d03050' : '#f0a020' }, 
          { default: () => h(status.icon) }),
        h(NTag, { type: status.color }, { default: () => status.text })
      ])
    }
  },
  {
    title: '进度',
    key: 'progress',
    render: (row) => h('div', { class: 'w-20' }, [
      h(NProgress, { percentage: row.progress || 0, size: 'small' })
    ])
  },
  {
    title: '开始时间',
    key: 'started_at',
    render: (row) => new Date(row.started_at).toLocaleString()
  },
  {
    title: '耗时',
    key: 'duration',
    render: (row) => {
      if (row.status === 'running') return '进行中'
      const duration = new Date(row.completed_at) - new Date(row.started_at)
      return `${Math.round(duration / 1000)}秒`
    }
  }
]

// 分页配置
const documentPagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const taskPagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 计算属性
const filteredDocuments = computed(() => {
  let result = documents.value
  
  if (documentSearch.value) {
    result = result.filter(doc => 
      doc.name.toLowerCase().includes(documentSearch.value.toLowerCase())
    )
  }
  
  if (documentStatusFilter.value) {
    result = result.filter(doc => doc.status === documentStatusFilter.value)
  }
  
  return result
})

const filteredTasks = computed(() => {
  let result = tasks.value
  
  if (taskStatusFilter.value) {
    result = result.filter(task => task.status === taskStatusFilter.value)
  }
  
  return result
})

// 工具函数
const getStatusType = (status) => {
  const statusMap = {
    active: 'success',
    disabled: 'error',
    processing: 'warning'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '活跃',
    disabled: '已禁用',
    processing: '处理中'
  }
  return statusMap[status] || '未知'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 事件处理函数
const handleViewDocument = (document) => {
  // 实现文档查看逻辑
  window.open(`/api/documents/${document.id}/view`, '_blank')
}

const handleDownloadDocument = (document) => {
  // 实现文档下载逻辑
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
      await loadDocuments()
    } catch (error) {
      message.error('删除失败')
    }
  }
}

const refreshGraph = () => {
  // 刷新图谱数据
  const graphComponent = document.querySelector('graph-visualization')
  if (graphComponent) {
    graphComponent.refresh()
  }
}

const refreshTasks = async () => {
  tasksLoading.value = true
  try {
    tasks.value = await knowledgeBaseStore.getTasks(route.params.id)
  } catch (error) {
    message.error('加载任务失败')
  } finally {
    tasksLoading.value = false
  }
}

const handleUpdateSettings = async () => {
  settingsLoading.value = true
  try {
    await knowledgeBaseStore.updateKnowledgeBase(route.params.id, settingsForm)
    message.success('设置更新成功')
  } catch (error) {
    message.error('更新失败')
  } finally {
    settingsLoading.value = false
  }
}

// 数据加载函数
const loadKnowledgeBase = async () => {
  try {
    knowledgeBase.value = await knowledgeBaseStore.getKnowledgeBase(route.params.id)
    Object.assign(settingsForm, knowledgeBase.value)
  } catch (error) {
    message.error('加载知识库信息失败')
  }
}

const loadStats = async () => {
  try {
    const statsData = await knowledgeBaseStore.getKnowledgeBaseStats(route.params.id)
    Object.assign(stats, statsData)
  } catch (error) {
    message.error('加载统计信息失败')
  }
}

const loadDocuments = async () => {
  documentsLoading.value = true
  try {
    documents.value = await knowledgeBaseStore.getDocuments(route.params.id)
  } catch (error) {
    message.error('加载文档失败')
  } finally {
    documentsLoading.value = false
  }
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadKnowledgeBase(),
    loadStats(),
    loadDocuments(),
    refreshTasks()
  ])
})
</script>

<style scoped>
.n-statistic {
  text-align: center;
}
</style>
