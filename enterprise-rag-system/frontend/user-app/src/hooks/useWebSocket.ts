import {useCallback, useEffect, useRef, useState} from 'react'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

export interface WebSocketOptions {
  autoConnect?: boolean
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export function useWebSocket(url: string, options: WebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectCountRef = useRef(0)
  
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    onOpen,
    onClose,
    onError,
    onMessage
  } = options

  // 获取WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    const token = localStorage.getItem('auth-token')
    const fullUrl = `${baseUrl}${url}`
    
    if (token) {
      const separator = fullUrl.includes('?') ? '&' : '?'
      return `${fullUrl}${separator}token=${token}`
    }
    
    return fullUrl
  }, [url])

  // 连接WebSocket
  const connect = useCallback(() => {
    if (isConnecting || isConnected) {
      return
    }

    setIsConnecting(true)
    setConnectionError(null)

    try {
      const wsUrl = getWebSocketUrl()
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = (event) => {
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionError(null)
        reconnectCountRef.current = 0
        
        // 启动心跳
        if (heartbeatInterval > 0) {
          heartbeatIntervalRef.current = setInterval(() => {
            send('ping', { timestamp: Date.now() })
          }, heartbeatInterval)
        }
        
        onOpen?.(event)
      }

      wsRef.current.onclose = (event) => {
        setIsConnected(false)
        setIsConnecting(false)
        
        // 停止心跳
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }
        
        onClose?.(event)
        
        // 自动重连
        if (reconnectCountRef.current < reconnectAttempts) {
          scheduleReconnect()
        } else {
          setConnectionError('连接失败，已达到最大重连次数')
        }
      }

      wsRef.current.onerror = (event) => {
        setIsConnecting(false)
        setConnectionError('WebSocket连接错误')
        onError?.(event)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
    } catch (error) {
      setIsConnecting(false)
      setConnectionError('创建WebSocket连接失败')
      console.error('WebSocket连接错误:', error)
    }
  }, [isConnecting, isConnected, getWebSocketUrl, heartbeatInterval, onOpen, onClose, onError, onMessage, reconnectAttempts])

  // 断开连接
  const disconnect = useCallback(() => {
    // 清除重连定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    // 清除心跳定时器
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    
    // 关闭WebSocket连接
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setIsConnecting(false)
    reconnectCountRef.current = 0
  }, [])

  // 发送消息
  const send = useCallback((type: string, data: any) => {
    if (!isConnected || !wsRef.current) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: Date.now()
      }
      
      wsRef.current.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }, [isConnected])

  // 重连
  const reconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      setConnectionError('已达到最大重连次数')
      return
    }

    reconnectCountRef.current++
    disconnect()
    
    setTimeout(() => {
      connect()
    }, 100)
  }, [reconnectAttempts, disconnect, connect])

  // 计划重连
  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnect()
    }, reconnectInterval)
  }, [reconnect, reconnectInterval])

  // 清除错误
  const clearError = useCallback(() => {
    setConnectionError(null)
  }, [])

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    isConnected,
    isConnecting,
    lastMessage,
    connectionError,
    connect,
    disconnect,
    send,
    reconnect,
    clearError
  }
}

// 聊天WebSocket Hook
export function useChatWebSocket() {
  const [messages, setMessages] = useState<any[]>([])
  
  const { isConnected, send, ...ws } = useWebSocket('/chat', {
    onMessage: (message) => {
      if (message.type === 'chat_message') {
        setMessages(prev => [...prev, message.data])
      }
    }
  })

  const joinConversation = useCallback((conversationId: string) => {
    send('join_conversation', { conversation_id: conversationId })
  }, [send])

  const leaveConversation = useCallback((conversationId: string) => {
    send('leave_conversation', { conversation_id: conversationId })
  }, [send])

  const sendChatMessage = useCallback((conversationId: string, message: string) => {
    send('chat_message', {
      conversation_id: conversationId,
      message
    })
  }, [send])

  return {
    ...ws,
    isConnected,
    messages,
    joinConversation,
    leaveConversation,
    sendChatMessage
  }
}

// 文档处理WebSocket Hook
export function useDocumentProcessingWebSocket() {
  const [processingStatus, setProcessingStatus] = useState<Record<string, any>>({})
  
  const { send, ...ws } = useWebSocket('/document-processing', {
    onMessage: (message) => {
      if (message.type === 'document_status') {
        setProcessingStatus(prev => ({
          ...prev,
          [message.data.document_id]: message.data
        }))
      }
    }
  })

  const subscribeToDocument = useCallback((documentId: string) => {
    send('subscribe', { document_id: documentId })
  }, [send])

  const unsubscribeFromDocument = useCallback((documentId: string) => {
    send('unsubscribe', { document_id: documentId })
  }, [send])

  return {
    ...ws,
    processingStatus,
    subscribeToDocument,
    unsubscribeFromDocument
  }
}
