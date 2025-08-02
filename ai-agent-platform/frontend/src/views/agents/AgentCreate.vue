<template>
  <div class="agent-create">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/agents' }">
          <el-icon><ArrowLeft /></el-icon>
          智能体管理
        </el-breadcrumb-item>
        <el-breadcrumb-item>创建智能体</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-content">
        <h1 class="page-title">
          <el-icon class="title-icon"><Plus /></el-icon>
          创建智能体
        </h1>
        <p class="page-description">配置您的专属AI助手，让它更好地为您服务</p>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="create-container">
      <!-- 左侧表单区域 -->
      <div class="form-section">
        <el-card class="form-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><Setting /></el-icon>
              <span class="header-title">基础配置</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            label-position="top"
            @submit.prevent="handleSubmit"
          >
            <!-- 基础信息组 -->
            <div class="form-group">
              <h3 class="group-title">
                <el-icon><User /></el-icon>
                基础信息
              </h3>

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="智能体名称" prop="name">
                    <el-input
                      v-model="form.name"
                      placeholder="为您的智能体起一个响亮的名字"
                      maxlength="50"
                      show-word-limit
                      size="large"
                    >
                      <template #prefix>
                        <el-icon><User /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="智能体类型" prop="type">
                    <el-select
                      v-model="form.type"
                      placeholder="选择智能体类型"
                      size="large"
                      style="width: 100%"
                    >
                      <el-option label="🤖 通用助手" value="assistant" />
                      <el-option label="💬 聊天机器人" value="chatbot" />
                      <el-option label="📊 数据分析师" value="analyzer" />
                      <el-option label="🔧 自定义助手" value="custom" />
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="头像设置">
                    <div class="avatar-upload">
                      <el-avatar
                        :size="50"
                        :src="form.avatar_url || '/default-avatar.png'"
                        class="avatar-preview"
                      >
                        <el-icon><User /></el-icon>
                      </el-avatar>
                      <el-input
                        v-model="form.avatar_url"
                        placeholder="头像URL（可选）"
                        size="large"
                        style="margin-left: 12px; flex: 1;"
                      >
                        <template #prefix>
                          <el-icon><Picture /></el-icon>
                        </template>
                      </el-input>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>

            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="智能体描述" prop="description">
                  <el-input
                    v-model="form.description"
                    type="textarea"
                    :rows="4"
                    placeholder="详细描述您的智能体功能和特点，让用户更好地了解它的能力"
                    maxlength="500"
                    show-word-limit
                    size="large"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            </div>

            <!-- 模型配置组 -->
            <div class="form-group">
              <h3 class="group-title">
                <el-icon><Setting /></el-icon>
                模型配置
              </h3>

              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="AI模型" prop="model_name">
                    <el-select
                      v-model="form.model_name"
                      placeholder="选择AI模型"
                      size="large"
                      style="width: 100%"
                    >
                      <el-option label="🚀 GPT-3.5 Turbo" value="gpt-3.5-turbo" />
                      <el-option label="⭐ GPT-4" value="gpt-4" />
                      <el-option label="🔥 Claude-3" value="claude-3" />
                      <el-option label="🇨🇳 通义千问" value="qwen" />
                    </el-select>
                    <div class="field-tip">选择适合的AI模型</div>
                  </el-form-item>
                </el-col>

                <el-col :span="8">
                  <el-form-item label="创造性">
                    <div class="slider-container">
                      <el-slider
                        v-model="form.temperature"
                        :min="0"
                        :max="2"
                        :step="0.1"
                        show-input
                        :show-input-controls="false"
                        size="large"
                      />
                      <div class="slider-labels">
                        <span>保守</span>
                        <span>创新</span>
                      </div>
                    </div>
                    <div class="field-tip">控制回答的创造性程度</div>
                  </el-form-item>
                </el-col>

                <el-col :span="8">
                  <el-form-item label="回答长度">
                    <el-input-number
                      v-model="form.max_tokens"
                      :min="100"
                      :max="8000"
                      :step="100"
                      controls-position="right"
                      size="large"
                      style="width: 100%"
                    />
                    <div class="field-tip">限制回答的最大长度</div>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 提示词配置组 -->
            <div class="form-group">
              <h3 class="group-title">
                <el-icon><ChatDotRound /></el-icon>
                提示词配置
              </h3>

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="提示词模板" prop="prompt_template">
                    <el-input
                      v-model="form.prompt_template"
                      type="textarea"
                      :rows="8"
                      placeholder="定义智能体的行为和回答风格。使用 {input} 作为用户输入的占位符。&#10;&#10;示例：&#10;你是一个专业的AI助手，请根据用户的问题提供准确、有帮助的回答。&#10;&#10;用户问题：{input}&#10;&#10;请提供详细的回答："
                      size="large"
                      show-word-limit
                      maxlength="2000"
                    />
                    <div class="field-tip">
                      <el-icon><InfoFilled /></el-icon>
                      提示词决定了智能体的性格和回答风格，请仔细设计
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 知识库配置组 -->
            <div class="form-group">
              <h3 class="group-title">
                <el-icon><Collection /></el-icon>
                知识库配置
              </h3>

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="关联知识库">
                    <el-select
                      v-model="form.knowledge_base_ids"
                      multiple
                      placeholder="选择要关联的知识库，智能体将基于这些知识回答问题"
                      style="width: 100%"
                      size="large"
                      collapse-tags
                      collapse-tags-tooltip
                    >
                      <el-option
                        v-for="kb in knowledgeBases"
                        :key="kb.id"
                        :label="kb.name"
                        :value="kb.id"
                      >
                        <div class="kb-option">
                          <span class="kb-name">{{ kb.name }}</span>
                          <span class="kb-desc">{{ kb.description }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <div class="field-tip">选择知识库后，智能体将能够基于这些知识回答问题</div>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 权限配置组 -->
            <div class="form-group">
              <h3 class="group-title">
                <el-icon><Lock /></el-icon>
                权限设置
              </h3>

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="访问权限">
                    <el-radio-group v-model="form.is_public" size="large">
                      <el-radio :label="false" class="permission-radio">
                        <div class="radio-content">
                          <div class="radio-title">
                            <el-icon><Lock /></el-icon>
                            私有
                          </div>
                          <div class="radio-desc">仅自己可见和使用</div>
                        </div>
                      </el-radio>
                      <el-radio :label="true" class="permission-radio">
                        <div class="radio-content">
                          <div class="radio-title">
                            <el-icon><Unlock /></el-icon>
                            公开
                          </div>
                          <div class="radio-desc">所有人都可以查看和使用</div>
                        </div>
                      </el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 操作按钮 -->
            <div class="form-actions">
              <el-button
                type="primary"
                size="large"
                @click="handleSubmit"
                :loading="loading"
                class="submit-btn"
              >
                <el-icon><Plus /></el-icon>
                创建智能体
              </el-button>
              <el-button
                size="large"
                @click="handleCancel"
                class="cancel-btn"
              >
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧预览区域 -->
      <div class="preview-section">
        <el-card class="preview-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><View /></el-icon>
              <span class="header-title">智能体预览</span>
            </div>
          </template>

          <div class="agent-preview">
            <div class="preview-avatar">
              <el-avatar
                :size="80"
                :src="form.avatar_url || '/default-avatar.png'"
              >
                <el-icon><User /></el-icon>
              </el-avatar>
            </div>

            <div class="preview-info">
              <h3 class="preview-name">{{ form.name || '智能体名称' }}</h3>
              <div class="preview-type">
                <el-tag :type="getTypeTagType(form.type)" size="large">
                  {{ getTypeLabel(form.type) }}
                </el-tag>
              </div>
              <p class="preview-description">
                {{ form.description || '智能体描述将在这里显示...' }}
              </p>
            </div>

            <div class="preview-config">
              <h4>配置信息</h4>
              <div class="config-item">
                <span class="config-label">AI模型:</span>
                <span class="config-value">{{ getModelLabel(form.model_name) }}</span>
              </div>
              <div class="config-item">
                <span class="config-label">创造性:</span>
                <span class="config-value">{{ form.temperature }}</span>
              </div>
              <div class="config-item">
                <span class="config-label">最大长度:</span>
                <span class="config-value">{{ form.max_tokens }} tokens</span>
              </div>
              <div class="config-item">
                <span class="config-label">访问权限:</span>
                <span class="config-value">{{ form.is_public ? '公开' : '私有' }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus, Close, User, Setting, ChatDotRound, Collection,
  Lock, Unlock, View, Document, Picture, InfoFilled,
  ArrowLeft
} from '@element-plus/icons-vue'
import { agentApi, type CreateAgentParams } from '@/api/agent'
import { knowledgeApi } from '@/api/knowledge'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const knowledgeBases = ref<any[]>([])

// 表单数据
const form = reactive<CreateAgentParams>({
  name: '',
  description: '',
  avatar_url: '',
  type: 'assistant',
  model_name: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 2000,
  prompt_template: '你是一个有用的AI助手。请根据用户的问题提供准确、有帮助的回答。\n\n用户问题：{input}',
  knowledge_base_ids: [],
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

// 获取知识库列表
const fetchKnowledgeBases = async () => {
  try {
    const response = await knowledgeApi.getKnowledgeBases()
    knowledgeBases.value = response.data || []
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    knowledgeBases.value = []
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    await agentApi.create(form)
    ElMessage.success('智能体创建成功')
    router.push('/agents')
  } catch (error) {
    console.error('创建智能体失败:', error)
    ElMessage.error('创建智能体失败')
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
    router.push('/agents')
  } catch {
    // 用户取消
  }
}

// 获取类型标签类型
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    assistant: 'primary',
    chatbot: 'success',
    analyzer: 'warning',
    custom: 'info'
  }
  return typeMap[type] || 'info'
}

// 获取类型标签文本
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    assistant: '🤖 通用助手',
    chatbot: '💬 聊天机器人',
    analyzer: '📊 数据分析师',
    custom: '🔧 自定义助手'
  }
  return labelMap[type] || '🤖 通用助手'
}

