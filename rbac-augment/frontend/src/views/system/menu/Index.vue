<template>
  <PageContainer
    title="菜单管理"
    description="管理系统菜单结构，包括菜单的创建、编辑、删除和排序"
    :icon="Menu"
    badge="Tree"
    badge-type="info"
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

    <!-- 菜单树表格 -->
    <el-card shadow="never" class="menu-tree-card">
      <template #header>
        <div class="tree-header">
          <div class="header-left">
            <el-icon class="header-icon"><Menu /></el-icon>
            <span class="header-title">菜单树结构</span>
          </div>
          <div class="header-right">
            <el-button size="small" :icon="Expand" @click="handleExpandAll">展开全部</el-button>
            <el-button size="small" :icon="Fold" @click="handleCollapseAll">收起全部</el-button>
          </div>
        </div>
      </template>

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
              <span class="title-text">{{ row.title }}</span>
              <el-tag v-if="row.badge" size="small" :type="row.badgeType || 'primary'">
                {{ row.badge }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="路由名称" width="150" />
        <el-table-column prop="path" label="路由路径" min-width="180" />
        <el-table-column prop="component" label="组件路径" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <StatusTag
              :status="getMenuType(row)"
              :status-map="menuTypeMap"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <StatusTag :status="row.is_visible" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="外链" width="80">
          <template #default="{ row }">
            <StatusTag
              :status="row.is_external"
              :status-map="{ true: { text: '外链', type: 'danger' }, false: { text: '内部', type: 'info' } }"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column label="缓存" width="80">
          <template #default="{ row }">
            <StatusTag
              :status="row.cache"
              :status-map="{ true: { text: '缓存', type: 'success' }, false: { text: '不缓存', type: 'info' } }"
              size="small"
            />
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <ActionButtons
              :actions="getRowActions(row)"
              :permissions="userPermissions"
              size="small"
              compact
              @action="handleRowAction"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 菜单表单对话框 -->
    <FormDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :form-data="formData"
      :form-rules="formRules"
      :form-fields="formFields"
      :loading="submitLoading"
      width="900px"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Menu, Plus, Refresh, Expand, Fold,
  View, Edit, Delete, DocumentCopy
} from '@element-plus/icons-vue'
import {
  getMenuTree,
  deleteMenu,
  createMenu,
  updateMenu,
  getMenuDetail
} from '@/api/menu'
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
  title: '',
  path: '',
  is_visible: undefined as boolean | undefined
})

const searchFields: SearchField[] = [
  {
    prop: 'title',
    label: '菜单名称',
    type: 'input',
    placeholder: '请输入菜单名称',
    prefixIcon: Menu
  },
  {
    prop: 'path',
    label: '路由路径',
    type: 'input',
    placeholder: '请输入路由路径'
  },
  {
    prop: 'is_visible',
    label: '显示状态',
    type: 'select',
    placeholder: '请选择显示状态',
    options: [
      { label: '显示', value: true },
      { label: '隐藏', value: false }
    ]
  }
]

// 数据状态
const loading = ref(false)
const submitLoading = ref(false)
const menuTree = ref<any[]>([])
const tableRef = ref()

// 菜单类型映射
const menuTypeMap = {
  directory: { text: '目录', type: 'warning', icon: 'Folder' },
  menu: { text: '菜单', type: 'success', icon: 'Document' },
  button: { text: '按钮', type: 'info', icon: 'Operation' }
}

// 获取菜单类型
const getMenuType = (menu: any) => {
  if (menu.children && menu.children.length > 0) {
    return 'directory'
  }
  return menu.type || 'menu'
}

