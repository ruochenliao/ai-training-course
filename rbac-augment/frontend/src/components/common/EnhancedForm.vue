<template>
  <el-form
    ref="formRef"
    :model="modelValue"
    :rules="computedRules"
    :label-width="labelWidth"
    :label-position="labelPosition"
    :size="size"
    :disabled="disabled"
    :validate-on-rule-change="validateOnRuleChange"
    :status-icon="statusIcon"
    class="enhanced-form"
    @validate="handleValidate"
    @submit.prevent="handleSubmit"
  >
    <slot :form-data="modelValue" :validate="validate" :reset="reset" />
    
    <!-- 表单操作按钮 -->
    <div v-if="showActions" class="form-actions">
      <el-button
        v-if="showReset"
        :size="size"
        @click="handleReset"
      >
        {{ resetText }}
      </el-button>
      <el-button
        v-if="showSubmit"
        type="primary"
        :size="size"
        :loading="loading"
        @click="handleSubmit"
      >
        {{ submitText }}
      </el-button>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { FormInstance, FormRules, FormValidateCallback } from 'element-plus'
import { ElMessage } from 'element-plus'
import { commonRules } from '@/utils/validation'

// 组件属性
interface Props {
  modelValue: Record<string, any>
  rules?: FormRules
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  validateOnRuleChange?: boolean
  statusIcon?: boolean
  loading?: boolean
  showActions?: boolean
  showSubmit?: boolean
  showReset?: boolean
  submitText?: string
  resetText?: string
  autoValidate?: boolean
  realTimeValidate?: boolean
  validateDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  labelWidth: '120px',
  labelPosition: 'right',
  size: 'default',
  disabled: false,
  validateOnRuleChange: true,
  statusIcon: true,
  loading: false,
  showActions: true,
  showSubmit: true,
  showReset: true,
  submitText: '提交',
  resetText: '重置',
  autoValidate: false,
  realTimeValidate: false,
  validateDelay: 300
})

// 组件事件
interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'submit', value: Record<string, any>): void
  (e: 'reset'): void
  (e: 'validate', prop: string, isValid: boolean, message: string): void
  (e: 'field-change', field: string, value: any): void
}

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 验证状态
const validationState = ref<Record<string, { isValid: boolean; message: string }>>({})

// 计算属性：合并验证规则
const computedRules = computed(() => {
  const mergedRules: FormRules = {}
  
  // 合并传入的规则和通用规则
  if (props.rules) {
    Object.keys(props.rules).forEach(field => {
      mergedRules[field] = props.rules![field]
    })
  }
  
  return mergedRules
})

// 实时验证防抖定时器
let validateTimer: NodeJS.Timeout | null = null

// 监听表单数据变化
watch(
  () => props.modelValue,
  (newValue, oldValue) => {
    if (props.realTimeValidate && formRef.value) {
      // 找出变化的字段
      const changedFields = Object.keys(newValue).filter(
        key => newValue[key] !== oldValue?.[key]
      )
      
      changedFields.forEach(field => {
        emit('field-change', field, newValue[field])
        
        // 防抖验证
        if (validateTimer) {
          clearTimeout(validateTimer)
        }
        
        validateTimer = setTimeout(() => {
          validateField(field)
        }, props.validateDelay)
      })
    }
  },
  { deep: true }
)

/**
 * 验证整个表单
 */
const validate = async (): Promise<boolean> => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    console.error('Form validation failed:', error)
    return false
  }
}

/**
 * 验证指定字段
 */
const validateField = async (prop: string): Promise<boolean> => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validateField(prop)
    return true
  } catch (error) {
    console.error(`Field validation failed for ${prop}:`, error)
    return false
  }
}

/**
 * 清除验证
 */
const clearValidate = (props?: string | string[]): void => {
  if (formRef.value) {
    formRef.value.clearValidate(props)
  }
}

/**
 * 重置表单
 */
const reset = (): void => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  validationState.value = {}
  emit('reset')
}

/**
 * 处理表单验证事件
 */
const handleValidate = (prop: string, isValid: boolean, message: string): void => {
  validationState.value[prop] = { isValid, message }
  emit('validate', prop, isValid, message)
}

/**
 * 处理表单提交
 */
const handleSubmit = async (): void => {
  const isValid = await validate()
  
  if (isValid) {
    emit('submit', props.modelValue)
  } else {
    ElMessage.warning('请检查表单填写是否正确')
  }
}

/**
 * 处理表单重置
 */
const handleReset = (): void => {
  reset()
}

/**
 * 获取验证状态
 */
const getValidationState = (field?: string) => {
  if (field) {
    return validationState.value[field]
  }
  return validationState.value
}

/**
 * 设置字段值
 */
const setFieldValue = (field: string, value: any): void => {
  const newValue = { ...props.modelValue, [field]: value }
  emit('update:modelValue', newValue)
}

/**
 * 获取字段值
 */
const getFieldValue = (field: string): any => {
  return props.modelValue[field]
}

// 暴露方法给父组件
defineExpose({
  validate,
  validateField,
  clearValidate,
  reset,
  getValidationState,
  setFieldValue,
  getFieldValue,
  formRef
})
</script>

<style lang="scss" scoped>
.enhanced-form {
  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-light);
  }
  
  // 实时验证样式
  :deep(.el-form-item) {
    transition: all 0.3s ease;
    
    &.is-error {
      .el-form-item__label {
        color: var(--el-color-danger);
      }
    }
    
    &.is-success {
      .el-form-item__label {
        color: var(--el-color-success);
      }
    }
  }
  
  // 加载状态样式
  &.is-loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

// 暗色主题适配
.dark .enhanced-form {
  .form-actions {
    border-top-color: var(--el-border-color);
  }
}
</style>
