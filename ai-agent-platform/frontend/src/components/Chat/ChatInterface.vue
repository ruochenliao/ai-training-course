<template>
  <div class="chat-interface">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="agent-info">
        <el-avatar :size="40" :src="currentAgent.avatar">
          <el-icon><Robot /></el-icon>
        </el-avatar>
        <div class="agent-details">
          <h3>{{ currentAgent.name }}</h3>
          <p class="agent-status" :class="connectionStatus">
            {{ connectionStatusText }}
          </p>
        </div>
      </div>
      
      <div class="chat-actions">
        <el-dropdown @command="handleAgentSelect">
          <el-button type="primary" size="small">
            切换智能体 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-for="agent in availableAgents" 
                :key="agent.type"
                :command="agent.type"
                :disabled="agent.type === currentAgent.type"
              >
                <el-icon>{{ agent.icon }}</el-icon>
                {{ agent.name }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <el-button size="small" @click="clearChat">
          <el-icon><Delete /></el-icon>
          清空对话
        </el-button>
      </div>
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message-item"
        :class="message.sender"
      >
        <div class="message-avatar">
          <el-avatar :size="32" v-if="message.sender === 'user'">
            <el-icon><User /></el-icon>
          </el-avatar>
          <el-avatar :size="32" v-else>
            <el-icon><Robot /></el-icon>
          </el-avatar>
        </div>
        
        <div class="message-content">
          <div class="message-header">
            <span class="sender-name">
              {{ message.sender === 'user' ? '我' : currentAgent.name }}
            </span>
            <span class="message-time">
              {{ formatTime(message.timestamp) }}
            </span>
          </div>
          
          <div class="message-body">
            <div v-if="message.type === 'text'" class="text-message">
              {{ message.content }}
            </div>
            
            <div v-else-if="message.type === 'thinking'" class="thinking-message">
              <el-icon class="thinking-icon"><Loading /></el-icon>
              {{ message.content }}
            </div>
            
            <div v-else-if="message.type === 'error'" class="error-message">
              <el-icon><Warning /></el-icon>
              {{ message.content }}
            </div>
            
            <!-- 智能体响应的额外信息 -->
            <div v-if="message.sender === 'agent' && message.metadata" class="message-metadata">
              <div v-if="message.metadata.confidence" class="confidence">
                置信度: {{ (message.metadata.confidence * 100).toFixed(1) }}%
              </div>
              
              <div v-if="message.metadata.sources && message.metadata.sources.length > 0" class="sources">
                <el-collapse size="small">
                  <el-collapse-item title="参考来源" name="sources">
                    <div v-for="source in message.metadata.sources" :key="source.id" class="source-item">
                      <strong>{{ source.title }}</strong>
                      <p>{{ source.content }}</p>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入提示 -->
      <div v-if="isTyping" class="typing-indicator">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        {{ currentAgent.name }}正在输入...
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题..."
          @keydown.enter.exact="sendMessage"
          @keydown.enter.shift.exact.prevent="inputMessage += '\n'"
          :disabled="!isConnected || isSending"
          resize="none"
        />
        
        <div class="input-actions">
          <el-button 
            type="primary" 
            @click="sendMessage"
            :loading="isSending"
            :disabled="!inputMessage.trim() || !isConnected"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
      
      <!-- 快捷操作 -->
      <div class="quick-actions">
        <el-button 
          v-for="action in quickActions" 
          :key="action.text"
          size="small" 
          type="info" 
          plain
          @click="inputMessage = action.text"
        >
          {{ action.text }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Robot, User, ArrowDown, Delete, Loading, Warning, Promotion 
} from '@element-plus/icons-vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useUserStore } from '@/stores/user'

// 接口定义
interface Message {
  id: string
  content: string
  sender: 'user' | 'agent'
  type: 'text' | 'thinking' | 'error'
  timestamp: Date
  metadata?: {
    confidence?: number
    sources?: Array<{
      id: string
      title: string
      content: string
    }>
  }
}

interface Agent {
  type: string
  name: string
  description: string
  avatar?: string
  icon: string
}

// 响应式数据
const userStore = useUserStore()
const inputMessage = ref('')
const messages = ref<Message[]>([])
const isSending = ref(false)
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement>()

// 可用智能体
const availableAgents: Agent[] = [
  {
    type: 'customer_service',
    name: '智能客服',
    description: '处理客户咨询、投诉、售后等问题',
    icon: 'service'
  },
  {
    type: 'knowledge_qa',
    name: '知识问答',
    description: '基于知识库回答专业问题',
    icon: 'question'
  },
  {
    type: 'text2sql',
    name: '数据分析',
    description: '将自然语言转换为SQL查询',
    icon: 'data-analysis'
  },
  {
    type: 'content_creation',
    name: '内容创作',
    description: '创作各类文案、文章、营销内容',
    icon: 'edit'
  }
]

// 当前智能体
const currentAgent = ref<Agent>(availableAgents[0])

// 快捷操作
const quickActions = computed(() => {
  const actions = {
    customer_service: [
      { text: '我想咨询产品信息' },
      { text: '我遇到了技术问题' },
      { text: '我要投诉' }
    ],
    knowledge_qa: [
      { text: '什么是人工智能？' },
      { text: '如何使用这个系统？' },
      { text: '有什么新功能？' }
    ],
    text2sql: [
      { text: '查询所有用户信息' },
      { text: '统计订单数量' },
      { text: '分析销售趋势' }
    ],
    content_creation: [
      { text: '写一篇关于AI的文章' },
      { text: '创作产品宣传文案' },
      { text: '生成社交媒体内容' }
    ]
  }
  return actions[currentAgent.value.type] || []
})

// WebSocket连接
const { 
  isConnected, 
  connectionStatus, 
  connect, 
  disconnect, 
  sendMessage: sendWebSocketMessage 
} = useWebSocket()

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '在线'
    case 'connecting': return '连接中...'
    case 'disconnected': return '离线'
    case 'error': return '连接错误'
    default: return '未知状态'
  }
})

