<template>
  <div class="knowledge-create">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/knowledge' }">知识库管理</el-breadcrumb-item>
        <el-breadcrumb-item>创建知识库</el-breadcrumb-item>
      </el-breadcrumb>
      <h2>创建知识库</h2>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="知识库名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入知识库名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="知识库描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入知识库描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="访问权限">
          <el-radio-group v-model="form.type">
            <el-radio label="private">私有（仅自己可见）</el-radio>
            <el-radio label="public">公开（所有人可见）</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="文件上传">
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              class="upload-demo"
              drag
              multiple
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 txt、md、pdf、doc、docx、ppt、pptx、xls、xlsx 格式文件，单个文件不超过 10MB
                </div>
              </template>
            </el-upload>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            创建知识库
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile, UploadFiles } from 'element-plus'
import { knowledgeApi } from '@/api/knowledge'

const router = useRouter()
const formRef = ref<FormInstance>()
const uploadRef = ref()
const loading = ref(false)
const fileList = ref<UploadFile[]>([])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  type: 'private'
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ]
}

// 文件变化处理
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  // 检查文件大小
  if (file.raw && file.raw.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    files.splice(files.indexOf(file), 1)
    return
  }
  
  // 检查文件类型
  const allowedTypes = [
    'text/plain',
    'text/markdown',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]
  
  if (file.raw && !allowedTypes.includes(file.raw.type)) {
    ElMessage.error('不支持的文件类型')
    files.splice(files.indexOf(file), 1)
    return
  }
  
  fileList.value = files
}

// 文件移除处理
const handleFileRemove = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 创建知识库
    const response = await knowledgeApi.createKnowledge({
      name: form.name,
      description: form.description,
      type: form.type
    })
    
    const knowledgeId = response.data.id
    
    // 如果有文件，上传文件
    if (fileList.value.length > 0) {
      const files = fileList.value.map(file => file.raw!).filter(Boolean)
      await knowledgeApi.uploadFiles(knowledgeId, files)
    }
    
    ElMessage.success('知识库创建成功')
    router.push('/knowledge')
  } catch (error) {
    console.error('创建知识库失败:', error)
    ElMessage.error('创建知识库失败')
  } finally {
    loading.value = false
  }
}

// 取消操作
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消创建吗？未保存的数据将丢失。', '确认取消', {
      type: 'warning'
    })
    router.push('/knowledge')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.knowledge-create {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  h2 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 16px 0 0 0;
  }
}

.el-form {
  max-width: 600px;
}

.upload-section {
  .upload-demo {
    width: 100%;
  }
  
  .el-upload-dragger {
    width: 100%;
  }
}
</style>
