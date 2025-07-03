<template>
  <div class="department-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>🏢 部门管理</h2>
        <p>管理组织架构和部门信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增部门
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索区域 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="部门名称">
          <el-input 
            v-model="searchForm.name" 
            placeholder="请输入部门名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="部门编码">
          <el-input 
            v-model="searchForm.code" 
            placeholder="请输入部门编码"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 部门树表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="departmentTree"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        :default-expand-all="false"
        style="width: 100%"
      >
        <el-table-column prop="name" label="部门名称" min-width="200">
          <template #default="{ row }">
            <div class="department-name">
              <el-icon v-if="row.children && row.children.length > 0">
                <OfficeBuilding />
              </el-icon>
              <el-icon v-else><User /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="code" label="部门编码" width="150" />
        
        <el-table-column prop="manager_name" label="负责人" width="120">
          <template #default="{ row }">
            <span v-if="row.manager_name">{{ row.manager_name }}</span>
            <el-text v-else type="info">未设置</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="user_count" label="人员数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.user_count }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">
              查看
            </el-button>
            <el-button size="small" type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDelete(row)"
              :disabled="row.children && row.children.length > 0"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 部门表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入部门名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门编码" prop="code">
              <el-input v-model="formData.code" placeholder="请输入部门编码" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上级部门">
              <el-tree-select
                v-model="formData.parent_id"
                :data="departmentOptions"
                :props="{ label: 'name', value: 'id' }"
                placeholder="请选择上级部门"
                clearable
                check-strictly
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number 
                v-model="formData.sort_order" 
                :min="0" 
                :max="999"
                placeholder="排序"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="部门描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入部门描述"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="联系电话">
              <el-input v-model="formData.phone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="邮箱">
              <el-input v-model="formData.email" placeholder="邮箱地址" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="办公地址">
              <el-input v-model="formData.address" placeholder="办公地址" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, RefreshLeft, OfficeBuilding, User } from '@element-plus/icons-vue'
import * as departmentApi from '@/api/department'
import type { DepartmentTreeNode, DepartmentCreateRequest, DepartmentUpdateRequest } from '@/types'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentId = ref<number>()

const departmentTree = ref<DepartmentTreeNode[]>([])
const departmentOptions = ref<any[]>([])

// 搜索表单
const searchForm = reactive({
  name: '',
  code: ''
})

// 表单数据
const formData = reactive<DepartmentCreateRequest>({
  name: '',
  code: '',
  description: '',
  parent_id: undefined,
  manager_id: undefined,
  phone: '',
  email: '',
  address: '',
  sort_order: 0
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 50, message: '部门名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { min: 2, max: 50, message: '部门编码长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const formRef = ref()

// 方法
const fetchDepartmentTree = async () => {
  loading.value = true
  try {
    const response = await departmentApi.getDepartmentTree()
    departmentTree.value = response.data || []
  } catch (error) {
    ElMessage.error('获取部门树失败')
  } finally {
    loading.value = false
  }
}

const fetchDepartmentOptions = async () => {
  try {
    const response = await departmentApi.getDepartmentOptions()
    departmentOptions.value = response.data || []
  } catch (error) {
    console.error('获取部门选项失败:', error)
  }
}

const handleSearch = () => {
  // 实现搜索逻辑
  fetchDepartmentTree()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.code = ''
  fetchDepartmentTree()
}

const handleAdd = () => {
  dialogTitle.value = '新增部门'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: DepartmentTreeNode) => {
  dialogTitle.value = '编辑部门'
  isEdit.value = true
  currentId.value = row.id
  
  // 填充表单数据
  Object.assign(formData, {
    name: row.name,
    code: row.code,
    description: '',
    parent_id: row.parent_id,
    sort_order: row.sort_order
  })
  
  dialogVisible.value = true
}

const handleView = (row: DepartmentTreeNode) => {
  ElMessage.info('查看功能开发中...')
}

const handleDelete = async (row: DepartmentTreeNode) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门"${row.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await departmentApi.deleteDepartment(row.id)
    ElMessage.success('删除成功')
    await fetchDepartmentTree()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value && currentId.value) {
      await departmentApi.updateDepartment(currentId.value, formData as DepartmentUpdateRequest)
      ElMessage.success('更新成功')
    } else {
      await departmentApi.createDepartment(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    await fetchDepartmentTree()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    description: '',
    parent_id: undefined,
    manager_id: undefined,
    phone: '',
    email: '',
    address: '',
    sort_order: 0
  })
  
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

const refreshData = () => {
  fetchDepartmentTree()
  fetchDepartmentOptions()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  fetchDepartmentTree()
  fetchDepartmentOptions()
})
</script>

<style scoped lang="scss">
.department-container {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      h2 {
        margin: 0 0 5px 0;
        color: #303133;
        font-size: 20px;
      }
      
      p {
        margin: 0;
        color: #909399;
        font-size: 14px;
      }
    }
    
    .header-right {
      display: flex;
      gap: 10px;
    }
  }
  
  .search-card {
    margin-bottom: 20px;
    
    :deep(.el-card__body) {
      padding: 20px;
    }
  }
  
  .table-card {
    :deep(.el-card__body) {
      padding: 0;
    }
    
    .department-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-icon {
        color: #409eff;
      }
    }
  }
}
</style>
