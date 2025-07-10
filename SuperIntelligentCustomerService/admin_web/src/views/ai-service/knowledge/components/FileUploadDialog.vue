<template>
  <n-modal
    :show="visible"
    @update:show="$emit('update:visible', $event)"
    title="批量上传文件"
    preset="dialog"
    style="width: 600px"
    :mask-closable="false"
    @close="handleClose"
  >
    <div class="upload-container">
      <!-- 上传区域 -->
      <n-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-before-upload="beforeUpload"
        :on-finish="handleUploadSuccess"
        :on-error="handleUploadError"
        :on-progress="handleUploadProgress"
        :show-file-list="false"
        multiple
        directory-dnd
      >
        <n-upload-dragger>
          <div style="margin-bottom: 12px">
            <n-icon size="48" :depth="3" :component="renderIcon('material-symbols:cloud-upload')" />
          </div>
          <n-text style="font-size: 16px">
            点击或者拖动文件到该区域来上传
          </n-text>
          <n-p depth="3" style="margin: 8px 0 0 0">
            支持单个或批量上传，严禁上传公司数据或其他敏感信息
          </n-p>
        </n-upload-dragger>
      </n-upload>

      <!-- 文件类型说明 -->
      <div class="file-types">
        <n-text depth="3">支持的文件类型：</n-text>
        <n-space>
          <n-tag v-for="type in allowedTypes" :key="type.value" size="small" type="info">
            {{ type.label }}
          </n-tag>
        </n-space>
      </div>

      <!-- 上传列表 -->
      <div v-if="uploadList.length > 0" class="upload-list">
        <n-divider>上传进度</n-divider>
        <div v-for="(item, index) in uploadList" :key="index" class="upload-item">
          <div class="upload-info">
            <div class="file-info">
              <n-icon class="file-icon" :component="renderIcon('material-symbols:description')" />
              <div class="file-details">
                <div class="file-name">{{ item.name }}</div>
                <div class="file-size">{{ formatFileSize(item.size) }}</div>
              </div>
            </div>
            <div class="upload-status">
              <n-tag :type="getStatusType(item.status)" size="small">
                {{ getStatusText(item.status) }}
              </n-tag>
              <n-button
                v-if="item.status === 'error'"
                size="tiny"
                type="primary"
                @click="retryUpload(item)"
              >
                重试
              </n-button>
            </div>
          </div>
          <n-progress
            v-if="item.status === 'uploading'"
            :percentage="item.progress"
            :height="6"
            style="margin-top: 8px"
          />
        </div>
      </div>
    </div>

    <template #action>
      <n-space>
        <n-button @click="handleClose">关闭</n-button>
        <n-button
          v-if="hasCompletedUploads"
          type="primary"
          @click="handleConfirm"
        >
          确定
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  NModal,
  NUpload,
  NUploadDragger,
  NIcon,
  NText,
  NP,
  NSpace,
  NTag,
  NButton,
  NDivider,
  NProgress,
  useMessage
} from 'naive-ui'
import { renderIcon } from '@/utils'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  kbId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:visible', 'success'])

const message = useMessage()
const uploadRef = ref()
const uploadList = ref([])

// 计算属性
const uploadUrl = computed(() => `/api/v1/knowledge/${props.kbId}/files`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

const hasCompletedUploads = computed(() => {
  return uploadList.value.some(item => item.status === 'success')
})

// 允许的文件类型
const allowedTypes = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word', value: 'docx' },
  { label: '文本', value: 'txt' },
  { label: 'Markdown', value: 'md' },
  { label: '图片', value: 'jpg,png' },
  { label: 'Excel', value: 'xlsx' },
  { label: 'PPT', value: 'pptx' }
]

// 监听visible变化，重置上传列表
watch(() => props.visible, (newVal) => {
  if (newVal) {
    uploadList.value = []
  }
})

// 上传前检查
const beforeUpload = (file) => {
  // 检查文件大小（50MB）
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    message.error(`文件 ${file.name} 大小超过50MB限制`)
    return false
  }

  // 检查文件类型
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowedExts = ['pdf', 'docx', 'doc', 'txt', 'md', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'pptx', 'ppt']
  if (!allowedExts.includes(ext)) {
    message.error(`不支持的文件类型: ${ext}`)
    return false
  }

  // 添加到上传列表
  uploadList.value.push({
    name: file.name,
    size: file.size,
    status: 'uploading',
    progress: 0,
    file: file
  })

  return true
}

// 上传进度
const handleUploadProgress = (event) => {
  const fileName = event.file?.name
  const item = uploadList.value.find(item => item.name === fileName)
  if (item) {
    item.progress = Math.round(event.percent || 0)
  }
}

// 上传成功
const handleUploadSuccess = (response, file) => {
  const item = uploadList.value.find(item => item.name === file.name)
  if (item) {
    if (response.code === 200) {
      item.status = 'success'
      item.progress = 100
      message.success(`文件 ${file.name} 上传成功`)
    } else {
      item.status = 'error'
      item.error = response.msg || '上传失败'
      message.error(`文件 ${file.name} 上传失败: ${item.error}`)
    }
  }
}

// 上传失败
const handleUploadError = (error, file) => {
  const item = uploadList.value.find(item => item.name === file.name)
  if (item) {
    item.status = 'error'
    item.error = error.message || '上传失败'
    message.error(`文件 ${file.name} 上传失败`)
  }
}

// 重试上传
const retryUpload = (item) => {
  item.status = 'uploading'
  item.progress = 0
  // 这里可以实现重试逻辑
  message.info('重试功能开发中...')
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    uploading: 'info',
    success: 'success',
    error: 'error'
  }
  return typeMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    uploading: '上传中',
    success: '成功',
    error: '失败'
  }
  return textMap[status] || status
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 关闭对话框
const handleClose = () => {
  emit('update:visible', false)
}

// 确认
const handleConfirm = () => {
  emit('success')
  handleClose()
}
</script>

<style scoped>
.upload-container {
  padding: 16px 0;
}

.file-types {
  margin: 16px 0;
  padding: 12px;
  background-color: var(--n-color-target);
  border-radius: 6px;
}

.upload-list {
  margin-top: 16px;
}

.upload-item {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
}

.upload-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.file-icon {
  margin-right: 8px;
  color: var(--n-text-color-disabled);
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.file-size {
  font-size: 12px;
  color: var(--n-text-color-disabled);
}

.upload-status {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
