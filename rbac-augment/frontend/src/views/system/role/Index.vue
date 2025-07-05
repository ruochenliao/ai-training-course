<template>
  <PageContainer
    title="角色管理"
    description="管理系统角色信息、权限分配和用户关联"
    :icon="UserFilled"
    badge="Pro"
    badge-type="success"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <ActionButtons
        :actions="headerActions"
        :permissions="userPermissions"
        @action="handleHeaderAction"
      />
    </template>

    <!-- 搜索筛选区域 -->
    <SearchForm
      v-model="searchForm"
      :fields="searchFields"
      :loading="loading"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 数据表格 -->
    <DataTable
      v-model:selected="selectedIds"
      :data="tableData"
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
          :actions="getRowActions(row)"
          :permissions="userPermissions"
          size="small"
          compact
          @action="handleRowAction"
        />
      </template>
    </DataTable>

    <!-- 角色表单对话框 -->
    <FormDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :form-data="formData"
      :form-rules="formRules"
      :form-fields="formFields"
      :loading="submitLoading"
      width="600px"
      @submit="handleSubmit"
      @cancel="handleCancel"
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

    <!-- 菜单分配对话框 -->
    <el-dialog
      v-model="menuDialogVisible"
      title="菜单分配"
      width="700px"
      :close-on-click-modal="false"
      class="menu-dialog"
    >
      <div v-if="currentRole" class="dialog-header">
        <el-alert
          :title="`为角色 &quot;${currentRole.name}&quot; 分配菜单`"
          type="success"
          :closable="false"
          show-icon
        />
      </div>

      <div class="menu-content">
        <el-tree
          ref="menuTreeRef"
          :data="menuTree"
          :props="{ children: 'children', label: 'title' }"
          node-key="id"
          show-checkbox
          check-strictly
          :default-checked-keys="selectedMenus"
          class="menu-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <el-icon v-if="data.icon" class="node-icon">
                <component :is="data.icon" />
              </el-icon>
              <span class="node-label">{{ node.label }}</span>
              <el-tag v-if="data.path" size="small" type="primary">{{ data.path }}</el-tag>
            </div>
          </template>
        </el-tree>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="menuDialogVisible = false">取消</el-button>
          <el-button @click="handleExpandAllMenus">展开全部</el-button>
          <el-button @click="handleCollapseAllMenus">收起全部</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSaveMenus">
            保存菜单
          </el-button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Plus, DocumentCopy, Edit, Delete, Key, Menu, View } from '@element-plus/icons-vue'
import { getRoleList, deleteRole, bulkDeleteRoles, assignRolePermissions, assignRoleMenus, createRole, updateRole, getRoleDetail, getRolePermissions, getRoleMenus } from '@/api/role'
import { getPermissionTree } from '@/api/permission'
import { getMenuTree } from '@/api/menu'
import { formatDateTime } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import SearchForm from '@/components/common/SearchForm.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import type { RoleListItem, PaginationParams, RoleCreateRequest, RoleUpdateRequest } from '@/types'
import type { SearchField } from '@/components/common/SearchForm.vue'
import type { ActionButton } from '@/components/common/ActionButtons.vue'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单配置
const searchForm = reactive({
  name: '',
  code: '',
  is_active: undefined as boolean | undefined
})

const searchFields: SearchField[] = [
  {
    prop: 'name',
    label: '角色名称',
    type: 'input',
    placeholder: '请输入角色名称',
    prefixIcon: UserFilled
  },
  {
    prop: 'code',
    label: '角色代码',
    type: 'input',
    placeholder: '请输入角色代码'
  },
  {
    prop: 'is_active',
    label: '状态',
    type: 'select',
    placeholder: '请选择状态',
    options: [
      { label: '激活', value: true },
      { label: '禁用', value: false }
    ]
  }
]

// 表格数据
const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<RoleListItem[]>([])
const selectedIds = ref<number[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: 80, sortable: true },
  { prop: 'name', label: '角色名称', minWidth: 120 },
  { prop: 'code', label: '角色代码', minWidth: 120 },
  { prop: 'description', label: '描述', minWidth: 200, showOverflowTooltip: true },
  { prop: 'user_count', label: '用户数量', width: 100 },
  { prop: 'permission_count', label: '权限数量', width: 100 },
  { prop: 'is_active', label: '状态', width: 80, slot: 'status' },
  { prop: 'sort_order', label: '排序', width: 80 },
  { prop: 'created_at', label: '创建时间', width: 160, formatter: (row: any) => formatDateTime(row.created_at) },
  { prop: 'actions', label: '操作', width: 280, fixed: 'right', slot: 'actions' }
]

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'add',
    label: '新增角色',
    type: 'primary',
    icon: Plus,
    permission: 'role:create'
  },
  {
    key: 'export',
    label: '导出数据',
    icon: DocumentCopy,
    permission: 'role:export'
  },
  {
    key: 'batchDelete',
    label: '批量删除',
    type: 'danger',
    icon: Delete,
    permission: 'role:delete',
    disabled: computed(() => selectedIds.value.length === 0)
  }
]

