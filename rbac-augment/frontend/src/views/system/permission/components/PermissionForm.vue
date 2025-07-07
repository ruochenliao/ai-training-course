<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="700px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="permission-form"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="权限名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入权限名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="权限代码" prop="code">
            <el-input
              v-model="formData.code"
              placeholder="请输入权限代码"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="资源" prop="resource">
            <el-input
              v-model="formData.resource"
              placeholder="请输入资源名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="动作" prop="action">
            <el-select
              v-model="formData.action"
              placeholder="请选择动作"
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="action in actionOptions"
                :key="action.value"
                :label="action.label"
                :value="action.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="父级权限">
            <el-cascader
              v-model="formData.parent_id"
              :options="permissionOptions"
              :props="cascaderProps"
              placeholder="请选择父级权限"
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

      <el-form-item label="权限描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入权限描述"
        />
      </el-form-item>

      <el-form-item label="状态">
        <el-switch
          v-model="formData.is_active"
          active-text="启用"
          inactive-text="禁用"
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
import { createPermission, updatePermission, getPermissionOptions } from '@/api/permission'
import type { PermissionCreateRequest, PermissionUpdateRequest } from '@/types'

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
  return props.formType === 'add' ? '新增权限' : '编辑权限'
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
  resource: '',
  action: '',
  description: '',
  parent_id: null as number | null,
  sort_order: 0,
  is_active: true
})

// 动作选项
const actionOptions = [
  { label: '查看', value: 'read' },
  { label: '创建', value: 'create' },
  { label: '更新', value: 'update' },
  { label: '删除', value: 'delete' },
  { label: '管理', value: 'manage' },
  { label: '配置', value: 'config' },
  { label: '导出', value: 'export' },
  { label: '导入', value: 'import' }
]

// 权限选项
const permissionOptions = ref<any[]>([])

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
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '权限名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z][a-zA-Z0-9_:]*$/, 
      message: '权限代码只能包含字母、数字、下划线和冒号，且以字母开头', 
      trigger: 'blur' 
    }
  ],
  resource: [
    { required: true, message: '请输入资源名称', trigger: 'blur' }
  ],
  action: [
    { required: true, message: '请选择动作', trigger: 'change' }
  ]
}

/**
 * 获取权限选项
 */
const fetchPermissionOptions = async () => {
  try {
    const response = await getPermissionOptions()
    permissionOptions.value = response.data
  } catch (error) {
    console.error('Failed to fetch permission options:', error)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    resource: '',
    action: '',
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
    resource: data.resource || '',
    action: data.action || '',
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
      resource: formData.resource,
      action: formData.action,
      description: formData.description,
      parent_id: formData.parent_id,
      sort_order: formData.sort_order,
      is_active: formData.is_active
    }

    if (props.formType === 'add') {
      await createPermission(submitData as PermissionCreateRequest)
      ElMessage.success('权限创建成功')
    } else {
      await updatePermission(props.formData.id, submitData as PermissionUpdateRequest)
      ElMessage.success('权限更新成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Submit permission error:', error)
    ElMessage.error(props.formType === 'add' ? '权限创建失败' : '权限更新失败')
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
      fetchPermissionOptions()
      if (props.formType === 'add') {
        resetForm()
      }
    }
  }
)
</script>

<style lang="scss" scoped>
.permission-form {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
