<template>
  <div class="role-page">
    <!-- 搜索表单 -->
    <div class="search-form">
      <el-form
        ref="searchFormRef"
        :model="searchForm"
        :inline="true"
        label-width="80px"
      >
        <el-form-item label="角色名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入角色名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="角色代码">
          <el-input
            v-model="searchForm.code"
            placeholder="请输入角色代码"
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
          v-permission="['role:create']"
          type="primary"
          @click="handleAdd"
        >
          <el-icon><Plus /></el-icon>
          新增角色
        </el-button>
        <el-button
          v-permission="['role:delete']"
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
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="code" label="角色代码" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="user_count" label="用户数量" width="100" />
        <el-table-column prop="permission_count" label="权限数量" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
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
                v-permission="['role:read']"
                type="primary"
                size="small"
                @click="handleView(row)"
              >
                查看
              </el-button>
              <el-button
                v-permission="['role:update']"
                type="warning"
                size="small"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                v-permission="['role:delete']"
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoleList, deleteRole, bulkDeleteRoles } from '@/api/role'
import { formatDateTime } from '@/utils'
import type { RoleListItem, PaginationParams } from '@/types'

// 搜索表单
const searchFormRef = ref()
const searchForm = reactive({
  name: '',
  code: '',
  is_active: undefined as boolean | undefined
})

// 表格数据
const loading = ref(false)
const tableData = ref<RoleListItem[]>([])
const selectedIds = ref<number[]>([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

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
  searchFormRef.value?.resetFields()
  Object.assign(searchForm, {
    name: '',
    code: '',
    is_active: undefined
  })
  pagination.page = 1
  fetchRoleList()
}

/**
 * 处理刷新
 */
const handleRefresh = () => {
  fetchRoleList()
}

/**
 * 处理新增
 */
const handleAdd = () => {
  ElMessage.info('角色新增功能开发中...')
}

/**
 * 处理编辑
 */
const handleEdit = (row: RoleListItem) => {
  ElMessage.info('角色编辑功能开发中...')
}

/**
 * 处理查看
 */
const handleView = (row: RoleListItem) => {
  ElMessage.info('角色详情功能开发中...')
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
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchRoleList()
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchRoleList()
}

onMounted(() => {
  fetchRoleList()
})
</script>

<style lang="scss" scoped>
.role-page {
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

// 暗色主题
.dark {
  .role-page {
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
