import { ref, computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

interface WebSocketOptions {
  autoConnect?: boolean
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export function useWebSocket(url: string | Ref<string>, options: WebSocketOptions = {}) {
  const config = useRuntimeConfig()
  const { token } = useAuth()
  
  // 默认选项
  const defaultOptions: Required<WebSocketOptions> = {
    autoConnect: true,
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    onOpen: () => {},
    onClose: () => {},
    onError: () => {},
    onMessage: () => {}
  }
  
  const opts = { ...defaultOptions, ...options }
  
  // 状态
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const reconnectCount = ref(0)
  const lastMessage = ref<WebSocketMessage | null>(null)
  const messageHistory = ref<WebSocketMessage[]>([])
  
  // 定时器
  let reconnectTimer: NodeJS.Timeout | null = null
  let heartbeatTimer: NodeJS.Timeout | null = null
  
  // 计算WebSocket URL
  const wsUrl = computed(() => {
    const baseUrl = config.public.wsBase || 'ws://localhost:8000/ws'
    const endpoint = unref(url)
    const fullUrl = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
    
    // 添加认证token
    if (token.value) {
      const separator = fullUrl.includes('?') ? '&' : '?'
      return `${fullUrl}${separator}token=${token.value}`
    }
    
    return fullUrl
  })
  
  // 连接WebSocket
  const connect = () => {
    if (isConnecting.value || isConnected.value) {
      return
    }
    
    isConnecting.value = true
    
    try {
      ws.value = new WebSocket(wsUrl.value)
      
      ws.value.onopen = (event) => {
        isConnected.value = true
        isConnecting.value = false
        reconnectCount.value = 0
        
        // 启动心跳
        startHeartbeat()
        
        opts.onOpen(event)
        console.log('WebSocket连接已建立')
      }
      
      ws.value.onclose = (event) => {
        isConnected.value = false
        isConnecting.value = false
        
        // 停止心跳
        stopHeartbeat()
        
        opts.onClose(event)
        console.log('WebSocket连接已关闭')
        
        // 自动重连
        if (reconnectCount.value < opts.reconnectAttempts) {
          scheduleReconnect()
        }
      }
      
      ws.value.onerror = (event) => {
        isConnecting.value = false
        opts.onError(event)
        console.error('WebSocket连接错误:', event)
      }
      
      ws.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          lastMessage.value = message
          messageHistory.value.push(message)
          
          // 限制历史消息数量
          if (messageHistory.value.length > 100) {
            messageHistory.value = messageHistory.value.slice(-100)
          }
          
          opts.onMessage(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
    } catch (error) {
      isConnecting.value = false
      console.error('创建WebSocket连接失败:', error)
    }
  }
  
  // 断开连接
  const disconnect = () => {
    stopHeartbeat()
    clearReconnectTimer()
    
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    
    isConnected.value = false
    isConnecting.value = false
  }
  
  // 发送消息
  const send = (type: string, data: any) => {
    if (!isConnected.value || !ws.value) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }
    
    try {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: Date.now()
      }
      
      ws.value.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }
  
  // 重连
  const reconnect = () => {
    if (reconnectCount.value >= opts.reconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      return
    }
    
    reconnectCount.value++
    console.log(`尝试重连 (${reconnectCount.value}/${opts.reconnectAttempts})`)
    
    disconnect()
    connect()
  }
  
  // 计划重连
  const scheduleReconnect = () => {
    clearReconnectTimer()
    reconnectTimer = setTimeout(() => {
      reconnect()
    }, opts.reconnectInterval)
  }
  
  // 清除重连定时器
  const clearReconnectTimer = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }
  
  // 启动心跳
  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      send('ping', { timestamp: Date.now() })
    }, opts.heartbeatInterval)
  }
  
  // 停止心跳
  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }
  
  // 清理资源
  const cleanup = () => {
    disconnect()
    clearReconnectTimer()
  }
  
  // 自动连接
  if (opts.autoConnect) {
    connect()
  }
  
  // 组件卸载时清理
  onUnmounted(() => {
    cleanup()
  })
  
  return {
    // 状态
    isConnected: readonly(isConnected),
    isConnecting: readonly(isConnecting),
    reconnectCount: readonly(reconnectCount),
    lastMessage: readonly(lastMessage),
    messageHistory: readonly(messageHistory),
    
    // 方法
    connect,
    disconnect,
    send,
    reconnect,
    cleanup
  }
}

// 专用的WebSocket组合式函数
export function useDocumentProcessingWS() {
  const { send, ...ws } = useWebSocket('/document-processing', {
    onMessage: (message) => {
      console.log('文档处理消息:', message)
    }
  })
  
  const subscribeToDocument = (documentId: string) => {
    send('subscribe', { document_id: documentId })
  }
  
  const unsubscribeFromDocument = (documentId: string) => {
    send('unsubscribe', { document_id: documentId })
  }
  
  return {
    ...ws,
    subscribeToDocument,
    unsubscribeFromDocument
  }
}

export function useSystemMonitorWS() {
  const { send, ...ws } = useWebSocket('/system-monitor', {
    onMessage: (message) => {
      console.log('系统监控消息:', message)
    }
  })
  
  const subscribeToMetrics = (metrics: string[]) => {
    send('subscribe_metrics', { metrics })
  }
  
  const unsubscribeFromMetrics = () => {
    send('unsubscribe_metrics', {})
  }
  
  return {
    ...ws,
    subscribeToMetrics,
    unsubscribeFromMetrics
  }
}

export function useChatWS() {
  const { send, ...ws } = useWebSocket('/chat', {
    onMessage: (message) => {
      console.log('聊天消息:', message)
    }
  })
  
  const joinConversation = (conversationId: string) => {
    send('join_conversation', { conversation_id: conversationId })
  }
  
  const leaveConversation = (conversationId: string) => {
    send('leave_conversation', { conversation_id: conversationId })
  }
  
  const sendChatMessage = (conversationId: string, message: string) => {
    send('chat_message', {
      conversation_id: conversationId,
      message
    })
  }
  
  return {
    ...ws,
    joinConversation,
    leaveConversation,
    sendChatMessage
  }
}
