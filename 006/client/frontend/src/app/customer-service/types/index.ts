export interface ImageContent {
  url: string
  file_name?: string
}

export interface MultiModalContent {
  text?: string
  image?: ImageContent
}

export interface MessageContent {
  type: 'text' | 'multi-modal'
  text?: string
  content?: MultiModalContent[]
  task?: string // 任务类型，参考AutoGen多模态消息格式
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string | MessageContent
  timestamp?: Date
  status: 'pending' | 'complete' | 'error' | 'done' | 'streaming'
}

export interface ChatRequestBody {
  messages: {
    role: 'user' | 'assistant'
    content: string
  }[]
  model: string
  system_prompt?: string
  user_id?: string
  session_id?: string
}

export interface SessionResponse {
  session_id: string
  user_id: string
  created_at: string
  last_active: string
  messages: {
    role: 'user' | 'assistant'
    content: string
  }[]
}