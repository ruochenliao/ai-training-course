import {useCallback, useEffect, useRef, useState} from 'react'
import apiClient from '../utils/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    id: string
    content_preview: string
    score: number
    source_type: string
    metadata: any
  }>
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ChatOptions {
  knowledgeBaseIds?: number[]
  stream?: boolean
  onMessage?: (message: Message) => void
  onError?: (error: any) => void
}

export function useChat(options: ChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const abortControllerRef = useRef<AbortController | null>(null)

  // 发送消息
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    try {
      const response = await apiClient.sendChatMessage({
        message: content,
        conversation_id: currentConversationId || undefined,
        knowledge_base_ids: options.knowledgeBaseIds,
        stream: options.stream || false
      })

      const assistantMessage: Message = {
        id: response.message_id.toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        sources: response.sources
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // 更新当前对话ID
      if (!currentConversationId && response.conversation_id) {
        setCurrentConversationId(response.conversation_id)
      }

      options.onMessage?.(assistantMessage)
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMessage = err.message || '发送消息失败'
        setError(errorMessage)
        options.onError?.(err)
      }
    } finally {
      setIsLoading(false)
    }
  }, [currentConversationId, options, isLoading])

  // 加载对话列表
  const loadConversations = useCallback(async () => {
    try {
      const response = await apiClient.getConversations()
      setConversations(response.items || [])
    } catch (err: any) {
      console.error('加载对话列表失败:', err)
    }
  }, [])

  // 加载对话详情
  const loadConversation = useCallback(async (conversationId: number) => {
    try {
      setIsLoading(true)
      const response = await apiClient.getConversation(conversationId.toString())
      
      const conversationMessages: Message[] = response.messages.map((msg: any) => ({
        id: msg.id.toString(),
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        sources: msg.metadata?.sources
      }))

      setMessages(conversationMessages)
      setCurrentConversationId(conversationId)
    } catch (err: any) {
      setError('加载对话失败')
      console.error('加载对话失败:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 创建新对话
  const startNewConversation = useCallback(() => {
    setMessages([])
    setCurrentConversationId(null)
    setError(null)
  }, [])

  // 删除对话
  const deleteConversation = useCallback(async (conversationId: number) => {
    try {
      await apiClient.deleteConversation(conversationId.toString())
      setConversations(prev => prev.filter(conv => conv.id !== conversationId))
      
      // 如果删除的是当前对话，创建新对话
      if (conversationId === currentConversationId) {
        startNewConversation()
      }
    } catch (err: any) {
      console.error('删除对话失败:', err)
    }
  }, [currentConversationId, startNewConversation])

  // 清除错误
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // 停止生成
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsLoading(false)
    }
  }, [])

  // 重新发送最后一条消息
  const resendLastMessage = useCallback(() => {
    const lastUserMessage = messages.filter(msg => msg.role === 'user').pop()
    if (lastUserMessage) {
      // 移除最后一条助手消息（如果存在）
      setMessages(prev => {
        const lastIndex = prev.length - 1
        if (lastIndex >= 0 && prev[lastIndex].role === 'assistant') {
          return prev.slice(0, lastIndex)
        }
        return prev
      })
      
      sendMessage(lastUserMessage.content)
    }
  }, [messages, sendMessage])

  // 组件卸载时取消请求
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // 初始化时加载对话列表
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  return {
    // 状态
    messages,
    conversations,
    currentConversationId,
    isLoading,
    error,
    
    // 方法
    sendMessage,
    loadConversations,
    loadConversation,
    startNewConversation,
    deleteConversation,
    clearError,
    stopGeneration,
    resendLastMessage
  }
}

// 流式聊天Hook
export function useStreamChat(options: ChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  
  const sendStreamMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsStreaming(true)
    setStreamingMessage('')

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
        },
        body: JSON.stringify({
          message: content,
          knowledge_base_ids: options.knowledgeBaseIds
        })
      })

      if (!response.ok) {
        throw new Error('流式请求失败')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      let fullMessage = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                fullMessage += data.content
                setStreamingMessage(fullMessage)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      // 添加完整的助手消息
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: fullMessage,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      setStreamingMessage('')
      
    } catch (err: any) {
      console.error('流式聊天失败:', err)
      options.onError?.(err)
    } finally {
      setIsStreaming(false)
    }
  }, [isStreaming, options])

  return {
    messages,
    isStreaming,
    streamingMessage,
    sendStreamMessage
  }
}
