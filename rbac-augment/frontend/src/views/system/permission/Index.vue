<template>
  <div class="permission-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">权限管理</h2>
      <p class="page-description">管理系统中的所有权限，包括权限的创建、编辑、删除和分组管理。</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-button
          v-permission="['permission:create']"
          type="primary"
          @click="handleAdd"
        >
          <el-icon><Plus /></el-icon>
          新增权限
        </el-button>
        <el-button
          type="success"
          @click="handleRefreshTree"
        >
          <el-icon><Refresh /></el-icon>
          刷新权限树
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="viewMode" @change="handleViewModeChange">
          <el-radio-button label="tree">树形视图</el-radio-button>
          <el-radio-button label="table">表格视图</el-radio-button>
          <el-radio-button label="group">分组视图</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 权限树视图 -->
    <div v-if="viewMode === 'tree'" class="permission-tree">
      <el-card>
        <template #header>
          <span>权限树结构</span>
        </template>
        <el-tree
          v-loading="loading"
          :data="permissionTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span class="node-label">{{ data.name }}</span>
              <span class="node-code">{{ data.code }}</span>
              <div class="node-actions">
                <el-button
                  v-permission="['permission:read']"
                  type="primary"
                  size="small"
                  @click="handleView(data)"
                >
                  查看
                </el-button>
                <el-button
                  v-permission="['permission:update']"
                  type="warning"
                  size="small"
                  @click="handleEdit(data)"
                >
                  编辑
                </el-button>
                <el-button
                  v-permission="['permission:delete']"
                  type="danger"
                  size="small"
                  @click="handleDelete(data)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>
        </el-tree>
      </el-card>
    </div>

    <!-- 权限分组视图 -->
    <div v-else-if="viewMode === 'group'" class="permission-groups">
      <el-row :gutter="16">
        <el-col
          v-for="group in permissionGroups"
          :key="group.resource"
          :span="8"
        >
          <el-card class="group-card">
            <template #header>
              <div class="group-header">
                <span class="group-title">{{ group.resource }}</span>
                <el-tag size="small">{{ group.permissions.length }} 个权限</el-tag>
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
                  <div class="permission-action">{{ permission.action }}</div>
                </div>
                <div class="permission-actions">
                  <el-button
                    v-permission="['permission:update']"
                    type="text"
                    size="small"
                    @click="handleEdit(permission)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-permission="['permission:delete']"
                    type="text"
                    size="small"
                    @click="handleDelete(permission)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 权限表格视图 -->
    <div v-else class="permission-table">
      <el-card>
        <el-table
          v-loading="loading"
          :data="permissionList"
          stripe
          border
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="权限名称" min-width="150" />
          <el-table-column prop="code" label="权限代码" min-width="150" />
          <el-table-column prop="resource" label="资源" width="120" />
          <el-table-column prop="action" label="操作" width="100" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  v-permission="['permission:read']"
                  type="primary"
                  size="small"
                  @click="handleView(row)"
                >
                  查看
                </el-button>
                <el-button
                  v-permission="['permission:update']"
                  type="warning"
                  size="small"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>
                <el-button
                  v-permission="['permission:delete']"
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

    <!-- 权限表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
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
            <el-form-item label="权限名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入权限名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="权限代码" prop="code">
              <el-input v-model="formData.code" placeholder="请输入权限代码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="资源" prop="resource">
              <el-input v-model="formData.resource" placeholder="请输入资源名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="操作" prop="action">
              <el-input v-model="formData.action" placeholder="请输入操作名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="权限分组">
              <el-input v-model="formData.group" placeholder="请输入权限分组" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="父级权限">
          <el-cascader
            v-model="formData.parent_id"
            :options="permissionOptions"
            :props="{ checkStrictly: true, emitPath: false }"
            placeholder="请选择父级权限"
            clearable
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="权限描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
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
import type { PermissionListItem, PermissionTreeNode, PermissionGroup } from '@/types'

// 视图模式
const viewMode = ref<'tree' | 'table' | 'group'>('tree')

// 加载状态
const loading = ref(false)

// 数据
const permissionList = ref<PermissionListItem[]>([])
const permissionTree = ref<PermissionTreeNode[]>([])
const permissionGroups = ref<PermissionGroup[]>([])

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

