// 聊天状态管理

import { create } from 'zustand'
import { chatApi, type ChatMessage, type Conversation, type ChatRequest } from '@/api/chat'
import { messageService } from '@/services/messageService'

export interface ChatState {
  // 状态
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: ChatMessage[]
  loading: boolean
  sending: boolean

  // 操作
  fetchConversations: () => Promise<void>
  createConversation: (data?: any) => Promise<Conversation | null>
  setCurrentConversation: (conversation: Conversation | null) => void
  fetchMessages: (conversationId: number) => Promise<void>
  sendMessage: (data: ChatRequest) => Promise<boolean>
  addMessage: (message: ChatMessage) => void
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void
  deleteConversation: (conversationId: number) => Promise<boolean>
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  setSending: (sending: boolean) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  // 初始状态
  conversations: [],
  currentConversation: null,
  messages: [],
  loading: false,
  sending: false,

  // 获取对话列表
  fetchConversations: async () => {
    try {
      set({ loading: true })

      const response = await chatApi.getConversations()

      if (response.data) {
        set({
          conversations: response.data.items,
          loading: false,
        })
      }
    } catch (error: any) {
      set({ loading: false })
      message.error(error.response?.data?.message || '获取对话列表失败')
    }
  },

  // 创建新对话
  createConversation: async (data = {}) => {
    try {
      const response = await chatApi.createConversation(data)

      if (response.data) {
        const newConversation = response.data

        set({
          conversations: [newConversation, ...get().conversations],
          currentConversation: newConversation,
        })

        return newConversation
      }

      return null
    } catch (error: any) {
      message.error(error.response?.data?.message || '创建对话失败')
      return null
    }
  },

  // 设置当前对话
  setCurrentConversation: (conversation: Conversation | null) => {
    set({
      currentConversation: conversation,
      messages: [], // 清空消息，等待重新加载
    })

    if (conversation) {
      get().fetchMessages(conversation.id)
    }
  },

  // 获取对话消息
  fetchMessages: async (conversationId: number) => {
    try {
      set({ loading: true })

      const response = await chatApi.getConversationMessages(conversationId)

      if (response.data) {
        set({
          messages: response.data,
          loading: false,
        })
      }
    } catch (error: any) {
      set({ loading: false })
      messageService.error(error.response?.data?.message || '获取消息失败')
    }
  },

  // 发送消息
  sendMessage: async (data: ChatRequest) => {
    try {
      set({ sending: true })

      // 添加用户消息到本地状态
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: data.message,
        timestamp: new Date().toISOString(),
      }

      get().addMessage(userMessage)

      const response = await chatApi.sendMessage(data)

      if (response.data) {
        // 添加AI回复到本地状态
        const assistantMessage: ChatMessage = {
          id: response.data.message_id,
          role: 'assistant',
          content: response.data.content,
          timestamp: new Date().toISOString(),
          metadata: response.data.metadata,
        }

        get().addMessage(assistantMessage)

        // 更新当前对话ID
        if (response.data.conversation_id && !get().currentConversation) {
          // 如果是新对话，获取对话信息
          try {
            const convResponse = await chatApi.getConversation(response.data.conversation_id)
            if (convResponse.data) {
              set({ currentConversation: convResponse.data })
            }
          } catch (error) {
            console.error('Failed to fetch conversation:', error)
          }
        }

        set({ sending: false })
        return true
      }

      set({ sending: false })
      return false
    } catch (error: any) {
      set({ sending: false })
      messageService.error(error.response?.data?.message || '发送消息失败')
      return false
    }
  },

  // 添加消息
  addMessage: (message: ChatMessage) => {
    set({
      messages: [...get().messages, message],
    })
  },

  // 更新消息
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => {
    const messages = get().messages.map(msg => (msg.id === messageId ? { ...msg, ...updates } : msg))

    set({ messages })
  },

  // 删除对话
  deleteConversation: async (conversationId: number) => {
    try {
      await chatApi.deleteConversation(conversationId)

      const conversations = get().conversations.filter(conv => conv.id !== conversationId)

      set({
        conversations,
        currentConversation: get().currentConversation?.id === conversationId ? null : get().currentConversation,
        messages: get().currentConversation?.id === conversationId ? [] : get().messages,
      })

      message.success('对话删除成功')
      return true
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除对话失败')
      return false
    }
  },

  // 清空消息
  clearMessages: () => {
    set({ messages: [] })
  },

  // 设置加载状态
  setLoading: (loading: boolean) => {
    set({ loading })
  },

  // 设置发送状态
  setSending: (sending: boolean) => {
    set({ sending })
  },
}))