// 方法
const handleAgentSelect = (agentType: string) => {
  const agent = availableAgents.find(a => a.type === agentType)
  if (agent) {
    currentAgent.value = agent
    
    // 发送智能体选择消息
    sendWebSocketMessage({
      type: 'agent_select',
      data: {
        agent_type: agentType,
        session_id: `session_${userStore.userInfo?.id}`
      }
    })
    
    // 添加系统消息
    addMessage({
      id: `system_${Date.now()}`,
      content: `已切换到${agent.name}`,
      sender: 'agent',
      type: 'text',
      timestamp: new Date()
    })
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || !isConnected.value || isSending.value) {
    return
  }

  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''
  isSending.value = true

  // 添加用户消息
  const userMessage: Message = {
    id: `user_${Date.now()}`,
    content: messageContent,
    sender: 'user',
    type: 'text',
    timestamp: new Date()
  }
  addMessage(userMessage)

  try {
    // 发送WebSocket消息
    await sendWebSocketMessage({
      type: 'chat_message',
      data: {
        content: messageContent,
        agent_type: currentAgent.value.type,
        session_id: `session_${userStore.userInfo?.id}`,
        metadata: {}
      }
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
    
    // 添加错误消息
    addMessage({
      id: `error_${Date.now()}`,
      content: '消息发送失败，请重试',
      sender: 'agent',
      type: 'error',
      timestamp: new Date()
    })
  } finally {
    isSending.value = false
  }
}

const addMessage = (message: Message) => {
  messages.value.push(message)
  nextTick(() => {
    scrollToBottom()
  })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const clearChat = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// WebSocket消息处理
const handleWebSocketMessage = (event: any) => {
  const { type, data } = event

  switch (type) {
    case 'chat_response':
      addMessage({
        id: data.message_id,
        content: data.content,
        sender: 'agent',
        type: 'text',
        timestamp: new Date(data.timestamp),
        metadata: {
          confidence: data.confidence,
          sources: data.sources
        }
      })
      isTyping.value = false
      break

    case 'agent_thinking':
      isTyping.value = true
      break

    case 'agent_selected':
      ElMessage.success(data.message)
      break

    case 'error':
      addMessage({
        id: `error_${Date.now()}`,
        content: data.message,
        sender: 'agent',
        type: 'error',
        timestamp: new Date()
      })
      isTyping.value = false
      break
  }
}

// 生命周期
onMounted(async () => {
  // 连接WebSocket
  await connect(`/api/v1/ws/chat/${userStore.userInfo?.id}`, handleWebSocketMessage)
  
  // 添加欢迎消息
  addMessage({
    id: 'welcome',
    content: `您好！我是${currentAgent.value.name}，很高兴为您服务。请问有什么可以帮助您的吗？`,
    sender: 'agent',
    type: 'text',
    timestamp: new Date()
  })
})

onUnmounted(() => {
  disconnect()
})

// 监听当前智能体变化
watch(currentAgent, (newAgent) => {
  // 可以在这里添加智能体切换的逻辑
})
</script>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-details h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.agent-status {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #909399;
}

.agent-status.connected {
  color: #67c23a;
}

.agent-status.connecting {
  color: #e6a23c;
}

.agent-status.disconnected,
.agent-status.error {
  color: #f56c6c;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  min-width: 200px;
}

.message-item.user .message-content {
  text-align: right;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #909399;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.message-body {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-item.user .message-body {
  background: #409eff;
  color: white;
}

.thinking-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-style: italic;
}

.thinking-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-message {
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-metadata {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.confidence {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.source-item {
  margin-bottom: 8px;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 4px;
}

.source-item strong {
  display: block;
  margin-bottom: 4px;
  color: #303133;
}

.source-item p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 20px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container .el-textarea {
  flex: 1;
}

.quick-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
