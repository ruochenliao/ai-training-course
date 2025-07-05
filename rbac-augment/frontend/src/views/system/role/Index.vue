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
        <el-table-column label="操作" width="320" fixed="right">
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
                v-permission="['role:update']"
                type="success"
                size="small"
                @click="handleAssignPermissions(row)"
              >
                权限分配
              </el-button>
              <el-button
                v-permission="['role:update']"
                type="info"
                size="small"
                @click="handleAssignMenus(row)"
              >
                菜单分配
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

    <!-- 权限分配对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限分配"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentRole" class="dialog-header">
        <p>为角色 <strong>{{ currentRole.name }}</strong> 分配权限</p>
      </div>

      <el-tree
        ref="permissionTreeRef"
        :data="permissionTree"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        show-checkbox
        check-strictly
        :default-checked-keys="selectedPermissions"
        class="permission-tree"
      />

      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSavePermissions">保存</el-button>
      </template>
    </el-dialog>

    <!-- 菜单分配对话框 -->
    <el-dialog
      v-model="menuDialogVisible"
      title="菜单分配"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentRole" class="dialog-header">
        <p>为角色 <strong>{{ currentRole.name }}</strong> 分配菜单</p>
      </div>

      <el-tree
        ref="menuTreeRef"
        :data="menuTree"
        :props="{ children: 'children', label: 'title' }"
        node-key="id"
        show-checkbox
        check-strictly
        :default-checked-keys="selectedMenus"
        class="menu-tree"
      />

      <template #footer>
        <el-button @click="menuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveMenus">保存</el-button>
      </template>
    </el-dialog>

    <!-- 角色表单对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="roleDialogTitle"
      width="600px"
      :close-on-click-modal="false"
      @close="handleRoleDialogClose"
    >
      <el-form
        ref="roleFormRef"
        :model="roleFormData"
        :rules="roleFormRules"
        label-width="100px"
        :disabled="roleDialogTitle.includes('查看')"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色名称" prop="name">
              <el-input v-model="roleFormData.name" placeholder="请输入角色名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色代码" prop="code">
              <el-input v-model="roleFormData.code" placeholder="请输入角色代码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch
                v-model="roleFormData.is_active"
                active-text="激活"
                inactive-text="禁用"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number
                v-model="roleFormData.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="角色描述">
          <el-input
            v-model="roleFormData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div v-if="!roleDialogTitle.includes('查看')">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRoleSubmit">
            {{ isEditRole ? '更新' : '创建' }}
          </el-button>
        </div>
        <div v-else>
          <el-button @click="roleDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoleList, deleteRole, bulkDeleteRoles, assignRolePermissions, assignRoleMenus, createRole, updateRole, getRoleDetail, getRolePermissions, getRoleMenus } from '@/api/role'
import { getPermissionTree } from '@/api/permission'
import { getMenuTree } from '@/api/menu'
import { formatDateTime } from '@/utils'
import type { RoleListItem, PaginationParams, RoleCreateRequest, RoleUpdateRequest } from '@/types'

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

// 权限分配对话框
const permissionDialogVisible = ref(false)
const currentRole = ref<RoleListItem | null>(null)
const permissionTree = ref<any[]>([])
const selectedPermissions = ref<number[]>([])

// 菜单分配对话框
const menuDialogVisible = ref(false)
const menuTree = ref<any[]>([])
const selectedMenus = ref<number[]>([])

// 树形组件引用
const permissionTreeRef = ref()
const menuTreeRef = ref()

// 角色表单对话框
const roleDialogVisible = ref(false)
const roleDialogTitle = ref('')
const isEditRole = ref(false)
const currentRoleId = ref<number>()

// 表单引用
const roleFormRef = ref()

// 角色表单数据
const roleFormData = ref<RoleCreateRequest>({
  name: '',
  code: '',
  description: '',
  is_active: true,
  sort_order: 0
})

// 角色表单验证规则
const roleFormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '角色代码只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ]
}

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
  roleDialogTitle.value = '新增角色'
  isEditRole.value = false
  resetRoleForm()
  roleDialogVisible.value = true
}

/**
 * 处理编辑
 */
const handleEdit = async (row: RoleListItem) => {
  try {
    roleDialogTitle.value = '编辑角色'
    isEditRole.value = true
    currentRoleId.value = row.id

    // 获取角色详情
    const response = await getRoleDetail(row.id)
    fillRoleForm(response.data)

    roleDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch role detail:', error)
    ElMessage.error('获取角色详情失败')
  }
}

/**
 * 处理查看
 */
