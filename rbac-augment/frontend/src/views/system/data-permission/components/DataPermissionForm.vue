<template>
  <el-dialog
    :model-value="visible"
    :title="formType === 'add' ? '新增数据权限' : '编辑数据权限'"
    width="600px"
    :before-close="handleClose"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      label-position="right"
    >
      <el-form-item label="权限名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入权限名称"
          clearable
        />
      </el-form-item>

      <el-form-item label="权限编码" prop="code">
        <el-input
          v-model="form.code"
          placeholder="请输入权限编码，如：user:read"
          clearable
        />
      </el-form-item>

      <el-form-item label="权限类型" prop="permission_type">
        <el-select
          v-model="form.permission_type"
          placeholder="请选择权限类型"
          style="width: 100%"
        >
          <el-option label="部门权限" value="department" />
          <el-option label="角色权限" value="role" />
          <el-option label="用户权限" value="user" />
          <el-option label="自定义权限" value="custom" />
        </el-select>
      </el-form-item>

      <el-form-item label="数据范围" prop="data_scope">
        <el-select
          v-model="form.data_scope"
          placeholder="请选择数据范围"
          style="width: 100%"
        >
          <el-option label="全部数据" value="all" />
          <el-option label="本部门数据" value="department" />
          <el-option label="本部门及下级部门数据" value="department_and_children" />
          <el-option label="仅本人数据" value="self" />
          <el-option label="自定义数据" value="custom" />
        </el-select>
      </el-form-item>

      <el-form-item label="资源类型" prop="resource_type">
        <el-input
          v-model="form.resource_type"
          placeholder="请输入资源类型，如：user, role, department"
          clearable
        />
      </el-form-item>

      <el-form-item label="资源ID" prop="resource_id">
        <el-input
          v-model="form.resource_id"
          placeholder="请输入资源ID（可选）"
          clearable
        />
      </el-form-item>

      <el-form-item label="条件表达式" prop="conditions">
        <el-input
          v-model="form.conditions"
          type="textarea"
          :rows="3"
          placeholder="请输入条件表达式（JSON格式，可选）"
        />
      </el-form-item>

      <el-form-item label="权限描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入权限描述"
        />
      </el-form-item>

      <el-form-item label="状态" prop="is_active">
        <el-switch
          v-model="form.is_active"
          active-text="启用"
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
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createDataPermission, updateDataPermission } from '@/api/data-permission'
import type { DataPermissionCreateRequest, DataPermissionUpdateRequest } from '@/types/data-permission'

interface Props {
  visible: boolean
  formData?: any
  formType: 'add' | 'edit'
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  formData: () => ({})
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive({
  name: '',
  code: '',
  permission_type: 'department',
  data_scope: 'department',
  resource_type: '',
  resource_id: '',
  conditions: '',
  description: '',
  is_active: true
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '权限名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_:]*$/, message: '权限编码格式不正确', trigger: 'blur' }
  ],
  permission_type: [
    { required: true, message: '请选择权限类型', trigger: 'change' }
  ],
  data_scope: [
    { required: true, message: '请选择数据范围', trigger: 'change' }
  ],
  resource_type: [
    { required: true, message: '请输入资源类型', trigger: 'blur' }
  ]
}

// 监听弹窗显示状态
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      nextTick(() => {
        resetForm()
        if (props.formType === 'edit' && props.formData) {
          Object.assign(form, props.formData)
        }
      })
    }
  }
)

/**
 * 重置表单
 */
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(form, {
    name: '',
    code: '',
    permission_type: 'department',
    data_scope: 'department',
    resource_type: '',
    resource_id: '',
    conditions: '',
    description: '',
    is_active: true
  })
}

/**
 * 关闭弹窗
 */
const handleClose = () => {
  emit('update:visible', false)
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 处理条件表达式
    let conditions = null
    if (form.conditions) {
      try {
        conditions = JSON.parse(form.conditions)
      } catch (error) {
        ElMessage.error('条件表达式格式不正确，请输入有效的JSON')
        return
      }
    }

    const submitData = {
      ...form,
      conditions,
      resource_id: form.resource_id || null
    }

    if (props.formType === 'add') {
      await createDataPermission(submitData as DataPermissionCreateRequest)
      ElMessage.success('创建数据权限成功')
    } else {
      await updateDataPermission(props.formData.id, submitData as DataPermissionUpdateRequest)
      ElMessage.success('更新数据权限成功')
    }

    emit('success')
    handleClose()
  } catch (error) {
    console.error('Submit failed:', error)
    ElMessage.error('操作失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>
