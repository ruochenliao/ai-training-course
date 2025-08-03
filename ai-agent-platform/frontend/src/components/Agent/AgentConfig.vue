<template>
  <div class="agent-config">
    <el-form 
      ref="formRef" 
      :model="form" 
      :rules="rules" 
      label-width="120px"
      @submit.prevent
    >
      <!-- 基本配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <span>基本配置</span>
        </template>

        <el-form-item label="智能体名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入智能体名称" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入智能体描述"
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-card>

      <!-- 模型配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <span>模型配置</span>
        </template>

        <el-form-item label="模型" prop="model">
          <el-select v-model="form.model" placeholder="请选择模型">
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-4 Turbo" value="gpt-4-turbo" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
            <el-option label="Claude-3" value="claude-3" />
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
          <div class="param-description">
            控制输出的随机性。较低的值使输出更确定，较高的值使输出更随机。
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
          <div class="param-description">
            生成回复的最大Token数量。
          </div>
        </el-form-item>

        <el-form-item label="Top P" prop="topP">
          <el-slider 
            v-model="form.topP" 
            :min="0" 
            :max="1" 
            :step="0.01"
            show-input
            :format-tooltip="formatTopP"
          />
          <div class="param-description">
            核心采样参数，控制考虑的词汇范围。
          </div>
        </el-form-item>
      </el-card>

      <!-- 提示词配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="section-header">
            <span>提示词配置</span>
            <el-button size="small" @click="showPromptTemplates = true">
              选择模板
            </el-button>
          </div>
        </template>

        <el-form-item label="系统提示词" prop="systemPrompt">
          <el-input 
            v-model="form.systemPrompt" 
            type="textarea" 
            :rows="8"
            placeholder="请输入系统提示词，定义智能体的角色和行为..."
          />
          <div class="param-description">
            系统提示词定义了智能体的角色、行为准则和回答风格。
          </div>
        </el-form-item>

        <el-form-item label="用户提示词前缀" prop="userPromptPrefix">
          <el-input 
            v-model="form.userPromptPrefix" 
            placeholder="可选：在用户输入前添加的前缀"
          />
        </el-form-item>
      </el-card>

      <!-- 高级配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <span>高级配置</span>
        </template>

        <el-form-item label="启用记忆" prop="enableMemory">
          <el-switch v-model="form.enableMemory" />
          <div class="param-description">
            是否保持对话上下文记忆。
          </div>
        </el-form-item>

        <el-form-item label="记忆长度" prop="memoryLength" v-if="form.enableMemory">
          <el-input-number 
            v-model="form.memoryLength" 
            :min="1" 
            :max="50" 
            style="width: 200px;"
          />
          <div class="param-description">
            保持的对话轮数。
          </div>
        </el-form-item>

        <el-form-item label="启用工具调用" prop="enableTools">
          <el-switch v-model="form.enableTools" />
          <div class="param-description">
            是否允许智能体调用外部工具。
          </div>
        </el-form-item>

        <el-form-item label="可用工具" prop="availableTools" v-if="form.enableTools">
          <el-select 
            v-model="form.availableTools" 
            multiple 
            placeholder="请选择可用工具"
            style="width: 100%;"
          >
            <el-option label="计算器" value="calculator" />
            <el-option label="搜索引擎" value="search" />
            <el-option label="文档生成" value="document" />
            <el-option label="图片生成" value="image" />
          </el-select>
        </el-form-item>

        <el-form-item label="响应超时" prop="timeout">
          <el-input-number 
            v-model="form.timeout" 
            :min="5" 
            :max="300" 
            style="width: 200px;"
          />
          <span style="margin-left: 8px;">秒</span>
          <div class="param-description">
            智能体响应的超时时间。
          </div>
        </el-form-item>

        <el-form-item label="自定义配置" prop="customConfig">
          <el-input 
            v-model="form.customConfig" 
            type="textarea" 
            :rows="4"
            placeholder="JSON格式的自定义配置..."
          />
          <div class="param-description">
            JSON格式的额外配置参数。
          </div>
        </el-form-item>
      </el-card>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存配置
        </el-button>
      </div>
    </el-form>

    <!-- 提示词模板对话框 -->
    <el-dialog 
      v-model="showPromptTemplates" 
      title="选择提示词模板" 
      width="600px"
    >
      <div class="template-list">
        <div 
          v-for="template in promptTemplates" 
          :key="template.id"
          class="template-item"
          @click="selectTemplate(template)"
        >
          <h4>{{ template.name }}</h4>
          <p>{{ template.description }}</p>
          <div class="template-preview">{{ template.content.substring(0, 100) }}...</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

