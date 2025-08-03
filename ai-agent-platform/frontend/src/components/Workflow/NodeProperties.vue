<template>
  <div class="node-properties">
    <div class="property-header">
      <h4>{{ node.name }}</h4>
      <el-tag size="small">{{ getNodeTypeName(node.type) }}</el-tag>
    </div>

    <el-form :model="form" label-width="80px" size="small">
      <!-- 基本属性 -->
      <el-form-item label="名称">
        <el-input v-model="form.name" @change="updateProperty('name', form.name)" />
      </el-form-item>

      <el-form-item label="描述">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="2"
          @change="updateProperty('description', form.description)"
        />
      </el-form-item>

      <!-- 根据节点类型显示不同配置 -->
      <template v-if="node.type === 'http_request'">
        <el-divider content-position="left">HTTP配置</el-divider>
        
        <el-form-item label="URL">
          <el-input 
            v-model="form.config.url" 
            placeholder="https://api.example.com/endpoint"
            @change="updateConfig('url', form.config.url)"
          />
        </el-form-item>

        <el-form-item label="方法">
          <el-select 
            v-model="form.config.method" 
            @change="updateConfig('method', form.config.method)"
          >
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>

        <el-form-item label="请求头">
          <KeyValueEditor 
            v-model="form.config.headers"
            @change="updateConfig('headers', form.config.headers)"
          />
        </el-form-item>

        <el-form-item label="请求体">
          <el-input 
            v-model="form.config.body" 
            type="textarea" 
            :rows="3"
            placeholder="JSON格式的请求体"
            @change="updateConfig('body', form.config.body)"
          />
        </el-form-item>

        <el-form-item label="超时时间">
          <el-input-number 
            v-model="form.config.timeout" 
            :min="1000" 
            :max="60000" 
            :step="1000"
            @change="updateConfig('timeout', form.config.timeout)"
          />
          <span style="margin-left: 8px;">毫秒</span>
        </el-form-item>
      </template>

      <template v-else-if="node.type === 'condition'">
        <el-divider content-position="left">条件配置</el-divider>
        
        <el-form-item label="条件表达式">
          <el-input 
            v-model="form.config.condition" 
            type="textarea" 
            :rows="3"
            placeholder="例如: input.status === 'success'"
            @change="updateConfig('condition', form.config.condition)"
          />
        </el-form-item>

        <el-form-item label="条件类型">
          <el-radio-group 
            v-model="form.config.conditionType"
            @change="updateConfig('conditionType', form.config.conditionType)"
          >
            <el-radio label="javascript">JavaScript表达式</el-radio>
            <el-radio label="simple">简单比较</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="form.config.conditionType === 'simple'">
          <el-form-item label="字段">
            <el-input 
              v-model="form.config.field" 
              placeholder="input.fieldName"
              @change="updateConfig('field', form.config.field)"
            />
          </el-form-item>

          <el-form-item label="操作符">
            <el-select 
              v-model="form.config.operator"
              @change="updateConfig('operator', form.config.operator)"
            >
              <el-option label="等于" value="==" />
              <el-option label="不等于" value="!=" />
              <el-option label="大于" value=">" />
              <el-option label="小于" value="<" />
              <el-option label="包含" value="includes" />
              <el-option label="正则匹配" value="regex" />
            </el-select>
          </el-form-item>

          <el-form-item label="值">
            <el-input 
              v-model="form.config.value" 
              @change="updateConfig('value', form.config.value)"
            />
          </el-form-item>
        </template>
      </template>

      <template v-else-if="node.type === 'database_query'">
        <el-divider content-position="left">数据库配置</el-divider>
        
        <el-form-item label="数据源">
          <el-select 
            v-model="form.config.datasource"
            @change="updateConfig('datasource', form.config.datasource)"
          >
            <el-option label="默认数据库" value="default" />
            <el-option label="用户数据库" value="user_db" />
            <el-option label="日志数据库" value="log_db" />
          </el-select>
        </el-form-item>

        <el-form-item label="SQL查询">
          <el-input 
            v-model="form.config.query" 
            type="textarea" 
            :rows="4"
            placeholder="SELECT * FROM users WHERE id = ${input.userId}"
            @change="updateConfig('query', form.config.query)"
          />
        </el-form-item>

        <el-form-item label="参数">
          <KeyValueEditor 
            v-model="form.config.parameters"
            @change="updateConfig('parameters', form.config.parameters)"
          />
        </el-form-item>
      </template>

      <template v-else-if="isAgentNode(node.type)">
        <el-divider content-position="left">智能体配置</el-divider>
        
        <el-form-item label="模型">
          <el-select 
            v-model="form.config.model"
            @change="updateConfig('model', form.config.model)"
          >
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-4 Turbo" value="gpt-4-turbo" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
            <el-option label="Claude-3" value="claude-3" />
          </el-select>
        </el-form-item>

        <el-form-item label="温度">
          <el-slider 
            v-model="form.config.temperature" 
            :min="0" 
            :max="2" 
            :step="0.1"
            show-input
            @change="updateConfig('temperature', form.config.temperature)"
          />
        </el-form-item>

        <el-form-item label="最大Token">
          <el-input-number 
            v-model="form.config.maxTokens" 
            :min="100" 
            :max="8000" 
            :step="100"
            @change="updateConfig('maxTokens', form.config.maxTokens)"
          />
        </el-form-item>

        <el-form-item label="系统提示词">
          <el-input 
            v-model="form.config.systemPrompt" 
            type="textarea" 
            :rows="4"
            @change="updateConfig('systemPrompt', form.config.systemPrompt)"
          />
        </el-form-item>

        <el-form-item label="启用记忆">
          <el-switch 
            v-model="form.config.enableMemory"
            @change="updateConfig('enableMemory', form.config.enableMemory)"
          />
        </el-form-item>

        <el-form-item v-if="form.config.enableMemory" label="记忆长度">
          <el-input-number 
            v-model="form.config.memoryLength" 
            :min="1" 
            :max="50"
            @change="updateConfig('memoryLength', form.config.memoryLength)"
          />
        </el-form-item>
      </template>

      <template v-else-if="node.type === 'parallel'">
        <el-divider content-position="left">并行配置</el-divider>
        
        <el-form-item label="并行分支数">
          <el-input-number 
            v-model="form.config.branchCount" 
            :min="2" 
            :max="10"
            @change="updateConfig('branchCount', form.config.branchCount)"
          />
        </el-form-item>

        <el-form-item label="等待策略">
          <el-radio-group 
            v-model="form.config.waitStrategy"
            @change="updateConfig('waitStrategy', form.config.waitStrategy)"
          >
            <el-radio label="all">等待全部完成</el-radio>
            <el-radio label="any">等待任意完成</el-radio>
            <el-radio label="majority">等待大多数完成</el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else-if="node.type === 'loop'">
        <el-divider content-position="left">循环配置</el-divider>
        
        <el-form-item label="循环类型">
          <el-radio-group 
            v-model="form.config.loopType"
            @change="updateConfig('loopType', form.config.loopType)"
          >
            <el-radio label="count">计数循环</el-radio>
            <el-radio label="condition">条件循环</el-radio>
            <el-radio label="foreach">遍历循环</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.config.loopType === 'count'" label="循环次数">
          <el-input-number 
            v-model="form.config.count" 
            :min="1" 
            :max="1000"
            @change="updateConfig('count', form.config.count)"
          />
        </el-form-item>

        <el-form-item v-if="form.config.loopType === 'condition'" label="循环条件">
          <el-input 
            v-model="form.config.condition" 
            placeholder="例如: index < 10"
            @change="updateConfig('condition', form.config.condition)"
          />
        </el-form-item>

        <el-form-item v-if="form.config.loopType === 'foreach'" label="遍历数组">
          <el-input 
            v-model="form.config.array" 
            placeholder="例如: input.items"
            @change="updateConfig('array', form.config.array)"
          />
        </el-form-item>

        <el-form-item label="最大迭代次数">
          <el-input-number 
            v-model="form.config.maxIterations" 
            :min="1" 
            :max="10000"
            @change="updateConfig('maxIterations', form.config.maxIterations)"
          />
        </el-form-item>
      </template>

      <!-- 通用配置 -->
      <el-divider content-position="left">高级配置</el-divider>
      
      <el-form-item label="错误处理">
        <el-radio-group 
          v-model="form.config.errorHandling"
          @change="updateConfig('errorHandling', form.config.errorHandling)"
        >
          <el-radio label="stop">停止执行</el-radio>
          <el-radio label="continue">继续执行</el-radio>
          <el-radio label="retry">重试</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.config.errorHandling === 'retry'" label="重试次数">
        <el-input-number 
          v-model="form.config.retryCount" 
          :min="1" 
          :max="10"
          @change="updateConfig('retryCount', form.config.retryCount)"
        />
      </el-form-item>

      <el-form-item label="超时时间">
        <el-input-number 
          v-model="form.config.timeout" 
          :min="1000" 
          :max="300000" 
          :step="1000"
          @change="updateConfig('timeout', form.config.timeout)"
        />
        <span style="margin-left: 8px;">毫秒</span>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import type { WorkflowNode } from '@/composables/useWorkflowDesigner'
