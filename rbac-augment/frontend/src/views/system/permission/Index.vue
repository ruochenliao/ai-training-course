<template>
  <PageContainer
    title="权限管理"
    description="管理系统权限信息、权限分配和访问控制"
    :icon="Key"
    badge="Beta"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <el-button
        v-permission="['permission:create']"
        type="primary"
        :icon="Plus"
        @click="handleAdd"
      >
        新增权限
      </el-button>
      <el-button
        v-permission="['permission:export']"
        :icon="DocumentCopy"
        @click="handleExport"
      >
        导出数据
      </el-button>
    </template>

    <!-- 搜索筛选区域 -->
    <div class="search-container">
      <el-card class="search-card" shadow="never">
        <el-form
          ref="searchFormRef"
          :model="searchForm"
          :inline="true"
          label-width="auto"
          class="search-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="权限名称">
                <el-input
                  v-model="searchForm.name"
                  placeholder="请输入权限名称"
                  clearable
                  :prefix-icon="Search"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="权限代码">
                <el-input
                  v-model="searchForm.code"
                  placeholder="请输入权限代码"
                  clearable
                  :prefix-icon="Key"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="资源">
                <el-input
                  v-model="searchForm.resource"
                  placeholder="请输入资源名称"
                  clearable
                  :prefix-icon="Collection"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item>
                <el-button type="primary" :icon="Search" @click="handleSearch">
                  搜索
                </el-button>
                <el-button :icon="Refresh" @click="handleReset">
                  重置
                </el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </div>

    <!-- 数据表格 -->
    <DataTable
      :data="tableData"
      :columns="tableColumns"
      :loading="loading"
      :pagination="pagination"
      show-selection
      show-index
      :show-batch-delete="true"
      :action-width="280"
      @refresh="fetchPermissionList"
      @batch-delete="handleBatchDelete"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @size-change="handleSizeChange"
      @current-page-change="handleCurrentPageChange"
    >
      <!-- 权限代码列 -->
      <template #code="{ row }">
        <el-tag type="info" size="small">{{ row.code }}</el-tag>
      </template>

      <!-- 资源列 -->
      <template #resource="{ row }">
        <el-tag type="primary" size="small">{{ row.resource }}</el-tag>
      </template>

      <!-- 动作列 -->
      <template #action="{ row }">
        <el-tag :type="getActionTagType(row.action)" size="small">
          {{ row.action }}
        </el-tag>
      </template>

      <!-- 状态列 -->
      <template #status="{ row }">
        <el-switch
          v-model="row.is_active"
          :loading="row.statusLoading"
          @change="handleStatusChange(row)"
        />
      </template>

      <!-- 操作列 -->
      <template #actions="{ row }">
        <ActionButtons
          :actions="getRowActions(row)"
          :permissions="userPermissions"
          size="small"
          compact
          :max-visible="4"
          @action="handleRowAction"
        />
      </template>
    </DataTable>

    <!-- 权限表单对话框 -->
    <PermissionForm
      v-model:visible="formVisible"
      :form-data="formData"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 权限详情对话框 -->
    <PermissionDetail
      v-model:visible="detailVisible"
      :permission-id="selectedPermissionId"
    />
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Key,
  Plus,
  DocumentCopy,
  Search,
  Collection,
  Refresh,
  View,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { getPermissionList, deletePermission, updatePermissionStatus } from '@/api/permission'
import { formatDateTime } from '@/utils'
import type { PermissionListItem, PaginationParams, TableColumn, ActionButton } from '@/types'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import PermissionForm from './components/PermissionForm.vue'
import PermissionDetail from './components/PermissionDetail.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  name: '',
  code: '',
  resource: ''
})

// 表格数据
const loading = ref(false)
const tableData = ref<PermissionListItem[]>([])
const selectedRows = ref<PermissionListItem[]>([])

// 分页数据
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表格列配置
const tableColumns = computed<TableColumn[]>(() => [
  {
    prop: 'id',
    label: 'ID',
    width: 80,
    sortable: true
  },
  {
    prop: 'name',
    label: '权限名称',
    minWidth: 150,
    showOverflowTooltip: true
  },
  {
    prop: 'code',
    label: '权限代码',
    minWidth: 150,
    slot: 'code'
  },
  {
    prop: 'resource',
    label: '资源',
    width: 120,
    slot: 'resource'
  },
  {
    prop: 'action',
    label: '动作',
    width: 100,
    slot: 'action'
  },
  {
    prop: 'description',
    label: '描述',
    minWidth: 200,
    showOverflowTooltip: true
  },
  {
    prop: 'is_active',
    label: '状态',
    width: 100,
    align: 'center',
    slot: 'status'
  },
  {
    prop: 'sort_order',
    label: '排序',
    width: 80,
    sortable: true
  },
  {
    prop: 'created_at',
    label: '创建时间',
    width: 160,
    sortable: true
  }
])