// Props
interface Props {
  agent: {
    id: string
    name: string
    type: string
    description: string
    status: string
    model: string
    config?: any
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['save', 'cancel'])

// 响应式数据
const formRef = ref<FormInstance>()
const saving = ref(false)
const showPromptTemplates = ref(false)

const form = reactive({
  name: '',
  description: '',
  status: 'active',
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  topP: 0.9,
  systemPrompt: '',
  userPromptPrefix: '',
  enableMemory: true,
  memoryLength: 10,
  enableTools: false,
  availableTools: [],
  timeout: 30,
  customConfig: ''
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
  ],
  systemPrompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' }
  ]
}

const promptTemplates = ref([
  {
    id: 1,
    name: '客服助手',
    description: '专业的客户服务智能体模板',
    content: '你是一个专业、友好的客户服务代表。你的目标是帮助客户解决问题，提供优质的服务体验...'
  },
  {
    id: 2,
    name: '知识问答',
    description: '基于知识库的问答智能体模板',
    content: '你是一个专业的知识库问答助手，能够基于提供的知识库内容回答用户问题...'
  },
  {
    id: 3,
    name: '内容创作',
    description: '专业的内容创作智能体模板',
    content: '你是一个专业的内容创作专家，擅长创作各种类型的高质量内容...'
  }
])

// 方法
const initForm = () => {
  form.name = props.agent.name
  form.description = props.agent.description
  form.status = props.agent.status
  form.model = props.agent.model
  
  if (props.agent.config) {
    Object.assign(form, props.agent.config)
  }
}

const formatTemperature = (value: number) => {
  return `${value} (${value < 0.5 ? '保守' : value < 1.5 ? '平衡' : '创新'})`
}

const formatTopP = (value: number) => {
  return `${value} (${value < 0.3 ? '聚焦' : value < 0.7 ? '平衡' : '多样'})`
}

const selectTemplate = (template: any) => {
  form.systemPrompt = template.content
  showPromptTemplates.value = false
  ElMessage.success(`已应用模板：${template.name}`)
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    saving.value = true
    
    // 验证自定义配置JSON
    if (form.customConfig) {
      try {
        JSON.parse(form.customConfig)
      } catch (error) {
        ElMessage.error('自定义配置格式错误，请检查JSON格式')
        saving.value = false
        return
      }
    }

    // 构建配置对象
    const config = {
      temperature: form.temperature,
      maxTokens: form.maxTokens,
      topP: form.topP,
      systemPrompt: form.systemPrompt,
      userPromptPrefix: form.userPromptPrefix,
      enableMemory: form.enableMemory,
      memoryLength: form.memoryLength,
      enableTools: form.enableTools,
      availableTools: form.availableTools,
      timeout: form.timeout,
      customConfig: form.customConfig ? JSON.parse(form.customConfig) : {}
    }

    emit('save', {
      name: form.name,
      description: form.description,
      status: form.status,
      model: form.model,
      config
    })

  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有配置吗？这将丢失当前的修改。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    initForm()
    ElMessage.success('配置已重置')
  } catch (error) {
    // 用户取消操作
  }
}

// 生命周期
onMounted(() => {
  initForm()
})
</script>

<style scoped>
.agent-config {
  max-height: 70vh;
  overflow-y: auto;
}

.config-section {
  margin-bottom: 20px;
}

.config-section:last-of-type {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.template-item:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.template-item h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.template-item p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.template-preview {
  font-size: 12px;
  color: #909399;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
}
</style>
