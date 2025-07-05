<template>
  <el-dialog
    v-model="dialogVisible"
    :title="formType === 'add' ? '新增用户' : '编辑用户'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      label-width="80px"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :disabled="formType === 'edit'"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20" v-if="formType === 'add'">
        <el-col :span="12">
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="form.confirm_password"
              type="password"
              placeholder="请确认密码"
              show-password
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="姓名" prop="full_name">
            <el-input
              v-model="form.full_name"
              placeholder="请输入姓名"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="请输入手机号"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="角色" prop="role_ids">
        <el-select
          v-model="form.role_ids"
          multiple
          placeholder="请选择角色"
          style="width: 100%"
        >
          <el-option
            v-for="role in roleOptions"
            :key="role.id"
            :label="role.name"
            :value="role.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="状态">
        <el-switch
          v-model="form.is_active"
          active-text="激活"
          inactive-text="禁用"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createUser, updateUser } from '@/api/user'
import { getRoleOptions } from '@/api/role'
import { isValidEmail, isValidPhone } from '@/utils'
import { commonRules, validateEmail, validatePhone, validatePassword } from '@/utils/validation'
import { loadingManager } from '@/utils/performance'
import type { UserCreateRequest, UserUpdateRequest, RoleSelectOption } from '@/types'

interface Props {
  visible: boolean
  formData: any
  formType: 'add' | 'edit'
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表单引用
const formRef = ref<FormInstance>()

// 加载状态
const loading = ref(false)

// 角色选项
const roleOptions = ref<RoleSelectOption[]>([])

// 表单数据
const form = reactive<UserCreateRequest & { confirm_password?: string }>({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  full_name: '',
  phone: '',
  is_active: true,
  role_ids: []
})

// 表单验证规则 - 使用新的验证规则库
const formRules: FormRules = {
  username: commonRules.username(),
  email: commonRules.email(),
  password: commonRules.password(),
  confirm_password: [
    commonRules.required('请确认密码'),
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  phone: commonRules.phone(false), // 手机号非必填
  full_name: [
    commonRules.required('请输入姓名'),
    commonRules.length(2, 50, '姓名长度在 2 到 50 个字符')
  ]
}

/**
 * 获取角色选项
 */
const fetchRoleOptions = async () => {
  try {
    const response = await getRoleOptions()
    roleOptions.value = response.data
  } catch (error) {
    console.error('Failed to fetch role options:', error)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(form, {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    full_name: '',
    phone: '',
    is_active: true,
    role_ids: []
  })
  formRef.value?.clearValidate()
}

/**
 * 处理提交 - 使用增强的加载管理和错误处理
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    // 表单验证
    await formRef.value.validate()

    // 使用加载管理器包装异步操作
    await loadingManager.wrap(async () => {
      if (props.formType === 'add') {
        // 新增用户
        const { confirm_password, ...createData } = form
        await createUser(createData as UserCreateRequest)
        ElMessage.success('用户创建成功')
      } else {
        // 编辑用户
        const { password, confirm_password, username, ...updateData } = form
        await updateUser(props.formData.id, updateData as UserUpdateRequest)
        ElMessage.success('用户更新成功')
      }
    }, 'user-form-submit')

    emit('success')
    handleClose()
  } catch (error) {
    console.error('Failed to submit user form:', error)
    // 错误处理已由全局错误处理器处理
  }
}

/**
 * 处理关闭
 */
const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

// 监听表单数据变化
watch(
  () => props.formData,
  (newData) => {
    if (newData && props.visible) {
      Object.assign(form, {
        username: newData.username || '',
        email: newData.email || '',
        full_name: newData.full_name || '',
        phone: newData.phone || '',
        is_active: newData.is_active ?? true,
        role_ids: newData.role_ids || []
      })
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      fetchRoleOptions()
    }
  }
)
</script>

<style lang="scss" scoped>
.dialog-footer {
  text-align: right;
}
</style>
