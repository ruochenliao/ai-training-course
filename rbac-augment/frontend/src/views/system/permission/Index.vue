<template>
  <PageContainer
    title="权限管理"
    description="管理系统中的所有权限，包括权限的创建、编辑、删除和分组管理"
    :icon="Key"
    badge="Advanced"
    badge-type="warning"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <ActionButtons
        :actions="headerActions"
        :permissions="userPermissions"
        @action="handleHeaderAction"
      />
    </template>

    <!-- 视图切换和搜索 -->
    <div class="view-controls">
      <el-card shadow="never" class="controls-card">
        <div class="controls-content">
          <div class="view-switcher">
            <el-radio-group v-model="viewMode" @change="handleViewModeChange">
              <el-radio-button label="tree">
                <el-icon><Menu /></el-icon>
                树形视图
              </el-radio-button>
              <el-radio-button label="table">
                <el-icon><Grid /></el-icon>
                表格视图
              </el-radio-button>
              <el-radio-button label="group">
                <el-icon><Collection /></el-icon>
                分组视图
              </el-radio-button>
            </el-radio-group>
          </div>

          <!-- 搜索筛选 -->
          <div v-if="viewMode === 'table'" class="search-section">
            <SearchForm
              v-model="searchForm"
              :fields="searchFields"
              :loading="loading"
              :show-advanced="false"
              @search="handleSearch"
              @reset="handleReset"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 权限树视图 -->
    <div v-if="viewMode === 'tree'" class="permission-tree-view">
      <el-card shadow="never" class="tree-card">
        <template #header>
          <div class="tree-header">
            <div class="header-left">
              <el-icon class="header-icon"><Menu /></el-icon>
              <span class="header-title">权限树结构</span>
            </div>
            <div class="header-right">
              <el-button size="small" @click="handleExpandAll">展开全部</el-button>
              <el-button size="small" @click="handleCollapseAll">收起全部</el-button>
            </div>
          </div>
        </template>

        <el-tree
          ref="permissionTreeRef"
          v-loading="loading"
          :data="permissionTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
          class="permission-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <div class="node-content">
                <el-icon v-if="data.icon" class="node-icon">
                  <component :is="data.icon" />
                </el-icon>
                <div class="node-info">
                  <div class="node-name">{{ data.name }}</div>
                  <div class="node-details">
                    <el-tag size="small" type="info">{{ data.code }}</el-tag>
                    <el-tag v-if="data.resource" size="small" type="primary">{{ data.resource }}</el-tag>
                    <el-tag v-if="data.action" size="small" type="success">{{ data.action }}</el-tag>
                  </div>
                </div>
              </div>
              <div class="node-actions">
                <ActionButtons
                  :actions="getTreeNodeActions(data)"
                  :permissions="userPermissions"
                  size="small"
                  compact
                  @action="handleTreeNodeAction"
                />
              </div>
            </div>
          </template>
        </el-tree>
      </el-card>
    </div>

    <!-- 权限分组视图 -->
    <div v-else-if="viewMode === 'group'" class="permission-groups-view">
      <el-row :gutter="16">
        <el-col
          v-for="group in permissionGroups"
          :key="group.resource"
          :span="8"
          :xs="24"
          :sm="12"
          :md="8"
        >
          <el-card class="group-card" shadow="hover">
            <template #header>
              <div class="group-header">
                <div class="group-info">
                  <el-icon class="group-icon"><Collection /></el-icon>
                  <span class="group-title">{{ group.resource }}</span>
                </div>
                <el-tag size="small" type="primary">{{ group.permissions.length }} 个权限</el-tag>
              </div>
            </template>

            <div class="permission-list">
              <div
                v-for="permission in group.permissions"
                :key="permission.id"
                class="permission-item"
              >
                <div class="permission-info">
                  <div class="permission-name">{{ permission.name }}</div>
                  <div class="permission-meta">
                    <el-tag size="small" type="success">{{ permission.action }}</el-tag>
                    <StatusTag :status="permission.is_active" size="small" />
                  </div>
                </div>
                <div class="permission-actions">
                  <ActionButtons
                    :actions="getGroupItemActions(permission)"
                    :permissions="userPermissions"
                    size="small"
                    compact
                    @action="handleGroupItemAction"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 权限表格视图 -->
    <div v-else class="permission-table-view">
      <DataTable
        v-model:selected="selectedIds"
        :data="permissionList"
        :columns="tableColumns"
        :loading="loading"
        :pagination="pagination"
        :show-selection="true"
        :show-index="true"
        @sort-change="handleSortChange"
        @page-change="handlePageChange"
        @size-change="handleSizeChange"
      >
        <!-- 状态列自定义渲染 -->
        <template #status="{ row }">
          <StatusTag :status="row.is_active" />
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <ActionButtons
            :actions="getTableRowActions(row)"
            :permissions="userPermissions"
            size="small"
            compact
            @action="handleTableRowAction"
          />
        </template>
      </DataTable>
    </div>

    <!-- 权限表单对话框 -->
    <FormDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :form-data="formData"
      :form-rules="formRules"
      :form-fields="formFields"
      :loading="submitLoading"
      width="700px"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Key, Plus, Refresh, Menu, Grid, Collection,
  View, Edit, Delete, Expand, Fold, Download
} from '@element-plus/icons-vue'
import {
  getPermissionList,
  getPermissionTree,
  getPermissionGroups,
  deletePermission,
  createPermission,
  updatePermission,
  getPermissionDetail
} from '@/api/permission'
import { formatDateTime } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import SearchForm from '@/components/common/SearchForm.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import type { SearchField } from '@/components/common/SearchForm.vue'
import type { ActionButton } from '@/components/common/ActionButtons.vue'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 视图模式
const viewMode = ref('tree')

