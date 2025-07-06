<template>
  <PageContainer
    title="数据权限管理"
    description="管理系统数据访问权限，控制用户对不同数据范围的访问能力"
    :icon="Lock"
    badge="Data"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <ActionButtons
        :actions="headerActions"
        :permissions="userPermissions"
        @action="handleHeaderAction"
      />
    </template>

    <!-- 权限配置向导 -->
    <el-card shadow="never" class="wizard-card">
      <template #header>
        <div class="wizard-header">
          <el-icon class="header-icon"><Setting /></el-icon>
          <span class="header-title">数据权限配置向导</span>
        </div>
      </template>

      <div class="permission-wizard">
        <el-steps :active="currentStep" align-center>
          <el-step title="选择权限类型" description="选择数据权限的类型" />
          <el-step title="配置权限范围" description="设置数据访问范围" />
          <el-step title="分配用户角色" description="将权限分配给用户或角色" />
          <el-step title="完成配置" description="确认并保存权限配置" />
        </el-steps>

        <div class="wizard-content">
          <!-- 步骤1：选择权限类型 -->
          <div v-if="currentStep === 0" class="step-content">
            <h4>选择数据权限类型</h4>
            <el-row :gutter="16">
              <el-col :span="8" v-for="type in permissionTypes" :key="type.value">
                <el-card
                  class="permission-type-card"
                  :class="{ active: wizardForm.permission_type === type.value }"
                  shadow="hover"
                  @click="selectPermissionType(type.value)"
                >
                  <div class="type-content">
                    <el-icon class="type-icon">
                      <component :is="type.icon" />
                    </el-icon>
                    <h5>{{ type.label }}</h5>
                    <p>{{ type.description }}</p>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 步骤2：配置权限范围 -->
          <div v-if="currentStep === 1" class="step-content">
            <h4>配置数据访问范围</h4>
            <el-form :model="wizardForm" label-width="120px">
              <el-form-item label="权限范围">
                <el-radio-group v-model="wizardForm.scope">
                  <el-radio-button
                    v-for="scope in permissionScopes"
                    :key="scope.value"
                    :label="scope.value"
                  >
                    {{ scope.label }}
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="wizardForm.scope === 'department'" label="选择部门">
                <el-tree-select
                  v-model="wizardForm.department_ids"
                  :data="departmentOptions"
                  multiple
                  :props="{ label: 'name', value: 'id' }"
                  placeholder="请选择部门"
                  check-strictly
                />
              </el-form-item>

              <el-form-item v-if="wizardForm.scope === 'custom'" label="自定义条件">
                <el-input
                  v-model="wizardForm.custom_condition"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入自定义数据过滤条件（SQL WHERE 子句）"
                />
              </el-form-item>
            </el-form>
          </div>

          <!-- 步骤3：分配用户角色 -->
          <div v-if="currentStep === 2" class="step-content">
            <h4>分配给用户或角色</h4>
            <el-tabs v-model="assignmentTab">
              <el-tab-pane label="分配给用户" name="users">
                <el-transfer
                  v-model="wizardForm.user_ids"
                  :data="userOptions"
                  :titles="['可选用户', '已选用户']"
                  filterable
                />
              </el-tab-pane>
              <el-tab-pane label="分配给角色" name="roles">
                <el-transfer
                  v-model="wizardForm.role_ids"
                  :data="roleOptions"
                  :titles="['可选角色', '已选角色']"
                  filterable
                />
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 步骤4：完成配置 -->
          <div v-if="currentStep === 3" class="step-content">
            <h4>确认权限配置</h4>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="权限名称">
                <el-input v-model="wizardForm.name" placeholder="请输入权限名称" />
              </el-descriptions-item>
              <el-descriptions-item label="权限代码">
                <el-input v-model="wizardForm.code" placeholder="请输入权限代码" />
              </el-descriptions-item>
              <el-descriptions-item label="权限类型">
                {{ getPermissionTypeLabel(wizardForm.permission_type) }}
              </el-descriptions-item>
              <el-descriptions-item label="权限范围">
                {{ getPermissionScopeLabel(wizardForm.scope) }}
              </el-descriptions-item>
              <el-descriptions-item label="分配用户" :span="2">
                {{ wizardForm.user_ids.length }} 个用户
              </el-descriptions-item>
              <el-descriptions-item label="分配角色" :span="2">
                {{ wizardForm.role_ids.length }} 个角色
              </el-descriptions-item>
              <el-descriptions-item label="权限描述" :span="2">
                <el-input
                  v-model="wizardForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入权限描述"
                />
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <div class="wizard-actions">
          <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
          <el-button v-if="currentStep < 3" type="primary" @click="nextStep">下一步</el-button>
          <el-button v-if="currentStep === 3" type="success" @click="savePermission">保存配置</el-button>
          <el-button @click="resetWizard">重置</el-button>
        </div>
      </div>
    </el-card>



    <!-- 数据权限表单对话框 -->
    <FormDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :form-data="formData"
      :form-rules="formRules"
      :form-fields="formFields"
      :loading="submitLoading"
      width="800px"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />

    <!-- 权限分配对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="权限分配"
      width="900px"
      :close-on-click-modal="false"
      class="assign-dialog"
    >
      <div v-if="currentPermission" class="assign-content">
        <el-alert
          :title="`为数据权限 &quot;${currentPermission.name}&quot; 分配用户和角色`"
          type="info"
          :closable="false"
          show-icon
        />

        <el-tabs v-model="assignTab" class="assign-tabs">
          <el-tab-pane label="用户分配" name="users">
            <el-transfer
              v-model="assignedUsers"
              :data="userOptions"
              :titles="['可选用户', '已分配用户']"
              filterable
              :filter-placeholder="'搜索用户'"
              :props="{ key: 'id', label: 'name' }"
            />
          </el-tab-pane>
          <el-tab-pane label="角色分配" name="roles">
            <el-transfer
              v-model="assignedRoles"
              :data="roleOptions"
              :titles="['可选角色', '已分配角色']"
              filterable
              :filter-placeholder="'搜索角色'"
              :props="{ key: 'id', label: 'name' }"
            />
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="assignDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSaveAssignment">
            保存分配
          </el-button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Lock, Plus, Refresh, DocumentCopy, Setting,
  View, Edit, Delete, UserFilled, Key, DataBoard
} from '@element-plus/icons-vue'
import {
  deleteDataPermission,
  createDataPermission,
  updateDataPermission,
  assignDataPermission,
  getDataPermissionDetail
} from '@/api/data-permission'
import { getDepartmentOptions } from '@/api/department'
import { getUserOptions } from '@/api/user'
import { getRoleOptions } from '@/api/role'
import { formatDateTime } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import PageContainer from '@/components/common/PageContainer.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import type { ActionButton } from '@/components/common/ActionButtons.vue'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)



