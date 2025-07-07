<template>
  <PageContainer
    title="部门管理"
    description="管理组织架构和部门信息，支持层级结构和人员分配"
    :icon="OfficeBuilding"
    badge="Beta"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <el-button
        v-permission="['department:create']"
        type="primary"
        :icon="Plus"
        @click="handleAdd"
      >
        新增部门
      </el-button>
      <el-button
        v-permission="['department:export']"
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
              <el-form-item label="部门名称">
                <el-input
                  v-model="searchForm.name"
                  placeholder="请输入部门名称"
                  clearable
                  :prefix-icon="Search"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="部门代码">
                <el-input
                  v-model="searchForm.code"
                  placeholder="请输入部门代码"
                  clearable
                  :prefix-icon="Key"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="状态">
                <el-select
                  v-model="searchForm.is_active"
                  placeholder="请选择部门状态"
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
                <el-button :icon="Expand" @click="handleExpandAll">
                  展开全部
                </el-button>
                <el-button :icon="Fold" @click="handleCollapseAll">
                  收起全部
                </el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </div>

    <!-- 部门树表格 -->
    <el-card shadow="never" class="department-tree-card">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="filteredDepartmentTree"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        stripe
        border
        class="department-tree-table"
      >
        <el-table-column prop="name" label="部门名称" min-width="200">
          <template #default="{ row }">
            <div class="department-name">
              <el-icon class="department-icon">
                <OfficeBuilding />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="code" label="部门代码" min-width="120" show-overflow-tooltip />
        
        <el-table-column prop="manager_name" label="负责人" min-width="100" show-overflow-tooltip />
        
        <el-table-column prop="phone" label="联系电话" min-width="120" show-overflow-tooltip />
        
        <el-table-column prop="user_count" label="人员数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.user_count || 0 }} 人</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :loading="row.statusLoading"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160" />

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <ActionButtons
              :actions="getRowActions(row)"
              :permissions="userPermissions"
              size="small"
              compact
              :max-visible="4"
              @action="handleRowAction"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 部门表单对话框 -->
    <DepartmentForm
      v-model:visible="formVisible"
      :form-data="formData"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 部门详情对话框 -->
    <DepartmentDetail
      v-model:visible="detailVisible"
      :department-id="selectedDepartmentId"
    />
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  OfficeBuilding,
  Plus,
  DocumentCopy,
  Search,
  Key,
  Refresh,
  CircleCheck,
  CircleClose,
  Expand,
  Fold,
  View,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { getDepartmentTree, deleteDepartment, updateDepartmentStatus } from '@/api/department'
import { formatDateTime } from '@/utils'
import type { DepartmentTreeItem, ActionButton } from '@/types'
import PageContainer from '@/components/common/PageContainer.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import DepartmentForm from './components/DepartmentForm.vue'
import DepartmentDetail from './components/DepartmentDetail.vue'
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
const tableRef = ref()
const departmentTree = ref<DepartmentTreeItem[]>([])

// 表单对话框
const formVisible = ref(false)
const formType = ref<'add' | 'edit'>('add')
const formData = ref<any>({})

// 详情对话框
const detailVisible = ref(false)
const selectedDepartmentId = ref<number>()

// 过滤后的部门树
const filteredDepartmentTree = computed(() => {
  if (!searchForm.name && !searchForm.code && searchForm.is_active === undefined) {
    return departmentTree.value
  }

  const filterTree = (nodes: DepartmentTreeItem[]): DepartmentTreeItem[] => {
    return nodes.filter(node => {
      const matchName = !searchForm.name || node.name.includes(searchForm.name)
      const matchCode = !searchForm.code || (node.code && node.code.includes(searchForm.code))
      const matchStatus = searchForm.is_active === undefined || node.is_active === searchForm.is_active

      const hasMatchingChildren = node.children && filterTree(node.children).length > 0

      if (matchName && matchCode && matchStatus) {
        return true
      }

      return hasMatchingChildren
    }).map(node => ({
      ...node,
      children: node.children ? filterTree(node.children) : undefined
    }))
  }

  return filterTree(departmentTree.value)
})

/**
 * 获取部门树
 */
const fetchDepartmentTree = async () => {
  try {
    loading.value = true
    const response = await getDepartmentTree()
    departmentTree.value = response.data.map(item => ({
      ...item,
      statusLoading: false
    }))
  } catch (error) {
    console.error('Failed to fetch department tree:', error)
    ElMessage.error('获取部门列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  // 搜索是通过计算属性实现的，这里不需要额外操作
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
const handleEdit = (row: DepartmentTreeItem) => {
  formType.value = 'edit'
  formData.value = { ...row }
  formVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: DepartmentTreeItem) => {
  selectedDepartmentId.value = row.id
  detailVisible.value = true
}

// 行操作按钮配置
const getRowActions = (row: DepartmentTreeItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'department:read',
    row
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'department:update',
    row
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'department:delete',
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
const handleStatusChange = async (row: DepartmentTreeItem) => {
  try {
    row.statusLoading = true
    await updateDepartmentStatus(row.id, { is_active: row.is_active })
    ElMessage.success(`部门已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('Update department status error:', error)
  } finally {
    row.statusLoading = false
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: DepartmentTreeItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>此操作将永久删除该部门，是否继续？</p>
            <p style="color: #f56c6c; font-size: 12px;">注意：删除后无法恢复</p>
          </div>
        `
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
 * 展开全部
 */
const handleExpandAll = () => {
  const expandAll = (data: DepartmentTreeItem[]) => {
    data.forEach(item => {
      tableRef.value?.toggleRowExpansion(item, true)
      if (item.children && item.children.length > 0) {
        expandAll(item.children)
      }
    })
  }
  expandAll(departmentTree.value)
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  const collapseAll = (data: DepartmentTreeItem[]) => {
    data.forEach(item => {
      tableRef.value?.toggleRowExpansion(item, false)
      if (item.children && item.children.length > 0) {
        collapseAll(item.children)
      }
    })
  }
  collapseAll(departmentTree.value)
}

/**
 * 处理表单成功
 */
const handleFormSuccess = () => {
  fetchDepartmentTree()
}

onMounted(() => {
  fetchDepartmentTree()
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

// ==================== 部门树表格样式 ====================
.department-tree-card {
  border: 1px solid $border-color-light;

  .department-tree-table {
    .department-name {
      display: flex;
      align-items: center;
      gap: 8px;

      .department-icon {
        font-size: 16px;
        color: var(--el-color-primary);
      }
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

  .department-tree-card {
    background: $dark-card-color;
    border-color: $dark-border-color;
  }
}
</style>
