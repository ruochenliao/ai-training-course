/**
 * 多智能体协作API接口
 */

import { request } from '@/utils/request'

// 检索模式类型
export type SearchMode = 'semantic' | 'hybrid' | 'graph' | 'all'

// 聊天请求接口
export interface MultiAgentChatRequest {
  query: string
  search_modes: SearchMode[]
  top_k?: number
  knowledge_base_ids?: number[]
  session_id?: string
  stream?: boolean
}

// 检索结果接口
export interface SearchResult {
  content: string
  source: string
  score: number
  search_type: string
  confidence: number
  relevance_explanation: string
  metadata: Record<string, any>
}

// 质量评估接口
export interface QualityAssessment {
  confidence: number
  completeness: number
  relevance: number
  accuracy: number
  overall_score: number
  assessment: string
}

// 聊天响应接口
export interface MultiAgentChatResponse {
  query: string
  answer: string
  search_results: SearchResult[]
  quality_assessment: QualityAssessment
  processing_time: number
  modes_used: string[]
  metadata: {
    total_results: number
    confidence_score: number
    session_id?: string
  }
}

// 检索模式信息接口
export interface SearchModeInfo {
  mode: string
  name: string
  description: string
  enabled: boolean
}

// 智能体统计接口
export interface AgentStats {
  coordinator_stats: {
    total_requests: number
    avg_response_time: number
    mode_usage: Record<string, number>
  }
  agent_info: {
    total_agents: number
    active_agents: string[]
    agent_roles: Record<string, string>
  }
  performance_metrics: {
    avg_response_time: number
    total_requests: number
    mode_usage: Record<string, number>
  }
}

// 测试结果接口
export interface AgentTestResult {
  test_query: string
  test_result: {
    answer_generated: boolean
    search_results_count: number
    processing_time: number
    quality_score: number
    modes_tested: string[]
  }
  detailed_result: MultiAgentChatResponse
}

/**
 * 多智能体协作问答
 */
export const multiAgentChat = async (data: MultiAgentChatRequest): Promise<MultiAgentChatResponse> => {
  return request.post('/api/v1/multi-agent/chat', data)
}

/**
 * 获取支持的检索模式
 */
export const getSearchModes = async (): Promise<{ search_modes: SearchModeInfo[] }> => {
  return request.get('/api/v1/multi-agent/search-modes')
}

/**
 * 获取多智能体协作统计
 */
export const getMultiAgentStats = async (): Promise<AgentStats> => {
  return request.get('/api/v1/multi-agent/stats')
}

/**
 * 测试智能体协作
 */
export const testAgentCollaboration = async (query?: string): Promise<AgentTestResult> => {
  const params = query ? { query } : {}
  return request.post('/api/v1/multi-agent/test-agents', params)
}

/**
 * WebSocket流式聊天连接
 */
export class MultiAgentWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private token: string | null

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    this.url = `${protocol}//${host}/api/v1/multi-agent/chat-stream`
    this.token = localStorage.getItem('token')
  }

  /**
   * 连接WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.token ? `${this.url}?token=${this.token}` : this.url
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          resolve()
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭')
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * 发送消息
   */
  sendMessage(data: {
    query: string
    search_modes: SearchMode[]
    top_k?: number
    knowledge_base_ids?: number[]
  }): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      throw new Error('WebSocket未连接')
    }
  }

  /**
   * 监听消息
   */
  onMessage(callback: (data: any) => void): void {
    if (this.ws) {
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          callback(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
    }
  }

  /**
   * 监听错误
   */
  onError(callback: (error: Event) => void): void {
    if (this.ws) {
      this.ws.onerror = callback
    }
  }

  /**
   * 监听关闭
   */
  onClose(callback: (event: CloseEvent) => void): void {
    if (this.ws) {
      this.ws.onclose = callback
    }
  }

  /**
   * 关闭连接
   */
  close(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 获取连接状态
   */
  getReadyState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

/**
 * 创建WebSocket实例的工厂函数
 */
export const createMultiAgentWebSocket = (): MultiAgentWebSocket => {
  return new MultiAgentWebSocket()
}

/**
 * 检索模式配置
 */
export const SEARCH_MODE_CONFIG = {
  semantic: {
    name: '语义检索',
    description: '基于Qwen3-8B嵌入模型的向量相似度搜索',
    icon: 'SearchOutlined',
    color: '#1890ff'
  },
  hybrid: {
    name: '混合检索',
    description: '结合语义检索和关键词检索，使用RRF算法融合',
    icon: 'ThunderboltOutlined',
    color: '#52c41a'
  },
  graph: {
    name: '图谱检索',
    description: '基于Neo4j知识图谱的实体关系搜索',
    icon: 'BranchesOutlined',
    color: '#722ed1'
  },
  all: {
    name: '全模式检索',
    description: '同时使用所有检索模式，通过智能体协作融合',
    icon: 'DatabaseOutlined',
    color: '#fa8c16'
  }
} as const

/**
 * 默认配置
 */
export const DEFAULT_CONFIG = {
  TOP_K: 10,
  DEFAULT_MODES: ['semantic'] as SearchMode[],
  TIMEOUT: 30000, // 30秒超时
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000 // 1秒重试延迟
}

/**
 * 错误处理工具
 */
export const handleMultiAgentError = (error: any): string => {
  if (error.response) {
    // HTTP错误
    const status = error.response.status
    const message = error.response.data?.message || error.response.data?.detail || '请求失败'
    
    switch (status) {
      case 400:
        return `请求参数错误: ${message}`
      case 401:
        return '未授权，请重新登录'
      case 403:
        return '权限不足'
      case 404:
        return '服务不存在'
      case 500:
        return `服务器错误: ${message}`
      case 503:
        return '服务暂时不可用'
      default:
        return `请求失败 (${status}): ${message}`
    }
  } else if (error.code === 'NETWORK_ERROR') {
    return '网络连接失败，请检查网络设置'
  } else if (error.code === 'TIMEOUT') {
    return '请求超时，请稍后重试'
  } else {
    return error.message || '未知错误'
  }
}

/**
 * 重试机制
 */
export const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  maxAttempts: number = DEFAULT_CONFIG.RETRY_ATTEMPTS,
  delay: number = DEFAULT_CONFIG.RETRY_DELAY
): Promise<T> => {
  let lastError: any

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      
      if (attempt === maxAttempts) {
        break
      }
      
      // 等待后重试
      await new Promise(resolve => setTimeout(resolve, delay * attempt))
    }
  }
  
  throw lastError
}