// 过滤后的菜单树
const filteredMenuTree = computed(() => {
  if (!searchForm.title && !searchForm.path && searchForm.is_visible === undefined) {
    return menuTree.value
  }

  const filterTree = (nodes: any[]): any[] => {
    return nodes.filter(node => {
      let match = true

      if (searchForm.title) {
        match = match && node.title.toLowerCase().includes(searchForm.title.toLowerCase())
      }

      if (searchForm.path) {
        match = match && node.path && node.path.toLowerCase().includes(searchForm.path.toLowerCase())
      }

      if (searchForm.is_visible !== undefined) {
        match = match && node.is_visible === searchForm.is_visible
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

  return filterTree([...menuTree.value])
})

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'add',
    label: '新增菜单',
    type: 'primary',
    icon: Plus,
    permission: 'menu:create'
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
    icon: DocumentCopy,
    permission: 'menu:export'
  }
]

// 行操作按钮
const getRowActions = (row: any): ActionButton[] => [
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

// 表单对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑菜单' : '新增菜单')
const isEdit = ref(false)
const currentMenuId = ref<number>()

// 表单数据
const formData = ref({
  title: '',
  name: '',
  path: '',
  component: '',
  icon: '',
  parent_id: null,
  sort_order: 0,
  is_visible: true,
  is_external: false,
  cache: false,
  redirect: '',
  meta: {
    title: '',
    icon: '',
    noCache: false,
    affix: false,
    breadcrumb: true,
    activeMenu: ''
  }
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入菜单名称', trigger: 'blur' },
    { min: 2, max: 50, message: '菜单名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入路由名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9]*$/, message: '路由名称只能包含字母和数字，且以字母开头', trigger: 'blur' }
  ],
  path: [
    { required: true, message: '请输入路由路径', trigger: 'blur' }
  ]
}

// 表单字段配置
const formFields = [
  {
    prop: 'title',
    label: '菜单名称',
    type: 'input',
    placeholder: '请输入菜单名称',
    span: 12
  },
  {
    prop: 'name',
    label: '路由名称',
    type: 'input',
    placeholder: '请输入路由名称',
    span: 12
  },
  {
    prop: 'path',
    label: '路由路径',
    type: 'input',
    placeholder: '请输入路由路径',
    span: 12
  },
  {
    prop: 'component',
    label: '组件路径',
    type: 'input',
    placeholder: '请输入组件路径',
    span: 12
  },
  {
    prop: 'parent_id',
    label: '父级菜单',
    type: 'cascader',
    placeholder: '请选择父级菜单',
    options: computed(() => menuOptions.value),
    props: { checkStrictly: true, emitPath: false },
    span: 12
  },
  {
    prop: 'icon',
    label: '菜单图标',
    type: 'input',
    placeholder: '请输入图标名称',
    span: 12
  },
  {
    prop: 'sort_order',
    label: '排序',
    type: 'number',
    min: 0,
    max: 999,
    span: 8
  },
  {
    prop: 'is_visible',
    label: '是否显示',
    type: 'switch',
    activeText: '显示',
    inactiveText: '隐藏',
    span: 8
  },
  {
    prop: 'is_external',
    label: '外部链接',
    type: 'switch',
    activeText: '是',
    inactiveText: '否',
    span: 8
  },
  {
    prop: 'cache',
    label: '页面缓存',
    type: 'switch',
    activeText: '缓存',
    inactiveText: '不缓存',
    span: 12
  },
  {
    prop: 'redirect',
    label: '重定向',
    type: 'input',
    placeholder: '请输入重定向路径',
    span: 12
  }
]

// 菜单选项
const menuOptions = ref<any[]>([])

/**
 * 获取菜单树
 */
const fetchMenuTree = async () => {
  try {
    loading.value = true
    const response = await getMenuTree()
    menuTree.value = response.data
    // 同时获取菜单选项用于表单
    menuOptions.value = buildMenuOptions(response.data)
  } catch (error) {
    console.error('Failed to fetch menu tree:', error)
    ElMessage.error('获取菜单树失败')
  } finally {
    loading.value = false
  }
}

/**
 * 构建菜单选项
 */
const buildMenuOptions = (menus: any[]): any[] => {
  return menus.map(menu => ({
    value: menu.id,
    label: menu.title,
    children: menu.children ? buildMenuOptions(menu.children) : undefined
  }))
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
    title: '',
    path: '',
    is_visible: undefined
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
 * 行操作处理
 */
const handleRowAction = (action: ActionButton) => {
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
 * 刷新数据
 */
const handleRefresh = () => {
  fetchMenuTree()
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
    const response = await getMenuDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch menu detail:', error)
    ElMessage.error('获取菜单详情失败')
  }
}

/**
 * 处理编辑
 */
const handleEdit = async (row: any) => {
  try {
    isEdit.value = true
    currentMenuId.value = row.id
    const response = await getMenuDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch menu detail:', error)
    ElMessage.error('获取菜单详情失败')
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除菜单 "${row.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
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
  const table = tableRef.value
  if (table) {
    const expandAll = (data: any[]) => {
      data.forEach(item => {
        table.toggleRowExpansion(item, true)
        if (item.children && item.children.length > 0) {
          expandAll(item.children)
        }
      })
    }
    expandAll(menuTree.value)
  }
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  const table = tableRef.value
  if (table) {
    const collapseAll = (data: any[]) => {
      data.forEach(item => {
        table.toggleRowExpansion(item, false)
        if (item.children && item.children.length > 0) {
          collapseAll(item.children)
        }
      })
    }
    collapseAll(menuTree.value)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    title: '',
    name: '',
    path: '',
    component: '',
    icon: '',
    parent_id: null,
    sort_order: 0,
    is_visible: true,
    is_external: false,
    cache: false,
    redirect: '',
    meta: {
      title: '',
      icon: '',
      noCache: false,
      affix: false,
      breadcrumb: true,
      activeMenu: ''
    }
  }
}

/**
 * 填充表单数据
 */
const fillForm = (menu: any) => {
  formData.value = {
    title: menu.title,
    name: menu.name,
    path: menu.path,
    component: menu.component || '',
    icon: menu.icon || '',
    parent_id: menu.parent_id,
    sort_order: menu.sort_order || 0,
    is_visible: menu.is_visible !== undefined ? menu.is_visible : true,
    is_external: menu.is_external || false,
    cache: menu.cache || false,
    redirect: menu.redirect || '',
    meta: menu.meta || {
      title: menu.title,
      icon: menu.icon || '',
      noCache: !menu.cache,
      affix: false,
      breadcrumb: true,
      activeMenu: ''
    }
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async (data: any) => {
  try {
    submitLoading.value = true

    if (isEdit.value && currentMenuId.value) {
      await updateMenu(currentMenuId.value, data)
      ElMessage.success('菜单更新成功')
    } else {
      await createMenu(data)
      ElMessage.success('菜单创建成功')
    }

    dialogVisible.value = false
    fetchMenuTree()
  } catch (error) {
    console.error('Failed to submit menu:', error)
    ElMessage.error(isEdit.value ? '菜单更新失败' : '菜单创建失败')
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
  currentMenuId.value = undefined
}

onMounted(() => {
  fetchMenuTree()
})
</script>

<style lang="scss" scoped>
// 菜单树卡片样式
.menu-tree-card {
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

// 菜单树表格样式
.menu-tree-table {
  .menu-title {
    display: flex;
    align-items: center;
    gap: 8px;

    .menu-icon {
      font-size: 16px;
      color: var(--el-color-primary);
    }

    .title-text {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .el-tag {
      margin-left: 8px;
    }
  }

  // 表格行样式优化
  :deep(.el-table__row) {
    &:hover {
      background-color: var(--el-color-primary-light-9);
    }
  }

  // 树形表格缩进优化
  :deep(.el-table__indent) {
    padding-left: 20px;
  }

  // 展开图标样式
  :deep(.el-table__expand-icon) {
    color: var(--el-color-primary);
    font-size: 14px;

    &.el-table__expand-icon--expanded {
      transform: rotate(90deg);
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .menu-tree-card {
    .tree-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;

      .header-right {
        width: 100%;
        justify-content: flex-end;
      }
    }
  }

  .menu-tree-table {
    // 移动端隐藏部分列
    :deep(.el-table__header-wrapper),
    :deep(.el-table__body-wrapper) {
      .el-table__cell:nth-child(4),
      .el-table__cell:nth-child(5),
      .el-table__cell:nth-child(6),
      .el-table__cell:nth-child(7) {
        display: none;
      }
    }

    .menu-title {
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;

      .el-tag {
        margin-left: 0;
        margin-top: 4px;
      }
    }
  }
}

// 暗色主题适配
.dark {
  .menu-tree-card {
    background-color: var(--el-bg-color-page);
    border-color: var(--el-border-color);

    .tree-header {
      .header-title {
        color: var(--el-text-color-primary);
      }
    }
  }

  .menu-tree-table {
    background-color: var(--el-bg-color-page);

    .menu-title {
      .title-text {
        color: var(--el-text-color-primary);
      }
    }

    :deep(.el-table__row) {
      background-color: var(--el-bg-color-page);

      &:hover {
        background-color: var(--el-color-primary-dark-2);
      }
    }
  }
}

// 表格加载状态优化
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);

  .el-loading-spinner {
    .el-loading-text {
      color: var(--el-color-primary);
    }
  }
}

.dark {
  :deep(.el-loading-mask) {
    background-color: rgba(0, 0, 0, 0.8);
  }
}
</style>
