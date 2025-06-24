<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <n-icon><PersonAdd /></n-icon>
        </template>
        添加用户
      </n-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="mb-6 flex gap-4">
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索用户名、邮箱或姓名"
        class="flex-1"
        @input="handleSearch"
      >
        <template #prefix>
          <n-icon><Search /></n-icon>
        </template>
      </n-input>
      <n-select
        v-model:value="roleFilter"
        placeholder="角色筛选"
        :options="roleOptions"
        class="w-40"
        @update:value="handleFilter"
      />
      <n-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        :options="statusOptions"
        class="w-40"
        @update:value="handleFilter"
      />
      <n-button @click="refreshData">
        <template #icon>
          <n-icon><Refresh /></n-icon>
        </template>
        刷新
      </n-button>
    </div>

    <!-- 用户列表 -->
    <n-data-table
      :columns="columns"
      :data="filteredUsers"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      @update:checked-row-keys="handleCheck"
    />

    <!-- 批量操作 -->
    <div v-if="checkedRowKeys.length > 0" class="mt-4 flex gap-2">
      <n-button @click="handleBatchEnable">
        批量启用 ({{ checkedRowKeys.length }})
      </n-button>
      <n-button @click="handleBatchDisable">
        批量禁用
      </n-button>
      <n-button type="error" @click="handleBatchDelete">
        批量删除
      </n-button>
    </div>

    <!-- 创建用户模态框 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="添加用户">
      <n-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="createForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="createForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
          <n-input v-model:value="createForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="createForm.password"
            type="password"
            placeholder="请输入密码"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="角色" path="role">
          <n-select
            v-model:value="createForm.role"
            :options="roleOptions.filter(r => r.value)"
            placeholder="选择用户角色"
          />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="createForm.department" placeholder="请输入部门" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </n-button>
      </template>
    </n-modal>

    <!-- 编辑用户模态框 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑用户">
      <n-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="editForm.username" disabled />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="editForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
          <n-input v-model:value="editForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="角色" path="role">
          <n-select
            v-model:value="editForm.role"
            :options="roleOptions.filter(r => r.value)"
            placeholder="选择用户角色"
          />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="editForm.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item label="状态" path="is_active">
          <n-switch v-model:value="editForm.is_active" />
          <span class="ml-2 text-sm text-gray-500">
            {{ editForm.is_active ? '启用' : '禁用' }}
          </span>
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="handleUpdate" :loading="updating">
          更新
        </n-button>
      </template>
    </n-modal>

    <!-- 重置密码模态框 -->
    <n-modal v-model:show="showPasswordModal" preset="dialog" title="重置密码">
      <n-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="新密码" path="password">
          <n-input
            v-model:value="passwordForm.password"
            type="password"
            placeholder="请输入新密码"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="确认密码" path="confirmPassword">
          <n-input
            v-model:value="passwordForm.confirmPassword"
            type="password"
            placeholder="请确认新密码"
            show-password-on="click"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showPasswordModal = false">取消</n-button>
        <n-button type="primary" @click="handleResetPassword" :loading="resettingPassword">
          重置密码
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSwitch,
  NTag,
  useMessage
} from 'naive-ui'
import {
  Create as Edit,
  Key,
  PersonAdd,
  Refresh,
  Search,
  Trash as Delete
} from '@vicons/ionicons5'
import { useUserStore } from '~/stores/user'

const message = useMessage()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const resettingPassword = ref(false)
const searchQuery = ref('')
const roleFilter = ref(null)
const statusFilter = ref(null)
const checkedRowKeys = ref([])
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showPasswordModal = ref(false)
const createFormRef = ref()
const editFormRef = ref()
const passwordFormRef = ref()
const selectedUserId = ref('')

// 表单数据
const createForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role: 'user',
  department: ''
})

const editForm = reactive({
  id: '',
  username: '',
  email: '',
  full_name: '',
  role: 'user',
  department: '',
  is_active: true
})

const passwordForm = reactive({
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const editRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const passwordRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value) => {
        return value === passwordForm.password
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 选项数据
const roleOptions = [
  { label: '全部角色', value: null },
  { label: '超级管理员', value: 'admin' },
  { label: '管理员', value: 'manager' },
  { label: '普通用户', value: 'user' }
]

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '启用', value: true },
  { label: '禁用', value: false }
]

// 表格列配置
const columns = [
  { type: 'selection' },
  {
    title: '用户名',
    key: 'username',
    render: (row) => h('div', { class: 'font-medium' }, row.username)
  },
  {
    title: '姓名',
    key: 'full_name'
  },
  {
    title: '邮箱',
    key: 'email'
  },
  {
    title: '角色',
    key: 'role',
    render: (row) => {
      const roleMap = {
        admin: { color: 'error', text: '超级管理员' },
        manager: { color: 'warning', text: '管理员' },
        user: { color: 'info', text: '普通用户' }
      }
      const role = roleMap[row.role] || { color: 'default', text: '未知' }
      return h(NTag, { type: role.color }, { default: () => role.text })
    }
  },
  {
    title: '部门',
    key: 'department'
  },
  {
    title: '状态',
    key: 'is_active',
    render: (row) => h(NTag, { 
      type: row.is_active ? 'success' : 'error' 
    }, { 
      default: () => row.is_active ? '启用' : '禁用' 
    })
  },
  {
    title: '最后登录',
    key: 'last_login_at',
    render: (row) => row.last_login_at ? new Date(row.last_login_at).toLocaleString() : '从未登录'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h('div', { class: 'flex gap-2' }, [
      h(NButton, {
        size: 'small',
        type: 'primary',
        onClick: () => handleEdit(row)
      }, { default: () => '编辑', icon: () => h(NIcon, null, { default: () => h(Edit) }) }),
      h(NButton, {
        size: 'small',
        onClick: () => handleResetPasswordModal(row)
      }, { default: () => '重置密码', icon: () => h(NIcon, null, { default: () => h(Key) }) }),
      h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => handleDelete(row)
      }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(Delete) }) })
    ])
  }
]

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

// 计算属性
const filteredUsers = computed(() => {
  let result = userStore.users
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(user => 
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query) ||
      user.full_name.toLowerCase().includes(query)
    )
  }
  
  if (roleFilter.value) {
    result = result.filter(user => user.role === roleFilter.value)
  }
  
  if (statusFilter.value !== null) {
    result = result.filter(user => user.is_active === statusFilter.value)
  }
  
  return result
})

// 事件处理函数
const handleSearch = () => {
  pagination.page = 1
}

const handleFilter = () => {
  pagination.page = 1
}

const refreshData = async () => {
  loading.value = true
  try {
    await userStore.fetchUsers()
  } catch (error) {
    message.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const handleCheck = (keys: string[]) => {
  checkedRowKeys.value = keys
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>
