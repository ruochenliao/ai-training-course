<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="600px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="role-form"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="角色名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入角色名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="角色代码" prop="code">
            <el-input
              v-model="formData.code"
              placeholder="请输入角色代码"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="排序">
            <el-input-number
              v-model="formData.sort_order"
              :min="0"
              :max="999"
              placeholder="排序"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态">
            <el-switch
              v-model="formData.is_active"
              active-text="启用"
              inactive-text="禁用"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="角色描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入角色描述"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button
        type="primary"
        :loading="submitLoading"
        @click="handleSubmit"
      >
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createRole, updateRole } from '@/api/role'
import type { RoleCreateRequest, RoleUpdateRequest } from '@/types'

interface Props {
  visible: boolean
  formData?: any
  formType: 'add' | 'edit'
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  formData: () => ({}),
  formType: 'add'
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()
const submitLoading = ref(false)

// 对话框标题
const dialogTitle = computed(() => {
  return props.formType === 'add' ? '新增角色' : '编辑角色'
})

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表单数据
const formData = reactive({
  name: '',
  code: '',
  description: '',
  sort_order: 0,
  is_active: true
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, 
      message: '角色代码只能包含字母、数字和下划线，且以字母开头', 
      trigger: 'blur' 
    }
  ]
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    description: '',
    sort_order: 0,
    is_active: true
  })
  formRef.value?.resetFields()
}

/**
 * 填充表单数据
 */
const fillForm = (data: any) => {
  Object.assign(formData, {
    name: data.name || '',
    code: data.code || '',
    description: data.description || '',
    sort_order: data.sort_order || 0,
    is_active: data.is_active !== undefined ? data.is_active : true
  })
}

/**
 * 处理提交
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    const submitData = {
      name: formData.name,
      code: formData.code,
      description: formData.description,
      sort_order: formData.sort_order,
      is_active: formData.is_active
    }

    if (props.formType === 'add') {
      await createRole(submitData as RoleCreateRequest)
      ElMessage.success('角色创建成功')
    } else {
      await updateRole(props.formData.id, submitData as RoleUpdateRequest)
      ElMessage.success('角色更新成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Submit role error:', error)
    ElMessage.error(props.formType === 'add' ? '角色创建失败' : '角色更新失败')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  emit('update:visible', false)
  resetForm()
}

// 监听表单数据变化
watch(
  () => props.formData,
  (newData) => {
    if (newData && Object.keys(newData).length > 0) {
      fillForm(newData)
    }
  },
  { immediate: true, deep: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.formType === 'add') {
      resetForm()
    }
  }
)
</script>

<style lang="scss" scoped>
.role-form {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
