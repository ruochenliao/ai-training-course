import api from './api';
import { AgentConfig, AgentTool, AgentModel, WritingFieldConfig } from '@/types';

export interface AgentConfigCreate {
  name: string;
  description?: string;
  system_prompt: string;
  user_prompt_template?: string;
  model_name: string;
  temperature: string;
  max_tokens: number;
  tools: string[];
  tool_choice: string;
  max_consecutive_auto_reply: number;
  human_input_mode: string;
  code_execution_config: Record<string, any>;
  is_active: boolean;
}

export interface AgentConfigUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  user_prompt_template?: string;
  model_name?: string;
  temperature?: string;
  max_tokens?: number;
  tools?: string[];
  tool_choice?: string;
  max_consecutive_auto_reply?: number;
  human_input_mode?: string;
  code_execution_config?: Record<string, any>;
  is_active?: boolean;
}

export interface WritingFieldConfigUpdate {
  field_name?: string;
  field_key?: string;
  field_type?: 'text' | 'textarea' | 'select';
  placeholder?: string;
  options?: string[];
  required?: boolean;
  ai_enabled?: boolean;
  doc_enabled?: boolean;
  sort_order?: number;
  agent_config_id?: number;
  is_active?: boolean;
}

class AgentConfigService {
  // 智能体配置管理
  async getAgentConfigs(): Promise<AgentConfig[]> {
    const response = await api.get('/agent-configs/agents');
    return response.data;
  }

  async getAgentConfig(agentId: number): Promise<AgentConfig> {
    const response = await api.get(`/agent-configs/agents/${agentId}`);
    return response.data;
  }

  async createAgentConfig(data: AgentConfigCreate): Promise<AgentConfig> {
    const response = await api.post('/agent-configs/agents', data);
    return response.data;
  }

  async updateAgentConfig(agentId: number, data: AgentConfigUpdate): Promise<AgentConfig> {
    const response = await api.put(`/agent-configs/agents/${agentId}`, data);
    return response.data;
  }

  async deleteAgentConfig(agentId: number): Promise<void> {
    await api.delete(`/agent-configs/agents/${agentId}`);
  }

  // 工具管理
  async getAgentTools(): Promise<AgentTool[]> {
    const response = await api.get('/agent-configs/tools');
    return response.data;
  }

  // 模型管理
  async getAgentModels(): Promise<AgentModel[]> {
    const response = await api.get('/agent-configs/models');
    return response.data;
  }

  // 字段配置管理
  async getFieldConfigsByScenario(scenarioConfigId: number): Promise<WritingFieldConfig[]> {
    const response = await api.get(`/agent-configs/fields/scenario/${scenarioConfigId}`);
    return response.data;
  }

  async updateFieldConfig(fieldId: number, data: WritingFieldConfigUpdate): Promise<WritingFieldConfig> {
    const response = await api.put(`/agent-configs/fields/${fieldId}`, data);
    return response.data;
  }

  async assignAgentToField(fieldId: number, agentId: number): Promise<void> {
    await api.post(`/agent-configs/fields/${fieldId}/assign-agent/${agentId}`);
  }

  async removeAgentFromField(fieldId: number): Promise<void> {
    await api.delete(`/agent-configs/fields/${fieldId}/agent`);
  }

  // AI生成相关
  async generateContent(data: {
    field_key: string;
    field_name: string;
    template_type_id: number;
    context?: Record<string, any>;
    user_input?: string;
  }): Promise<{
    success: boolean;
    content?: string;
    error?: string;
  }> {
    const response = await api.post('/agent-configs/ai-generate', data);
    return response.data;
  }

  async generateContentDirect(
    agentId: number,
    userPrompt: string,
    context: Record<string, any> = {}
  ): Promise<{
    success: boolean;
    content?: string;
    error?: string;
  }> {
    const response = await api.post(`/agent-configs/ai-generate-direct/${agentId}`, {
      user_prompt: userPrompt,
      context
    });
    return response.data;
  }
}

export const agentConfigService = new AgentConfigService();
