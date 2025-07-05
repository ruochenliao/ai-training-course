<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :width="width"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :before-close="handleClose"
    :destroy-on-close="true"
    class="form-dialog"
    :class="dialogClass"
  >
    <!-- 对话框头部 -->
    <template #header="{ titleId, titleClass }">
      <div class="dialog-header">
        <div class="header-title">
          <el-icon v-if="icon" class="title-icon">
            <component :is="icon" />
          </el-icon>
          <span :id="titleId" :class="titleClass" class="title-text">
            {{ dialogTitle }}
          </span>
          <el-tag v-if="badge" :type="badgeType" size="small" class="title-badge">
            {{ badge }}
          </el-tag>
        </div>
        <div v-if="showSteps" class="header-steps">
          <el-steps :active="currentStep" :space="120" finish-status="success">
            <el-step
              v-for="(step, index) in steps"
              :key="index"
              :title="step.title"
              :description="step.description"
            />
          </el-steps>
        </div>
      </div>
    </template>

    <!-- 对话框内容 -->
    <div class="dialog-content" v-loading="loading">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-width="labelWidth"
        :label-position="labelPosition"
        :size="formSize"
        :disabled="readonly"
        class="enterprise-form"
        @submit.prevent
      >
        <template v-if="showSteps">
          <!-- 步骤式表单 -->
          <div class="step-content">
            <slot :name="`step-${currentStep}`" :form-data="formData" />
          </div>
        </template>
        <template v-else>
          <!-- 普通表单 -->
          <slot :form-data="formData" />
        </template>
      </el-form>
    </div>

    <!-- 对话框底部 -->
    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <slot name="footer-left" />
        </div>
        <div class="footer-right">
          <template v-if="showSteps">
            <!-- 步骤式按钮 -->
            <el-button
              v-if="currentStep > 0"
              @click="handlePrevStep"
              :disabled="loading"
            >
              上一步
            </el-button>
            <el-button
              v-if="currentStep < steps.length - 1"
              type="primary"
              @click="handleNextStep"
              :loading="loading"
            >
              下一步
            </el-button>
            <el-button
              v-if="currentStep === steps.length - 1"
              type="primary"
              @click="handleSubmit"
              :loading="loading"
            >
              {{ submitText }}
            </el-button>
          </template>
          <template v-else>
            <!-- 普通按钮 -->
            <el-button @click="handleCancel" :disabled="loading">
              {{ cancelText }}
            </el-button>
            <el-button
              type="primary"
              @click="handleSubmit"
              :loading="loading"
            >
              {{ submitText }}
            </el-button>
          </template>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

interface Step {
  title: string
  description?: string
}

interface Props {
  visible: boolean
  title: string
  width?: string | number
  icon?: string
  badge?: string
  badgeType?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  formData: Record<string, any>
  formRules?: FormRules
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  formSize?: 'large' | 'default' | 'small'
  loading?: boolean
  readonly?: boolean
  submitText?: string
  cancelText?: string
  showSteps?: boolean
  steps?: Step[]
  validateOnStepChange?: boolean
  dialogClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '600px',
  badgeType: 'primary',
  labelWidth: '100px',
  labelPosition: 'right',
  formSize: 'default',
  loading: false,
  readonly: false,
  submitText: '确定',
  cancelText: '取消',
  showSteps: false,
  steps: () => [],
  validateOnStepChange: true,
  dialogClass: ''
})

const emit = defineEmits([
  'update:visible',
  'submit',
  'cancel',
  'close',
  'step-change'
])

// 响应式数据
const formRef = ref<FormInstance>()
const currentStep = ref(0)

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

const dialogTitle = computed(() => {
  if (props.showSteps && props.steps.length > 0) {
    return `${props.title} - ${props.steps[currentStep.value]?.title || ''}`
  }
  return props.title
})

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible) {
    currentStep.value = 0
  }
})

// 方法定义
const handleClose = (done: () => void) => {
  if (props.loading) {
    ElMessage.warning('操作进行中，请稍候...')
    return
  }
  
  emit('close')
  done()
}

const handleCancel = () => {
  if (props.loading) {
    ElMessage.warning('操作进行中，请稍候...')
    return
  }
  
  emit('cancel')
  dialogVisible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    emit('submit', props.formData)
  } catch (error) {
    console.error('Form validation failed:', error)
  }
}

const handlePrevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    emit('step-change', currentStep.value)
  }
}

