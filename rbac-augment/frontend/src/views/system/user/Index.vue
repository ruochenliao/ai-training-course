<template>
  <PageContainer
    title="用户管理"
    description="管理系统用户信息、角色分配和权限控制"
    :icon="User"
    badge="Beta"
    badge-type="primary"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <el-button
        v-permission="['user:create']"
        type="primary"
        :icon="Plus"
        @click="handleAdd"
      >
        新增用户
      </el-button>
      <el-button
        v-permission="['user:export']"
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
              <el-form-item label="用户名">
                <el-input
                  v-model="searchForm.username"
                  placeholder="请输入用户名"
                  clearable
                  :prefix-icon="Search"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="邮箱">
                <el-input
                  v-model="searchForm.email"
                  placeholder="请输入邮箱地址"
                  clearable
                  :prefix-icon="Message"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="状态">
                <el-select
                  v-model="searchForm.is_active"
                  placeholder="请选择用户状态"
                  clearable
                  style="width: 100%"
                >
                  <el-option label="激活" :value="true">
                    <span class="status-option">
                      <el-icon color="#52c41a"><CircleCheck /></el-icon>
                      激活
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
      @refresh="fetchUserList"
      @batch-delete="handleBatchDelete"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @size-change="handleSizeChange"
      @current-page-change="handleCurrentPageChange"
    >
      <!-- 角色列 -->
      <template #roles="{ row }">
        <div class="role-tags">
          <el-tag
            v-for="role in row.role_names"
            :key="role"
            size="small"
            type="primary"
            class="role-tag"
          >
            {{ role }}
          </el-tag>
          <el-tag v-if="!row.role_names?.length" size="small" type="info">
            未分配角色
          </el-tag>
        </div>
      </template>

      <!-- 状态列 -->
      <template #status="{ row }">
        <el-switch
          v-model="row.is_active"
          :loading="row.statusLoading"
          @change="handleStatusChange(row)"
        />
      </template>

      <!-- 最后登录时间列 -->
      <template #lastLogin="{ row }">
        <span v-if="row.last_login_at" class="last-login">
          {{ formatDateTime(row.last_login_at) }}
        </span>
        <el-text v-else type="info">从未登录</el-text>
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

    <!-- 用户表单对话框 -->
    <UserForm
      v-model:visible="formVisible"
      :form-data="formData"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 用户详情对话框 -->
    <UserDetail
      v-model:visible="detailVisible"
      :user-id="selectedUserId"
    />

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordVisible"
      title="重置密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resetPasswordFormRef"
        :model="resetPasswordForm"
        :rules="resetPasswordRules"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="resetPasswordForm.password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="resetPasswordForm.confirmPassword"
            type="password"
            show-password
            placeholder="请确认新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="resetPasswordLoading"
          @click="handleResetPasswordSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Plus,
  DocumentCopy,
  Search,
  Message,
  Refresh,
  CircleCheck,
  CircleClose,
  View,
  Edit,
  Key,
  Delete
} from '@element-plus/icons-vue'
import { getUserList, deleteUser, bulkDeleteUsers, resetUserPassword, updateUserStatus } from '@/api/user'
import { formatDateTime } from '@/utils'
import type { UserListItem, PaginationParams, TableColumn, ActionButton } from '@/types'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import UserForm from './components/UserForm.vue'
import UserDetail from './components/UserDetail.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单
const searchFormRef = ref<FormInstance>()
const searchForm = reactive({
  username: '',
  email: '',
  is_active: undefined as boolean | undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<UserListItem[]>([])
const selectedRows = ref<UserListItem[]>([])

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
    prop: 'username',
    label: '用户名',
    minWidth: 120,
    showOverflowTooltip: true
  },
  {
    prop: 'email',
    label: '邮箱',
    minWidth: 180,
    showOverflowTooltip: true
  },
  {
    prop: 'full_name',
    label: '姓名',
    minWidth: 120,
    showOverflowTooltip: true
  },
  {
    prop: 'phone',
    label: '手机号',
    minWidth: 130
  },
  {
    prop: 'role_names',
    label: '角色',
    minWidth: 150,
    slot: 'roles'
  },
  {
    prop: 'is_active',
    label: '状态',
    width: 100,
    align: 'center',
    slot: 'status'
  },
  {
    prop: 'last_login_at',
    label: '最后登录',
    width: 160,
    slot: 'lastLogin'
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
const selectedUserId = ref<number>()

// 重置密码对话框
const resetPasswordVisible = ref(false)
const resetPasswordLoading = ref(false)
const resetPasswordFormRef = ref<FormInstance>()
const resetPasswordForm = reactive({
  userId: 0,
  password: '',
  confirmPassword: ''
})

// 重置密码表单验证规则
const resetPasswordRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

/**
 * 获取用户列表
 */
const fetchUserList = async () => {
  try {
    loading.value = true

    const params: PaginationParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchForm.username || searchForm.email || undefined
    }

    // 添加状态筛选
    if (searchForm.is_active !== undefined) {
      Object.assign(params, { is_active: searchForm.is_active })
    }

    const response = await getUserList(params)
    const { items, total } = response.data

    tableData.value = items.map(item => ({
      ...item,
      statusLoading: false
    }))
    pagination.total = total
  } catch (error) {
    console.error('Failed to fetch user list:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  searchFormRef.value?.resetFields()
  Object.assign(searchForm, {
    username: '',
    email: '',
    is_active: undefined
  })
  pagination.page = 1
  fetchUserList()
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
const handleEdit = (row: UserListItem) => {
  formType.value = 'edit'
  formData.value = { ...row }
  formVisible.value = true
}

/**
 * 处理查看
 */
const handleView = (row: UserListItem) => {
  selectedUserId.value = row.id
  detailVisible.value = true
}

// 行操作按钮配置
const getRowActions = (row: UserListItem): ActionButton[] => [
  {
    key: 'view',
    label: '查看',
    type: 'primary',
    icon: View,
    permission: 'user:read',
    row
  },
  {
    key: 'edit',
    label: '编辑',
    type: 'warning',
    icon: Edit,
    permission: 'user:update',
    row
  },
  {
    key: 'reset_password',
    label: '重置密码',
    type: 'info',
    icon: Key,
    permission: 'user:reset_password',
    row
  },
  {
    key: 'delete',
    label: '删除',
    type: 'danger',
    icon: Delete,
    permission: 'user:delete',
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
    case 'reset_password':
      handleResetPassword(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

/**
 * 处理重置密码
 */
const handleResetPassword = (row: UserListItem) => {
  resetPasswordForm.userId = row.id
  resetPasswordForm.password = ''
  resetPasswordForm.confirmPassword = ''
  resetPasswordVisible.value = true
}

/**
 * 提交重置密码
 */
const handleResetPasswordSubmit = async () => {
  if (!resetPasswordFormRef.value) return

  try {
    await resetPasswordFormRef.value.validate()

    resetPasswordLoading.value = true
    await resetUserPassword(resetPasswordForm.userId, {
      password: resetPasswordForm.password
    })

    resetPasswordVisible.value = false
    ElMessage.success('密码重置成功')

    // 重置表单
    resetPasswordFormRef.value.resetFields()
  } catch (error) {
    console.error('Reset password error:', error)
  } finally {
    resetPasswordLoading.value = false
  }
}

/**
 * 处理状态切换
 */
const handleStatusChange = async (row: UserListItem) => {
  try {
    row.statusLoading = true
    await updateUserStatus(row.id, { is_active: row.is_active })
    ElMessage.success(`用户已${row.is_active ? '激活' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('Update user status error:', error)
  } finally {
    row.statusLoading = false
  }
}

/**
 * 处理删除
 */
const handleDelete = async (row: UserListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p>此操作将永久删除该用户，是否继续？</p>
            <p style="color: #f56c6c; font-size: 12px;">注意：删除后无法恢复</p>
          </div>
        `
      }
    )

    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete user:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async (rows: UserListItem[]) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个用户吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = rows.map(row => row.id)
    await bulkDeleteUsers({ ids, action: 'delete' })
    ElMessage.success('批量删除成功')
    fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete users:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: UserListItem[]) => {
  selectedRows.value = selection
}

/**
 * 处理排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现排序逻辑
  console.log('Sort change:', prop, order)
  fetchUserList()
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchUserList()
}

/**
 * 处理当前页变化
 */
const handleCurrentPageChange = (page: number) => {
  pagination.page = page
  fetchUserList()
}

/**
 * 处理表单成功
 */
const handleFormSuccess = () => {
  fetchUserList()
}

onMounted(() => {
  fetchUserList()
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
    gap: $spacing-xs;
  }
}

// ==================== 表格样式 ====================
.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-xs;

  .role-tag {
    margin: 0;
  }
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  justify-content: center;
}

.last-login {
  color: $text-color-2;
  font-size: $font-size-sm;
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

  .action-buttons {
    flex-direction: column;
    gap: $spacing-xs;
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

  .last-login {
    color: $dark-text-color-2;
  }
}
</style>
