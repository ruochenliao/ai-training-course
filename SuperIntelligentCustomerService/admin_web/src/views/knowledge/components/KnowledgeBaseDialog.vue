<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑知识库' : '创建知识库'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="知识库名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入知识库名称"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="知识库类型" prop="knowledge_type">
        <el-select v-model="form.knowledge_type" placeholder="请选择知识库类型" style="width: 100%">
          <el-option
            v-for="type in knowledgeTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="访问权限" prop="is_public">
        <el-radio-group v-model="form.is_public">
          <el-radio :label="false">私有（仅自己可见）</el-radio>
          <el-radio :label="true">公开（所有人可见）</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="描述信息">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入知识库描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 高级配置 -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="高级配置" name="advanced">
          <el-form-item label="最大文件大小">
            <el-input-number
              v-model="form.max_file_size_mb"
              :min="1"
              :max="100"
              :step="1"
              style="width: 150px"
            />
            <span style="margin-left: 8px; color: #909399;">MB</span>
          </el-form-item>

          <el-form-item label="允许文件类型">
            <el-checkbox-group v-model="form.allowed_file_types">
              <el-checkbox label="pdf">PDF</el-checkbox>
              <el-checkbox label="docx">Word文档</el-checkbox>
              <el-checkbox label="txt">文本文件</el-checkbox>
              <el-checkbox label="md">Markdown</el-checkbox>
              <el-checkbox label="jpg">图片(JPG)</el-checkbox>
              <el-checkbox label="png">图片(PNG)</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="嵌入模型">
            <el-select v-model="form.embedding_model" placeholder="选择嵌入模型" style="width: 100%">
              <el-option label="BAAI/bge-small-zh-v1.5" value="BAAI/bge-small-zh-v1.5" />
              <el-option label="text-embedding-ada-002" value="text-embedding-ada-002" />
            </el-select>
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="分块大小">
                <el-input-number
                  v-model="form.chunk_size"
                  :min="256"
                  :max="4096"
                  :step="256"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="分块重叠">
                <el-input-number
                  v-model="form.chunk_overlap"
                  :min="0"
                  :max="512"
                  :step="50"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { knowledgeBaseApi } from '@/api/knowledge'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  knowledgeBase: {
    type: Object,
    default: null
  },
  knowledgeTypes: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const formRef = ref()
const loading = ref(false)
const activeCollapse = ref([])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  knowledge_type: '',
  is_public: false,
  max_file_size_mb: 50,
  allowed_file_types: ['pdf', 'docx', 'txt', 'md'],
  embedding_model: 'BAAI/bge-small-zh-v1.5',
  chunk_size: 1024,
  chunk_overlap: 100
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  knowledge_type: [
    { required: true, message: '请选择知识库类型', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.knowledgeBase)

// 监听知识库数据变化
watch(() => props.knowledgeBase, (newVal) => {
  if (newVal) {
    // 编辑模式，填充表单
    Object.assign(form, {
      name: newVal.name,
      description: newVal.description || '',
      knowledge_type: newVal.knowledge_type,
      is_public: newVal.is_public,
      max_file_size_mb: Math.round((newVal.max_file_size || 52428800) / 1024 / 1024),
      allowed_file_types: newVal.allowed_file_types || ['pdf', 'docx', 'txt', 'md'],
      embedding_model: newVal.embedding_model || 'BAAI/bge-small-zh-v1.5',
      chunk_size: newVal.chunk_size || 1024,
      chunk_overlap: newVal.chunk_overlap || 100
    })
  } else {
    // 创建模式，重置表单
    resetForm()
  }
}, { immediate: true })

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    knowledge_type: '',
    is_public: false,
    max_file_size_mb: 50,
    allowed_file_types: ['pdf', 'docx', 'txt', 'md'],
    embedding_model: 'BAAI/bge-small-zh-v1.5',
    chunk_size: 1024,
    chunk_overlap: 100
  })
  
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  resetForm()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    // 准备提交数据
    const submitData = {
      ...form,
      max_file_size: form.max_file_size_mb * 1024 * 1024 // 转换为字节
    }
    delete submitData.max_file_size_mb
    
    let response
    if (isEdit.value) {
      // 更新知识库
      response = await knowledgeBaseApi.update(props.knowledgeBase.id, submitData)
    } else {
      // 创建知识库
      response = await knowledgeBaseApi.create(submitData)
    }
    
    if (response.code === 200) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>
