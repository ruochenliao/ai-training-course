<template>
  <div class="test-api-page">
    <h1>API 接口测试页面</h1>
    
    <div class="test-section">
      <h2>会话管理测试</h2>
      
      <div class="test-item">
        <h3>1. 获取会话列表</h3>
        <button @click="testGetSessionList" :disabled="loading">
          {{ loading ? '加载中...' : '获取会话列表' }}
        </button>
        <div v-if="sessionListResult" class="result">
          <pre>{{ JSON.stringify(sessionListResult, null, 2) }}</pre>
        </div>
      </div>

      <div class="test-item">
        <h3>2. 创建新会话</h3>
        <input v-model="newSessionTitle" placeholder="会话标题" />
        <input v-model="newSessionContent" placeholder="会话内容" />
        <button @click="testCreateSession" :disabled="loading">
          {{ loading ? '创建中...' : '创建会话' }}
        </button>
        <div v-if="createSessionResult" class="result">
          <pre>{{ JSON.stringify(createSessionResult, null, 2) }}</pre>
        </div>
      </div>

      <div class="test-item">
        <h3>3. 获取单个会话</h3>
        <input v-model="sessionIdToGet" placeholder="会话ID" />
        <button @click="testGetSession" :disabled="loading">
          {{ loading ? '获取中...' : '获取会话' }}
        </button>
        <div v-if="getSessionResult" class="result">
          <pre>{{ JSON.stringify(getSessionResult, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>聊天功能测试</h2>
      
      <div class="test-item">
        <h3>4. 上传图片</h3>
        <input type="file" @change="handleFileSelect" accept="image/*" />
        <input v-model="uploadSessionId" placeholder="会话ID（可选）" />
        <button @click="testUploadImage" :disabled="loading || !selectedFile">
          {{ loading ? '上传中...' : '上传图片' }}
        </button>
        <div v-if="uploadResult" class="result">
          <pre>{{ JSON.stringify(uploadResult, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <div v-if="error" class="error">
      <h3>错误信息：</h3>
      <pre>{{ error }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { get_session_list, create_session, get_session } from '@/api/session'
import { uploadImage } from '@/api/chat'

// 响应式数据
const loading = ref(false)
const error = ref('')

// 会话相关
const sessionListResult = ref(null)
const createSessionResult = ref(null)
const getSessionResult = ref(null)
const newSessionTitle = ref('测试会话')
const newSessionContent = ref('这是一个测试会话')
const sessionIdToGet = ref('')

// 文件上传相关
const selectedFile = ref<File | null>(null)
const uploadSessionId = ref('')
const uploadResult = ref(null)

// 测试函数
const testGetSessionList = async () => {
  loading.value = true
  error.value = ''
  try {
    const result = await get_session_list({
      page: 1,
      page_size: 10
    })
    sessionListResult.value = result
    console.log('获取会话列表结果:', result)
  } catch (err: any) {
    error.value = `获取会话列表失败: ${err.message}`
    console.error('获取会话列表失败:', err)
  } finally {
    loading.value = false
  }
}

const testCreateSession = async () => {
  if (!newSessionTitle.value) {
    error.value = '请输入会话标题'
    return
  }
  
  loading.value = true
  error.value = ''
  try {
    const result = await create_session({
      session_title: newSessionTitle.value,
      session_content: newSessionContent.value,
      remark: '测试备注'
    })
    createSessionResult.value = result
    console.log('创建会话结果:', result)
  } catch (err: any) {
    error.value = `创建会话失败: ${err.message}`
    console.error('创建会话失败:', err)
  } finally {
    loading.value = false
  }
}

const testGetSession = async () => {
  if (!sessionIdToGet.value) {
    error.value = '请输入会话ID'
    return
  }
  
  loading.value = true
  error.value = ''
  try {
    const result = await get_session(sessionIdToGet.value)
    getSessionResult.value = result
    console.log('获取会话结果:', result)
  } catch (err: any) {
    error.value = `获取会话失败: ${err.message}`
    console.error('获取会话失败:', err)
  } finally {
    loading.value = false
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

const testUploadImage = async () => {
  if (!selectedFile.value) {
    error.value = '请选择图片文件'
    return
  }
  
  loading.value = true
  error.value = ''
  try {
    const result = await uploadImage(selectedFile.value, uploadSessionId.value || undefined)
    uploadResult.value = result
    console.log('上传图片结果:', result)
  } catch (err: any) {
    error.value = `上传图片失败: ${err.message}`
    console.error('上传图片失败:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.test-api-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-section {
  margin-bottom: 40px;
  border: 1px solid #ddd;
  padding: 20px;
  border-radius: 8px;
}

.test-item {
  margin-bottom: 30px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 5px;
}

.test-item h3 {
  margin-top: 0;
  color: #333;
}

.test-item input {
  margin: 5px 10px 5px 0;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 200px;
}

.test-item button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin: 5px;
}

.test-item button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.test-item button:hover:not(:disabled) {
  background: #0056b3;
}

.result {
  margin-top: 15px;
  padding: 10px;
  background: #e8f5e8;
  border: 1px solid #4caf50;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background: #ffe8e8;
  border: 1px solid #f44336;
  border-radius: 4px;
}

.error h3 {
  margin-top: 0;
  color: #d32f2f;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 12px;
  line-height: 1.4;
}
</style>
