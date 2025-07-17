<template>
  <div class="file-upload-component">
    <NUpload
      ref="uploadRef"
      :custom-request="customRequest"
      :default-upload="false"
      :max="maxFiles"
      :multiple="multiple"
      :max-size="50 * 1024 * 1024"
      :accept="'.txt,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.zip,.rar,.7z'"
      @change="handleUploadChange"
      @exceed-size="handleExceedSize"
    >
      <NUploadDragger>
        <div class="flex flex-col justify-center items-center">
          <TheIcon icon="material-symbols:upload" :size="48" />
          <p>点击或拖动文件到此区域上传</p>
          <p class="text-xs text-gray-500">{{ hint || '支持单个或批量上传' }}</p>
          <p class="text-xs text-gray-500 mt-2">支持的文件类型：txt, pdf, doc, docx, xls, xlsx, ppt, pptx, 图片和压缩文件</p>
          <p class="text-xs text-gray-500">单文件大小限制：50MB</p>
        </div>
      </NUploadDragger>
    </NUpload>

    <div class="mt-4 flex justify-end">
      <NButton @click="$emit('cancel')">取消</NButton>
      <NButton
        :loading="uploading"
        :disabled="!fileList.length"
        ml-20
        type="primary"
        @click="submitUpload"
      >
        上传
      </NButton>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { NButton, NUpload, NUploadDragger, useMessage } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

const props = defineProps({
  maxFiles: {
    type: Number,
    default: 5,
  },
  multiple: {
    type: Boolean,
    default: true,
  },
  hint: {
    type: String,
    default: '',
  },
  uploadUrl: {
    type: String,
    required: true,
  },
  formData: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['cancel', 'success', 'error'])
const message = useMessage()

const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)

// 自定义上传请求（不实际上传，只是为了获取文件列表）
function customRequest({ file, onFinish }) {
  onFinish()
}

// 上传文件变化
function handleUploadChange(options) {
  fileList.value = options.fileList
}

// 处理文件大小超出限制
function handleExceedSize({ file }) {
  message.error(`文件 ${file.name} 超出大小限制（50MB）`)
}

// 提交上传
async function submitUpload() {
  if (fileList.value.length === 0) return

  // 显示全局加载提示
  const loadingMessage = message.loading('正在准备上传文件...', {
    duration: 0, // 不自动关闭
  })

  uploading.value = true
  let successCount = 0
  let failCount = 0

  // 创建一个数组来存储每个文件的上传进度
  const progressMap = new Map()
  fileList.value.forEach(file => {
    progressMap.set(file.id, 0)
    file.status = 'uploading'
  })

  // 更新文件上传进度的函数
  const updateProgress = (fileId, percent) => {
    progressMap.set(fileId, percent)
    const file = fileList.value.find(f => f.id === fileId)
    if (file) {
      file.percentage = percent
    }
  }

  for (const file of fileList.value) {
    const formData = new FormData()

    // Check if file.file exists and is valid
    if (!file.file || typeof file.file === 'undefined') {
      console.error('Invalid file object:', file)
      message.error(`文件 ${file.name} 无效`)
      file.status = 'error'
      failCount++
      continue
    }

    console.log('Uploading file:', file.name, 'Type:', typeof file.file, 'Size:', file.file.size)
    formData.append('file', file.file)

    // 添加额外的表单数据
    for (const [key, value] of Object.entries(props.formData)) {
      formData.append(key, value)
      console.log(`Adding form data: ${key}=${value}`)
    }

    try {
      // 使用 XMLHttpRequest 来跟踪上传进度
      const xhr = new XMLHttpRequest()

      // 设置超时时间为 5 分钟
      xhr.timeout = 5 * 60 * 1000 // 5分钟

      // 设置超时处理函数
      xhr.ontimeout = () => {
        file.status = 'error'
        failCount++
        console.error('Upload timeout for file:', file.name)
        message.error(`文件 ${file.name} 上传超时，请检查文件大小或网络连接`)
      }

      // 设置进度事件
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100)
          updateProgress(file.id, percent)
        }
      }

      // 创建 Promise 来处理异步上传
      await new Promise((resolve, reject) => {
        xhr.open('POST', props.uploadUrl, true)
        xhr.setRequestHeader('Authorization', localStorage.getItem('token') || 'dev')

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              // 尝试解析响应数据
              const response = JSON.parse(xhr.responseText)
              if (response.code === 200) {
                file.status = 'finished'
                updateProgress(file.id, 100)
                successCount++
                resolve(response)
              } else {
                file.status = 'error'
                failCount++
                console.error('Server error:', response.msg || 'Unknown error')
                reject(new Error(response.msg || 'Server error'))
              }
            } catch (e) {
              // JSON 解析错误
              file.status = 'finished' // 假设成功，因为 HTTP 状态码是成功的
              updateProgress(file.id, 100)
              successCount++
              resolve(xhr.responseText)
            }
          } else {
            file.status = 'error'
            failCount++
            console.error('Failed to upload file:', xhr.statusText, xhr.responseText)
            let errorMsg = xhr.statusText
            try {
              const response = JSON.parse(xhr.responseText)
              errorMsg = response.msg || errorMsg
            } catch (e) {}
            reject(new Error(errorMsg))
          }
        }

        xhr.onerror = () => {
          file.status = 'error'
          failCount++
          console.error('Network error during file upload:', file.name)
          reject(new Error('网络错误，请检查您的网络连接'))
        }

        // 添加上传开始时的日志
        console.log(`Starting upload for file: ${file.name}, size: ${file.file.size} bytes`)

        // 发送请求
        xhr.send(formData)
      })
    } catch (error) {
      console.error('Failed to upload file:', error)
      file.status = 'error'
      failCount++

      // 显示更友好的错误信息
      let errorMessage = error.message || '未知错误'

      // 处理超时错误
      if (errorMessage.includes('timeout')) {
        errorMessage = '上传超时，请检查文件大小或网络连接'
      }
      // 处理网络错误
      else if (errorMessage.includes('Network Error')) {
        errorMessage = '网络错误，请检查您的网络连接'
      }

      message.error(`文件 ${file.name} 上传失败: ${errorMessage}`)
    }
  }

  // 关闭加载提示
  loadingMessage.destroy()
  uploading.value = false

  if (successCount > 0) {
    message.success(`成功上传 ${successCount} 个文件`)
    // 无论后端处理状态如何，都立即触发成功事件
    emit('success', successCount)
    // 清空文件列表
    clearFiles()
  }

  if (failCount > 0) {
    message.error(`${failCount} 个文件上传失败`)
    emit('error', failCount)
  }
}

// 清空文件列表
function clearFiles() {
  fileList.value = []
  if (uploadRef.value) {
    uploadRef.value.clear()
  }
}

// 暴露方法给父组件
defineExpose({
  clearFiles,
  submitUpload,
})
</script>
