<template>
  <div class="chat-container">
    <!-- 侧边栏 - 会话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <h3>对话记录</h3>
        <el-button type="primary" size="small" @click="showAgentSelector = true">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>

      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="selectSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-time">{{ formatTime(session.updated_at) }}</div>
          <el-button
            type="text"
            size="small"
            class="delete-btn"
            @click.stop="deleteSession(session.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>

        <div v-if="sessions.length === 0" class="empty-sessions">
          <el-empty description="暂无对话记录" :image-size="60" />
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <div v-if="!currentSessionId" class="welcome-screen">
        <el-icon size="80" color="#409eff">
          <ChatDotRound />
        </el-icon>
        <h3>欢迎使用智能体对话</h3>
        <p>选择一个对话或创建新的对话开始聊天</p>
        <el-button type="primary" @click="showAgentSelector = true">
          开始新对话
        </el-button>
      </div>

      <template v-else>
        <!-- 智能体信息 -->
        <div class="chat-header" v-if="currentAgent">
          <div class="agent-info">
            <el-avatar :src="currentAgent.avatar_url" :size="40">
              {{ currentAgent.name?.charAt(0) }}
            </el-avatar>
            <div class="agent-details">
              <h4>{{ currentAgent.name }}</h4>
              <p>{{ currentAgent.description }}</p>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="message-list" ref="messageListRef">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="message.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="message.role === 'assistant'" :src="currentAgent?.avatar_url" :size="32">
                {{ currentAgent?.name?.charAt(0) }}
              </el-avatar>
              <el-avatar v-else :size="32">
                {{ userStore.userInfo?.username?.charAt(0) }}
              </el-avatar>
            </div>

            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>

          <!-- 正在输入指示器 -->
          <div v-if="isTyping" class="message-item assistant typing">
            <div class="message-avatar">
              <el-avatar :src="currentAgent?.avatar_url" :size="32">
                {{ currentAgent?.name?.charAt(0) }}
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            @keydown.enter.exact="handleSendMessage"
            @keydown.enter.shift.exact.prevent="inputMessage += '\n'"
            :disabled="isTyping"
          />
          <div class="input-actions">
            <el-button
              type="primary"
              @click="handleSendMessage"
              :loading="isTyping"
              :disabled="!inputMessage.trim()"
            >
              发送
            </el-button>
          </div>
        </div>
      </template>
    </div>

    <!-- 智能体选择对话框 -->
    <el-dialog
      v-model="showAgentSelector"
      title="选择智能体"
      width="600px"
    >
      <div class="agent-selector">
        <el-input
          v-model="agentSearchKeyword"
          placeholder="搜索智能体..."
          clearable
          style="margin-bottom: 16px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="agent-list">
          <div
            v-for="agent in filteredAgents"
            :key="agent.id"
            class="agent-item"
            @click="createSessionWithAgent(agent)"
          >
            <el-avatar :src="agent.avatar_url" :size="40">
              {{ agent.name?.charAt(0) }}
            </el-avatar>
            <div class="agent-info">
              <h4>{{ agent.name }}</h4>
              <p>{{ agent.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatDotRound, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { agentApi, type Agent } from '@/api/agent'
import { formatTime } from '@/utils'

const userStore = useUserStore()

// 响应式数据
const messageListRef = ref<HTMLElement>()
const sessions = ref<any[]>([])
const currentSessionId = ref<number | null>(null)
const currentAgent = ref<Agent | null>(null)
const messages = ref<any[]>([])
const inputMessage = ref('')
const isTyping = ref(false)
const showAgentSelector = ref(false)
const agentSearchKeyword = ref('')
const availableAgents = ref<Agent[]>([])

// 计算属性
const filteredAgents = computed(() => {
  if (!agentSearchKeyword.value) return availableAgents.value
  return availableAgents.value.filter(agent =>
    agent.name.toLowerCase().includes(agentSearchKeyword.value.toLowerCase()) ||
    agent.description?.toLowerCase().includes(agentSearchKeyword.value.toLowerCase())
  )
})

// 获取智能体列表
const fetchAgents = async () => {
  try {
    const response = await agentApi.getList()
    availableAgents.value = response.data
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  }
}

// 模拟会话数据
const fetchSessions = async () => {
  // TODO: 实现真实的会话API调用
  sessions.value = [
    {
      id: 1,
      title: '与AI助手的对话',
      agent_id: 1,
      updated_at: new Date().toISOString()
    }
  ]
}

// 创建与指定智能体的会话
const createSessionWithAgent = async (agent: Agent) => {
  try {
    // TODO: 实现真实的会话创建API
    const newSession = {
      id: Date.now(),
      title: `与${agent.name}的对话`,
      agent_id: agent.id,
      updated_at: new Date().toISOString()
    }

    sessions.value.unshift(newSession)
    currentAgent.value = agent
    currentSessionId.value = newSession.id
    messages.value = []
    showAgentSelector.value = false

    ElMessage.success('新对话创建成功')
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败')
  }
}

// 选择会话
const selectSession = async (sessionId: number) => {
  currentSessionId.value = sessionId

  // 获取会话对应的智能体
  const session = sessions.value.find(s => s.id === sessionId)
  if (session) {
    try {
      const response = await agentApi.getDetail(session.agent_id)
      currentAgent.value = response.data
    } catch (error) {
      console.error('获取智能体信息失败:', error)
    }
  }

  // TODO: 获取会话消息
  messages.value = [
    {
      id: '1',
      role: 'assistant',
      content: '您好！我是您的AI助手，有什么可以帮助您的吗？',
      timestamp: Date.now() - 60000
    }
  ]

  scrollToBottom()
}

// 删除会话
const deleteSession = async (sessionId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除', {
      type: 'warning'
    })

    sessions.value = sessions.value.filter(s => s.id !== sessionId)

    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
      currentAgent.value = null
    }

    ElMessage.success('对话删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || !currentAgent.value) return

  const messageText = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  const userMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: messageText,
    timestamp: Date.now()
  }

  messages.value.push(userMessage)
  scrollToBottom()

  // 显示正在输入状态
  isTyping.value = true

  try {
    // 模拟AI回复
    setTimeout(() => {
      const aiResponse = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `我收到了您的消息："${messageText}"。这是一个模拟回复，实际的AI回复功能正在开发中。`,
        timestamp: Date.now()
      }

      messages.value.push(aiResponse)
      scrollToBottom()
      isTyping.value = false
    }, 1000 + Math.random() * 2000)

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
    isTyping.value = false
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 格式化消息内容
const formatMessage = (content: string) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

