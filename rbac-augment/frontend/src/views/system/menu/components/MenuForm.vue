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
      class="menu-form"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="菜单名称" prop="title">
            <el-input
              v-model="formData.title"
              placeholder="请输入菜单名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="菜单类型" prop="type">
            <el-select
              v-model="formData.type"
              placeholder="请选择菜单类型"
              style="width: 100%"
            >
              <el-option label="目录" value="目录" />
              <el-option label="菜单" value="菜单" />
              <el-option label="按钮" value="按钮" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="路由路径" prop="path">
            <el-input
              v-model="formData.path"
              placeholder="请输入路由路径"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="组件路径">
            <el-input
              v-model="formData.component"
              placeholder="请输入组件路径"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="菜单图标">
            <el-input
              v-model="formData.icon"
              placeholder="请输入图标名称"
              clearable
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
          <el-form-item label="父级菜单">
            <el-cascader
              v-model="formData.parent_id"
              :options="menuOptions"
              :props="cascaderProps"
              placeholder="请选择父级菜单"
              clearable
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="权限标识">
            <el-input
              v-model="formData.permission"
              placeholder="请输入权限标识"
              clearable
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="状态">
            <el-switch
              v-model="formData.is_active"
              active-text="启用"
              inactive-text="禁用"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="隐藏">
            <el-switch
              v-model="formData.is_hidden"
              active-text="隐藏"
              inactive-text="显示"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="缓存">
            <el-switch
              v-model="formData.keep_alive"
              active-text="缓存"
              inactive-text="不缓存"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="菜单描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入菜单描述"
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
import { createMenu, updateMenu, getMenuOptions } from '@/api/menu'
import type { MenuCreateRequest, MenuUpdateRequest } from '@/types'

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
  return props.formType === 'add' ? '新增菜单' : '编辑菜单'
})

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表单数据
const formData = reactive({
  title: '',
  type: '菜单',
  path: '',
  component: '',
  icon: '',
  permission: '',
  parent_id: null as number | null,
  sort_order: 0,
  is_active: true,
  is_hidden: false,
  keep_alive: false,
  description: ''
})

// 菜单选项
const menuOptions = ref<any[]>([])

// 级联选择器属性
const cascaderProps = {
  checkStrictly: true,
  emitPath: false,
  value: 'id',
  label: 'title',
  children: 'children'
}

// 表单验证规则
const formRules: FormRules = {
  title: [
    { required: true, message: '请输入菜单名称', trigger: 'blur' },
    { min: 2, max: 50, message: '菜单名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择菜单类型', trigger: 'change' }
  ],
  path: [
    { required: true, message: '请输入路由路径', trigger: 'blur' }
  ]
}

/**
 * 获取菜单选项
 */
const fetchMenuOptions = async () => {
  try {
    const response = await getMenuOptions()
    menuOptions.value = response.data
  } catch (error) {
    console.error('Failed to fetch menu options:', error)
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(formData, {
    title: '',
    type: '菜单',
    path: '',
    component: '',
    icon: '',
    permission: '',
    parent_id: null,
    sort_order: 0,
    is_active: true,
    is_hidden: false,
    keep_alive: false,
    description: ''
  })
  formRef.value?.resetFields()
}

/**
 * 填充表单数据
 */
const fillForm = (data: any) => {
  Object.assign(formData, {
    title: data.title || '',
    type: data.type || '菜单',
    path: data.path || '',
    component: data.component || '',
    icon: data.icon || '',
    permission: data.permission || '',
    parent_id: data.parent_id || null,
    sort_order: data.sort_order || 0,
    is_active: data.is_active !== undefined ? data.is_active : true,
    is_hidden: data.is_hidden !== undefined ? data.is_hidden : false,
    keep_alive: data.keep_alive !== undefined ? data.keep_alive : false,
    description: data.description || ''
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
      title: formData.title,
      type: formData.type,
      path: formData.path,
      component: formData.component,
      icon: formData.icon,
      permission: formData.permission,
      parent_id: formData.parent_id,
      sort_order: formData.sort_order,
      is_active: formData.is_active,
      is_hidden: formData.is_hidden,
      keep_alive: formData.keep_alive,
      description: formData.description
    }

    if (props.formType === 'add') {
      await createMenu(submitData as MenuCreateRequest)
      ElMessage.success('菜单创建成功')
    } else {
      await updateMenu(props.formData.id, submitData as MenuUpdateRequest)
      ElMessage.success('菜单更新成功')
    }

    emit('success')
    handleCancel()
  } catch (error) {
    console.error('Submit menu error:', error)
    ElMessage.error(props.formType === 'add' ? '菜单创建失败' : '菜单更新失败')
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
      fetchMenuOptions()
      if (props.formType === 'add') {
        resetForm()
      }
    }
  }
)
</script>

<style lang="scss" scoped>
.menu-form {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
