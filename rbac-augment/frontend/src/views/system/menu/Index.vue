<template>
  <div class="menu-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">菜单管理</h2>
      <p class="page-description">管理系统菜单结构，包括菜单的创建、编辑、删除和排序。</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-button
          v-permission="['menu:create']"
          type="primary"
          @click="handleAdd"
        >
          <el-icon><Plus /></el-icon>
          新增菜单
        </el-button>
        <el-button
          type="success"
          @click="handleExpandAll"
        >
          <el-icon><Expand /></el-icon>
          展开全部
        </el-button>
        <el-button
          type="info"
          @click="handleCollapseAll"
        >
          <el-icon><Fold /></el-icon>
          折叠全部
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 菜单树表格 -->
    <div class="menu-table">
      <el-card>
        <el-table
          ref="tableRef"
          v-loading="loading"
          :data="menuTree"
          row-key="id"
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
          stripe
          border
        >
          <el-table-column prop="title" label="菜单名称" min-width="200">
            <template #default="{ row }">
              <div class="menu-title">
                <el-icon v-if="row.icon" class="menu-icon">
                  <component :is="row.icon" />
                </el-icon>
                <span>{{ row.title }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="路由名称" width="150" />
          <el-table-column prop="path" label="路由路径" min-width="180" />
          <el-table-column prop="component" label="组件路径" min-width="200" show-overflow-tooltip />
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.children && row.children.length" type="warning" size="small">
                目录
              </el-tag>
              <el-tag v-else type="success" size="small">
                菜单
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_visible ? 'success' : 'info'" size="small">
                {{ row.is_visible ? '显示' : '隐藏' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="外链" width="60">
            <template #default="{ row }">
              <el-tag v-if="row.is_external" type="danger" size="small">
                是
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="缓存" width="60">
            <template #default="{ row }">
              <el-tag v-if="row.cache" type="success" size="small">
                是
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  v-permission="['menu:read']"
                  type="primary"
                  size="small"
                  @click="handleView(row)"
                >
                  查看
                </el-button>
                <el-button
                  v-permission="['menu:update']"
                  type="warning"
                  size="small"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>
                <el-button
                  v-permission="['menu:delete']"
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 菜单表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        :disabled="!isEdit && dialogTitle.includes('查看')"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="菜单名称" prop="title">
              <el-input v-model="formData.title" placeholder="请输入菜单名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="路由名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入路由名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="路由路径" prop="path">
              <el-input v-model="formData.path" placeholder="请输入路由路径" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="组件路径">
              <el-input v-model="formData.component" placeholder="请输入组件路径" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="父级菜单">
              <el-cascader
                v-model="formData.parent_id"
                :options="menuOptions"
                :props="{ checkStrictly: true, emitPath: false }"
                placeholder="请选择父级菜单"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="菜单图标">
              <el-input v-model="formData.icon" placeholder="请输入图标名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否显示">
              <el-switch v-model="formData.is_visible" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="外部链接">
              <el-switch v-model="formData.is_external" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="页面缓存">
              <el-switch v-model="formData.cache" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重定向">
              <el-input v-model="formData.redirect" placeholder="请输入重定向路径" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="菜单描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入菜单描述"
          />
        </el-form-item>
      </el-form>

      <template #footer v-if="isEdit || !dialogTitle.includes('查看')">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMenuTree, deleteMenu, createMenu, updateMenu } from '@/api/menu'
import { formatDateTime } from '@/utils'
import type { MenuTreeNode } from '@/types'

// 表格引用
const tableRef = ref()

// 加载状态
const loading = ref(false)

// 菜单树数据
const menuTree = ref<MenuTreeNode[]>([])

/**
 * 获取菜单树
 */
const fetchMenuTree = async () => {
  try {
    loading.value = true
    const response = await getMenuTree()
    menuTree.value = response.data
  } catch (error) {
    console.error('Failed to fetch menu tree:', error)
    ElMessage.error('获取菜单树失败')
  } finally {
    loading.value = false
  }
}

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentMenuId = ref<number>()

// 表单引用
const formRef = ref()

// 表单数据
const formData = ref({
  title: '',
  name: '',
  path: '',
  component: '',
  parent_id: null as number | null,
  icon: '',
  sort_order: 0,
  is_visible: true,
  is_external: false,
  cache: false,
  redirect: '',
  description: ''
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入菜单名称', trigger: 'blur' },
    { min: 2, max: 50, message: '菜单名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入路由名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '路由名称只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ],
  path: [
    { required: true, message: '请输入路由路径', trigger: 'blur' }
  ]
}

// 菜单选项（用于父菜单选择）
const menuOptions = ref<any[]>([])

/**
 * 获取菜单选项
 */
const fetchMenuOptions = async () => {
  try {
    const response = await getMenuTree()
    menuOptions.value = buildMenuOptions(response.data)
  } catch (error) {
    console.error('Failed to fetch menu options:', error)
  }
}

/**
 * 构建菜单选项树
 */
const buildMenuOptions = (menus: MenuTreeNode[]): any[] => {
  return menus.map(menu => ({
    value: menu.id,
    label: menu.title,
    children: menu.children && menu.children.length > 0 ? buildMenuOptions(menu.children) : undefined
  }))
}

/**
 * 处理新增
 */
const handleAdd = () => {
  dialogTitle.value = '新增菜单'
  isEdit.value = false
  resetForm()
  fetchMenuOptions()
  dialogVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: MenuTreeNode) => {
  dialogTitle.value = '查看菜单'
  isEdit.value = false
  fillForm(row)
  fetchMenuOptions()
  dialogVisible.value = true
}

/**
 * 处理编辑
 */
const handleEdit = (row: MenuTreeNode) => {
  dialogTitle.value = '编辑菜单'
  isEdit.value = true
  currentMenuId.value = row.id
  fillForm(row)
  fetchMenuOptions()
  dialogVisible.value = true
}

/**
 * 处理删除
 */
const handleDelete = async (row: MenuTreeNode) => {
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
 * 处理展开全部
 */
const handleExpandAll = () => {
  // 遍历所有行并展开
  const expandAll = (data: MenuTreeNode[]) => {
    data.forEach(item => {
      if (item.children && item.children.length) {
        tableRef.value?.toggleRowExpansion(item, true)
        expandAll(item.children)
      }
    })
  }
  expandAll(menuTree.value)
}

/**
 * 处理折叠全部
 */
const handleCollapseAll = () => {
  // 遍历所有行并折叠
  const collapseAll = (data: MenuTreeNode[]) => {
    data.forEach(item => {
      if (item.children && item.children.length) {
        tableRef.value?.toggleRowExpansion(item, false)
        collapseAll(item.children)
      }
    })
  }
  collapseAll(menuTree.value)
}

/**
 * 处理刷新
 */
const handleRefresh = () => {
  fetchMenuTree()
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
    parent_id: null,
    icon: '',
    sort_order: 0,
    is_visible: true,
    is_external: false,
    cache: false,
    redirect: '',
    description: ''
  }
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

/**
 * 填充表单数据
 */
const fillForm = (menu: MenuTreeNode) => {
  formData.value = {
    title: menu.title,
    name: menu.name,
    path: menu.path,
    component: menu.component || '',
    parent_id: menu.parent_id,
    icon: menu.icon || '',
    sort_order: menu.sort_order,
    is_visible: menu.is_visible,
    is_external: menu.is_external || false,
    cache: menu.cache || false,
    redirect: menu.redirect || '',
    description: menu.description || ''
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (isEdit.value && currentMenuId.value) {
      await updateMenu(currentMenuId.value, formData.value)
      ElMessage.success('菜单更新成功')
    } else {
      await createMenu(formData.value)
      ElMessage.success('菜单创建成功')
    }

    dialogVisible.value = false
    fetchMenuTree()
  } catch (error) {
    console.error('Failed to submit menu:', error)
    ElMessage.error(isEdit.value ? '菜单更新失败' : '菜单创建失败')
  }
}

/**
 * 处理对话框关闭
 */
const handleDialogClose = () => {
  resetForm()
  currentMenuId.value = undefined
}

onMounted(() => {
  fetchMenuTree()
})
</script>

<style lang="scss" scoped>
.menu-page {
  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .page-description {
      color: #606266;
      font-size: 14px;
    }
  }

  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 16px 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    .toolbar-left {
      display: flex;
      gap: 8px;
    }

    .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }

  .menu-table {
    .menu-title {
      display: flex;
      align-items: center;
      gap: 8px;

      .menu-icon {
        color: #409eff;
      }
    }

    .action-buttons {
      display: flex;
      gap: 4px;
    }
  }
}

// 暗色主题
.dark {
  .menu-page {
    .page-header {
      .page-title {
        color: #e5eaf3;
      }

      .page-description {
        color: #a3a6ad;
      }
    }

    .table-toolbar {
      background-color: #2b2b2b;
      color: #e5eaf3;
    }
  }
}
</style>
