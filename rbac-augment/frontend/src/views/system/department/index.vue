<template>
  <PageContainer
    title="部门管理"
    description="管理组织架构和部门信息，支持层级结构和人员分配"
    :icon="OfficeBuilding"
    badge="Org"
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

    <!-- 搜索筛选区域 -->
    <SearchForm
      v-model="searchForm"
      :fields="searchFields"
      :loading="loading"
      :show-advanced="false"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 部门组织架构 -->
    <div class="department-layout">
      <!-- 左侧：部门树 -->
      <el-card shadow="never" class="tree-card">
        <template #header>
          <div class="tree-header">
            <div class="header-left">
              <el-icon class="header-icon"><OfficeBuilding /></el-icon>
              <span class="header-title">组织架构</span>
            </div>
            <div class="header-right">
              <el-button size="small" :icon="Expand" @click="handleExpandAll">展开全部</el-button>
              <el-button size="small" :icon="Fold" @click="handleCollapseAll">收起全部</el-button>
            </div>
          </div>
        </template>

        <el-tree
          ref="departmentTreeRef"
          v-loading="loading"
          :data="filteredDepartmentTree"
          :props="treeProps"
          node-key="id"
          :default-expand-all="false"
          :expand-on-click-node="false"
          :highlight-current="true"
          class="department-tree"
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <div class="node-content">
                <el-icon class="node-icon">
                  <component :is="getNodeIcon(data)" />
                </el-icon>
                <div class="node-info">
                  <div class="node-name">{{ data.name }}</div>
                  <div class="node-details">
                    <el-tag size="small" type="info">{{ data.code }}</el-tag>
                    <el-tag v-if="data.employee_count" size="small" type="primary">
                      {{ data.employee_count }}人
                    </el-tag>
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

      <!-- 右侧：部门详情 -->
      <el-card shadow="never" class="detail-card">
        <template #header>
          <div class="detail-header">
            <div class="header-left">
              <el-icon class="header-icon"><InfoFilled /></el-icon>
              <span class="header-title">部门详情</span>
            </div>
          </div>
        </template>

        <div v-if="selectedDepartment" class="department-detail">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h4 class="section-title">基本信息</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="部门名称">
                {{ selectedDepartment.name }}
              </el-descriptions-item>
              <el-descriptions-item label="部门编码">
                {{ selectedDepartment.code }}
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                {{ selectedDepartment.manager_name || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="联系电话">
                {{ selectedDepartment.phone || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="部门状态">
                <StatusTag :status="selectedDepartment.status" />
              </el-descriptions-item>
              <el-descriptions-item label="员工数量">
                {{ selectedDepartment.employee_count || 0 }}人
              </el-descriptions-item>
              <el-descriptions-item label="创建时间" :span="2">
                {{ formatDateTime(selectedDepartment.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="部门描述" :span="2">
                {{ selectedDepartment.description || '暂无描述' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 部门员工 -->
          <div class="detail-section">
            <h4 class="section-title">部门员工</h4>
            <el-table
              :data="departmentEmployees"
              size="small"
              stripe
            >
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="email" label="邮箱" min-width="150" />
              <el-table-column prop="phone" label="电话" width="120" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <StatusTag :status="row.is_active" size="small" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <el-empty v-else description="请选择一个部门查看详情" />
      </el-card>
    </div>

    <!-- 部门表单对话框 -->
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
  OfficeBuilding, Plus, Refresh, Expand, Fold,
  View, Edit, Delete, Download, InfoFilled, User
} from '@element-plus/icons-vue'
import {
  getDepartmentTree,
  deleteDepartment,
  createDepartment,
  updateDepartment,
  getDepartmentDetail,
  getDepartmentEmployees
} from '@/api/department'
import { formatDateTime } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import PageContainer from '@/components/common/PageContainer.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import SearchForm from '@/components/common/SearchForm.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import type { SearchField } from '@/components/common/SearchForm.vue'
import type { ActionButton } from '@/components/common/ActionButtons.vue'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单配置
const searchForm = reactive({
  name: '',
  code: '',
  status: undefined as string | undefined
})

const searchFields: SearchField[] = [
  {
    prop: 'name',
    label: '部门名称',
    type: 'input',
    placeholder: '请输入部门名称',
    prefixIcon: OfficeBuilding
  },
  {
    prop: 'code',
    label: '部门编码',
    type: 'input',
    placeholder: '请输入部门编码'
  },
  {
    prop: 'status',
    label: '部门状态',
    type: 'select',
    placeholder: '请选择状态',
    options: [
      { label: '正常', value: 'normal' },
      { label: '暂停', value: 'suspended' },
      { label: '禁用', value: 'disabled' }
    ]
  }
]

// 数据状态
const loading = ref(false)
const submitLoading = ref(false)
const departmentTree = ref<any[]>([])
const selectedDepartment = ref<any>(null)
const departmentEmployees = ref<any[]>([])

// 树形组件引用
const departmentTreeRef = ref()

// 树形属性
const treeProps = {
  children: 'children',
  label: 'name'
}

// 获取节点图标
const getNodeIcon = (node: any) => {
  if (node.children && node.children.length > 0) {
    return OfficeBuilding
  }
  return User
}

// 过滤后的部门树
const filteredDepartmentTree = computed(() => {
  if (!searchForm.name && !searchForm.code && !searchForm.status) {
    return departmentTree.value
  }

  const filterTree = (nodes: any[]): any[] => {
    return nodes.filter(node => {
      let match = true

      if (searchForm.name) {
        match = match && node.name.toLowerCase().includes(searchForm.name.toLowerCase())
      }

      if (searchForm.code) {
        match = match && node.code && node.code.toLowerCase().includes(searchForm.code.toLowerCase())
      }

      if (searchForm.status) {
        match = match && node.status === searchForm.status
      }

      // 如果当前节点匹配，返回整个节点（包括子节点）
      if (match) {
        return true
      }

      // 如果当前节点不匹配，检查子节点
      if (node.children && node.children.length > 0) {
        const filteredChildren = filterTree(node.children)
        if (filteredChildren.length > 0) {
          node.children = filteredChildren
          return true
        }
      }

      return false
    })
  }

  return filterTree([...departmentTree.value])
})

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'add',
    label: '新增部门',
    type: 'primary',
    icon: Plus,
    permission: 'department:create'
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
    permission: 'department:export'
  }
]

// 树节点操作按钮
const getTreeNodeActions = (node: any): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'department:read',
    row: node
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'department:update',
    row: node
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'department:delete',
    disabled: node.children && node.children.length > 0,
    row: node
  }
]

// 表单对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑部门' : '新增部门')
const isEdit = ref(false)
const currentDepartmentId = ref<number>()

// 表单数据
const formData = ref({
  name: '',
  code: '',
  parent_id: null,
  manager_id: null,
  manager_name: '',
  phone: '',
  email: '',
  address: '',
  description: '',
  sort_order: 0,
  status: 'normal'
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 50, message: '部门名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '部门编码只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ]
}

// 表单字段配置
const formFields = [
  {
    prop: 'name',
    label: '部门名称',
    type: 'input',
    placeholder: '请输入部门名称',
    span: 12
  },
  {
    prop: 'code',
    label: '部门编码',
    type: 'input',
    placeholder: '请输入部门编码',
    span: 12
  },
  {
    prop: 'parent_id',
    label: '上级部门',
    type: 'cascader',
    placeholder: '请选择上级部门',
    options: computed(() => departmentOptions.value),
    props: { checkStrictly: true, emitPath: false },
    span: 12
  },
  {
    prop: 'manager_name',
    label: '部门负责人',
    type: 'input',
    placeholder: '请输入负责人姓名',
    span: 12
  },
  {
    prop: 'phone',
    label: '联系电话',
    type: 'input',
    placeholder: '请输入联系电话',
    span: 12
  },
  {
    prop: 'email',
    label: '邮箱地址',
    type: 'input',
    placeholder: '请输入邮箱地址',
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
    prop: 'status',
    label: '部门状态',
    type: 'select',
    placeholder: '请选择状态',
    options: [
      { label: '正常', value: 'normal' },
      { label: '暂停', value: 'suspended' },
      { label: '禁用', value: 'disabled' }
    ],
    span: 12
  },
  {
    prop: 'address',
    label: '办公地址',
    type: 'input',
    placeholder: '请输入办公地址',
    span: 24
  },
  {
    prop: 'description',
    label: '部门描述',
    type: 'textarea',
    placeholder: '请输入部门描述',
    rows: 3,
    span: 24
  }
]

// 部门选项
const departmentOptions = ref<any[]>([])

/**
 * 获取部门树
 */
const fetchDepartmentTree = async () => {
  try {
    loading.value = true
    const response = await getDepartmentTree()
    departmentTree.value = response.data
    // 同时获取部门选项用于表单
    departmentOptions.value = buildDepartmentOptions(response.data)
  } catch (error) {
    console.error('Failed to fetch department tree:', error)
    ElMessage.error('获取部门树失败')
  } finally {
    loading.value = false
  }
}

/**
 * 构建部门选项
 */
const buildDepartmentOptions = (departments: any[]): any[] => {
  return departments.map(dept => ({
    value: dept.id,
    label: dept.name,
    children: dept.children ? buildDepartmentOptions(dept.children) : undefined
  }))
}

/**
 * 获取部门员工
 */
const fetchDepartmentEmployees = async (departmentId: number) => {
  try {
    const response = await getDepartmentEmployees(departmentId)
    departmentEmployees.value = response.data
  } catch (error) {
    console.error('Failed to fetch department employees:', error)
    departmentEmployees.value = []
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  // 搜索逻辑已在 computed 中实现
}

/**
 * 重置处理
 */
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    code: '',
    status: undefined
  })
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
 * 树节点点击处理
 */
const handleNodeClick = async (data: any) => {
  selectedDepartment.value = data
  await fetchDepartmentEmployees(data.id)
}

/**
 * 刷新数据
 */
const handleRefresh = () => {
  fetchDepartmentTree()
}

/**
 * 导出数据
 */
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

/**
 * 展开全部
 */
const handleExpandAll = () => {
  const tree = departmentTreeRef.value
  if (tree) {
    const expandAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, true)
        if (node.children) {
          expandAll(node.children)
        }
      })
    }
    expandAll(departmentTree.value)
  }
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  const tree = departmentTreeRef.value
  if (tree) {
    const collapseAll = (nodes: any[]) => {
      nodes.forEach(node => {
        tree.setExpanded(node.id, false)
        if (node.children) {
          collapseAll(node.children)
        }
      })
    }
    collapseAll(departmentTree.value)
  }
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
  selectedDepartment.value = row
  await fetchDepartmentEmployees(row.id)
}

