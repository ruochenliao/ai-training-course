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
      class="department-form"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="部门名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入部门名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="部门代码" prop="code">
            <el-input
              v-model="formData.code"
              placeholder="请输入部门代码"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="负责人">
            <el-input
              v-model="formData.manager_name"
              placeholder="请输入负责人姓名"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话">
            <el-input
              v-model="formData.phone"
              placeholder="请输入联系电话"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="父级部门">
            <el-cascader
              v-model="formData.parent_id"
              :options="departmentOptions"
              :props="cascaderProps"
              placeholder="请选择父级部门"
              clearable
              style="width: 100%"
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
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="邮箱">
            <el-input
              v-model="formData.email"
              placeholder="请输入部门邮箱"
              clearable
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

      <el-form-item label="部门地址">
        <el-input
          v-model="formData.address"
          placeholder="请输入部门地址"
          clearable
        />
      </el-form-item>

      <el-form-item label="部门描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入部门描述"
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
import { createDepartment, updateDepartment, getDepartmentOptions } from '@/api/department'
import type { DepartmentCreateRequest, DepartmentUpdateRequest } from '@/types'

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
  return props.formType === 'add' ? '新增部门' : '编辑部门'
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
  manager_name: '',
  phone: '',
  email: '',
  address: '',
  description: '',
  parent_id: null as number | null,
  sort_order: 0,
  is_active: true
})

// 部门选项
const departmentOptions = ref<any[]>([])

// 级联选择器属性
const cascaderProps = {
  checkStrictly: true,
  emitPath: false,
  value: 'id',
  label: 'name',
  children: 'children'
}

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 50, message: '部门名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门代码', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, 
      message: '部门代码只能包含字母、数字和下划线，且以字母开头', 
      trigger: 'blur' 
    }
  ]
}

/**
 * 获取部门选项
 */
const fetchDepartmentOptions = async () => {
  try {
    const response = await getDepartmentOptions()
    departmentOptions.value = response.data
  } catch (error) {
    console.error('Failed to fetch department options:', error)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    manager_name: '',
    phone: '',
    email: '',
    address: '',
    description: '',
    parent_id: null,
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
    manager_name: data.manager_name || '',
    phone: data.phone || '',
    email: data.email || '',
    address: data.address || '',
    description: data.description || '',
    parent_id: data.parent_id || null,
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
      manager_name: formData.manager_name,
      phone: formData.phone,
      email: formData.email,
      address: formData.address,
      description: formData.description,
      parent_id: formData.parent_id,
      sort_order: formData.sort_order,
      is_active: formData.is_active
    }

    if (props.formType === 'add') {
      await createDepartment(submitData as DepartmentCreateRequest)
      ElMessage.success('部门创建成功')
    } else {
      await updateDepartment(props.formData.id, submitData as DepartmentUpdateRequest)
      ElMessage.success('部门更新成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Submit department error:', error)
    ElMessage.error(props.formType === 'add' ? '部门创建失败' : '部门更新失败')
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
    if (visible) {
      fetchDepartmentOptions()
      if (props.formType === 'add') {
        resetForm()
      }
    }
  }
)
</script>

<style lang="scss" scoped>
.department-form {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