import KeyValueEditor from './KeyValueEditor.vue'

// Props
interface Props {
  node: WorkflowNode
}

const props = defineProps<Props>()
const emit = defineEmits(['update'])

// 响应式数据
const form = reactive({
  name: '',
  description: '',
  config: {} as Record<string, any>
})

// 方法
const initForm = () => {
  form.name = props.node.name
  form.description = props.node.config.description || ''
  form.config = { ...props.node.config }
  
  // 设置默认值
  setDefaultValues()
}

const setDefaultValues = () => {
  const defaults = {
    http_request: {
      method: 'GET',
      timeout: 30000,
      headers: {}
    },
    condition: {
      conditionType: 'javascript'
    },
    database_query: {
      datasource: 'default',
      parameters: {}
    },
    parallel: {
      branchCount: 2,
      waitStrategy: 'all'
    },
    loop: {
      loopType: 'count',
      count: 1,
      maxIterations: 1000
    }
  }

  const nodeDefaults = defaults[props.node.type] || {}
  Object.keys(nodeDefaults).forEach(key => {
    if (form.config[key] === undefined) {
      form.config[key] = nodeDefaults[key]
    }
  })

  // 智能体默认配置
  if (isAgentNode(props.node.type)) {
    const agentDefaults = {
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 2000,
      enableMemory: true,
      memoryLength: 10
    }
    Object.keys(agentDefaults).forEach(key => {
      if (form.config[key] === undefined) {
        form.config[key] = agentDefaults[key]
      }
    })
  }

  // 通用默认配置
  if (form.config.errorHandling === undefined) {
    form.config.errorHandling = 'stop'
  }
  if (form.config.timeout === undefined) {
    form.config.timeout = 30000
  }
}