// 行操作按钮
const getRowActions = (row: RoleListItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'role:read'
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'role:update'
  },
  {
    key: 'permissions',
    label: '权限分配',
    type: 'success',
    icon: Key,
    permission: 'role:update'
  },
  {
    key: 'menus',
    label: '菜单分配',
    type: 'info',
    icon: Menu,
    permission: 'role:update'
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'role:delete'
  }
]

// 表单对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEditRole.value ? '编辑角色' : '新增角色')
const isEditRole = ref(false)
const currentRoleId = ref<number>()

// 表单数据
const formData = ref<RoleCreateRequest>({
  name: '',
  code: '',
  description: '',
  is_active: true,
  sort_order: 0
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '角色代码只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ]
}

// 表单字段配置
const formFields = [
  {
    prop: 'name',
    label: '角色名称',
    type: 'input',
    placeholder: '请输入角色名称',
    span: 12
  },
  {
    prop: 'code',
    label: '角色代码',
    type: 'input',
    placeholder: '请输入角色代码',
    span: 12
  },
  {
    prop: 'is_active',
    label: '状态',
    type: 'switch',
    activeText: '激活',
    inactiveText: '禁用',
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
    prop: 'description',
    label: '角色描述',
    type: 'textarea',
    placeholder: '请输入角色描述',
    rows: 3,
    span: 24
  }
]

// 权限分配对话框
const permissionDialogVisible = ref(false)
const currentRole = ref<RoleListItem | null>(null)
const permissionTree = ref<any[]>([])
const selectedPermissions = ref<number[]>([])

// 菜单分配对话框
const menuDialogVisible = ref(false)
const menuTree = ref<any[]>([])
const selectedMenus = ref<number[]>([])

// 树形组件引用
const permissionTreeRef = ref()
const menuTreeRef = ref()

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
    
    // 添加状态筛选
    if (searchForm.is_active !== undefined) {
      Object.assign(params, { is_active: searchForm.is_active })
    }
    
    const response = await getRoleList(params)
    const { items, total } = response.data
    
    tableData.value = items
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
  Object.assign(searchForm, {
    name: '',
    code: '',
    is_active: undefined
  })
  pagination.page = 1
  fetchRoleList()
}

/**
 * 头部操作处理
 */
const handleHeaderAction = (action: ActionButton) => {
  switch (action.key) {
    case 'add':
      handleAdd()
      break
    case 'export':
      handleExport()
      break
    case 'batchDelete':
      handleBatchDelete()
      break
  }
}

/**
 * 行操作处理
 */
