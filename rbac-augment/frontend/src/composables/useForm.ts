// 企业级表单管理组合式函数

import { ref, reactive, computed, nextTick } from 'vue'
import type { Ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { loadingManager } from '@/utils/performance'
import { errorHandler } from '@/utils/errorHandler'

/**
 * 表单配置接口
 */
export interface FormConfig {
  rules?: FormRules
  autoValidate?: boolean
  realTimeValidate?: boolean
  validateDelay?: number
  resetOnSubmit?: boolean
  showSuccessMessage?: boolean
  successMessage?: string
}

/**
 * 表单状态接口
 */
export interface FormState {
  loading: boolean
  submitting: boolean
  validating: boolean
  errors: Record<string, string[]>
  touched: Record<string, boolean>
  dirty: boolean
}

/**
 * 表单操作接口
 */
export interface FormActions<T = any> {
  validate: () => Promise<boolean>
  validateField: (field: string) => Promise<boolean>
  clearValidate: (fields?: string | string[]) => void
  reset: () => void
  submit: (submitFn: (data: T) => Promise<any>) => Promise<void>
  setFieldValue: (field: string, value: any) => void
  setFieldError: (field: string, error: string) => void
  clearFieldError: (field: string) => void
  markFieldTouched: (field: string) => void
  markFormDirty: () => void
}

/**
 * 表单返回值接口
 */
export interface FormReturn<T = any> {
  formRef: Ref<FormInstance | undefined>
  formData: T
  formState: FormState
  formActions: FormActions<T>
  isValid: Ref<boolean>
  hasErrors: Ref<boolean>
  isDirty: Ref<boolean>
  isTouched: Ref<boolean>
}

/**
 * 企业级表单管理组合式函数
 */
export function useForm<T extends Record<string, any>>(
  initialData: T,
  config: FormConfig = {}
): FormReturn<T> {
  // 表单引用
  const formRef = ref<FormInstance>()
  
  // 表单数据
  const formData = reactive<T>({ ...initialData })
  
  // 表单状态
  const formState = reactive<FormState>({
    loading: false,
    submitting: false,
    validating: false,
    errors: {},
    touched: {},
    dirty: false
  })
  
  // 防抖定时器
  let validateTimer: NodeJS.Timeout | null = null
  
  // 计算属性
  const isValid = computed(() => Object.keys(formState.errors).length === 0)
  const hasErrors = computed(() => Object.keys(formState.errors).length > 0)
  const isDirty = computed(() => formState.dirty)
  const isTouched = computed(() => Object.keys(formState.touched).length > 0)
  
  /**
   * 验证整个表单
   */
  const validate = async (): Promise<boolean> => {
    if (!formRef.value) return false
    
    formState.validating = true
    
    try {
      await formRef.value.validate()
      formState.errors = {}
      return true
    } catch (error: any) {
      // 处理验证错误
      if (error.fields) {
        const errors: Record<string, string[]> = {}
        Object.keys(error.fields).forEach(field => {
          errors[field] = error.fields[field].map((err: any) => err.message)
        })
        formState.errors = errors
      }
      return false
    } finally {
      formState.validating = false
    }
  }
  
  /**
   * 验证指定字段
   */
  const validateField = async (field: string): Promise<boolean> => {
    if (!formRef.value) return false
    
    try {
      await formRef.value.validateField(field)
      delete formState.errors[field]
      return true
    } catch (error: any) {
      formState.errors[field] = [error.message]
      return false
    }
  }
  
  /**
   * 清除验证
   */
  const clearValidate = (fields?: string | string[]): void => {
    if (formRef.value) {
      formRef.value.clearValidate(fields)
    }
    
    if (fields) {
      const fieldsArray = Array.isArray(fields) ? fields : [fields]
      fieldsArray.forEach(field => {
        delete formState.errors[field]
      })
    } else {
      formState.errors = {}
    }
  }
  
  /**
   * 重置表单
   */
  const reset = (): void => {
    if (formRef.value) {
      formRef.value.resetFields()
    }
    
    // 重置表单数据
    Object.assign(formData, initialData)
    
    // 重置表单状态
    formState.errors = {}
    formState.touched = {}
    formState.dirty = false
  }
  
  /**
   * 提交表单
   */
  const submit = async (submitFn: (data: T) => Promise<any>): Promise<void> => {
    try {
      // 验证表单
      const isValid = await validate()
      if (!isValid) {
        ElMessage.warning('请检查表单填写是否正确')
        return
      }
      
      // 使用加载管理器包装提交操作
      await loadingManager.wrap(async () => {
        formState.submitting = true
        await submitFn(formData)
        
        if (config.showSuccessMessage !== false) {
          ElMessage.success(config.successMessage || '操作成功')
        }
        
        if (config.resetOnSubmit) {
          reset()
        }
      }, 'form-submit')
      
    } catch (error) {
      errorHandler.handleError(error as Error)
    } finally {
      formState.submitting = false
    }
  }
  
  /**
   * 设置字段值
   */
  const setFieldValue = (field: string, value: any): void => {
    ;(formData as any)[field] = value
    markFieldTouched(field)
    markFormDirty()
    
    // 实时验证
    if (config.realTimeValidate) {
      if (validateTimer) {
        clearTimeout(validateTimer)
      }
      
      validateTimer = setTimeout(() => {
        validateField(field)
      }, config.validateDelay || 300)
    }
  }
  
  /**
   * 设置字段错误
   */
  const setFieldError = (field: string, error: string): void => {
    formState.errors[field] = [error]
  }
  
  /**
   * 清除字段错误
   */
  const clearFieldError = (field: string): void => {
    delete formState.errors[field]
  }
  
  /**
   * 标记字段已触摸
   */
  const markFieldTouched = (field: string): void => {
    formState.touched[field] = true
  }
  
  /**
   * 标记表单已修改
   */
  const markFormDirty = (): void => {
    formState.dirty = true
  }
  
  // 表单操作对象
  const formActions: FormActions<T> = {
    validate,
    validateField,
    clearValidate,
    reset,
    submit,
    setFieldValue,
    setFieldError,
    clearFieldError,
    markFieldTouched,
    markFormDirty
  }
  
  return {
    formRef,
    formData,
    formState,
    formActions,
    isValid,
    hasErrors,
    isDirty,
    isTouched
  }
}

/**
 * 表单字段组合式函数
 */
export function useFormField<T>(
  formData: T,
  fieldName: keyof T,
  formActions: FormActions<T>
) {
  const value = computed({
    get: () => (formData as any)[fieldName],
    set: (newValue) => formActions.setFieldValue(fieldName as string, newValue)
  })
  
  const error = computed(() => {
    const errors = (formActions as any).formState?.errors?.[fieldName as string]
    return errors?.[0] || ''
  })
  
  const hasError = computed(() => !!error.value)
  
  const touch = () => formActions.markFieldTouched(fieldName as string)
  const clearError = () => formActions.clearFieldError(fieldName as string)
  
  return {
    value,
    error,
    hasError,
    touch,
    clearError
  }
}

/**
 * 表单验证组合式函数
 */
export function useFormValidation(formRef: Ref<FormInstance | undefined>) {
  const validationState = ref<Record<string, { isValid: boolean; message: string }>>({})
  
  const validateAll = async (): Promise<boolean> => {
    if (!formRef.value) return false
    
    try {
      await formRef.value.validate()
      return true
    } catch (error) {
      return false
    }
  }
  
  const validateField = async (field: string): Promise<boolean> => {
    if (!formRef.value) return false
    
    try {
      await formRef.value.validateField(field)
      validationState.value[field] = { isValid: true, message: '' }
      return true
    } catch (error: any) {
      validationState.value[field] = { isValid: false, message: error.message }
      return false
    }
  }
  
  const clearValidation = (fields?: string | string[]): void => {
    if (formRef.value) {
      formRef.value.clearValidate(fields)
    }
    
    if (fields) {
      const fieldsArray = Array.isArray(fields) ? fields : [fields]
      fieldsArray.forEach(field => {
        delete validationState.value[field]
      })
    } else {
      validationState.value = {}
    }
  }
  
  const getFieldValidation = (field: string) => {
    return validationState.value[field] || { isValid: true, message: '' }
  }
  
  return {
    validationState,
    validateAll,
    validateField,
    clearValidation,
    getFieldValidation
  }
}
