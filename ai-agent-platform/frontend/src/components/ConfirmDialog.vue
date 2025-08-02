<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="confirm-content">
      <el-icon v-if="type === 'warning'" class="warning-icon" :size="48">
        <WarningFilled />
      </el-icon>
      <el-icon v-else-if="type === 'error'" class="error-icon" :size="48">
        <CircleCloseFilled />
      </el-icon>
      <el-icon v-else-if="type === 'info'" class="info-icon" :size="48">
        <InfoFilled />
      </el-icon>
      <el-icon v-else class="success-icon" :size="48">
        <CircleCheckFilled />
      </el-icon>
      
      <div class="message">
        <p>{{ message }}</p>
        <p v-if="subMessage" class="sub-message">{{ subMessage }}</p>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel" :disabled="loading">
          {{ cancelText }}
        </el-button>
        <el-button
          :type="confirmButtonType"
          @click="handleConfirm"
          :loading="loading"
        >
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  WarningFilled,
  CircleCloseFilled,
  InfoFilled,
  CircleCheckFilled
} from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
  title?: string
  message: string
  subMessage?: string
  type?: 'warning' | 'error' | 'info' | 'success'
  confirmText?: string
  cancelText?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认操作',
  type: 'warning',
  confirmText: '确定',
  cancelText: '取消',
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const confirmButtonType = computed(() => {
  switch (props.type) {
    case 'error':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'success':
      return 'success'
    default:
      return 'primary'
  }
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  visible.value = false
  emit('cancel')
}
</script>

<style lang="scss" scoped>
.confirm-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 0;
  
  .warning-icon {
    color: #e6a23c;
  }
  
  .error-icon {
    color: #f56c6c;
  }
  
  .info-icon {
    color: #409eff;
  }
  
  .success-icon {
    color: #67c23a;
  }
  
  .message {
    flex: 1;
    
    p {
      margin: 0 0 8px 0;
      font-size: 16px;
      line-height: 1.5;
      color: #303133;
    }
    
    .sub-message {
      font-size: 14px;
      color: #606266;
      margin: 0;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
