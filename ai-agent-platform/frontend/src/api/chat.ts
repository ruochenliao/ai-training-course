import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 消息类型
export enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  FILE = 'file',
  SYSTEM = 'system'
}

// 消息角色
export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

// 聊天消息
export interface ChatMessage {
  id: string
  role: MessageRole
  type: MessageType
  content: string
  timestamp: number
  metadata?: Record<string, any>
}

// 对话会话
export interface ChatSession {
  id: number
  title: string
  agent_id: number
  user_id: number
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

// 发送消息参数
export interface SendMessageParams {
  agent_id: number
  session_id?: number
  message: string
  type?: MessageType
}

// 创建会话参数
export interface CreateSessionParams {
  agent_id: number
  title?: string
}

// 对话API接口
export const chatApi = {
  // 创建对话会话
  createSession: (data: CreateSessionParams): Promise<ApiResponse<ChatSession>> => {
    return request({
      url: '/api/v1/chat/sessions',
      method: 'post',
      data
    })
  },

  // 获取对话会话列表
  getSessions: (params?: { skip?: number; limit?: number }): Promise<ApiResponse<ChatSession[]>> => {
    return request({
      url: '/api/v1/chat/sessions',
      method: 'get',
      params
    })
  },

  // 获取会话详情
  getSession: (sessionId: number): Promise<ApiResponse<ChatSession>> => {
    return request({
      url: `/api/v1/chat/sessions/${sessionId}`,
      method: 'get'
    })
  },

  // 删除会话
  deleteSession: (sessionId: number): Promise<ApiResponse<null>> => {
    return request({
      url: `/api/v1/chat/sessions/${sessionId}`,
      method: 'delete'
    })
  },

  // 发送消息
  sendMessage: (data: SendMessageParams): Promise<ApiResponse<ChatMessage>> => {
    return request({
      url: '/api/v1/chat/message',
      method: 'post',
      data
    })
  },

  // 获取会话消息
  getMessages: (sessionId: number, params?: { skip?: number; limit?: number }): Promise<ApiResponse<ChatMessage[]>> => {
    return request({
      url: `/api/v1/chat/sessions/${sessionId}/messages`,
      method: 'get',
      params
    })
  },

  // 流式对话（Server-Sent Events）
  streamChat: (data: SendMessageParams, onMessage: (message: string) => void, onComplete: () => void, onError: (error: Error) => void) => {
    const eventSource = new EventSource(`/api/v1/chat/stream?${new URLSearchParams({
      agent_id: data.agent_id.toString(),
      session_id: data.session_id?.toString() || '',
      message: data.message
    })}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'message') {
          onMessage(data.content)
        } else if (data.type === 'done') {
          onComplete()
          eventSource.close()
        }
      } catch (error) {
        onError(new Error('解析消息失败'))
      }
    }

    eventSource.onerror = (error) => {
      onError(new Error('连接错误'))
      eventSource.close()
    }

    return eventSource
  }
}

// WebSocket 对话客户端
export class ChatWebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private onMessage: (message: ChatMessage) => void
  private onError: (error: Error) => void
  private onConnect: () => void
  private onDisconnect: () => void

  constructor(
    agentId: number,
    sessionId: number,
    callbacks: {
      onMessage: (message: ChatMessage) => void
      onError: (error: Error) => void
      onConnect: () => void
      onDisconnect: () => void
    }
  ) {
    this.url = `ws://localhost:8000/api/v1/chat/ws/${agentId}/${sessionId}`
    this.onMessage = callbacks.onMessage
    this.onError = callbacks.onError
    this.onConnect = callbacks.onConnect
    this.onDisconnect = callbacks.onDisconnect
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        this.onConnect()
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.onMessage(message)
        } catch (error) {
          this.onError(new Error('解析消息失败'))
        }
      }

      this.ws.onerror = () => {
        this.onError(new Error('WebSocket连接错误'))
      }

      this.ws.onclose = () => {
        this.onDisconnect()
      }
    } catch (error) {
      this.onError(new Error('创建WebSocket连接失败'))
    }
  }

  sendMessage(message: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'message',
        content: message
      }))
    } else {
      this.onError(new Error('WebSocket连接未建立'))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
