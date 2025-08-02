<template>
  <div class="error-boundary">
    <div v-if="hasError" class="error-content">
      <el-result
        icon="error"
        title="出现了一些问题"
        :sub-title="errorMessage"
      >
        <template #extra>
          <el-button type="primary" @click="retry">重试</el-button>
          <el-button @click="goHome">返回首页</el-button>
        </template>
      </el-result>
    </div>
    <slot v-else />
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const hasError = ref(false)
const errorMessage = ref('')

const emit = defineEmits<{
  retry: []
}>()

onErrorCaptured((error: Error) => {
  console.error('Error caught by ErrorBoundary:', error)
  hasError.value = true
  errorMessage.value = error.message || '未知错误'
  ElMessage.error('页面出现错误，请重试')
  return false
})

const retry = () => {
  hasError.value = false
  errorMessage.value = ''
  emit('retry')
}

const goHome = () => {
  router.push('/')
}
</script>

<style lang="scss" scoped>
.error-boundary {
  width: 100%;
  height: 100%;
  
  .error-content {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    padding: 40px;
  }
}
</style>