const handleNextStep = async () => {
  if (props.validateOnStepChange && formRef.value) {
    try {
      await formRef.value.validate()
    } catch (error) {
      console.error('Step validation failed:', error)
      return
    }
  }
  
  if (currentStep.value < props.steps.length - 1) {
    currentStep.value++
    emit('step-change', currentStep.value)
  }
}

// 暴露方法
defineExpose({
  formRef,
  validate: () => formRef.value?.validate(),
  resetFields: () => formRef.value?.resetFields(),
  clearValidate: () => formRef.value?.clearValidate(),
  validateField: (props: string | string[]) => formRef.value?.validateField(props),
  scrollToField: (prop: string) => formRef.value?.scrollToField(prop)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

:deep(.form-dialog) {
  .el-dialog__header {
    padding: 0;
    border-bottom: 1px solid $border-color-light;
  }
  
  .el-dialog__body {
    padding: 0;
  }
  
  .el-dialog__footer {
    padding: 0;
    border-top: 1px solid $border-color-light;
  }
}

// ==================== 对话框头部 ====================
.dialog-header {
  padding: $spacing-lg $spacing-xl;
  
  .header-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
    
    .title-icon {
      font-size: 20px;
      color: $primary-color;
      flex-shrink: 0;
    }
    
    .title-text {
      font-size: $font-size-lg;
      font-weight: $font-weight-semibold;
      color: $text-color-1;
      margin: 0;
    }
    
    .title-badge {
      margin-left: $spacing-sm;
    }
  }
  
  .header-steps {
    :deep(.el-steps) {
      .el-step__title {
        font-size: $font-size-sm;
        line-height: 1.4;
      }
      
      .el-step__description {
        font-size: $font-size-xs;
        color: $text-color-3;
      }
    }
  }
}

// ==================== 对话框内容 ====================
.dialog-content {
  padding: $spacing-lg $spacing-xl;
  min-height: 200px;
  
  .enterprise-form {
    :deep(.el-form-item) {
      margin-bottom: $spacing-lg;
      
      .el-form-item__label {
        color: $text-color-1;
        font-weight: $font-weight-medium;
      }
      
      .el-form-item__error {
        font-size: $font-size-xs;
        color: $error-color;
        margin-top: $spacing-xs;
      }
    }
    
    :deep(.el-input),
    :deep(.el-select),
    :deep(.el-textarea) {
      .el-input__wrapper {
        border-radius: $border-radius-base;
        transition: all $transition-duration;
        
        &:hover {
          border-color: $primary-color;
        }
        
        &.is-focus {
          border-color: $primary-color;
          box-shadow: 0 0 0 2px rgba($primary-color, 0.2);
        }
      }
    }
  }
  
  .step-content {
    min-height: 300px;
  }
}

// ==================== 对话框底部 ====================
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md $spacing-xl;
  background: $bg-color-page;
  
  .footer-left {
    flex: 1;
  }
  
  .footer-right {
    display: flex;
    gap: $spacing-sm;
  }
}

// ==================== 响应式设计 ====================
@media (max-width: $breakpoint-md) {
  :deep(.form-dialog) {
    .el-dialog {
      width: 95% !important;
      margin: 5vh auto;
    }
  }
  
  .dialog-header {
    padding: $spacing-md;
    
    .header-steps {
      :deep(.el-steps) {
        .el-step {
          .el-step__head {
            .el-step__line {
              display: none;
            }
          }
        }
      }
    }
  }
  
  .dialog-content {
    padding: $spacing-md;
  }
  
  .dialog-footer {
    padding: $spacing-sm $spacing-md;
    flex-direction: column;
    gap: $spacing-sm;
    
    .footer-left,
    .footer-right {
      width: 100%;
      justify-content: center;
    }
  }
}

// ==================== 暗色主题 ====================
.dark {
  :deep(.form-dialog) {
    .el-dialog__header {
      border-bottom-color: $dark-border-color;
    }
    
    .el-dialog__footer {
      border-top-color: $dark-border-color;
    }
  }
  
  .dialog-header {
    .header-title .title-text {
      color: $dark-text-color-1;
    }
  }
  
  .dialog-content {
    .enterprise-form {
      :deep(.el-form-item) {
        .el-form-item__label {
          color: $dark-text-color-1;
        }
      }
    }
  }
  
  .dialog-footer {
    background: $dark-bg-color-page;
  }
}
</style>
