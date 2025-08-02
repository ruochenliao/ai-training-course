import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 智能体信息
export interface Agent {
  id: number
  name: string
  description: string
  avatar?: string
  type: string
  status: 'active' | 'inactive'
  config: Record<string, any>
  created_at: string
  updated_at: string
  user_id: number
}

// 创建智能体参数
export interface CreateAgentParams {
  name: string
  description: string
  type: string
  config?: Record<string, any>
  avatar?: string
}

// 更新智能体参数
export interface UpdateAgentParams extends Partial<CreateAgentParams> {
  status?: 'active' | 'inactive'
}

// 智能体列表查询参数
export interface AgentListParams {
  page?: number
  size?: number
  search?: string
  type?: string
  status?: string
}

// 智能体列表响应
export interface AgentListResponse {
  items: Agent[]
  total: number
  page: number
  size: number
  pages: number
}

// 聊天消息
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

// 聊天请求参数
export interface ChatParams {
  agent_id: number
  message: string
  session_id?: string
  stream?: boolean
}

// 聊天响应
export interface ChatResponse {
  message: ChatMessage
  session_id: string
}

// 智能体API接口
export const agentApi = {
  // 获取智能体列表
  getList: (params?: AgentListParams): Promise<ApiResponse<AgentListResponse>> => {
    return request({
      url: API_PATHS.AGENT.LIST,
      method: 'get',
      params
    })
  },

  // 获取智能体详情
  getDetail: (id: number): Promise<ApiResponse<Agent>> => {
    return request({
      url: `${API_PATHS.AGENT.DETAIL}/${id}`,
      method: 'get'
    })
  },

  // 创建智能体
  create: (data: CreateAgentParams): Promise<ApiResponse<Agent>> => {
    return request({
      url: API_PATHS.AGENT.CREATE,
      method: 'post',
      data
    })
  },

  // 更新智能体
  update: (id: number, data: UpdateAgentParams): Promise<ApiResponse<Agent>> => {
    return request({
      url: `${API_PATHS.AGENT.UPDATE}/${id}`,
      method: 'put',
      data
    })
  },

  // 删除智能体
  delete: (id: number): Promise<ApiResponse<null>> => {
    return request({
      url: `${API_PATHS.AGENT.DELETE}/${id}`,
      method: 'delete'
    })
  },

  // 与智能体聊天
  chat: (data: ChatParams): Promise<ApiResponse<ChatResponse>> => {
    return request({
      url: API_PATHS.AGENT.CHAT,
      method: 'post',
      data
    })
  }
}