onMounted(() => {
  fetchAgents()
  fetchSessions()
})</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
  background: #f5f5f5;
}

.chat-sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .session-list {
    flex: 1;
    overflow-y: auto;

    .session-item {
      padding: 12px 16px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      position: relative;
      transition: background-color 0.2s;

      &:hover {
        background: #f5f7fa;

        .delete-btn {
          opacity: 1;
        }
      }

      &.active {
        background: #e6f7ff;
        border-right: 3px solid #409eff;
      }

      .session-title {
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .session-time {
        font-size: 12px;
        color: #909399;
      }

      .delete-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        opacity: 0;
        transition: opacity 0.2s;
      }
    }

    .empty-sessions {
      padding: 40px 20px;
      text-align: center;
    }
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;

  .welcome-screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;

    h3 {
      margin: 20px 0 10px;
      color: #303133;
      font-size: 20px;
    }

    p {
      color: #909399;
      font-size: 14px;
      margin-bottom: 24px;
    }
  }

  .chat-header {
    padding: 16px 24px;
    border-bottom: 1px solid #e4e7ed;

    .agent-info {
      display: flex;
      align-items: center;
      gap: 12px;

      .agent-details {
        h4 {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 600;
        }

        p {
          margin: 0;
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }

  .message-list {
    flex: 1;
    padding: 24px;
    overflow-y: auto;

    .message-item {
      display: flex;
      margin-bottom: 24px;

      &.user {
        flex-direction: row-reverse;

        .message-content {
          background: #409eff;
          color: white;
          margin-right: 12px;
          margin-left: 0;
        }
      }

      &.assistant {
        .message-content {
          background: #f5f5f5;
          margin-left: 12px;
        }
      }

      .message-avatar {
        flex-shrink: 0;
      }

      .message-content {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 12px;

        .message-text {
          line-height: 1.5;
          word-wrap: break-word;
        }

        .message-time {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.7);
          margin-top: 8px;
        }
      }

      &.assistant .message-content .message-time {
        color: #909399;
      }

      &.typing .message-content {
        padding: 16px;

        .typing-indicator {
          display: flex;
          gap: 4px;

          span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #409eff;
            animation: typing 1.4s infinite ease-in-out;

            &:nth-child(1) { animation-delay: -0.32s; }
            &:nth-child(2) { animation-delay: -0.16s; }
          }
        }
      }
    }
  }

  .chat-input {
    padding: 16px 24px;
    border-top: 1px solid #e4e7ed;

    .input-actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 12px;
    }
  }
}

.agent-selector {
  .agent-list {
    max-height: 400px;
    overflow-y: auto;

    .agent-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background: #f5f7fa;
      }

      .agent-info {
        flex: 1;

        h4 {
          margin: 0 0 4px 0;
          font-size: 14px;
          font-weight: 500;
        }

        p {
          margin: 0;
          font-size: 12px;
          color: #909399;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>
