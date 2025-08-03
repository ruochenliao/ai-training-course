<template>
  <div class="create-agent">
    <el-steps :active="currentStep" finish-status="success" align-center>
      <el-step title="选择类型" />
      <el-step title="基本配置" />
      <el-step title="高级设置" />
      <el-step title="完成创建" />
    </el-steps>

    <div class="step-content">
      <!-- 步骤1：选择智能体类型 -->
      <div v-if="currentStep === 0" class="step-panel">
        <h3>选择智能体类型</h3>
        <p>请选择要创建的智能体类型，不同类型的智能体具有不同的能力和用途。</p>
        
        <div class="agent-types">
          <div 
            v-for="type in agentTypes" 
            :key="type.value"
            class="agent-type-card"
            :class="{ active: form.type === type.value }"
            @click="form.type = type.value"
          >
            <div class="type-icon">
              <el-icon :size="32">{{ type.icon }}</el-icon>
            </div>
            <h4>{{ type.label }}</h4>
            <p>{{ type.description }}</p>
            <div class="type-features">
              <el-tag 
                v-for="feature in type.features" 
                :key="feature"
                size="small"
                type="info"
              >
                {{ feature }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤2：基本配置 -->
      <div v-if="currentStep === 1" class="step-panel">
        <h3>基本配置</h3>
        <p>配置智能体的基本信息和参数。</p>
        
        <el-form :model="form" :rules="rules" ref="basicFormRef" label-width="120px">
          <el-form-item label="智能体名称" prop="name">
            <el-input 
              v-model="form.name" 
              placeholder="请输入智能体名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="描述" prop="description">
            <el-input 
              v-model="form.description" 
              type="textarea" 
              :rows="3"
              placeholder="请描述智能体的功能和用途"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="模型选择" prop="model">
            <el-select v-model="form.model" placeholder="请选择AI模型">
              <el-option 
                v-for="model in availableModels" 
                :key="model.value"
                :label="model.label" 
                :value="model.value"
              >
                <div class="model-option">
                  <span>{{ model.label }}</span>
                  <el-tag size="small" :type="model.recommended ? 'success' : 'info'">
                    {{ model.recommended ? '推荐' : '可用' }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="温度参数" prop="temperature">
            <el-slider 
              v-model="form.temperature" 
              :min="0" 
              :max="2" 
              :step="0.1"
              show-input
              :format-tooltip="formatTemperature"
            />
            <div class="param-help">
              控制输出的随机性和创造性
            </div>
          </el-form-item>

          <el-form-item label="最大Token数" prop="maxTokens">
            <el-input-number 
              v-model="form.maxTokens" 
              :min="100" 
              :max="8000" 
              :step="100"
              style="width: 200px;"
            />
            <div class="param-help">
              单次回复的最大长度
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤3：高级设置 -->
      <div v-if="currentStep === 2" class="step-panel">
        <h3>高级设置</h3>
        <p>配置智能体的高级功能和行为。</p>
        
        <el-form :model="form" label-width="120px">
          <el-form-item label="系统提示词">
            <el-input 
              v-model="form.systemPrompt" 
              type="textarea" 
              :rows="6"
              :placeholder="getSystemPromptPlaceholder()"
            />
            <div class="param-help">
              定义智能体的角色、行为准则和回答风格
            </div>
          </el-form-item>

          <el-form-item label="启用记忆">
            <el-switch v-model="form.enableMemory" />
            <div class="param-help">
              是否保持对话上下文记忆
            </div>
          </el-form-item>

          <el-form-item label="记忆长度" v-if="form.enableMemory">
            <el-input-number 
              v-model="form.memoryLength" 
              :min="1" 
              :max="50" 
              style="width: 200px;"
            />
          </el-form-item>

          <el-form-item label="启用工具调用" v-if="supportsTools">
            <el-switch v-model="form.enableTools" />
            <div class="param-help">
              是否允许智能体调用外部工具
            </div>
          </el-form-item>

          <el-form-item label="可用工具" v-if="form.enableTools && supportsTools">
            <el-select 
              v-model="form.availableTools" 
              multiple 
              placeholder="请选择可用工具"
              style="width: 100%;"
            >
              <el-option 
                v-for="tool in getAvailableTools()" 
                :key="tool.value"
                :label="tool.label" 
                :value="tool.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="响应超时">
            <el-input-number 
              v-model="form.timeout" 
              :min="5" 
              :max="300" 
              style="width: 200px;"
            />
            <span style="margin-left: 8px;">秒</span>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤4：确认创建 -->
      <div v-if="currentStep === 3" class="step-panel">
        <h3>确认创建</h3>
        <p>请确认以下配置信息，点击创建按钮完成智能体创建。</p>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="智能体类型">
            {{ getTypeLabel(form.type) }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ form.name }}
          </el-descriptions-item>
          <el-descriptions-item label="模型">
            {{ getModelLabel(form.model) }}
          </el-descriptions-item>
          <el-descriptions-item label="温度参数">
            {{ form.temperature }}
          </el-descriptions-item>
          <el-descriptions-item label="最大Token数">
            {{ form.maxTokens }}
          </el-descriptions-item>
          <el-descriptions-item label="启用记忆">
            {{ form.enableMemory ? '是' : '否' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ form.description }}
          </el-descriptions-item>
          <el-descriptions-item label="系统提示词" :span="2">
            <div class="prompt-preview">
              {{ form.systemPrompt || '使用默认提示词' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="step-actions">
      <el-button v-if="currentStep > 0" @click="prevStep">
        上一步
      </el-button>
      <el-button @click="handleCancel">
        取消
      </el-button>
      <el-button 
        v-if="currentStep < 3" 
        type="primary" 
        @click="nextStep"
        :disabled="!canProceed"
      >
        下一步
      </el-button>
      <el-button 
        v-if="currentStep === 3" 
        type="primary" 
        @click="handleCreate"
        :loading="creating"
      >
        创建智能体
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const emit = defineEmits(['create', 'cancel'])

// 响应式数据
const currentStep = ref(0)
const creating = ref(false)
const basicFormRef = ref<FormInstance>()

const form = reactive({
  type: '',
  name: '',
  description: '',
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  systemPrompt: '',
  enableMemory: true,
  memoryLength: 10,
  enableTools: false,
  availableTools: [],
  timeout: 30
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请选择模型', trigger: 'change' }
  ]
}

// 智能体类型
const agentTypes = [
  {
    value: 'customer_service',
    label: '智能客服',
    description: '处理客户咨询、投诉、售后等问题',
    icon: 'service',
    features: ['多轮对话', '情感识别', '工单管理']
  },
  {
    value: 'knowledge_qa',
    label: '知识问答',
    description: '基于知识库回答专业问题',
    icon: 'question',
    features: ['知识检索', '上下文理解', '来源引用']
  },
  {
    value: 'text2sql',
    label: '数据分析',
    description: '将自然语言转换为SQL查询',
    icon: 'data-analysis',
    features: ['SQL生成', '数据查询', '结果解释']
  },
  {
    value: 'content_creation',
    label: '内容创作',
    description: '创作各类文案、文章、营销内容',
    icon: 'edit',
    features: ['多种文体', '风格控制', 'SEO优化']
  }
]

// 可用模型
const availableModels = [
  { value: 'gpt-4', label: 'GPT-4', recommended: true },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', recommended: true },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', recommended: false },
  { value: 'claude-3', label: 'Claude-3', recommended: false }
]

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return form.type !== ''
    case 1:
      return form.name && form.description && form.model
    case 2:
      return true
    default:
      return true
  }
})

