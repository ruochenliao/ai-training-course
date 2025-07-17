import api from './api';
import { AIRequest, AIResponse, AISession, AIStreamResponse, WritingWizardRequest } from '@/types';

export const aiService = {
  // 创建AI会话
  async createSession(data: AIRequest): Promise<AIResponse> {
    const response = await api.post<AIResponse>('/ai/generate', data);
    return response.data;
  },

  // 获取AI会话信息
  async getSession(sessionId: string): Promise<AISession> {
    const response = await api.get<AISession>(`/ai/session/${sessionId}`);
    return response.data;
  },

  // 创建SSE连接获取流式响应
  createEventSource(sessionId: string): EventSource {
    const token = localStorage.getItem('token');
    const url = `/api/ai/stream/${sessionId}`;
    
    // 由于EventSource不支持自定义headers，我们需要通过URL参数传递token
    const eventSource = new EventSource(`${url}?token=${token}`);
    
    return eventSource;
  },

  // 解析SSE数据
  parseSSEData(data: string): AIStreamResponse {
    try {
      return JSON.parse(data);
    } catch (error) {
      console.error('Failed to parse SSE data:', error);
      return {
        session_id: '',
        content: '',
        is_complete: true,
        error: 'Failed to parse response'
      };
    }
  },

  // 获取可用智能体
  async getAvailableAgents(): Promise<any> {
    const response = await api.get('/ai/agents');
    return response.data;
  },

  // 获取协作策略建议
  async suggestStrategy(data: {
    prompt: string;
    ai_type: string;
    context?: string;
  }): Promise<any> {
    const response = await api.post('/ai/suggest-strategy', data);
    return response.data;
  },

  // 创建写作向导会话
  async createWritingWizardSession(data: WritingWizardRequest): Promise<AIResponse> {
    const response = await api.post<AIResponse>('/ai/writing-wizard', data);
    return response.data;
  },
};