// 表单对话框
const formVisible = ref(false)
const formType = ref<'add' | 'edit'>('add')
const formData = ref<any>({})

// 详情对话框
const detailVisible = ref(false)
const selectedPermissionId = ref<number>()

/**
 * 获取权限列表
 */
const fetchPermissionList = async () => {
  try {
    loading.value = true

    const params: PaginationParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchForm.name || searchForm.code || searchForm.resource || undefined
    }

    // 添加具体搜索条件
    if (searchForm.name) {
      Object.assign(params, { name: searchForm.name })
    }
    if (searchForm.code) {
      Object.assign(params, { code: searchForm.code })
    }
    if (searchForm.resource) {
      Object.assign(params, { resource: searchForm.resource })
    }

    const response = await getPermissionList(params)
    const { items, total } = response.data

    tableData.value = items.map(item => ({
      ...item,
      statusLoading: false
    }))
    pagination.total = total
  } catch (error) {
    console.error('Failed to fetch permission list:', error)
    ElMessage.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  searchFormRef.value?.resetFields()
  Object.assign(searchForm, {
    name: '',
    code: '',
    resource: ''
  })
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 处理导出
 */
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

/**
 * 处理新增
 */
const handleAdd = () => {
  formType.value = 'add'
  formData.value = {}
  formVisible.value = true
}

/**
 * 处理编辑
 */
const handleEdit = (row: PermissionListItem) => {
  formType.value = 'edit'
  formData.value = { ...row }
  formVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: PermissionListItem) => {
  selectedPermissionId.value = row.id
  detailVisible.value = true
}

// 行操作按钮配置
const getRowActions = (row: PermissionListItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'permission:read',
    row
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'permission:update',
    row
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'permission:delete',
    row
  }
]

// 处理行操作
const handleRowAction = (action: ActionButton) => {
  const { key, row } = action

  switch (key) {
    case 'view':
      handleView(row)
      break
    case 'edit':
      handleEdit(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

/**
 * 处理状态切换
 */
const handleStatusChange = async (row: PermissionListItem) => {
  try {
    row.statusLoading = true
    await updatePermissionStatus(row.id, { is_active: row.is_active })
    ElMessage.success(`权限已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('Update permission status error:', error)
  } finally {
    row.statusLoading = false
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: PermissionListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>此操作将永久删除该权限，是否继续？</p>
            <p style="color: #f56c6c; font-size: 12px;">注意：删除后无法恢复</p>
          </div>
        `
      }
    )

    await deletePermission(row.id)
    ElMessage.success('删除成功')
    fetchPermissionList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete permission:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async (rows: PermissionListItem[]) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个权限吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里可以调用批量删除API
    for (const row of rows) {
      await deletePermission(row.id)
    }

    ElMessage.success('批量删除成功')
    fetchPermissionList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete permissions:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 获取动作标签类型
 */
const getActionTagType = (action: string) => {
  switch (action) {
    case 'read':
    case 'view':
      return 'primary'
    case 'create':
    case 'add':
      return 'success'
    case 'update':
    case 'edit':
      return 'warning'
    case 'delete':
      return 'danger'
    case 'manage':
    case 'config':
      return 'info'
    default:
      return ''
  }
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: PermissionListItem[]) => {
  selectedRows.value = selection
}

/**
 * 处理排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现排序逻辑
  console.log('Sort change:', prop, order)
  fetchPermissionList()
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 处理当前页变化
 */
const handleCurrentPageChange = (page: number) => {
  pagination.page = page
  fetchPermissionList()
}

/**
 * 处理表单成功
 */
const handleFormSuccess = () => {
  fetchPermissionList()
}

onMounted(() => {
  fetchPermissionList()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

// ==================== 搜索容器样式 ====================
.search-container {
  margin-bottom: $spacing-lg;

  .search-card {
    border: 1px solid $border-color-light;

    :deep(.el-card__body) {
      padding: $spacing-lg;
    }
  }

  .search-form {
    .el-form-item {
      margin-bottom: $spacing-md;
    }
  }
}

// ==================== 响应式设计 ====================
@media (max-width: $breakpoint-lg) {
  .search-container {
    .search-form {
      :deep(.el-row) {
        .el-col {
          &:nth-child(1),
          &:nth-child(2) {
            span: 12;
          }
          &:nth-child(3),
          &:nth-child(4) {
            span: 12;
          }
        }
      }
    }
  }
}

@media (max-width: $breakpoint-md) {
  .search-container {
    .search-form {
      :deep(.el-row) {
        .el-col {
          span: 24;
          margin-bottom: $spacing-sm;
        }
      }
    }
  }
}

// ==================== 暗色主题 ====================
.dark {
  .search-container {
    .search-card {
      background: $dark-card-color;
      border-color: $dark-border-color;
    }
  }
}
</style>
