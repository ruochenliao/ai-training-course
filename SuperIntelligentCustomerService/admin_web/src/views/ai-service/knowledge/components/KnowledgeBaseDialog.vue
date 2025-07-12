<template>
  <n-modal
    v-model:show="visible"
    :title="isEdit ? '编辑知识库' : '创建知识库'"
    preset="dialog"
    style="width: 600px"
    :mask-closable="false"
    @close="handleClose"
  >
    <n-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-placement="left"
      label-width="100px"
    >
      <n-form-item label="知识库名称" path="name">
        <n-input
          v-model:value="form.name"
          placeholder="请输入知识库名称"
          maxlength="200"
          show-count
        />
      </n-form-item>

      <n-form-item label="知识库类型" path="knowledge_type">
        <n-select
          v-model:value="form.knowledge_type"
          placeholder="请选择知识库类型"
          :options="knowledgeTypeOptions"
        />
      </n-form-item>

      <n-form-item label="访问权限" path="is_public">
        <n-radio-group v-model:value="form.is_public">
          <n-space>
            <n-radio :value="false">私有（仅自己可见）</n-radio>
            <n-radio :value="true">公开（所有人可见）</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item label="描述信息">
        <n-input
          v-model:value="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入知识库描述"
          maxlength="500"
          show-count
        />
      </n-form-item>

      <!-- 高级配置 -->
      <n-collapse>
        <n-collapse-item title="高级配置" name="advanced">
          <n-form-item label="最大文件大小">
            <n-space align="center">
              <n-input-number
                v-model:value="form.max_file_size_mb"
                :min="1"
                :max="100"
                :step="1"
                style="width: 150px"
              />
              <span>MB</span>
            </n-space>
          </n-form-item>

          <n-form-item label="允许文件类型">
            <n-checkbox-group v-model:value="form.allowed_file_types">
              <n-space>
                <n-checkbox value="pdf" label="PDF" />
                <n-checkbox value="docx" label="Word文档" />
                <n-checkbox value="txt" label="文本文件" />
                <n-checkbox value="md" label="Markdown" />
                <n-checkbox value="jpg" label="图片(JPG)" />
                <n-checkbox value="png" label="图片(PNG)" />
              </n-space>
            </n-checkbox-group>
          </n-form-item>

          <n-form-item label="嵌入模型">
            <n-select
              v-model:value="form.embedding_model"
              placeholder="选择嵌入模型"
              :options="embeddingModelOptions"
            />
          </n-form-item>

          <n-grid :cols="2" :x-gap="20">
            <n-grid-item>
              <n-form-item label="分块大小">
                <n-input-number
                  v-model:value="form.chunk_size"
                  :min="256"
                  :max="4096"
                  :step="256"
                  style="width: 100%"
                />
              </n-form-item>
            </n-grid-item>
            <n-grid-item>
              <n-form-item label="分块重叠">
                <n-input-number
                  v-model:value="form.chunk_overlap"
                  :min="0"
                  :max="512"
                  :step="50"
                  style="width: 100%"
                />
              </n-form-item>
            </n-grid-item>
          </n-grid>
        </n-collapse-item>
      </n-collapse>
    </n-form>

    <template #action>
      <n-space>
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
import {computed, reactive, ref, watch} from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NCollapse,
  NCollapseItem,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NInputNumber,
  NModal,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  useMessage
} from 'naive-ui'
import api from '@/api'

// Props
const props = defineProps({
  show: {
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
const emit = defineEmits(['update:show', 'success'])

// 响应式数据
const formRef = ref()
const message = useMessage()
const loading = ref(false)

// 表单数据
const form = reactive({
  name: '',
  description: '',
  knowledge_type: null,
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

// 选项数据
const knowledgeTypeOptions = computed(() =>
  props.knowledgeTypes.map(type => ({
    label: type.label,
    value: type.value
  }))
)

const embeddingModelOptions = [
  { label: 'BAAI/bge-small-zh-v1.5', value: 'BAAI/bge-small-zh-v1.5' },
  { label: 'text-embedding-ada-002', value: 'text-embedding-ada-002' }
]

// 计算属性
const visible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const isEdit = computed(() => !!props.knowledgeBase)

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    knowledge_type: null,
    is_public: false,
    max_file_size_mb: 50,
    allowed_file_types: ['pdf', 'docx', 'txt', 'md'],
    embedding_model: 'BAAI/bge-small-zh-v1.5',
    chunk_size: 1024,
    chunk_overlap: 100
  })

  if (formRef.value) {
    formRef.value.restoreValidation()
  }
}

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

// 关闭对话框
const handleClose = () => {
  visible.value = false
  resetForm()
}

// 提交表单
const handleSubmit = async () => {
  try {
    // 简单的表单验证
    if (!form.name || !form.knowledge_type) {
      message.error('请填写必填字段')
      return
    }

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
      response = await api.updateKnowledgeBase(props.knowledgeBase.id, submitData)
    } else {
      // 创建知识库
      response = await api.createKnowledgeBase(submitData)
    }

    if (response.code === 200) {
      message.success(isEdit.value ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    }
  } catch (error) {
    console.error('提交失败:', error)
    message.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    loading.value = false
  }
}
</script>
