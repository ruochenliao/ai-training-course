<template>
  <PageContainer
    title="角色管理"
    description="管理系统角色信息、权限分配和用户关联"
    :icon="UserFilled"
    badge="Beta"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <el-button
        v-permission="['role:create']"
        type="primary"
        :icon="Plus"
        @click="handleAdd"
      >
        新增角色
      </el-button>
      <el-button
        v-permission="['role:export']"
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
              <el-form-item label="角色名称">
                <el-input
                  v-model="searchForm.name"
                  placeholder="请输入角色名称"
                  clearable
                  :prefix-icon="Search"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="角色代码">
                <el-input
                  v-model="searchForm.code"
                  placeholder="请输入角色代码"
                  clearable
                  :prefix-icon="Key"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="状态">
                <el-select
                  v-model="searchForm.is_active"
                  placeholder="请选择角色状态"
                  clearable
                  style="width:200px"
                >
                  <el-option label="启用" :value="true">
                    <span class="status-option">
                      <el-icon color="#52c41a"><CircleCheck /></el-icon>
                      启用
                    </span>
                  </el-option>
                  <el-option label="禁用" :value="false">
                    <span class="status-option">
                      <el-icon color="#ff4d4f"><CircleClose /></el-icon>
                      禁用
                    </span>
                  </el-option>
                </el-select>
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
      @refresh="fetchRoleList"
      @batch-delete="handleBatchDelete"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @size-change="handleSizeChange"
      @current-page-change="handleCurrentPageChange"
    >
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

    <!-- 角色表单对话框 -->
    <RoleForm
      v-model:visible="formVisible"
      :form-data="formData"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 角色详情对话框 -->
    <RoleDetail
      v-model:visible="detailVisible"
      :role-id="selectedRoleId"
    />

    <!-- 权限分配对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限分配"
      width="700px"
      :close-on-click-modal="false"
      class="permission-dialog"
    >
      <div v-if="currentRole" class="dialog-header">
        <el-alert
          :title="`为角色 &quot;${currentRole.name}&quot; 分配权限`"
          type="info"
          :closable="false"
          show-icon
        />
      </div>

      <div class="permission-content">
        <el-tree
          ref="permissionTreeRef"
          :data="permissionTree"
          :props="{ children: 'children', label: 'name' }"
          node-key="id"
          show-checkbox
          check-strictly
          :default-checked-keys="selectedPermissions"
          class="permission-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <el-icon v-if="data.icon" class="node-icon">
                <component :is="data.icon" />
              </el-icon>
              <span class="node-label">{{ node.label }}</span>
              <el-tag v-if="data.code" size="small" type="info">{{ data.code }}</el-tag>
            </div>
          </template>
        </el-tree>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button @click="handleExpandAll">展开全部</el-button>
          <el-button @click="handleCollapseAll">收起全部</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSavePermissions">
            保存权限
          </el-button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  UserFilled,
  Plus,
  DocumentCopy,
  Search,
  Key,
  Refresh,
  CircleCheck,
  CircleClose,
  View,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { getRoleList, deleteRole, updateRoleStatus, assignRolePermissions, getRolePermissions } from '@/api/role'
import { getPermissionTree } from '@/api/permission'
import { formatDateTime } from '@/utils'
import type { RoleListItem, PaginationParams, TableColumn, ActionButton } from '@/types'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import RoleForm from './components/RoleForm.vue'
import RoleDetail from './components/RoleDetail.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  name: '',
  code: '',
  is_active: undefined as boolean | undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<RoleListItem[]>([])
const selectedRows = ref<RoleListItem[]>([])