/**
 * 处理编辑
 */
const handleEdit = async (row: any) => {
  try {
    isEdit.value = true
    currentDepartmentId.value = row.id
    const response = await getDepartmentDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch department detail:', error)
    ElMessage.error('获取部门详情失败')
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteDepartment(row.id)
    ElMessage.success('删除成功')
    fetchDepartmentTree()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete department:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    name: '',
    code: '',
    parent_id: null,
    manager_id: null,
    manager_name: '',
    phone: '',
    email: '',
    address: '',
    description: '',
    sort_order: 0,
    status: 'normal'
  }
}

/**
 * 填充表单数据
 */
const fillForm = (department: any) => {
  formData.value = {
    name: department.name,
    code: department.code,
    parent_id: department.parent_id,
    manager_id: department.manager_id,
    manager_name: department.manager_name || '',
    phone: department.phone || '',
    email: department.email || '',
    address: department.address || '',
    description: department.description || '',
    sort_order: department.sort_order || 0,
    status: department.status || 'normal'
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async (data: any) => {
  try {
    submitLoading.value = true

    if (isEdit.value && currentDepartmentId.value) {
      await updateDepartment(currentDepartmentId.value, data)
      ElMessage.success('部门更新成功')
    } else {
      await createDepartment(data)
      ElMessage.success('部门创建成功')
    }

    dialogVisible.value = false
    fetchDepartmentTree()
  } catch (error) {
    console.error('Failed to submit department:', error)
    ElMessage.error(isEdit.value ? '部门更新失败' : '部门创建失败')
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
  currentDepartmentId.value = undefined
}

onMounted(() => {
  fetchDepartmentTree()
})
</script>
<style lang="scss" scoped>
// 部门布局样式
.department-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;

  .tree-card,
  .detail-card {
    height: 600px;

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-light);
    }

    :deep(.el-card__body) {
      padding: 20px;
      height: calc(100% - 60px);
      overflow-y: auto;
    }
  }

  .tree-header,
  .detail-header {
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

// 部门树样式
.department-tree {
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

  :deep(.el-tree-node) {
    .el-tree-node__content {
      height: auto;
      min-height: 40px;
      padding: 8px 0;

      &:hover {
        background-color: var(--el-color-primary-light-9);
      }
    }

    .el-tree-node__expand-icon {
      color: var(--el-color-primary);
    }
  }
}

// 部门详情样式
.department-detail {
  .detail-section {
    margin-bottom: 24px;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--el-border-color-lighter);
    }

    .el-descriptions {
      margin-bottom: 16px;
    }

    .el-table {
      margin-top: 12px;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .department-layout {
    grid-template-columns: 1fr;
    gap: 16px;

    .tree-card,
    .detail-card {
      height: 500px;
    }
  }
}

@media (max-width: 768px) {
  .department-layout {
    .tree-card,
    .detail-card {
      height: 400px;

      .tree-header,
      .detail-header {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;

        .header-right {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
  }

  .department-tree {
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
        align-self: flex-end;
      }
    }
  }

  .department-detail {
    .detail-section {
      .el-descriptions {
        :deep(.el-descriptions__body) {
          .el-descriptions__table {
            .el-descriptions__cell {
              padding: 8px;
            }
          }
        }
      }
    }
  }
}

// 暗色主题适配
.dark {
  .department-layout {
    .tree-card,
    .detail-card {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);
    }
  }

  .department-tree {
    :deep(.el-tree-node) {
      .el-tree-node__content {
        &:hover {
          background-color: var(--el-color-primary-dark-2);
        }
      }
    }
  }
}
</style>
