<template>
  <div class="user-page">
    <!-- 搜索表单 -->
    <div class="search-form">
      <el-form
        ref="searchFormRef"
        :model="searchForm"
        :inline="true"
        label-width="80px"
      >
        <el-form-item label="用户名">
          <el-input
            v-model="searchForm.username"
            placeholder="请输入用户名"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input
            v-model="searchForm.email"
            placeholder="请输入邮箱"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="激活" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-button
          v-permission="['user:create']"
          type="primary"
          @click="handleAdd"
        >
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
        <el-button
          v-permission="['user:delete']"
          type="danger"
          :disabled="!selectedIds.length"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="data-table">
      <el-table
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
        @sort-change="handleSortChange"
        stripe
        border
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" sortable="custom" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="full_name" label="姓名" min-width="120" />
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column label="角色" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.role_names"
              :key="role"
              size="small"
              style="margin-right: 4px"
            >
              {{ role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login_at ? formatDateTime(row.last_login_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-permission="['user:read']"
                type="primary"
                size="small"
                @click="handleView(row)"
              >
                查看
              </el-button>
              <el-button
                v-permission="['user:update']"
                type="warning"
                size="small"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                v-permission="['user:delete']"
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

      <!-- 分页 -->
      <div class="table-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, deleteUser, bulkDeleteUsers } from '@/api/user'
import { formatDateTime } from '@/utils'
import type { UserListItem, PaginationParams } from '@/types'
import UserForm from './components/UserForm.vue'
import UserDetail from './components/UserDetail.vue'

// 搜索表单
const searchFormRef = ref()
const searchForm = reactive({
  username: '',
  email: '',
  is_active: undefined as boolean | undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<UserListItem[]>([])
const selectedIds = ref<number[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表单对话框
const formVisible = ref(false)
const formType = ref<'add' | 'edit'>('add')
const formData = ref<any>({})

// 详情对话框
const detailVisible = ref(false)
const selectedUserId = ref<number>()

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
    
    tableData.value = items
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
 * 处理刷新
 */
const handleRefresh = () => {
  fetchUserList()
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
        type: 'warning'
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
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个用户吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await bulkDeleteUsers({ ids: selectedIds.value, action: 'delete' })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
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
  selectedIds.value = selection.map(item => item.id)
}

/**
 * 处理排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现排序逻辑
  console.log('Sort change:', prop, order)
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
const handleCurrentChange = (page: number) => {
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
.user-page {
  .search-form {
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    margin-bottom: 16px;
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

  .data-table {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    overflow: hidden;

    .action-buttons {
      display: flex;
      gap: 4px;
    }

    .table-pagination {
      padding: 16px 20px;
      text-align: right;
      border-top: 1px solid #ebeef5;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-page {
    .search-form {
      padding: 16px;

      :deep(.el-form) {
        .el-form-item {
          display: block;
          margin-bottom: 16px;

          .el-form-item__content {
            margin-left: 0 !important;
          }
        }
      }
    }

    .table-toolbar {
      flex-direction: column;
      gap: 12px;

      .toolbar-left,
      .toolbar-right {
        width: 100%;
        justify-content: center;
      }
    }

    .data-table {
      :deep(.el-table) {
        .action-buttons {
          flex-direction: column;
          gap: 2px;

          .el-button {
            width: 100%;
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .user-page {
    .search-form,
    .table-toolbar,
    .data-table {
      background-color: #2b2b2b;
      color: #e5eaf3;
    }

    .table-pagination {
      border-top-color: #4c4d4f;
    }
  }
}
</style>
