<template>
  <div class="data-permission-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入权限名称或代码"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="权限类型">
          <el-select
            v-model="searchForm.permission_type"
            placeholder="请选择权限类型"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="option in DATA_PERMISSION_TYPE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="权限范围">
          <el-select
            v-model="searchForm.scope"
            placeholder="请选择权限范围"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="option in DATA_PERMISSION_SCOPE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="启用" :value="true" />
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

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增数据权限
      </el-button>
      <el-button
        type="danger"
        :disabled="selectedIds.length === 0"
        @click="handleBatchDelete"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="权限名称" min-width="150" />
      <el-table-column prop="code" label="权限代码" min-width="150" />
      <el-table-column prop="permission_type" label="权限类型" width="150">
        <template #default="{ row }">
          <el-tag :type="getPermissionTypeTagType(row.permission_type)">
            {{ getPermissionTypeLabel(row.permission_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="scope" label="权限范围" width="120">
        <template #default="{ row }">
          <el-tag type="info">
            {{ getScopeLabel(row.scope) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource_type" label="资源类型" width="120" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button type="success" size="small" @click="handleAssign(row)">
            分配
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
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

    <!-- 数据权限表单对话框 -->
    <DataPermissionForm
      v-model:visible="formVisible"
      :form-data="currentPermission"
      :form-type="formType"
      @success="handleFormSuccess"
    />

    <!-- 权限分配对话框 -->
    <DataPermissionAssign
      v-model:visible="assignVisible"
      :permission="currentPermission"
      @success="handleAssignSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Delete } from '@element-plus/icons-vue'
import { getDataPermissionList, deleteDataPermission, bulkDeleteDataPermissions } from '@/api/data-permission'
import { formatDateTime } from '@/utils'
import DataPermissionForm from './components/DataPermissionForm.vue'
import DataPermissionAssign from './components/DataPermissionAssign.vue'
import {
  DATA_PERMISSION_TYPE_OPTIONS,
  DATA_PERMISSION_SCOPE_OPTIONS,
  type DataPermissionListItem,
  type DataPermissionSearchParams,
  DataPermissionType,
  DataPermissionScope
} from '@/types/data-permission'

// 搜索表单
const searchForm = reactive<DataPermissionSearchParams>({
  keyword: '',
  permission_type: undefined,
  scope: undefined,
  resource_type: '',
  is_active: undefined
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 表格数据
const tableData = ref<DataPermissionListItem[]>([])
const loading = ref(false)
const selectedIds = ref<number[]>([])

// 表单相关
const formVisible = ref(false)
const formType = ref<'add' | 'edit'>('add')
const currentPermission = ref<any>({})

// 分配相关
const assignVisible = ref(false)

/**
 * 获取数据权限列表
 */
const fetchDataPermissionList = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const response = await getDataPermissionList(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to fetch data permissions:', error)
    ElMessage.error('获取数据权限列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchDataPermissionList()
}

/**
 * 重置搜索
 */
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    permission_type: undefined,
    scope: undefined,
    resource_type: '',
    is_active: undefined
  })
  handleSearch()
}

/**
 * 新增数据权限
 */
const handleAdd = () => {
  formType.value = 'add'
  currentPermission.value = {}
  formVisible.value = true
}

/**
 * 编辑数据权限
 */
const handleEdit = (row: DataPermissionListItem) => {
  formType.value = 'edit'
  currentPermission.value = { ...row }
  formVisible.value = true
}

/**
 * 删除数据权限
 */
const handleDelete = async (row: DataPermissionListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据权限"${row.name}"吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )
    
    await deleteDataPermission(row.id)
    ElMessage.success('删除成功')
    fetchDataPermissionList()
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
        type: 'warning'
      }
    )
    
    await bulkDeleteDataPermissions({
      ids: selectedIds.value,
      action: 'delete'
    })
    
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchDataPermissionList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch delete:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 分配权限
 */
const handleAssign = (row: DataPermissionListItem) => {
  currentPermission.value = row
  assignVisible.value = true
}

/**
 * 表格选择变化
 */
const handleSelectionChange = (selection: DataPermissionListItem[]) => {
  selectedIds.value = selection.map(item => item.id)
}

/**
 * 分页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchDataPermissionList()
}

/**
 * 当前页变化
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchDataPermissionList()
}

/**
 * 表单提交成功
 */
const handleFormSuccess = () => {
  formVisible.value = false
  fetchDataPermissionList()
}

/**
 * 分配成功
 */
const handleAssignSuccess = () => {
  assignVisible.value = false
  ElMessage.success('权限分配成功')
}

/**
 * 获取权限类型标签类型
 */
const getPermissionTypeTagType = (type: DataPermissionType) => {
  const typeMap = {
    [DataPermissionType.ALL]: 'danger',
    [DataPermissionType.SELF]: 'success',
    [DataPermissionType.DEPARTMENT]: 'warning',
    [DataPermissionType.DEPARTMENT_AND_SUB]: 'info',
    [DataPermissionType.CUSTOM]: 'primary'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取权限类型标签文本
 */
const getPermissionTypeLabel = (type: DataPermissionType) => {
  const option = DATA_PERMISSION_TYPE_OPTIONS.find(opt => opt.value === type)
  return option?.label || type
}

/**
 * 获取权限范围标签文本
 */
const getScopeLabel = (scope: DataPermissionScope) => {
  const option = DATA_PERMISSION_SCOPE_OPTIONS.find(opt => opt.value === scope)
  return option?.label || scope
}

// 初始化
onMounted(() => {
  fetchDataPermissionList()
})
</script>

<style scoped>
.data-permission-container {
  padding: 20px;
}

.search-bar {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-bar {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style>
