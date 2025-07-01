// 聊天相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 聊天相关类型定义
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface Conversation {
  id: number
  title: string
  user_id: number
  knowledge_base_ids: number[]
  message_count: number
  created_at: string
  updated_at: string
  last_message_at?: string
}

export interface ChatRequest {
  message: string
  conversation_id?: number
  knowledge_base_ids?: number[]
  search_mode?: 'vector' | 'hybrid' | 'graph' | 'auto'
  max_tokens?: number
  temperature?: number
  stream?: boolean
}

export interface ChatResponse {
  message_id: string
  content: string
  conversation_id: number
  sources?: SearchSource[]
  metadata?: Record<string, any>
  processing_time: number
}

export interface SearchSource {
  document_id: number
  document_name: string
  chunk_id: number
  content: string
  score: number
  metadata?: Record<string, any>
}

export interface AutoGenChatRequest {
  query: string
  conversation_id?: number
  knowledge_base_ids?: number[]
  agent_config?: {
    use_retrieval_agent?: boolean
    use_analysis_agent?: boolean
    use_summary_agent?: boolean
    max_rounds?: number
    collaboration_mode?: 'sequential' | 'parallel'
  }
}

export interface AutoGenChatResponse {
  query: string
  answer: string
  conversation_id?: number
  sources: SearchSource[]
  confidence: number
  processing_time: number
  agent_results: Record<string, any>
  metadata: Record<string, any>
}

export interface ConversationListParams {
  page?: number
  size?: number
  search?: string
}

export interface ConversationListResponse {
  items: Conversation[]
  total: number
  page: number
  size: number
  pages: number
}

// 聊天API接口
export const chatApi = {
  // 发送聊天消息
  sendMessage: (data: ChatRequest): Promise<ApiResponseData<ChatResponse>> => {
    return httpClient.post('/chat', data)
  },

  // 流式聊天
  sendStreamMessage: (data: ChatRequest): Promise<ReadableStream> => {
    return httpClient.post('/chat/stream', data, {
      responseType: 'stream',
    })
  },

  // AutoGen多智能体聊天
  autoGenChat: (data: AutoGenChatRequest): Promise<ApiResponseData<AutoGenChatResponse>> => {
    return httpClient.post('/autogen/chat', data)
  },

  // 获取对话列表
  getConversations: (params?: ConversationListParams): Promise<ApiResponseData<ConversationListResponse>> => {
    return httpClient.get('/conversations', { params })
  },

  // 获取对话详情
  getConversation: (conversationId: number): Promise<ApiResponseData<Conversation>> => {
    return httpClient.get(`/conversations/${conversationId}`)
  },

  // 创建新对话
  createConversation: (data: {
    title?: string
    knowledge_base_ids?: number[]
  }): Promise<ApiResponseData<Conversation>> => {
    return httpClient.post('/conversations', data)
  },

  // 更新对话
  updateConversation: (conversationId: number, data: { title?: string }): Promise<ApiResponseData<Conversation>> => {
    return httpClient.put(`/conversations/${conversationId}`, data)
  },

  // 删除对话
  deleteConversation: (conversationId: number): Promise<ApiResponseData<any>> => {
    return httpClient.delete(`/conversations/${conversationId}`)
  },

  // 获取对话消息
  getConversationMessages: (
    conversationId: number,
    page?: number,
    size?: number
  ): Promise<ApiResponseData<ChatMessage[]>> => {
    return httpClient.get(`/conversations/${conversationId}/messages`, {
      params: { page, size },
    })
  },

  // 清空对话历史
  clearConversationHistory: (conversationId: number): Promise<ApiResponseData<any>> => {
    return httpClient.post(`/conversations/${conversationId}/clear`)
  },

  // 导出对话
  exportConversation: (conversationId: number, format: 'json' | 'txt' | 'pdf'): Promise<Blob> => {
    return httpClient.get(`/conversations/${conversationId}/export`, {
      params: { format },
      responseType: 'blob',
    })
  },
}