// 获取模型标签
const getModelLabel = (model: string) => {
  const modelMap: Record<string, string> = {
    'gpt-3.5-turbo': 'GPT-3.5 Turbo',
    'gpt-4': 'GPT-4',
    'claude-3': 'Claude-3',
    'qwen': '通义千问'
  }
  return modelMap[model] || model
}

// 快速模板数据
const quickTemplates = ref([
  {
    id: 'assistant',
    name: '通用助手',
    icon: '🤖',
    description: '友好的AI助手',
    template: {
      name: '通用AI助手',
      type: 'assistant',
      description: '一个友好、有帮助的AI助手，可以回答各种问题并提供建议',
      prompt_template: '你是一个友好、有帮助的AI助手。请根据用户的问题提供准确、有用的信息。\n\n用户问题：{input}\n\n请提供有帮助的回答：'
    }
  },
  {
    id: 'coder',
    name: '编程助手',
    icon: '💻',
    description: '专业的编程助手',
    template: {
      name: '编程助手',
      type: 'assistant',
      description: '专业的编程助手，帮助解决代码问题、代码审查和技术咨询',
      prompt_template: '你是一个专业的编程助手。请帮助用户解决编程问题，提供清晰的代码示例和解释。\n\n用户问题：{input}\n\n请提供详细的技术回答：'
    }
  },
  {
    id: 'writer',
    name: '文案助手',
    icon: '✍️',
    description: '创意文案写作',
    template: {
      name: '文案创作助手',
      type: 'assistant',
      description: '专业的文案创作助手，帮助创作各类文案内容',
      prompt_template: '你是一个专业的文案创作助手。请根据用户需求创作高质量的文案内容。\n\n用户需求：{input}\n\n请提供创意文案：'
    }
  }
])