/**
 * 获取权限列表
 */
const fetchPermissionList = async () => {
  try {
    loading.value = true
    const response = await getPermissionList({ page: 1, page_size: 1000 })
    permissionList.value = response.data.items
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
 * 处理视图模式变化
 */
const handleViewModeChange = (mode: string) => {
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

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentPermissionId = ref<number>()

// 表单引用
const formRef = ref()

// 表单数据
const formData = ref({
  name: '',
  code: '',
  resource: '',
  action: '',
  description: '',
  parent_id: null as number | null,
  sort_order: 0,
  group: ''
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

// 权限选项（用于父权限选择）
const permissionOptions = ref<any[]>([])

/**
 * 获取权限选项
 */
const fetchPermissionOptions = async () => {
  try {
    const response = await getPermissionTree()
    permissionOptions.value = buildPermissionOptions(response.data)
  } catch (error) {
    console.error('Failed to fetch permission options:', error)
  }
}

/**
 * 构建权限选项树
 */
const buildPermissionOptions = (permissions: PermissionTreeNode[]): any[] => {
  return permissions.map(permission => ({
    value: permission.id,
    label: permission.name,
    children: permission.children && permission.children.length > 0 ? buildPermissionOptions(permission.children) : undefined
  }))
}

/**
 * 处理新增
 */
const handleAdd = () => {
  dialogTitle.value = '新增权限'
  isEdit.value = false
  resetForm()
  fetchPermissionOptions()
  dialogVisible.value = true
}

/**
 * 处理查看
 */
const handleView = async (row: any) => {
  try {
    dialogTitle.value = '查看权限'
    isEdit.value = false
    const response = await getPermissionDetail(row.id)
    fillForm(response.data)
    fetchPermissionOptions()
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
    dialogTitle.value = '编辑权限'
    isEdit.value = true
    currentPermissionId.value = row.id
    const response = await getPermissionDetail(row.id)
    fillForm(response.data)
    fetchPermissionOptions()
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
    handleViewModeChange(viewMode.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete permission:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理刷新权限树
 */
const handleRefreshTree = () => {
  handleViewModeChange(viewMode.value)
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
    group: ''
  }
  if (formRef.value) {
    formRef.value.clearValidate()
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
    group: permission.group || ''
  }
}

/**
 * 处理表单提交
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (isEdit.value && currentPermissionId.value) {
      await updatePermission(currentPermissionId.value, formData.value)
      ElMessage.success('权限更新成功')
    } else {
      await createPermission(formData.value)
      ElMessage.success('权限创建成功')
    }

    dialogVisible.value = false
    handleViewModeChange(viewMode.value)
  } catch (error) {
    console.error('Failed to submit permission:', error)
    ElMessage.error(isEdit.value ? '权限更新失败' : '权限创建失败')
  }
}

/**
 * 处理对话框关闭
 */
const handleDialogClose = () => {
  resetForm()
  currentPermissionId.value = undefined
}

onMounted(() => {
  fetchPermissionTree()
})
</script>

<style lang="scss" scoped>
.permission-page {
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
  }

  .permission-tree {
    .tree-node {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding-right: 16px;

      .node-label {
        font-weight: 500;
      }

      .node-code {
        color: #909399;
        font-size: 12px;
        margin-left: 8px;
      }

      .node-actions {
        display: flex;
        gap: 4px;
      }
    }
  }

  .permission-groups {
    .group-card {
      margin-bottom: 16px;

      .group-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .group-title {
          font-weight: 600;
          color: #303133;
        }
      }

      .permission-list {
        .permission-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;

          &:last-child {
            border-bottom: none;
          }

          .permission-info {
            .permission-name {
              font-weight: 500;
              color: #303133;
            }

            .permission-action {
              font-size: 12px;
              color: #909399;
            }
          }

          .permission-actions {
            display: flex;
            gap: 4px;
          }
        }
      }
    }
  }

  .permission-table {
    .action-buttons {
      display: flex;
      gap: 4px;
    }
  }
}

// 暗色主题
.dark {
  .permission-page {
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

    .group-card {
      .group-title {
        color: #e5eaf3;
      }

      .permission-item {
        border-bottom-color: #4c4d4f;

        .permission-name {
          color: #e5eaf3;
        }
      }
    }
  }
}
</style>