// 搜索表单配置
const searchForm = reactive({
  name: '',
  code: '',
  resource: '',
  action: ''
})

const searchFields: SearchField[] = [
  {
    prop: 'name',
    label: '权限名称',
    type: 'input',
    placeholder: '请输入权限名称',
    prefixIcon: Key
  },
  {
    prop: 'code',
    label: '权限代码',
    type: 'input',
    placeholder: '请输入权限代码'
  },
  {
    prop: 'resource',
    label: '资源',
    type: 'input',
    placeholder: '请输入资源名称'
  },
  {
    prop: 'action',
    label: '操作',
    type: 'input',
    placeholder: '请输入操作名称'
  }
]

// 数据状态
const loading = ref(false)
const submitLoading = ref(false)
const permissionTree = ref<any[]>([])
const permissionList = ref<any[]>([])
const permissionGroups = ref<any[]>([])
const selectedIds = ref<number[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 树形属性
const treeProps = {
  children: 'children',
  label: 'name'
}

// 树形组件引用
const permissionTreeRef = ref()

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: 80, sortable: true },
  { prop: 'name', label: '权限名称', minWidth: 150 },
  { prop: 'code', label: '权限代码', minWidth: 150 },
  { prop: 'resource', label: '资源', width: 120 },
  { prop: 'action', label: '操作', width: 100 },
  { prop: 'description', label: '描述', minWidth: 200, showOverflowTooltip: true },
  { prop: 'is_active', label: '状态', width: 80, slot: 'status' },
  { prop: 'sort_order', label: '排序', width: 80 },
  { prop: 'created_at', label: '创建时间', width: 160, formatter: (row: any) => formatDateTime(row.created_at) },
  { prop: 'actions', label: '操作', width: 200, fixed: 'right', slot: 'actions' }
]

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'add',
    label: '新增权限',
    type: 'primary',
    icon: Plus,
    permission: 'permission:create'
  },
  {
    key: 'refresh',
    label: '刷新数据',
    type: 'success',
    icon: Refresh
  },
  {
    key: 'export',
    label: '导出数据',
    icon: Download,
    permission: 'permission:export'
  }
]

// 树节点操作按钮
const getTreeNodeActions = (node: any): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'permission:read',
    row: node
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'permission:update',
    row: node
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'permission:delete',
    row: node
  }
]

