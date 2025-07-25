<template>
  <PageContainer
    title="菜单管理"
    description="管理系统菜单结构，包括菜单的创建、编辑、删除和排序"
    :icon="Menu"
    badge="Beta"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <el-button
        v-permission="['menu:create']"
        type="primary"
        :icon="Plus"
        @click="handleAdd"
      >
        新增菜单
      </el-button>
      <el-button
        v-permission="['menu:export']"
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
              <el-form-item label="菜单名称">
                <el-input
                  v-model="searchForm.title"
                  placeholder="请输入菜单名称"
                  clearable
                  :prefix-icon="Search"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="路由路径">
                <el-input
                  v-model="searchForm.path"
                  placeholder="请输入路由路径"
                  clearable
                  :prefix-icon="Link"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="状态">
                <el-select
                  v-model="searchForm.is_active"
                  placeholder="请选择菜单状态"
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

    <!-- 菜单树表格 -->
    <el-card shadow="never" class="menu-tree-card">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="filteredMenuTree"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        stripe
        border
        class="menu-tree-table"
      >
        <el-table-column prop="title" label="菜单名称" min-width="200">
          <template #default="{ row }">
            <div class="menu-title">
              <el-icon v-if="row.icon" class="menu-icon">
                <component :is="row.icon" />
              </el-icon>
              <span>{{ row.title }}</span>
              <el-tag v-if="row.type" :type="getTypeTagType(row.type)" size="small">
                {{ row.type }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="path" label="路由路径" min-width="150" show-overflow-tooltip />
        
        <el-table-column prop="component" label="组件路径" min-width="150" show-overflow-tooltip />
        
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

        <el-table-column prop="is_hidden" label="隐藏" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_hidden ? 'danger' : 'success'" size="small">
              {{ row.is_hidden ? '隐藏' : '显示' }}
            </el-tag>
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

    <!-- 菜单表单对话框 -->
    <MenuForm
      v-model:visible="formVisible"
      :form-data="formData"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 菜单详情对话框 -->
    <MenuDetail
      v-model:visible="detailVisible"
      :menu-id="selectedMenuId"
    />
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Menu,
  Plus,
  DocumentCopy,
  Search,
  Link,
  Refresh,
  CircleCheck,
  CircleClose,
  Expand,
  Fold,
  View,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { getMenuTree, deleteMenu, updateMenuStatus } from '@/api/menu'
import { formatDateTime } from '@/utils'
import type { MenuTreeItem, ActionButton } from '@/types'
import PageContainer from '@/components/common/PageContainer.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import MenuForm from './components/MenuForm.vue'
import MenuDetail from './components/MenuDetail.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  title: '',
  path: '',
  is_active: undefined as boolean | undefined
})

// 表格数据
const loading = ref(false)
const tableRef = ref()
const menuTree = ref<MenuTreeItem[]>([])

// 表单对话框
const formVisible = ref(false)
const formType = ref<'add' | 'edit'>('add')
const formData = ref<any>({})

// 详情对话框
const detailVisible = ref(false)
const selectedMenuId = ref<number>()

// 过滤后的菜单树
const filteredMenuTree = computed(() => {
  if (!searchForm.title && !searchForm.path && searchForm.is_active === undefined) {
    return menuTree.value
  }

  const filterTree = (nodes: MenuTreeItem[]): MenuTreeItem[] => {
    return nodes.filter(node => {
      const matchTitle = !searchForm.title || node.title.includes(searchForm.title)
      const matchPath = !searchForm.path || (node.path && node.path.includes(searchForm.path))
      const matchStatus = searchForm.is_active === undefined || node.is_active === searchForm.is_active

      const hasMatchingChildren = node.children && filterTree(node.children).length > 0

      if (matchTitle && matchPath && matchStatus) {
        return true
      }

      return hasMatchingChildren
    }).map(node => ({
      ...node,
      children: node.children ? filterTree(node.children) : undefined
    }))
  }

  return filterTree(menuTree.value)
})

/**
 * 获取菜单树
 */
const fetchMenuTree = async () => {
  try {
    loading.value = true
    const response = await getMenuTree()
    menuTree.value = response.data.map(item => ({
      ...item,
      statusLoading: false
    }))
  } catch (error) {
    console.error('Failed to fetch menu tree:', error)
    ElMessage.error('获取菜单列表失败')
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
    title: '',
    path: '',
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
const handleEdit = (row: MenuTreeItem) => {
  formType.value = 'edit'
  formData.value = { ...row }
  formVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: MenuTreeItem) => {
  selectedMenuId.value = row.id
  detailVisible.value = true
}

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type: string) => {
  switch (type) {
    case '目录':
      return 'primary'
    case '菜单':
      return 'success'
    case '按钮':
      return 'warning'
    default:
      return 'info'
  }
}

// 行操作按钮配置
const getRowActions = (row: MenuTreeItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'menu:read',
    row
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'menu:update',
    row
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'menu:delete',
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
const handleStatusChange = async (row: MenuTreeItem) => {
  try {
    row.statusLoading = true
    await updateMenuStatus(row.id, { is_active: row.is_active })
    ElMessage.success(`菜单已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('Update menu status error:', error)
  } finally {
    row.statusLoading = false
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: MenuTreeItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除菜单 "${row.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>此操作将永久删除该菜单，是否继续？</p>
            <p style="color: #f56c6c; font-size: 12px;">注意：删除后无法恢复</p>
          </div>
        `
      }
    )

    await deleteMenu(row.id)
    ElMessage.success('删除成功')
    fetchMenuTree()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete menu:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 展开全部
 */
const handleExpandAll = () => {
  const expandAll = (data: MenuTreeItem[]) => {
    data.forEach(item => {
      tableRef.value?.toggleRowExpansion(item, true)
      if (item.children && item.children.length > 0) {
        expandAll(item.children)
      }
    })
  }
  expandAll(menuTree.value)
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  const collapseAll = (data: MenuTreeItem[]) => {
    data.forEach(item => {
      tableRef.value?.toggleRowExpansion(item, false)
      if (item.children && item.children.length > 0) {
        collapseAll(item.children)
      }
    })
  }
  collapseAll(menuTree.value)
}

/**
 * 处理表单成功
 */
const handleFormSuccess = () => {
  fetchMenuTree()
}

onMounted(() => {
  fetchMenuTree()
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

// ==================== 菜单树表格样式 ====================
.menu-tree-card {
  border: 1px solid $border-color-light;

  .menu-tree-table {
    .menu-title {
      display: flex;
      align-items: center;
      gap: 8px;

      .menu-icon {
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

  .menu-tree-card {
    background: $dark-card-color;
    border-color: $dark-border-color;
  }
}
</style>