const supportsTools = computed(() => {
  return ['customer_service', 'text2sql'].includes(form.type)
})

// 方法
const nextStep = async () => {
  if (currentStep.value === 1) {
    // 验证基本配置表单
    if (!basicFormRef.value) return
    
    try {
      await basicFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleCancel = () => {
  emit('cancel')
}

const handleCreate = async () => {
  creating.value = true
  
  try {
    // 构建智能体配置
    const agentData = {
      type: form.type,
      name: form.name,
      description: form.description,
      model: form.model,
      capabilities: getTypeCapabilities(form.type),
      config: {
        temperature: form.temperature,
        maxTokens: form.maxTokens,
        systemPrompt: form.systemPrompt || getDefaultSystemPrompt(form.type),
        enableMemory: form.enableMemory,
        memoryLength: form.memoryLength,
        enableTools: form.enableTools,
        availableTools: form.availableTools,
        timeout: form.timeout
      }
    }
    
    emit('create', agentData)
  } catch (error) {
    ElMessage.error('创建智能体失败')
  } finally {
    creating.value = false
  }
}

const formatTemperature = (value: number) => {
  return `${value} (${value < 0.5 ? '保守' : value < 1.5 ? '平衡' : '创新'})`
}

const getSystemPromptPlaceholder = () => {
  const placeholders = {
    customer_service: '你是一个专业、友好的客户服务代表...',
    knowledge_qa: '你是一个专业的知识库问答助手...',
    text2sql: '你是一个专业的SQL专家...',
    content_creation: '你是一个专业的内容创作专家...'
  }
  return placeholders[form.type] || '请输入系统提示词...'
}

const getAvailableTools = () => {
  const toolsByType = {
    customer_service: [
      { value: 'ticket_system', label: '工单系统' },
      { value: 'knowledge_base', label: '知识库' },
      { value: 'sentiment_analysis', label: '情感分析' }
    ],
    text2sql: [
      { value: 'database_schema', label: '数据库模式' },
      { value: 'query_optimizer', label: '查询优化器' },
      { value: 'result_formatter', label: '结果格式化' }
    ]
  }
  return toolsByType[form.type] || []
}

const getTypeLabel = (type: string) => {
  const typeObj = agentTypes.find(t => t.value === type)
  return typeObj ? typeObj.label : type
}

const getModelLabel = (model: string) => {
  const modelObj = availableModels.find(m => m.value === model)
  return modelObj ? modelObj.label : model
}

const getTypeCapabilities = (type: string) => {
  const typeObj = agentTypes.find(t => t.value === type)
  return typeObj ? typeObj.features : []
}

const getDefaultSystemPrompt = (type: string) => {
  const prompts = {
    customer_service: '你是一个专业、友好的客户服务代表。你的目标是帮助客户解决问题，提供优质的服务体验。',
    knowledge_qa: '你是一个专业的知识库问答助手，能够基于提供的知识库内容回答用户问题。',
    text2sql: '你是一个专业的SQL专家，能够将自然语言查询转换为准确的SQL语句。',
    content_creation: '你是一个专业的内容创作专家，擅长创作各种类型的高质量内容。'
  }
  return prompts[type] || ''
}
</script>

<style scoped>
.create-agent {
  padding: 20px 0;
}

.step-content {
  margin: 40px 0;
  min-height: 400px;
}

.step-panel h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.step-panel p {
  margin: 0 0 24px 0;
  color: #606266;
}

.agent-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.agent-type-card {
  padding: 24px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.agent-type-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.agent-type-card.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.type-icon {
  margin-bottom: 16px;
  color: #409eff;
}

.agent-type-card h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.agent-type-card p {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
}

.type-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.param-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.prompt-preview {
  max-height: 100px;
  overflow-y: auto;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}
</style>
