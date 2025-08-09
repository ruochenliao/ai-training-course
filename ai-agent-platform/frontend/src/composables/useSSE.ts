# Copyright (c) 2025 左岚. All rights reserved.
/**
 * SSE (Server-Sent Events) 连接管理
 */

import { ref, computed, readonly, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface SSEMessage {
  type: string
  data: any
  timestamp?: string
  user_id?: string
  session_id?: string
}

export function useSSE() {
  const eventSource = ref<EventSource | null>(null)
  const connectionStatus = ref<ConnectionStatus>('disconnected')
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectInterval = ref<number | null>(null)
  
  let messageHandler: ((message: SSEMessage) => void) | null = null
  let currentUrl = ''

  const isConnected = computed(() => connectionStatus.value === 'connected')

  /**
   * 连接SSE
   */
  const connect = async (url: string, onMessage?: (message: SSEMessage) => void): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        // 如果已经连接，先断开
        if (eventSource.value) {
          disconnect()
        }

        currentUrl = url
        messageHandler = onMessage || null
        connectionStatus.value = 'connecting'

        // 构建完整的SSE URL
        const protocol = window.location.protocol
        const host = window.location.host
        const sseUrl = `${protocol}//${host}${url}`

        eventSource.value = new EventSource(sseUrl)

        eventSource.value.onopen = () => {
          connectionStatus.value = 'connected'
          reconnectAttempts.value = 0
          console.log('SSE连接已建立:', sseUrl)
          resolve()
        }

        eventSource.value.onmessage = (event) => {
          try {
            const message: SSEMessage = JSON.parse(event.data)
            console.log('收到SSE消息:', message)
            
            if (messageHandler) {
              messageHandler(message)
            }
          } catch (error) {
            console.error('解析SSE消息失败:', error)
          }
        }

        eventSource.value.onerror = (error) => {
          console.error('SSE连接错误:', error)
          
          if (eventSource.value?.readyState === EventSource.CLOSED) {
            connectionStatus.value = 'disconnected'
            eventSource.value = null
            
            // 尝试重连
            if (reconnectAttempts.value < maxReconnectAttempts) {
              scheduleReconnect()
            }
          } else {
            connectionStatus.value = 'error'
            reject(error)
          }
        }

      } catch (error) {
        connectionStatus.value = 'error'
        reject(error)
      }
    })
  }

  /**
   * 断开SSE连接
   */
  const disconnect = () => {
    if (reconnectInterval.value) {
      clearTimeout(reconnectInterval.value)
      reconnectInterval.value = null
    }

    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    
    connectionStatus.value = 'disconnected'
    reconnectAttempts.value = 0
  }

  // SSE是单向通信，不需要发送消息方法

  /**
   * 安排重连
   */
  const scheduleReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      ElMessage.error('SSE连接失败，请刷新页面重试')
      return
    }

    reconnectAttempts.value++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000) // 指数退避，最大30秒

    console.log(`SSE重连中... (${reconnectAttempts.value}/${maxReconnectAttempts})`)
    
    reconnectInterval.value = window.setTimeout(async () => {
      try {
        await connect(currentUrl, messageHandler)
      } catch (error) {
        console.error('SSE重连失败:', error)
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

  // SSE由服务端控制心跳，客户端无需主动发送

  // 组件卸载时清理
  onUnmounted(() => {
    disconnect()
  })

  return {
    eventSource: readonly(eventSource),
    connectionStatus: readonly(connectionStatus),
    isConnected,
    reconnectAttempts: readonly(reconnectAttempts),
    connect,
    disconnect,
    reconnect
  }
}

/**
 * 聊天SSE连接
 */
export function useChatSSE(userId: string) {
  const { connect, disconnect, ...rest } = useSSE()

  const connectChat = (onMessage?: (message: SSEMessage) => void) => {
    return connect(`/api/v1/sse/chat/${userId}`, onMessage)
  }

  const sendChatMessage = async (content: string, agentType: string, sessionId?: string) => {
    // 通过HTTP API发送聊天消息
    const response = await fetch('/api/v1/sse/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        content,
        agent_type: agentType,
        session_id: sessionId || `session_${userId}`,
        metadata: {}
      })
    })
    
    if (!response.ok) {
      throw new Error('发送消息失败')
    }
    
    return response.json()
  }

  const selectAgent = async (agentType: string, sessionId?: string) => {
    // 通过HTTP API选择智能体
    const response = await fetch('/api/v1/sse/chat/select-agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        agent_type: agentType,
        session_id: sessionId || `session_${userId}`
      })
    })
    
    if (!response.ok) {
      throw new Error('选择智能体失败')
    }
    
    return response.json()
  }

  return {
    ...rest,
    connectChat,
    sendChatMessage,
    selectAgent,
    disconnect
  }
}

/**
 * 工作流SSE连接
 */
export function useWorkflowSSE(userId: string) {
  const { connect, disconnect, ...rest } = useSSE()

  const connectWorkflow = (onMessage?: (message: SSEMessage) => void) => {
    return connect(`/api/v1/sse/workflow/${userId}`, onMessage)
  }

  const startWorkflow = async (userRequest: string, context?: any) => {
    // 通过HTTP API启动工作流
    const response = await fetch('/api/v1/sse/workflow/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        user_request: userRequest,
        context: context || {}
      })
    })
    
    if (!response.ok) {
      throw new Error('启动工作流失败')
    }
    
    return response.json()
  }

  return {
    ...rest,
    connectWorkflow,
    startWorkflow,
    disconnect
  }
}

/**
 * 管理员SSE连接
 */
export function useAdminSSE(userId: string) {
  const { connect, disconnect, ...rest } = useSSE()

  const connectAdmin = (onMessage?: (message: SSEMessage) => void) => {
    return connect(`/api/v1/sse/admin/${userId}`, onMessage)
  }

  const broadcastMessage = async (title: string, message: string, level: string = 'info') => {
    // 通过HTTP API广播消息
    const response = await fetch('/api/v1/sse/broadcast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        title,
        message,
        level
      })
    })
    
    if (!response.ok) {
      throw new Error('广播消息失败')
    }
    
    return response.json()
  }

  const getConnectionStats = async () => {
    // 通过HTTP API获取连接统计
    const response = await fetch('/api/v1/sse/stats', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('获取统计失败')
    }
    
    return response.json()
  }

  return {
    ...rest,
    connectAdmin,
    broadcastMessage,
    getConnectionStats,
    disconnect
  }
}