const handleRowAction = (action: ActionButton) => {
  const row = action.row as RoleListItem
  switch (action.key) {
    case 'view':
      handleView(row)
      break
    case 'edit':
      handleEdit(row)
      break
    case 'permissions':
      handleAssignPermissions(row)
      break
    case 'menus':
      handleAssignMenus(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

/**
 * 处理新增
 */
const handleAdd = () => {
  isEditRole.value = false
  resetForm()
  dialogVisible.value = true
}

/**
 * 处理编辑
 */
const handleEdit = async (row: RoleListItem) => {
  try {
    isEditRole.value = true
    currentRoleId.value = row.id

    // 获取角色详情
    const response = await getRoleDetail(row.id)
    fillForm(response.data)

    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch role detail:', error)
    ElMessage.error('获取角色详情失败')
  }
}

/**
 * 处理查看
 */
const handleView = async (row: RoleListItem) => {
  try {
    isEditRole.value = false

    // 获取角色详情
    const response = await getRoleDetail(row.id)
    fillForm(response.data)

    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch role detail:', error)
    ElMessage.error('获取角色详情失败')
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
        type: 'warning'
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
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个角色吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await bulkDeleteRoles({ ids: selectedIds.value, action: 'delete' })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete roles:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: RoleListItem[]) => {
  selectedIds.value = selection.map(item => item.id)
}

/**
 * 处理排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  console.log('Sort change:', prop, order)
}

/**
 * 处理页面变化
 */
const handlePageChange = (page: number) => {
  pagination.page = page
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
 * 处理导出
 */
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

/**
 * 处理权限分配
 */
const handleAssignPermissions = async (row: RoleListItem) => {
  try {
    currentRole.value = row

    // 获取权限树
    const permissionResponse = await getPermissionTree()
    permissionTree.value = permissionResponse.data

    // 获取角色已有权限
    const rolePermissionResponse = await getRolePermissions(row.id)
    selectedPermissions.value = rolePermissionResponse.data.permission_ids

    permissionDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch permissions:', error)
    ElMessage.error('获取权限数据失败')
  }
}

/**
 * 处理菜单分配
 */
const handleAssignMenus = async (row: RoleListItem) => {
  try {
    currentRole.value = row

    // 获取菜单树
    const menuResponse = await getMenuTree()
    menuTree.value = menuResponse.data

    // 获取角色已有菜单
    const roleMenuResponse = await getRoleMenus(row.id)
    selectedMenus.value = roleMenuResponse.data.menu_ids

    menuDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch menus:', error)
    ElMessage.error('获取菜单数据失败')
  }
}

/**
 * 保存权限分配
 */
const handleSavePermissions = async () => {
  if (!currentRole.value) return

  try {
    const checkedKeys = permissionTreeRef.value?.getCheckedKeys() || []
    const halfCheckedKeys = permissionTreeRef.value?.getHalfCheckedKeys() || []
    const allPermissionIds = [...checkedKeys, ...halfCheckedKeys]

    await assignRolePermissions(currentRole.value.id, {
      permission_ids: allPermissionIds
    })

    ElMessage.success('权限分配成功')
    permissionDialogVisible.value = false
    // 刷新角色列表
    fetchRoleList()
  } catch (error) {
    console.error('Failed to assign permissions:', error)
    ElMessage.error('权限分配失败')
  }
}

/**
 * 保存菜单分配
 */
const handleSaveMenus = async () => {
  if (!currentRole.value) return

  try {
    const checkedKeys = menuTreeRef.value?.getCheckedKeys() || []
    const halfCheckedKeys = menuTreeRef.value?.getHalfCheckedKeys() || []
    const allMenuIds = [...checkedKeys, ...halfCheckedKeys]

    await assignRoleMenus(currentRole.value.id, {
      menu_ids: allMenuIds
    })

    ElMessage.success('菜单分配成功')
    menuDialogVisible.value = false
    // 刷新角色列表
    fetchRoleList()
  } catch (error) {
    console.error('Failed to assign menus:', error)
    ElMessage.error('菜单分配失败')
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    name: '',
    code: '',
    description: '',
    is_active: true,
    sort_order: 0
  }
  if (roleFormRef.value) {
    roleFormRef.value.clearValidate()
  }
}

/**
 * 填充表单数据
 */
const fillForm = (role: any) => {
  formData.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
    is_active: role.is_active,
    sort_order: role.sort_order || 0
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async (data: any) => {
  try {
    submitLoading.value = true

    if (isEditRole.value && currentRoleId.value) {
      await updateRole(currentRoleId.value, data)
      ElMessage.success('角色更新成功')
    } else {
      await createRole(data)
      ElMessage.success('角色创建成功')
    }

    dialogVisible.value = false
    fetchRoleList()
  } catch (error) {
    console.error('Failed to submit role:', error)
    ElMessage.error(isEditRole.value ? '角色更新失败' : '角色创建失败')
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
  currentRoleId.value = undefined
}

/**
 * 展开全部权限
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
 * 收起全部权限
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
 * 展开全部菜单
 */
const handleExpandAllMenus = () => {
  const tree = menuTreeRef.value
  if (tree) {
    const expandAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, true)
        if (node.children) {
          expandAll(node.children)
        }
      })
    }
    expandAll(menuTree.value)
  }
}

/**
 * 收起全部菜单
 */
const handleCollapseAllMenus = () => {
  const tree = menuTreeRef.value
  if (tree) {
    const collapseAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, false)
        if (node.children) {
          collapseAll(node.children)
        }
      })
    }
    collapseAll(menuTree.value)
  }
}

onMounted(() => {
  fetchRoleList()
})
</script>

<style lang="scss" scoped>
// 权限对话框样式
.permission-dialog,
.menu-dialog {
  .dialog-header {
    margin-bottom: 20px;
  }

  .permission-content,
  .menu-content {
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid var(--el-border-color);
    border-radius: 6px;
    padding: 12px;
    background-color: var(--el-bg-color-page);
  }

  .permission-tree,
  .menu-tree {
    .tree-node {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;

      .node-icon {
        font-size: 16px;
        color: var(--el-color-primary);
      }

      .node-label {
        flex: 1;
        font-size: 14px;
      }

      .el-tag {
        font-size: 12px;
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .permission-dialog,
  .menu-dialog {
    :deep(.el-dialog) {
      width: 95% !important;
      margin: 5vh auto;
    }

    .permission-content,
    .menu-content {
      max-height: 300px;
    }

    .dialog-footer {
      flex-direction: column;
      gap: 8px;

      .el-button {
        width: 100%;
      }
    }
  }
}

// 暗色主题适配
.dark {
  .permission-dialog,
  .menu-dialog {
    .permission-content,
    .menu-content {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);
    }

    .tree-node {
      .node-icon {
        color: var(--el-color-primary-light-3);
      }

      .node-label {
        color: var(--el-text-color-primary);
      }
    }
  }
}

// 树形组件优化
:deep(.el-tree) {
  .el-tree-node {
    .el-tree-node__content {
      height: 36px;
      padding: 0 8px;
      border-radius: 4px;
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--el-color-primary-light-9);
      }
    }

    .el-tree-node__expand-icon {
      color: var(--el-color-primary);
    }

    .el-checkbox {
      margin-right: 8px;
    }
  }
}
</style>
