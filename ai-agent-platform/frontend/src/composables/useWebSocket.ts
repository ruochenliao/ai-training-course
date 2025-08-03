/**
 * WebSocket连接管理
 */

import { ref, computed, readonly, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp?: string
  user_id?: string
  session_id?: string
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connectionStatus = ref<ConnectionStatus>('disconnected')
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectInterval = ref<number | null>(null)
  
  let messageHandler: ((message: WebSocketMessage) => void) | null = null
  let currentUrl = ''

  const isConnected = computed(() => connectionStatus.value === 'connected')

  /**
   * 连接WebSocket
   */
  const connect = async (url: string, onMessage?: (message: WebSocketMessage) => void): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        // 如果已经连接，先断开
        if (ws.value) {
          disconnect()
        }

        currentUrl = url
        messageHandler = onMessage || null
        connectionStatus.value = 'connecting'

        // 构建完整的WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//${host}${url}`

        ws.value = new WebSocket(wsUrl)

        ws.value.onopen = () => {
          connectionStatus.value = 'connected'
          reconnectAttempts.value = 0
          console.log('WebSocket连接已建立:', wsUrl)
          resolve()
        }

        ws.value.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            console.log('收到WebSocket消息:', message)
            
            if (messageHandler) {
              messageHandler(message)
            }
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }

        ws.value.onclose = (event) => {
          console.log('WebSocket连接已关闭:', event.code, event.reason)
          connectionStatus.value = 'disconnected'
          ws.value = null

          // 如果不是主动关闭，尝试重连
          if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
            scheduleReconnect()
          }
        }

        ws.value.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          connectionStatus.value = 'error'
          reject(error)
        }

      } catch (error) {
        connectionStatus.value = 'error'
        reject(error)
      }
    })
  }

  /**
   * 断开WebSocket连接
   */
  const disconnect = () => {
    if (reconnectInterval.value) {
      clearTimeout(reconnectInterval.value)
      reconnectInterval.value = null
    }

    if (ws.value) {
      ws.value.close(1000, 'Client disconnect')
      ws.value = null
    }
    
    connectionStatus.value = 'disconnected'
    reconnectAttempts.value = 0
  }

  /**
   * 发送消息
   */
  const sendMessage = async (message: WebSocketMessage): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!ws.value || connectionStatus.value !== 'connected') {
        reject(new Error('WebSocket未连接'))
        return
      }

      try {
        const messageStr = JSON.stringify(message)
        ws.value.send(messageStr)
        console.log('发送WebSocket消息:', message)
        resolve()
      } catch (error) {
        console.error('发送WebSocket消息失败:', error)
        reject(error)
      }
    })
  }

  /**
   * 安排重连
   */
  const scheduleReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      ElMessage.error('WebSocket连接失败，请刷新页面重试')
      return
    }

    reconnectAttempts.value++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000) // 指数退避，最大30秒

    console.log(`WebSocket重连中... (${reconnectAttempts.value}/${maxReconnectAttempts})`)
    
    reconnectInterval.value = window.setTimeout(async () => {
      try {
        await connect(currentUrl, messageHandler)
      } catch (error) {
        console.error('WebSocket重连失败:', error)
        scheduleReconnect()
      }
    }, delay)
  }

  /**
   * 手动重连
   */
  const reconnect = async (): Promise<void> => {
    disconnect()
    reconnectAttempts.value = 0
    return connect(currentUrl, messageHandler)
  }

  /**
   * 发送心跳
   */
  const sendHeartbeat = () => {
    if (isConnected.value) {
      sendMessage({
        type: 'heartbeat',
        data: { timestamp: new Date().toISOString() }
      }).catch(console.error)
    }
  }

  // 定期发送心跳
  const heartbeatInterval = setInterval(sendHeartbeat, 30000) // 30秒

  // 组件卸载时清理
  onUnmounted(() => {
    clearInterval(heartbeatInterval)
    disconnect()
  })

  return {
    ws: readonly(ws),
    connectionStatus: readonly(connectionStatus),
    isConnected,
    reconnectAttempts: readonly(reconnectAttempts),
    connect,
    disconnect,
    sendMessage,
    reconnect
  }
}

/**
 * 聊天WebSocket连接
 */
export function useChatWebSocket(userId: string) {
  const { connect, disconnect, sendMessage, ...rest } = useWebSocket()

  const connectChat = (onMessage?: (message: WebSocketMessage) => void) => {
    return connect(`/api/v1/ws/chat/${userId}`, onMessage)
  }

  const sendChatMessage = (content: string, agentType: string, sessionId?: string) => {
    return sendMessage({
      type: 'chat_message',
      data: {
        content,
        agent_type: agentType,
        session_id: sessionId || `session_${userId}`,
        metadata: {}
      }
    })
  }

  const selectAgent = (agentType: string, sessionId?: string) => {
    return sendMessage({
      type: 'agent_select',
      data: {
        agent_type: agentType,
        session_id: sessionId || `session_${userId}`
      }
    })
  }

  const getChatHistory = (sessionId?: string, limit?: number) => {
    return sendMessage({
      type: 'chat_history',
      data: {
        session_id: sessionId || `session_${userId}`,
        limit: limit || 50
      }
    })
  }

  return {
    ...rest,
    connectChat,
    sendChatMessage,
    selectAgent,
    getChatHistory,
    disconnect
  }
}

/**
 * 工作流WebSocket连接
 */
export function useWorkflowWebSocket(userId: string) {
  const { connect, disconnect, sendMessage, ...rest } = useWebSocket()

  const connectWorkflow = (onMessage?: (message: WebSocketMessage) => void) => {
    return connect(`/api/v1/ws/workflow/${userId}`, onMessage)
  }

  const startWorkflow = (userRequest: string, context?: any) => {
    return sendMessage({
      type: 'workflow_start',
      data: {
        user_request: userRequest,
        context: context || {}
      }
    })
  }

  const getWorkflowStatus = (workflowId: string) => {
    return sendMessage({
      type: 'workflow_status',
      data: {
        workflow_id: workflowId
      }
    })
  }

  return {
    ...rest,
    connectWorkflow,
    startWorkflow,
    getWorkflowStatus,
    disconnect
  }
}

/**
 * 管理员WebSocket连接
 */
export function useAdminWebSocket(userId: string) {
  const { connect, disconnect, sendMessage, ...rest } = useWebSocket()

  const connectAdmin = (onMessage?: (message: WebSocketMessage) => void) => {
    return connect(`/api/v1/ws/admin/${userId}`, onMessage)
  }

  const broadcastMessage = (title: string, message: string, level: string = 'info') => {
    return sendMessage({
      type: 'broadcast',
      data: {
        title,
        message,
        level
      }
    })
  }

  const getConnectionStats = () => {
    return sendMessage({
      type: 'get_stats',
      data: {}
    })
  }

  return {
    ...rest,
    connectAdmin,
    broadcastMessage,
    getConnectionStats,
    disconnect
  }
}