const updateProperty = (key: string, value: any) => {
  emit('update', { [key]: value })
}

const updateConfig = (key: string, value: any) => {
  emit('update', { 
    config: { 
      ...props.node.config, 
      [key]: value 
    } 
  })
}

const getNodeTypeName = (nodeType: string) => {
  const names = {
    start: '开始',
    end: '结束',
    condition: '条件判断',
    parallel: '并行执行',
    loop: '循环',
    http_request: 'HTTP请求',
    database_query: '数据库查询',
    file_operation: '文件操作',
    email_send: '发送邮件',
    webhook: 'Webhook',
    router_agent: '路由智能体',
    planning_agent: '规划智能体',
    customer_service_agent: '客服智能体',
    knowledge_qa_agent: '知识问答',
    text2sql_agent: '数据分析',
    content_creation_agent: '内容创作'
  }
  return names[nodeType] || nodeType
}

const isAgentNode = (nodeType: string) => {
  return nodeType.endsWith('_agent')
}

// 监听节点变化
watch(() => props.node, initForm, { immediate: true, deep: true })

// 生命周期
onMounted(() => {
  initForm()
})
</script>

<style scoped>
.node-properties {
  height: 100%;
  overflow-y: auto;
}

.property-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.property-header h4 {
  margin: 0;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.el-form {
  padding-right: 8px;
}

.el-divider {
  margin: 16px 0 12px 0;
}

.el-form-item {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
}

:deep(.el-input__inner),
:deep(.el-textarea__inner) {
  font-size: 12px;
}

:deep(.el-slider) {
  margin: 8px 0;
}
</style>