// 表格行操作按钮
const getTableRowActions = (row: any): ActionButton[] => [
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

// 分组项操作按钮
const getGroupItemActions = (item: any): ActionButton[] => [
  {
    key: 'edit',
    label: '编辑',
    type: 'text',
    icon: Edit,
    permission: 'permission:update',
    row: item
  },
  {
    key: 'delete',
    label: '删除',
    type: 'text',
    icon: Delete,
    permission: 'permission:delete',
    row: item
  }
]

// 表单对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑权限' : '新增权限')
const isEdit = ref(false)
const currentPermissionId = ref<number>()

// 表单数据
const formData = ref({
  name: '',
  code: '',
  resource: '',
  action: '',
  description: '',
  group: '',
  parent_id: null,
  sort_order: 0,
  is_active: true
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '权限名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_:]*$/, message: '权限代码只能包含字母、数字、下划线和冒号，且以字母开头', trigger: 'blur' }
  ],
  resource: [
    { required: true, message: '请输入资源名称', trigger: 'blur' }
  ],
  action: [
    { required: true, message: '请输入操作名称', trigger: 'blur' }
  ]
}

// 表单字段配置
const formFields = [
  {
    prop: 'name',
    label: '权限名称',
    type: 'input',
    placeholder: '请输入权限名称',
    span: 12
  },
  {
    prop: 'code',
    label: '权限代码',
    type: 'input',
    placeholder: '请输入权限代码',
    span: 12
  },
  {
    prop: 'resource',
    label: '资源',
    type: 'input',
    placeholder: '请输入资源名称',
    span: 12
  },
  {
    prop: 'action',
    label: '操作',
    type: 'input',
    placeholder: '请输入操作名称',
    span: 12
  },
  {
    prop: 'group',
    label: '权限分组',
    type: 'input',
    placeholder: '请输入权限分组',
    span: 12
  },
  {
    prop: 'sort_order',
    label: '排序',
    type: 'number',
    min: 0,
    max: 999,
    span: 12
  },
  {
    prop: 'parent_id',
    label: '父级权限',
    type: 'cascader',
    placeholder: '请选择父级权限',
    options: computed(() => permissionOptions.value),
    props: { checkStrictly: true, emitPath: false },
    span: 24
  },
  {
    prop: 'description',
    label: '权限描述',
    type: 'textarea',
    placeholder: '请输入权限描述',
    rows: 3,
    span: 24
  }
]

// 权限选项
const permissionOptions = ref<any[]>([])

/**
 * 获取权限列表
 */
const fetchPermissionList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    const response = await getPermissionList(params)
    permissionList.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to fetch permission list:', error)
    ElMessage.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取权限树
 */
const fetchPermissionTree = async () => {
  try {
    loading.value = true
    const response = await getPermissionTree()
    permissionTree.value = response.data
    // 同时获取权限选项用于表单
    permissionOptions.value = buildPermissionOptions(response.data)
  } catch (error) {
    console.error('Failed to fetch permission tree:', error)
    ElMessage.error('获取权限树失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取权限分组
 */
const fetchPermissionGroups = async () => {
  try {
    loading.value = true
    const response = await getPermissionGroups()
    permissionGroups.value = response.data
  } catch (error) {
    console.error('Failed to fetch permission groups:', error)
    ElMessage.error('获取权限分组失败')
  } finally {
    loading.value = false
  }
}

/**
 * 构建权限选项
 */
const buildPermissionOptions = (tree: any[]): any[] => {
  return tree.map(item => ({
    value: item.id,
    label: item.name,
    children: item.children ? buildPermissionOptions(item.children) : undefined
  }))
}

/**
 * 处理视图模式变化
 */
const handleViewModeChange = (mode: string) => {
  viewMode.value = mode as any
  switch (mode) {
    case 'tree':
      fetchPermissionTree()
      break
    case 'table':
      fetchPermissionList()
      break
    case 'group':
      fetchPermissionGroups()
      break
  }
}

/**
 * 头部操作处理
 */
const handleHeaderAction = (action: ActionButton) => {
  switch (action.key) {
    case 'add':
      handleAdd()
      break
    case 'refresh':
      handleRefresh()
      break
    case 'export':
      handleExport()
      break
  }
}

/**
 * 树节点操作处理
 */
const handleTreeNodeAction = (action: ActionButton) => {
  const node = action.row
  switch (action.key) {
    case 'view':
      handleView(node)
      break
    case 'edit':
      handleEdit(node)
      break
    case 'delete':
      handleDelete(node)
      break
  }
}

/**
 * 表格行操作处理
 */
const handleTableRowAction = (action: ActionButton) => {
  const row = action.row
  switch (action.key) {
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
 * 分组项操作处理
 */
const handleGroupItemAction = (action: ActionButton) => {
  const item = action.row
  switch (action.key) {
    case 'edit':
      handleEdit(item)
      break
    case 'delete':
      handleDelete(item)
      break
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 重置处理
 */
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    code: '',
    resource: '',
    action: ''
  })
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 刷新数据
 */
const handleRefresh = () => {
  switch (viewMode.value) {
    case 'tree':
      fetchPermissionTree()
      break
    case 'table':
      fetchPermissionList()
      break
    case 'group':
      fetchPermissionGroups()
      break
  }
}

/**
 * 导出数据
 */
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

/**
 * 处理新增
 */
const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

/**
 * 处理查看
 */
const handleView = async (row: any) => {
  try {
    isEdit.value = false
    const response = await getPermissionDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch permission detail:', error)
    ElMessage.error('获取权限详情失败')
  }
}

/**
 * 处理编辑
 */
const handleEdit = async (row: any) => {
  try {
    isEdit.value = true
    currentPermissionId.value = row.id
    const response = await getPermissionDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch permission detail:', error)
    ElMessage.error('获取权限详情失败')
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePermission(row.id)
    ElMessage.success('删除成功')

    // 刷新当前视图
    handleRefresh()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete permission:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 展开全部
 */
const handleExpandAll = () => {
  const tree = permissionTreeRef.value
  if (tree) {
    const expandAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, true)
        if (node.children) {
          expandAll(node.children)
        }
      })
    }
    expandAll(permissionTree.value)
  }
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  const tree = permissionTreeRef.value
  if (tree) {
    const collapseAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, false)
        if (node.children) {
          collapseAll(node.children)
        }
      })
    }
    collapseAll(permissionTree.value)
  }
}