const handleView = async (row: RoleListItem) => {
  try {
    roleDialogTitle.value = '查看角色'
    isEditRole.value = false

    // 获取角色详情
    const response = await getRoleDetail(row.id)
    fillRoleForm(response.data)

    roleDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch role detail:', error)
    ElMessage.error('获取角色详情失败')
  }
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

/**
 * 处理权限分配
 */
const handleAssignPermissions = async (row: RoleListItem) => {
  try {
    currentRole.value = row

    // 获取权限树
    const permissionResponse = await getPermissionTree()
    permissionTree.value = permissionResponse.data

    // 获取角色已有权限
    const rolePermissionResponse = await getRolePermissions(row.id)
    selectedPermissions.value = rolePermissionResponse.data.permission_ids

    permissionDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch permissions:', error)
    ElMessage.error('获取权限数据失败')
  }
}

/**
 * 处理菜单分配
 */
const handleAssignMenus = async (row: RoleListItem) => {
  try {
    currentRole.value = row

    // 获取菜单树
    const menuResponse = await getMenuTree()
    menuTree.value = menuResponse.data

    // 获取角色已有菜单
    const roleMenuResponse = await getRoleMenus(row.id)
    selectedMenus.value = roleMenuResponse.data.menu_ids

    menuDialogVisible.value = true
  } catch (error) {
    console.error('Failed to fetch menus:', error)
    ElMessage.error('获取菜单数据失败')
  }
}

/**
 * 保存权限分配
 */
const handleSavePermissions = async () => {
  if (!currentRole.value) return

  try {
    const checkedKeys = permissionTreeRef.value?.getCheckedKeys() || []
    const halfCheckedKeys = permissionTreeRef.value?.getHalfCheckedKeys() || []
    const allPermissionIds = [...checkedKeys, ...halfCheckedKeys]

    await assignRolePermissions(currentRole.value.id, {
      permission_ids: allPermissionIds
    })

    ElMessage.success('权限分配成功')
    permissionDialogVisible.value = false
    // 刷新角色列表
    fetchRoleList()
  } catch (error) {
    console.error('Failed to assign permissions:', error)
    ElMessage.error('权限分配失败')
  }
}

/**
 * 保存菜单分配
 */
const handleSaveMenus = async () => {
  if (!currentRole.value) return

  try {
    const checkedKeys = menuTreeRef.value?.getCheckedKeys() || []
    const halfCheckedKeys = menuTreeRef.value?.getHalfCheckedKeys() || []
    const allMenuIds = [...checkedKeys, ...halfCheckedKeys]

    await assignRoleMenus(currentRole.value.id, {
      menu_ids: allMenuIds
    })

    ElMessage.success('菜单分配成功')
    menuDialogVisible.value = false
    // 刷新角色列表
    fetchRoleList()
  } catch (error) {
    console.error('Failed to assign menus:', error)
    ElMessage.error('菜单分配失败')
  }
}

/**
 * 重置角色表单
 */
const resetRoleForm = () => {
  roleFormData.value = {
    name: '',
    code: '',
    description: '',
    is_active: true,
    sort_order: 0
  }
  if (roleFormRef.value) {
    roleFormRef.value.clearValidate()
  }
}

/**
 * 填充角色表单数据
 */
const fillRoleForm = (role: any) => {
  roleFormData.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
    is_active: role.is_active,
    sort_order: role.sort_order || 0
  }
}

/**
 * 处理角色表单提交
 */
const handleRoleSubmit = async () => {
  if (!roleFormRef.value) return

  try {
    await roleFormRef.value.validate()

    if (isEditRole.value && currentRoleId.value) {
      await updateRole(currentRoleId.value, roleFormData.value)
      ElMessage.success('角色更新成功')
    } else {
      await createRole(roleFormData.value)
      ElMessage.success('角色创建成功')
    }

    roleDialogVisible.value = false
    fetchRoleList()
  } catch (error) {
    console.error('Failed to submit role:', error)
    ElMessage.error(isEditRole.value ? '角色更新失败' : '角色创建失败')
  }
}

/**
 * 处理角色对话框关闭
 */
const handleRoleDialogClose = () => {
  resetRoleForm()
  currentRoleId.value = undefined
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
      flex-wrap: wrap;
    }

    .table-pagination {
      padding: 16px 20px;
      text-align: right;
      border-top: 1px solid #ebeef5;
    }
  }

  .dialog-header {
    margin-bottom: 16px;

    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }

  .permission-tree,
  .menu-tree {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 8px;
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