// 应用模板
const applyTemplate = (template: any) => {
  Object.assign(form, template.template)
  ElMessage.success(`已应用模板：${template.name}`)
}

onMounted(() => {
  fetchKnowledgeBases()
})
</script>

<style lang="scss" scoped>
.agent-create {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 0;
}

.page-header {
  background: white;
  padding: 24px 32px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 0;

  .breadcrumb {
    margin-bottom: 16px;

    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__inner {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #606266;

        &:hover {
          color: #409eff;
        }
      }
    }
  }

  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 600;
      color: #303133;
      margin: 0;

      .title-icon {
        color: #409eff;
      }
    }

    .page-description {
      color: #909399;
      font-size: 14px;
      margin: 8px 0 0 0;
    }
  }
}

.create-container {
  display: flex;
  gap: 24px;
  padding: 24px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.form-section {
  flex: 1;
  max-width: 800px;
}

.form-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);

  :deep(.el-card__header) {
    background: #f8f9fa;
    border-bottom: 1px solid #e4e7ed;
    padding: 20px 24px;
  }

  :deep(.el-card__body) {
    padding: 32px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;

  .header-icon {
    color: #409eff;
    font-size: 18px;
  }

  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.form-group {
  margin-bottom: 40px;

  .group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 24px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid #f0f2f5;

    .el-icon {
      color: #409eff;
    }
  }
}