// 数据状态
const loading = ref(false)
const submitLoading = ref(false)

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'add',
    label: '新增权限',
    type: 'primary',
    icon: Plus,
    permission: 'data-permission:create'
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
    permission: 'data-permission:export'
  },
  {
    key: 'batchDelete',
    label: '批量删除',
    type: 'danger',
    icon: Delete,
    permission: 'data-permission:delete',
    disabled: computed(() => selectedIds.value.length === 0)
  }
]



// 向导相关
const currentStep = ref(0)
const wizardForm = reactive({
  name: '',
  code: '',
  permission_type: '',
  scope: '',
  department_ids: [],
  custom_condition: '',
  user_ids: [],
  role_ids: [],
  description: ''
})

const assignmentTab = ref('users')

// 权限类型选项
const permissionTypes = [
  {
    value: 'view',
    label: '数据查看',
    description: '允许查看指定范围内的数据',
    icon: View
  },
  {
    value: 'edit',
    label: '数据编辑',
    description: '允许编辑指定范围内的数据',
    icon: Edit
  },
  {
    value: 'delete',
    label: '数据删除',
    description: '允许删除指定范围内的数据',
    icon: Delete
  },
  {
    value: 'export',
    label: '数据导出',
    description: '允许导出指定范围内的数据',
    icon: DocumentCopy
  }
]

// 权限范围选项
const permissionScopes = [
  { value: 'all', label: '全部数据' },
  { value: 'department', label: '部门数据' },
  { value: 'self', label: '个人数据' },
  { value: 'custom', label: '自定义条件' }
]