/**
 * 分页处理
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchPermissionList()
}

/**
 * 页面大小变化处理
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchPermissionList()
}

/**
 * 排序变化处理
 */
const handleSortChange = ({ prop, order }: any) => {
  console.log('Sort change:', prop, order)
  // 这里可以添加排序逻辑
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    name: '',
    code: '',
    resource: '',
    action: '',
    description: '',
    parent_id: null,
    sort_order: 0,
    group: '',
    is_active: true
  }
}

/**
 * 填充表单数据
 */
const fillForm = (permission: any) => {
  formData.value = {
    name: permission.name,
    code: permission.code,
    resource: permission.resource || '',
    action: permission.action || '',
    description: permission.description || '',
    parent_id: permission.parent_id,
    sort_order: permission.sort_order || 0,
    group: permission.group || '',
    is_active: permission.is_active !== undefined ? permission.is_active : true
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async (data: any) => {
  try {
    submitLoading.value = true

    if (isEdit.value && currentPermissionId.value) {
      await updatePermission(currentPermissionId.value, data)
      ElMessage.success('权限更新成功')
    } else {
      await createPermission(data)
      ElMessage.success('权限创建成功')
    }

    dialogVisible.value = false
    handleRefresh()
  } catch (error) {
    console.error('Failed to submit permission:', error)
    ElMessage.error(isEdit.value ? '权限更新失败' : '权限创建失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 处理表单取消
 */
const handleCancel = () => {
  dialogVisible.value = false
  resetForm()
  currentPermissionId.value = undefined
}

onMounted(() => {
  fetchPermissionTree()
})
</script>

<style lang="scss" scoped>
// 视图控制样式
.view-controls {
  margin-bottom: 20px;

  .controls-card {
    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .controls-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;

    .view-switcher {
      .el-radio-group {
        .el-radio-button {
          .el-radio-button__inner {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
          }
        }
      }
    }

    .search-section {
      flex: 1;
      max-width: 600px;
    }
  }
}

// 权限树视图样式
.permission-tree-view {
  .tree-card {
    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
    }

    .tree-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        display: flex;
        align-items: center;
        gap: 8px;

        .header-icon {
          font-size: 18px;
          color: var(--el-color-primary);
        }

        .header-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }

      .header-right {
        display: flex;
        gap: 8px;
      }
    }
  }

  .permission-tree {
    .tree-node {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 4px 0;

      .node-content {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;

        .node-icon {
          font-size: 16px;
          color: var(--el-color-primary);
        }

        .node-info {
          flex: 1;

          .node-name {
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }

          .node-details {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
          }
        }
      }

      .node-actions {
        margin-left: 12px;
      }
    }
  }
}

// 权限分组视图样式
.permission-groups-view {
  .group-card {
    height: 100%;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
    }

    .group-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .group-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .group-icon {
          font-size: 18px;
          color: var(--el-color-primary);
        }

        .group-title {
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
    }

    .permission-list {
      max-height: 400px;
      overflow-y: auto;

      .permission-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        transition: all 0.2s ease;

        &:last-child {
          border-bottom: none;
        }

        &:hover {
          background-color: var(--el-color-primary-light-9);
          border-radius: 4px;
          padding-left: 8px;
          padding-right: 8px;
        }

        .permission-info {
          flex: 1;

          .permission-name {
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }

          .permission-meta {
            display: flex;
            gap: 8px;
            align-items: center;
          }
        }

        .permission-actions {
          margin-left: 12px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .permission-groups-view {
    .el-col {
      margin-bottom: 16px;
    }
  }
}

@media (max-width: 768px) {
  .view-controls {
    .controls-content {
      flex-direction: column;
      gap: 16px;

      .search-section {
        max-width: 100%;
      }
    }
  }

  .permission-tree-view {
    .tree-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;

      .header-right {
        width: 100%;
        justify-content: flex-end;
      }
    }

    .tree-node {
      .node-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;

        .node-details {
          margin-top: 4px;
        }
      }

      .node-actions {
        margin-left: 0;
        margin-top: 8px;
      }
    }
  }

  .permission-groups-view {
    .group-card {
      .permission-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;

        .permission-actions {
          margin-left: 0;
          align-self: flex-end;
        }
      }
    }
  }
}

// 暗色主题适配
.dark {
  .view-controls {
    .controls-card {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);
    }
  }

  .permission-tree-view {
    .tree-card {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);
    }
  }

  .permission-groups-view {
    .group-card {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);

      &:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      }

      .permission-item {
        &:hover {
          background-color: var(--el-color-primary-dark-2);
        }
      }
    }
  }
}
</style>