.avatar-upload {
  display: flex;
  align-items: center;

  .avatar-preview {
    border: 2px dashed #dcdfe6;
    transition: border-color 0.3s;

    &:hover {
      border-color: #409eff;
    }
  }
}

.field-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-top: 8px;

  .el-icon {
    color: #409eff;
  }
}

.slider-container {
  .slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #909399;
    margin-top: 8px;
  }
}

.permission-radio {
  display: block !important;
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }

  :deep(.el-radio__input.is-checked) + .el-radio__label {
    color: #409eff;
  }

  .radio-content {
    margin-left: 24px;

    .radio-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 4px;
    }

    .radio-desc {
      font-size: 12px;
      color: #909399;
    }
  }
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 32px;
  border-top: 1px solid #e4e7ed;
  margin-top: 32px;

  .submit-btn {
    padding: 12px 32px;
    font-size: 16px;
    border-radius: 8px;
  }

  .cancel-btn {
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 8px;
  }
}

.preview-section {
  width: 400px;
  flex-shrink: 0;
}

.preview-card, .template-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;

  :deep(.el-card__header) {
    background: #f8f9fa;
    border-bottom: 1px solid #e4e7ed;
    padding: 16px 20px;
  }

  :deep(.el-card__body) {
    padding: 24px;
  }
}

.agent-preview {
  text-align: center;

  .preview-avatar {
    margin-bottom: 16px;
  }

  .preview-info {
    margin-bottom: 24px;

    .preview-name {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    .preview-type {
      margin-bottom: 12px;
    }

    .preview-description {
      font-size: 14px;
      color: #606266;
      line-height: 1.6;
      margin: 0;
    }
  }

  .preview-config {
    text-align: left;
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;

    h4 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 12px 0;
    }

    .config-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;

      .config-label {
        color: #909399;
      }

      .config-value {
        color: #303133;
        font-weight: 500;
      }
    }
  }

  .preview-prompt {
    text-align: left;

    h4 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    .prompt-content {
      background: #f8f9fa;
      padding: 12px;
      border-radius: 6px;
      font-size: 12px;
      color: #606266;
      line-height: 1.5;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }
  }
}

.template-list {
  .template-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      border-color: #409eff;
      background: #f0f9ff;
      transform: translateY(-1px);
    }

    .template-icon {
      font-size: 24px;
    }

    .template-info {
      flex: 1;

      .template-name {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 2px;
      }

      .template-desc {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.kb-option {
  display: flex;
  flex-direction: column;

  .kb-name {
    font-weight: 500;
    color: #303133;
  }

  .kb-desc {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #303133;
}

:deep(.el-input__inner), :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s;

  &:focus {
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
  }
}

:deep(.el-select) {
  .el-input__inner {
    border-radius: 8px;
  }
}

:deep(.el-slider__runway) {
  border-radius: 4px;
}

@media (max-width: 1200px) {
  .create-container {
    flex-direction: column;
  }

  .preview-section {
    width: 100%;
  }
}
</style>
