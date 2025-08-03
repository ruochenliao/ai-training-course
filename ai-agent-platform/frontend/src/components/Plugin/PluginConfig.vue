<template>
  <div class="plugin-config">
    <div class="config-header">
      <h4>{{ plugin.name }} 配置</h4>
      <p>配置插件参数以满足您的需求</p>
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <!-- 根据插件类型动态生成配置表单 -->
      <template v-if="plugin.name === 'email_sender'">
        <el-form-item label="SMTP服务器" prop="smtp_server">
          <el-input v-model="form.smtp_server" placeholder="例如: smtp.gmail.com" />
        </el-form-item>

        <el-form-item label="SMTP端口" prop="smtp_port">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" />
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="邮箱地址" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="邮箱密码或应用密码" show-password />
        </el-form-item>

        <el-form-item label="使用TLS" prop="use_tls">
          <el-switch v-model="form.use_tls" />
        </el-form-item>

        <el-form-item label="发件人名称" prop="from_name">
          <el-input v-model="form.from_name" placeholder="可选：显示的发件人名称" />
        </el-form-item>
      </template>

      <template v-else-if="plugin.type === 'integration'">
        <el-form-item label="API地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="第三方服务API地址" />
        </el-form-item>

        <el-form-item label="API密钥" prop="api_key">
          <el-input v-model="form.api_key" type="password" placeholder="API访问密钥" show-password />
        </el-form-item>

        <el-form-item label="超时时间" prop="timeout">
          <el-input-number v-model="form.timeout" :min="1000" :max="60000" :step="1000" />
          <span style="margin-left: 8px;">毫秒</span>
        </el-form-item>

        <el-form-item label="重试次数" prop="retry_count">
          <el-input-number v-model="form.retry_count" :min="0" :max="10" />
        </el-form-item>

        <el-form-item label="启用缓存" prop="enable_cache">
          <el-switch v-model="form.enable_cache" />
        </el-form-item>
      </template>

      <template v-else-if="plugin.type === 'agent'">
        <el-form-item label="模型" prop="model">
          <el-select v-model="form.model" placeholder="选择AI模型">
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-4 Turbo" value="gpt-4-turbo" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
            <el-option label="Claude-3" value="claude-3" />
          </el-select>
        </el-form-item>

        <el-form-item label="温度参数" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>

        <el-form-item label="最大Token数" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="8000" :step="100" />
        </el-form-item>

        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4" placeholder="定义智能体的角色和行为" />
        </el-form-item>

        <el-form-item label="启用记忆" prop="enable_memory">
          <el-switch v-model="form.enable_memory" />
        </el-form-item>

        <el-form-item v-if="form.enable_memory" label="记忆长度" prop="memory_length">
          <el-input-number v-model="form.memory_length" :min="1" :max="50" />
        </el-form-item>
      </template>

      <!-- 通用配置 -->
      <el-divider content-position="left">通用配置</el-divider>

      <el-form-item label="启用日志" prop="enable_logging">
        <el-switch v-model="form.enable_logging" />
      </el-form-item>

      <el-form-item v-if="form.enable_logging" label="日志级别" prop="log_level">
        <el-select v-model="form.log_level">
          <el-option label="调试" value="debug" />
          <el-option label="信息" value="info" />
          <el-option label="警告" value="warning" />
          <el-option label="错误" value="error" />
        </el-select>
      </el-form-item>

      <el-form-item label="错误处理" prop="error_handling">
        <el-radio-group v-model="form.error_handling">
          <el-radio label="stop">停止执行</el-radio>
          <el-radio label="continue">继续执行</el-radio>
          <el-radio label="retry">重试</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.error_handling === 'retry'" label="重试次数" prop="retry_count">
        <el-input-number v-model="form.retry_count" :min="1" :max="10" />
      </el-form-item>

      <!-- 高级配置 -->
      <el-divider content-position="left">高级配置</el-divider>

      <el-form-item label="自定义配置" prop="custom_config">
        <el-input 
          v-model="form.custom_config" 
          type="textarea" 
          :rows="6"
          placeholder="JSON格式的自定义配置参数"
        />
        <div class="form-help">
          请输入有效的JSON格式配置，例如: {"key": "value"}
        </div>
      </el-form-item>

      <!-- 测试连接 -->
      <el-form-item v-if="showTestConnection">
        <el-button @click="testConnection" :loading="testing">
          <el-icon><Link /></el-icon>
          测试连接
        </el-button>
      </el-form-item>
    </el-form>

    <div class="config-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">
        保存配置
      </el-button>
    </div>

    <!-- 配置预览 -->
    <el-card v-if="showPreview" class="config-preview">
      <template #header>
        <span>配置预览</span>
      </template>
      <pre class="config-json">{{ configPreview }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

// Props
interface Props {
  plugin: {
    name: string
    type: string
    config: Record<string, any>
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['save', 'cancel'])

// 响应式数据
const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)
const showPreview = ref(false)

const form = reactive({
  // 邮件插件配置
  smtp_server: '',
  smtp_port: 587,
  username: '',
  password: '',
  use_tls: true,
  from_name: '',
  
  // 集成插件配置
  api_url: '',
  api_key: '',
  timeout: 30000,
  retry_count: 3,
  enable_cache: true,
  
  // 智能体插件配置
  model: 'gpt-4',
  temperature: 0.7,
  max_tokens: 2000,
  system_prompt: '',
  enable_memory: true,
  memory_length: 10,
  
  // 通用配置
  enable_logging: true,
  log_level: 'info',
  error_handling: 'stop',
  custom_config: ''
})

const rules: FormRules = {
  smtp_server: [
    { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  api_url: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请选择模型', trigger: 'change' }
  ]
}

// 计算属性
const showTestConnection = computed(() => {
  return props.plugin.name === 'email_sender' || props.plugin.type === 'integration'
})

const configPreview = computed(() => {
  const config = buildConfig()
  return JSON.stringify(config, null, 2)
})

// 方法
const initForm = () => {
  // 从插件当前配置初始化表单
  const config = props.plugin.config || {}
  
  Object.keys(form).forEach(key => {
    if (config[key] !== undefined) {
      form[key] = config[key]
    }
  })
  
  // 处理自定义配置
  const customConfig = { ...config }
  Object.keys(form).forEach(key => {
    delete customConfig[key]
  })
  
  if (Object.keys(customConfig).length > 0) {
    form.custom_config = JSON.stringify(customConfig, null, 2)
  }
}

const buildConfig = () => {
  const config: Record<string, any> = {}
  
  // 根据插件类型添加相关配置
  if (props.plugin.name === 'email_sender') {
    config.smtp_server = form.smtp_server
    config.smtp_port = form.smtp_port
    config.username = form.username
    config.password = form.password
    config.use_tls = form.use_tls
    if (form.from_name) config.from_name = form.from_name
  } else if (props.plugin.type === 'integration') {
    config.api_url = form.api_url
    config.api_key = form.api_key
    config.timeout = form.timeout
    config.retry_count = form.retry_count
    config.enable_cache = form.enable_cache
  } else if (props.plugin.type === 'agent') {
    config.model = form.model
    config.temperature = form.temperature
    config.max_tokens = form.max_tokens
    config.system_prompt = form.system_prompt
    config.enable_memory = form.enable_memory
    if (form.enable_memory) {
      config.memory_length = form.memory_length
    }
  }
  
  // 添加通用配置
  config.enable_logging = form.enable_logging
  if (form.enable_logging) {
    config.log_level = form.log_level
  }
  config.error_handling = form.error_handling
  if (form.error_handling === 'retry') {
    config.retry_count = form.retry_count
  }
  
  // 添加自定义配置
  if (form.custom_config) {
    try {
      const customConfig = JSON.parse(form.custom_config)
      Object.assign(config, customConfig)
    } catch (error) {
      console.warn('自定义配置JSON格式错误')
    }
  }
  
  return config
}

const validateCustomConfig = () => {
  if (!form.custom_config) return true
  
  try {
    JSON.parse(form.custom_config)
    return true
  } catch (error) {
    ElMessage.error('自定义配置JSON格式错误')
    return false
  }
}

const testConnection = async () => {
  testing.value = true
  try {
    // 验证必需字段
    if (!await formRef.value?.validate()) {
      return
    }
    
    // 模拟测试连接
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}

const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (!validateCustomConfig()) {
      return
    }
    
    saving.value = true
    
    const config = buildConfig()
    emit('save', config)
    
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

const resetForm = () => {
  formRef.value?.resetFields()
  initForm()
  ElMessage.success('表单已重置')
}

// 监听表单变化，实时更新预览
watch(() => form, () => {
  // 可以在这里实时验证配置
}, { deep: true })

// 生命周期
onMounted(() => {
  initForm()
})
</script>

<style scoped>
.plugin-config {
  padding: 20px 0;
}

.config-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.config-header h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.config-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.config-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

.config-preview {
  margin-top: 20px;
}

.config-json {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #303133;
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.el-divider {
  margin: 24px 0 16px 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-slider) {
  margin: 12px 0;
}
</style>