// 选项数据
const departmentOptions = ref<any[]>([])
const userOptions = ref<any[]>([])
const roleOptions = ref<any[]>([])

// 表单对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑数据权限' : '新增数据权限')
const isEdit = ref(false)
const currentPermissionId = ref<number>()

// 分配对话框
const assignDialogVisible = ref(false)
const currentPermission = ref<any>(null)
const assignTab = ref('users')
const assignedUsers = ref<number[]>([])
const assignedRoles = ref<number[]>([])

// 表单数据
const formData = ref({
  name: '',
  code: '',
  permission_type: '',
  scope: '',
  resource_type: '',
  description: '',
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
  permission_type: [
    { required: true, message: '请选择权限类型', trigger: 'change' }
  ],
  scope: [
    { required: true, message: '请选择权限范围', trigger: 'change' }
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
    prop: 'permission_type',
    label: '权限类型',
    type: 'select',
    placeholder: '请选择权限类型',
    options: [
      { label: '数据查看', value: 'view' },
      { label: '数据编辑', value: 'edit' },
      { label: '数据删除', value: 'delete' },
      { label: '数据导出', value: 'export' }
    ],
    span: 12
  },
  {
    prop: 'scope',
    label: '权限范围',
    type: 'select',
    placeholder: '请选择权限范围',
    options: [
      { label: '全部数据', value: 'all' },
      { label: '部门数据', value: 'department' },
      { label: '个人数据', value: 'self' },
      { label: '自定义', value: 'custom' }
    ],
    span: 12
  },
  {
    prop: 'resource_type',
    label: '资源类型',
    type: 'input',
    placeholder: '请输入资源类型',
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
    label: '权限描述',
    type: 'textarea',
    placeholder: '请输入权限描述',
    rows: 3,
    span: 24
  }
]



/**
 * 获取选项数据
 */
const fetchOptions = async () => {
  try {
    const [deptRes, userRes, roleRes] = await Promise.all([
      getDepartmentOptions(),
      getUserOptions(),
      getRoleOptions()
    ])
    departmentOptions.value = deptRes.data
    userOptions.value = userRes.data
    roleOptions.value = roleRes.data
  } catch (error) {
    console.error('Failed to fetch options:', error)
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
    case 'batchDelete':
      handleBatchDelete()
      break
  }
}



/**
 * 刷新数据
 */
const handleRefresh = () => {
  ElMessage.success('数据已刷新')
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
    const response = await getDataPermissionDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch data permission detail:', error)
    ElMessage.error('获取数据权限详情失败')
  }
}

/**
 * 处理编辑
 */
const handleEdit = async (row: any) => {
  try {
    isEdit.value = true
    currentPermissionId.value = row.id
    const response = await getDataPermissionDetail(row.id)
    fillForm(response.data)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch data permission detail:', error)
    ElMessage.error('获取数据权限详情失败')
  }
}

/**
 * 处理分配
 */
