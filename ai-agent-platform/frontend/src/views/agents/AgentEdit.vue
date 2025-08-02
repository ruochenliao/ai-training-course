<template>
  <div class="agent-edit">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/agents' }">智能体管理</el-breadcrumb-item>
        <el-breadcrumb-item>编辑智能体</el-breadcrumb-item>
      </el-breadcrumb>
      <h2>编辑智能体</h2>
    </div>

    <el-card v-loading="pageLoading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="智能体名称" prop="name">
              <el-input
                v-model="form.name"
                placeholder="请输入智能体名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="智能体类型" prop="type">
              <el-select v-model="form.type" placeholder="请选择智能体类型">
                <el-option label="助手" value="assistant" />
                <el-option label="聊天机器人" value="chatbot" />
                <el-option label="分析师" value="analyzer" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="智能体描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入智能体描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="头像URL">
          <el-input
            v-model="form.avatar_url"
            placeholder="请输入头像URL（可选）"
          />
        </el-form-item>

        <el-form-item label="模型设置">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="模型名称" prop="model_name">
                <el-select v-model="form.model_name" placeholder="选择模型">
                  <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
                  <el-option label="GPT-4" value="gpt-4" />
                  <el-option label="Claude-3" value="claude-3" />
                  <el-option label="通义千问" value="qwen" />
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="8">
              <el-form-item label="温度参数">
                <el-slider
                  v-model="form.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                  :show-input-controls="false"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="8">
              <el-form-item label="最大Token">
                <el-input-number
                  v-model="form.max_tokens"
                  :min="100"
                  :max="8000"
                  :step="100"
                  controls-position="right"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item label="提示词模板" prop="prompt_template">
          <el-input
            v-model="form.prompt_template"
            type="textarea"
            :rows="6"
            placeholder="请输入提示词模板，使用 {input} 作为用户输入的占位符"
          />
        </el-form-item>

        <el-form-item label="知识库">
          <el-select
            v-model="form.knowledge_base_ids"
            multiple
            placeholder="选择关联的知识库（可选）"
            style="width: 100%"
          >
            <el-option
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="访问权限">
          <el-radio-group v-model="form.is_public">
            <el-radio :label="false">私有（仅自己可见）</el-radio>
            <el-radio :label="true">公开（所有人可见）</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            保存修改
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="danger" @click="handleDelete" :loading="deleteLoading">
            删除智能体
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { agentApi, type Agent } from '@/api/agent'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const loading = ref(false)
const deleteLoading = ref(false)
const pageLoading = ref(true)
const knowledgeBases = ref<any[]>([])

const agentId = Number(route.params.id)

// 表单数据
const form = reactive({
  name: '',
  description: '',
  avatar_url: '',
  type: 'assistant',
  model_name: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 2000,
  prompt_template: '',
  knowledge_base_ids: [] as number[],
  is_public: false
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择智能体类型', trigger: 'change' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  model_name: [
    { required: true, message: '请选择模型', trigger: 'change' }
  ],
  prompt_template: [
    { required: true, message: '请输入提示词模板', trigger: 'blur' },
    { min: 10, message: '提示词模板至少需要 10 个字符', trigger: 'blur' }
  ]
}

// 获取智能体详情
const fetchAgentDetail = async () => {
  try {
    pageLoading.value = true
    const response = await agentApi.getDetail(agentId)
    const agent = response.data
    
    // 填充表单数据
    Object.assign(form, {
      name: agent.name,
      description: agent.description || '',
      avatar_url: agent.avatar_url || '',
      type: agent.type,
      model_name: agent.model_name || 'gpt-3.5-turbo',
      temperature: parseFloat(agent.temperature || '0.7'),
      max_tokens: parseInt(agent.max_tokens || '2000'),
      prompt_template: agent.prompt_template || '',
      knowledge_base_ids: agent.knowledge_base_ids || [],
      is_public: agent.is_public
    })
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    ElMessage.error('获取智能体详情失败')
    router.push('/agents')
  } finally {
    pageLoading.value = false
  }
}

// 获取知识库列表
const fetchKnowledgeBases = async () => {
  try {
    // TODO: 实现知识库API调用
    knowledgeBases.value = []
  } catch (error) {
    console.error('获取知识库列表失败:', error)
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    await agentApi.update(agentId, form)
    ElMessage.success('智能体更新成功')
    router.push('/agents')
  } catch (error) {
    console.error('更新智能体失败:', error)
    ElMessage.error('更新智能体失败')
  } finally {
    loading.value = false
  }
}

// 取消操作
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消编辑吗？未保存的修改将丢失。', '确认取消', {
      type: 'warning'
    })
    router.push('/agents')
  } catch {
    // 用户取消
  }
}

// 删除智能体
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个智能体吗？此操作不可恢复。',
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    deleteLoading.value = true
    await agentApi.delete(agentId)
    ElMessage.success('智能体删除成功')
    router.push('/agents')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除智能体失败:', error)
      ElMessage.error('删除智能体失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  fetchAgentDetail()
  fetchKnowledgeBases()
})
</script>

<style lang="scss" scoped>
.agent-edit {
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
  max-width: 800px;
}

.el-textarea {
  :deep(.el-textarea__inner) {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  }
}
</style>
