<template>
  <div class="plugin-details">
    <!-- 插件基本信息 -->
    <div class="plugin-header">
      <div class="plugin-icon">
        <el-icon>{{ getPluginIcon(plugin.type) }}</el-icon>
      </div>
      <div class="plugin-info">
        <h2>{{ plugin.name }}</h2>
        <p>{{ plugin.description }}</p>
        <div class="plugin-meta">
          <el-tag :type="getStatusType(plugin.status)">
            {{ getStatusText(plugin.status) }}
          </el-tag>
          <span class="version">v{{ plugin.version }}</span>
          <span class="author">by {{ plugin.author }}</span>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="插件名称">
            {{ plugin.name }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            {{ plugin.version }}
          </el-descriptions-item>
          <el-descriptions-item label="作者">
            {{ plugin.author }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            {{ getTypeText(plugin.type) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(plugin.status)">
              {{ getStatusText(plugin.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="权限">
            <div class="permissions-list">
              <el-tag 
                v-for="permission in plugin.permissions" 
                :key="permission"
                size="small"
                type="warning"
              >
                {{ permission }}
              </el-tag>
              <span v-if="plugin.permissions.length === 0" class="no-data">无特殊权限</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="依赖" :span="2">
            <div class="dependencies-list">
              <el-tag 
                v-for="dependency in plugin.dependencies" 
                :key="dependency"
                size="small"
                type="info"
              >
                {{ dependency }}
              </el-tag>
              <span v-if="plugin.dependencies.length === 0" class="no-data">无依赖</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <div class="tags-list">
              <el-tag 
                v-for="tag in plugin.tags" 
                :key="tag"
                size="small"
              >
                {{ tag }}
              </el-tag>
              <span v-if="plugin.tags.length === 0" class="no-data">无标签</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ plugin.description }}
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <!-- 配置信息 -->
      <el-tab-pane label="配置" name="config">
        <div class="config-section">
          <div class="section-header">
            <h4>当前配置</h4>
            <el-button size="small" type="primary" @click="$emit('configure', plugin)">
              <el-icon><Setting /></el-icon>
              编辑配置
            </el-button>
          </div>
          
          <div v-if="Object.keys(plugin.config).length > 0" class="config-content">
            <pre class="config-json">{{ JSON.stringify(plugin.config, null, 2) }}</pre>
          </div>
          <div v-else class="no-config">
            <el-empty description="暂无配置信息" />
          </div>
        </div>
      </el-tab-pane>

      <!-- 操作面板 -->
      <el-tab-pane label="操作" name="actions" v-if="isToolPlugin">
        <div class="actions-section">
          <div class="section-header">
            <h4>可用操作</h4>
            <el-button size="small" @click="refreshActions" :loading="actionsLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div v-if="availableActions.length > 0" class="actions-list">
            <div 
              v-for="action in availableActions" 
              :key="action"
              class="action-item"
            >
              <div class="action-info">
                <h5>{{ action }}</h5>
                <p>{{ getActionDescription(action) }}</p>
              </div>
              <el-button size="small" @click="executeAction(action)">
                执行
              </el-button>
            </div>
          </div>
          <div v-else class="no-actions">
            <el-empty description="暂无可用操作" />
          </div>
        </div>
      </el-tab-pane>

      <!-- 日志 -->
      <el-tab-pane label="日志" name="logs">
        <div class="logs-section">
          <div class="section-header">
            <h4>插件日志</h4>
            <div class="log-controls">
              <el-select v-model="logLevel" size="small" style="width: 100px;">
                <el-option label="全部" value="all" />
                <el-option label="错误" value="error" />
                <el-option label="警告" value="warning" />
                <el-option label="信息" value="info" />
              </el-select>
              <el-button size="small" @click="refreshLogs" :loading="logsLoading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
          
          <div class="logs-container">
            <div 
              v-for="log in filteredLogs" 
              :key="log.id"
              class="log-entry"
              :class="`log-${log.level}`"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            
            <div v-if="filteredLogs.length === 0" class="no-logs">
              <el-empty description="暂无日志记录" />
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 执行操作对话框 -->
    <el-dialog v-model="showActionDialog" :title="`执行操作: ${selectedAction}`" width="500px">
      <el-form :model="actionForm" label-width="100px">
        <el-form-item label="操作参数">
          <el-input 
            v-model="actionForm.parameters" 
            type="textarea" 
            :rows="6"
            placeholder="请输入JSON格式的参数"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showActionDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmExecuteAction" :loading="executing">
          执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog v-model="showResultDialog" title="执行结果" width="600px">
      <div class="result-content">
        <div v-if="executionResult.success" class="result-success">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>执行成功</span>
        </div>
        <div v-else class="result-error">
          <el-icon><CircleCloseFilled /></el-icon>
          <span>执行失败</span>
        </div>
        
        <div class="result-data">
          <h4>返回数据:</h4>
          <pre>{{ JSON.stringify(executionResult, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Refresh, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'

// Props
interface Props {
  plugin: {
    name: string
    version: string
    description: string
    author: string
    type: string
    status: string
    dependencies: string[]
    permissions: string[]
    config: Record<string, any>
    tags: string[]
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['configure', 'execute'])

// 响应式数据
const activeTab = ref('info')
const actionsLoading = ref(false)
const logsLoading = ref(false)
const executing = ref(false)
const showActionDialog = ref(false)
const showResultDialog = ref(false)
const selectedAction = ref('')
const logLevel = ref('all')

const availableActions = ref<string[]>([])
const logs = ref<any[]>([])
const executionResult = ref<any>({})

const actionForm = reactive({
  parameters: '{}'
})

// 计算属性
const isToolPlugin = computed(() => props.plugin.type === 'tool')

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return logs.value
  }
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const getPluginIcon = (type: string) => {
  const icons = {
    agent: 'user',
    tool: 'tools',
    integration: 'link',
    middleware: 'connection',
    workflow: 'share',
    ui_component: 'grid'
  }
  return icons[type] || 'box'
}

const getStatusType = (status: string) => {
  const types = {
    active: 'success',
    inactive: 'info',
    error: 'danger',
    loading: 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts = {
    active: '已激活',
    inactive: '未激活',
    error: '错误',
    loading: '加载中'
  }
  return texts[status] || '未知'
}

const getTypeText = (type: string) => {
  const texts = {
    agent: '智能体',
    tool: '工具',
    integration: '集成',
    middleware: '中间件',
    workflow: '工作流',
    ui_component: 'UI组件'
  }
  return texts[type] || type
}

const getActionDescription = (action: string) => {
  const descriptions = {
    send_email: '发送邮件',
    send_bulk_email: '批量发送邮件',
    test_connection: '测试连接',
    execute_query: '执行查询',
    upload_file: '上传文件',
    download_file: '下载文件'
  }
  return descriptions[action] || '执行操作'
}

const refreshActions = async () => {
  if (!isToolPlugin.value) return
  
  actionsLoading.value = true
  try {
    // 模拟获取可用操作
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 根据插件类型设置可用操作
    if (props.plugin.name === 'email_sender') {
      availableActions.value = ['send_email', 'send_bulk_email', 'test_connection']
    } else {
      availableActions.value = ['execute', 'test', 'status']
    }
  } catch (error) {
    ElMessage.error('获取可用操作失败')
  } finally {
    actionsLoading.value = false
  }
}

const executeAction = (action: string) => {
  selectedAction.value = action
  actionForm.parameters = '{}'
  showActionDialog.value = true
}

const confirmExecuteAction = async () => {
  executing.value = true
  try {
    let parameters = {}
    
    if (actionForm.parameters.trim()) {
      try {
        parameters = JSON.parse(actionForm.parameters)
      } catch (error) {
        ElMessage.error('参数格式错误，请输入有效的JSON')
        return
      }
    }
    
    const result = await emit('execute', selectedAction.value, parameters)
    executionResult.value = result
    showActionDialog.value = false
    showResultDialog.value = true
    
  } catch (error) {
    ElMessage.error('执行操作失败')
  } finally {
    executing.value = false
  }
}

const refreshLogs = async () => {
  logsLoading.value = true
  try {
    // 模拟获取插件日志
    await new Promise(resolve => setTimeout(resolve, 500))
    
    logs.value = [
      {
        id: 1,
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        level: 'info',
        message: '插件初始化成功'
      },
      {
        id: 2,
        timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
        level: 'info',
        message: '配置加载完成'
      },
      {
        id: 3,
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        level: 'warning',
        message: '连接超时，正在重试'
      },
      {
        id: 4,
        timestamp: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
        level: 'error',
        message: '操作执行失败: 权限不足'
      }
    ]
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    logsLoading.value = false
  }
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  if (isToolPlugin.value) {
    refreshActions()
  }
  refreshLogs()
})
</script>

<style scoped>
.plugin-details {
  padding: 20px 0;
}

.plugin-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.plugin-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  color: white;
  font-size: 24px;
}

.plugin-info h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #303133;
}

.plugin-info p {
  margin: 0 0 12px 0;
  color: #606266;
  line-height: 1.5;
}

.plugin-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version, .author {
  font-size: 14px;
  color: #909399;
}

.permissions-list,
.dependencies-list,
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.no-data {
  color: #909399;
  font-style: italic;
}

.config-section,
.actions-section,
.logs-section {
  padding: 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  color: #303133;
}

.config-content {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
}

.config-json {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
}

.no-config,
.no-actions,
.no-logs {
  text-align: center;
  padding: 40px 20px;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}

.action-info h5 {
  margin: 0 0 4px 0;
  color: #303133;
}

.action-info p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}

.log-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-entry {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.log-time {
  color: #888;
  min-width: 160px;
}

.log-level {
  min-width: 60px;
  font-weight: bold;
}

.log-message {
  flex: 1;
  color: #e4e7ed;
}

.log-error .log-level {
  color: #f56c6c;
}

.log-warning .log-level {
  color: #e6a23c;
}

.log-info .log-level {
  color: #67c23a;
}

.result-content {
  padding: 16px 0;
}

.result-success,
.result-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 500;
}

.result-success {
  color: #67c23a;
}

.result-error {
  color: #f56c6c;
}

.result-data h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.result-data pre {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 12px;
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
}
</style>