const handleAssign = async (row: any) => {
  try {
    currentPermission.value = row
    // 获取已分配的用户和角色
    const response = await getDataPermissionDetail(row.id)
    assignedUsers.value = response.data.assigned_users || []
    assignedRoles.value = response.data.assigned_roles || []
    assignDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch assignment data:', error)
    ElMessage.error('获取分配信息失败')
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据权限 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteDataPermission(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete data permission:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 批量删除
 */
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个数据权限吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里需要实现批量删除API
    for (const id of selectedIds.value) {
      await deleteDataPermission(id)
    }

    ElMessage.success('批量删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete:', error)
      ElMessage.error('批量删除失败')
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
    permission_type: '',
    scope: '',
    resource_type: '',
    description: '',
    sort_order: 0,
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
    permission_type: permission.permission_type,
    scope: permission.scope,
    resource_type: permission.resource_type || '',
    description: permission.description || '',
    sort_order: permission.sort_order || 0,
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
      await updateDataPermission(currentPermissionId.value, data)
      ElMessage.success('数据权限更新成功')
    } else {
      await createDataPermission(data)
      ElMessage.success('数据权限创建成功')
    }

    dialogVisible.value = false
  } catch (error) {
    console.error('Failed to submit data permission:', error)
    ElMessage.error(isEdit.value ? '数据权限更新失败' : '数据权限创建失败')
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

/**
 * 保存权限分配
 */
const handleSaveAssignment = async () => {
  try {
    submitLoading.value = true
    await assignDataPermission(currentPermission.value.id, {
      user_ids: assignedUsers.value,
      role_ids: assignedRoles.value
    })
    ElMessage.success('权限分配成功')
    assignDialogVisible.value = false
  } catch (error) {
    console.error('Failed to assign permission:', error)
    ElMessage.error('权限分配失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 向导相关函数
 */
const selectPermissionType = (type: string) => {
  wizardForm.permission_type = type
}

const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const resetWizard = () => {
  currentStep.value = 0
  Object.assign(wizardForm, {
    name: '',
    code: '',
    permission_type: '',
    scope: '',
    department_ids: [],
    custom_condition: '',
    user_ids: [],
    role_ids: [],
    description: ''
  })
}

const savePermission = async () => {
  try {
    submitLoading.value = true
    await createDataPermission(wizardForm)
    ElMessage.success('数据权限配置成功')
    resetWizard()
  } catch (error) {
    console.error('Failed to save permission:', error)
    ElMessage.error('数据权限配置失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 获取权限类型标签类型
 */
const getPermissionTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    view: 'primary',
    edit: 'warning',
    delete: 'danger',
    export: 'success'
  }
  return typeMap[type] || 'default'
}

/**
 * 获取权限类型标签文本
 */
const getPermissionTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    view: '数据查看',
    edit: '数据编辑',
    delete: '数据删除',
    export: '数据导出'
  }
  return labelMap[type] || type
}

/**
 * 获取权限范围标签文本
 */
const getPermissionScopeLabel = (scope: string) => {
  const labelMap: Record<string, string> = {
    all: '全部数据',
    department: '部门数据',
    self: '个人数据',
    custom: '自定义'
  }
  return labelMap[scope] || scope
}

onMounted(() => {
  fetchOptions()
})
</script>

<style lang="scss" scoped>
// 权限配置向导样式
.wizard-card {
  margin-bottom: 20px;

  .wizard-header {
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

  .permission-wizard {
    .wizard-content {
      margin: 30px 0;
      min-height: 300px;

      .step-content {
        h4 {
          margin-bottom: 20px;
          color: var(--el-text-color-primary);
        }

        .permission-type-card {
          cursor: pointer;
          transition: all 0.3s ease;
          margin-bottom: 16px;

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          }

          &.active {
            border-color: var(--el-color-primary);
            box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
          }

          .type-content {
            text-align: center;
            padding: 20px;

            .type-icon {
              font-size: 32px;
              color: var(--el-color-primary);
              margin-bottom: 12px;
            }

            h5 {
              margin: 0 0 8px 0;
              color: var(--el-text-color-primary);
            }

            p {
              margin: 0;
              color: var(--el-text-color-regular);
              font-size: 14px;
            }
          }
        }
      }
    }

    .wizard-actions {
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid var(--el-border-color-lighter);

      .el-button {
        margin: 0 8px;
      }
    }
  }
}

// 分配信息样式
.assignment-info {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

// 分配对话框样式
.assign-dialog {
  .assign-content {
    .el-alert {
      margin-bottom: 20px;
    }

    .assign-tabs {
      margin-top: 20px;
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
  .wizard-card {
    .permission-wizard {
      .wizard-content {
        .step-content {
          .permission-type-card {
            .type-content {
              padding: 15px;

              .type-icon {
                font-size: 24px;
              }

              h5 {
                font-size: 14px;
              }

              p {
                font-size: 12px;
              }
            }
          }
        }
      }

      .wizard-actions {
        .el-button {
          margin: 4px;
          width: 100px;
        }
      }
    }
  }

  .assign-dialog {
    :deep(.el-dialog) {
      width: 95% !important;
      margin: 5vh auto;
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
  .wizard-card {
    background-color: var(--el-bg-color-page);
    border-color: var(--el-border-color);

    .permission-wizard {
      .wizard-content {
        .step-content {
          .permission-type-card {
            background-color: var(--el-bg-color-page);
            border-color: var(--el-border-color);

            &:hover {
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
          }
        }
      }
    }
  }
}
</style>
