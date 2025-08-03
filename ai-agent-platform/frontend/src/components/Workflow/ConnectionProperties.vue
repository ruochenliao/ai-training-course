<template>
  <div class="connection-properties">
    <div class="property-header">
      <h4>连接配置</h4>
      <el-tag size="small" type="info">{{ connection.from }} → {{ connection.to }}</el-tag>
    </div>

    <el-form :model="form" label-width="80px" size="small">
      <el-form-item label="连接名称">
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

      <el-form-item label="条件">
        <el-input 
          v-model="form.condition" 
          placeholder="连接触发条件（可选）"
          @change="updateProperty('condition', form.condition)"
        />
        <div class="form-help">
          例如: output.status === 'success'
        </div>
      </el-form-item>

      <el-form-item label="优先级">
        <el-input-number 
          v-model="form.priority" 
          :min="1" 
          :max="100"
          @change="updateProperty('priority', form.priority)"
        />
        <div class="form-help">
          数值越大优先级越高
        </div>
      </el-form-item>

      <el-form-item label="数据转换">
        <el-switch 
          v-model="form.enableTransform"
          @change="updateConfig('enableTransform', form.enableTransform)"
        />
      </el-form-item>

      <template v-if="form.enableTransform">
        <el-form-item label="转换脚本">
          <el-input 
            v-model="form.transformScript" 
            type="textarea" 
            :rows="4"
            placeholder="JavaScript代码，用于转换数据"
            @change="updateConfig('transformScript', form.transformScript)"
          />
          <div class="form-help">
            使用 input 变量访问输入数据，返回转换后的数据
          </div>
        </el-form-item>
      </template>

      <el-form-item label="延迟执行">
        <el-input-number 
          v-model="form.delay" 
          :min="0" 
          :max="60000" 
          :step="100"
          @change="updateConfig('delay', form.delay)"
        />
        <span style="margin-left: 8px;">毫秒</span>
      </el-form-item>

      <el-form-item label="重试配置">
        <el-switch 
          v-model="form.enableRetry"
          @change="updateConfig('enableRetry', form.enableRetry)"
        />
      </el-form-item>

      <template v-if="form.enableRetry">
        <el-form-item label="重试次数">
          <el-input-number 
            v-model="form.retryCount" 
            :min="1" 
            :max="10"
            @change="updateConfig('retryCount', form.retryCount)"
          />
        </el-form-item>

        <el-form-item label="重试间隔">
          <el-input-number 
            v-model="form.retryInterval" 
            :min="100" 
            :max="10000" 
            :step="100"
            @change="updateConfig('retryInterval', form.retryInterval)"
          />
          <span style="margin-left: 8px;">毫秒</span>
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, onMounted } from 'vue'
import type { WorkflowConnection } from '@/composables/useWorkflowDesigner'

// Props
interface Props {
  connection: WorkflowConnection
}

const props = defineProps<Props>()
const emit = defineEmits(['update'])

// 响应式数据
const form = reactive({
  name: '',
  description: '',
  condition: '',
  priority: 1,
  enableTransform: false,
  transformScript: '',
  delay: 0,
  enableRetry: false,
  retryCount: 3,
  retryInterval: 1000
})

// 方法
const initForm = () => {
  form.name = props.connection.config?.name || ''
  form.description = props.connection.config?.description || ''
  form.condition = props.connection.condition || ''
  form.priority = props.connection.config?.priority || 1
  form.enableTransform = props.connection.config?.enableTransform || false
  form.transformScript = props.connection.config?.transformScript || ''
  form.delay = props.connection.config?.delay || 0
  form.enableRetry = props.connection.config?.enableRetry || false
  form.retryCount = props.connection.config?.retryCount || 3
  form.retryInterval = props.connection.config?.retryInterval || 1000
}

const updateProperty = (key: string, value: any) => {
  if (key === 'condition') {
    emit('update', { condition: value })
  } else {
    emit('update', { 
      config: { 
        ...props.connection.config, 
        [key]: value 
      } 
    })
  }
}

const updateConfig = (key: string, value: any) => {
  emit('update', { 
    config: { 
      ...props.connection.config, 
      [key]: value 
    } 
  })
}

// 监听连接变化
watch(() => props.connection, initForm, { immediate: true, deep: true })

// 生命周期
onMounted(() => {
  initForm()
})
</script>

<style scoped>
.connection-properties {
  height: 100%;
  overflow-y: auto;
}

.property-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.property-header h4 {
  margin: 0;
  color: #303133;
}

.el-form {
  padding-right: 8px;
}

.el-form-item {
  margin-bottom: 12px;
}

.form-help {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
}

:deep(.el-input__inner),
:deep(.el-textarea__inner) {
  font-size: 12px;
}
</style>
