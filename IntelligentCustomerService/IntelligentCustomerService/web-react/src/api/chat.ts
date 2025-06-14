import {request} from './index'
import {useAuthStore} from '../store/auth'

export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  message_id?: string
  created_at?: string
}

export interface SendMessageRequest {
  message: string
  conversation_id?: string
}

export interface SendMessageResponse {
  conversation_id: string
  user_message: {
    id: string
    content: string
    sender: string
    timestamp: string
  }
  assistant_message: {
    id: string
    content: string
    sender: string
    timestamp: string
    response_time?: number
  }
}

export interface ChatConversation {
  id: string
  conversation_id: string
  user_id: number
  title: string
  is_active: boolean
  last_message_at?: string
  created_at: string
  updated_at: string
}

export interface StreamMessageChunk {
  conversation_id: string
  message_id: string
  content: string
  is_complete: boolean
  timestamp: string
}

/**
 * 智能客服聊天API
 */
export const chatApi = {
  /**
   * 发送消息到智能客服（非流式）
   */
  sendMessage: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await request.post('/api/v1/chat/send', data)
    return response.data
  },

  /**
   * 发送消息到智能客服（流式）
   */
  sendMessageStream: async (data: SendMessageRequest): Promise<ReadableStream> => {
    const { token } = useAuthStore.getState()

    const response = await fetch('/api/v1/chat/send-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        token: token || '', // 使用与其他API一致的认证方式
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`发送消息失败: ${response.status} ${errorText}`)
    }

    return response.body!
  },

  /**
   * 创建新的对话
   */
  createConversation: async (title?: string): Promise<ChatConversation> => {
    const response = await request.post(
      '/api/v1/chat/conversation/create',
      {},
      {
        params: { title: title || '新对话' },
      },
    )
    return response.data
  },

  /**
   * 获取对话列表
   */
  getConversations: async (
    page = 1,
    pageSize = 20,
  ): Promise<{
    data: ChatConversation[]
    total: number
    page: number
    page_size: number
  }> => {
    const response = await request.get('/api/v1/chat/conversations', {
      params: { page, page_size: pageSize },
    })
    return response
  },

  /**
   * 获取对话消息历史
   */
  getConversationMessages: async (conversationId: string, limit = 50): Promise<ChatMessage[]> => {
    const response = await request.get(`/api/v1/chat/conversation/${conversationId}/messages`, {
      params: { limit },
    })
    return response.data.map((msg: any) => ({
      id: msg.message_id || msg.id,
      content: msg.content,
      sender: msg.sender,
      timestamp: new Date(msg.created_at || msg.timestamp),
      message_id: msg.message_id,
    }))
  },

  /**
   * 更新对话标题
   */
  updateConversation: async (conversationId: string, title: string): Promise<void> => {
    await request.put(`/api/v1/chat/conversation/${conversationId}`, { title })
  },

  /**
   * 删除对话
   */
  deleteConversation: async (conversationId: string): Promise<void> => {
    await request.delete(`/api/v1/chat/conversation/${conversationId}`)
  },

  /**
   * 获取聊天统计信息
   */
  getChatStats: async (): Promise<{
    total_conversations: number
    total_messages: number
    total_tokens_used: number
    avg_response_time: number
  }> => {
    const response = await request.get('/api/v1/chat/stats')
    return response.data
  },

  /**
   * 获取聊天配置
   */
  getChatConfig: async (): Promise<{
    model_name: string
    max_tokens: number
    temperature: number
    stream_enabled: boolean
  }> => {
    const response = await request.get('/api/v1/chat/config')
    return response.data
  },

  /**
   * 健康检查
   */
  healthCheck: async (): Promise<{ status: string; model: string }> => {
    const response = await request.get('/api/v1/chat/health')
    return response.data
  },
}

export default chatApi