// 分页数据
const pagination = reactive({
  page: 1,
  page_size: 20,
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
    label: '角色名称',
    minWidth: 120,
    showOverflowTooltip: true
  },
  {
    prop: 'code',
    label: '角色代码',
    minWidth: 120,
    showOverflowTooltip: true
  },
  {
    prop: 'description',
    label: '角色描述',
    minWidth: 200,
    showOverflowTooltip: true
  },
  {
    prop: 'user_count',
    label: '用户数量',
    width: 100,
    align: 'center'
  },
  {
    prop: 'permission_count',
    label: '权限数量',
    width: 100,
    align: 'center'
  },
  {
    prop: 'is_active',
    label: '状态',
    width: 100,
    align: 'center',
    slot: 'status'
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
const selectedRoleId = ref<number>()

// 权限分配对话框
const permissionDialogVisible = ref(false)
const permissionTree = ref<any[]>([])
const selectedPermissions = ref<number[]>([])
const permissionTreeRef = ref()
const currentRole = ref<RoleListItem | null>(null)
const submitLoading = ref(false)

/**
 * 获取角色列表
 */
const fetchRoleList = async () => {
  try {
    loading.value = true

    const params: PaginationParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchForm.name || searchForm.code || undefined
    }

    // 添加具体搜索条件
    if (searchForm.name) {
      Object.assign(params, { name: searchForm.name })
    }
    if (searchForm.code) {
      Object.assign(params, { code: searchForm.code })
    }
    if (searchForm.is_active !== undefined) {
      Object.assign(params, { is_active: searchForm.is_active })
    }

    const response = await getRoleList(params)
    const { items, total } = response.data

    tableData.value = items.map(item => ({
      ...item,
      statusLoading: false
    }))
    pagination.total = total
  } catch (error) {
    console.error('Failed to fetch role list:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchRoleList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  searchFormRef.value?.resetFields()
  Object.assign(searchForm, {
    name: '',
    code: '',
    is_active: undefined
  })
  pagination.page = 1
  fetchRoleList()
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
const handleEdit = (row: RoleListItem) => {
  formType.value = 'edit'
  formData.value = { ...row }
  formVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: RoleListItem) => {
  selectedRoleId.value = row.id
  detailVisible.value = true
}

// 行操作按钮配置
const getRowActions = (row: RoleListItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'role:read',
    row
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'role:update',
    row
  },
  {
    key: 'permissions',
    label: '权限分配',
    type: 'success',
    icon: Key,
    permission: 'role:update',
    row
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'role:delete',
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
    case 'permissions':
      handleAssignPermissions(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

/**
 * 处理状态切换
 */
const handleStatusChange = async (row: RoleListItem) => {
  try {
    row.statusLoading = true
    await updateRoleStatus(row.id, { is_active: row.is_active })
    ElMessage.success(`角色已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('Update role status error:', error)
  } finally {
    row.statusLoading = false
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: RoleListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>此操作将永久删除该角色，是否继续？</p>
            <p style="color: #f56c6c; font-size: 12px;">注意：删除后无法恢复</p>
          </div>
        `
      }
    )

    await deleteRole(row.id)
    ElMessage.success('删除成功')
    fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete role:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async (rows: RoleListItem[]) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个角色吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里可以调用批量删除API
    for (const row of rows) {
      await deleteRole(row.id)
    }

    ElMessage.success('批量删除成功')
    fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete roles:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理权限分配
 */
const handleAssignPermissions = async (row: RoleListItem) => {
  try {
    currentRole.value = row

    // 获取权限树
    const treeResponse = await getPermissionTree()
    permissionTree.value = treeResponse.data

    // 获取角色已有权限
    const permissionsResponse = await getRolePermissions(row.id)
    selectedPermissions.value = permissionsResponse.data.map((p: any) => p.id)

    permissionDialogVisible.value = true
  } catch (error) {
    console.error('Failed to load permissions:', error)
    ElMessage.error('加载权限数据失败')
  }
}

/**
 * 保存权限分配
 */
const handleSavePermissions = async () => {
  if (!currentRole.value) return

  try {
    submitLoading.value = true
    const checkedKeys = permissionTreeRef.value?.getCheckedKeys() || []

    await assignRolePermissions(currentRole.value.id, { permission_ids: checkedKeys })
    ElMessage.success('权限分配成功')

    permissionDialogVisible.value = false
    fetchRoleList()
  } catch (error) {
    console.error('Failed to assign permissions:', error)
    ElMessage.error('权限分配失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 展开全部权限树
 */
const handleExpandAll = () => {
  const expandAll = (nodes: any[]) => {
    nodes.forEach(node => {
      permissionTreeRef.value?.setExpanded(node.id, true)
      if (node.children) {
        expandAll(node.children)
      }
    })
  }
  expandAll(permissionTree.value)
}

/**
 * 收起全部权限树
 */
const handleCollapseAll = () => {
  const collapseAll = (nodes: any[]) => {
    nodes.forEach(node => {
      permissionTreeRef.value?.setExpanded(node.id, false)
      if (node.children) {
        collapseAll(node.children)
      }
    })
  }
  collapseAll(permissionTree.value)
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: RoleListItem[]) => {
  selectedRows.value = selection
}

/**
 * 处理排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现排序逻辑
  console.log('Sort change:', prop, order)
  fetchRoleList()
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchRoleList()
}

/**
 * 处理当前页变化
 */
const handleCurrentPageChange = (page: number) => {
  pagination.page = page
  fetchRoleList()
}

/**
 * 处理表单成功
 */
const handleFormSuccess = () => {
  fetchRoleList()
}

onMounted(() => {
  fetchRoleList()
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

  .status-option {
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

// ==================== 权限分配对话框样式 ====================
.permission-dialog {
  .dialog-header {
    margin-bottom: 20px;
  }

  .permission-content {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid var(--el-border-color-light);
    border-radius: 4px;
    padding: 12px;

    .permission-tree {
      .tree-node {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;

        .node-icon {
          font-size: 16px;
          color: var(--el-color-primary);
        }

        .node-label {
          flex: 1;
          font-weight: 500;
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
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

  .permission-dialog {
    .permission-content {
      border-color: var(--el-border-color);
      background: var(--el-bg-color-page);
    }
  }
}
</style>
