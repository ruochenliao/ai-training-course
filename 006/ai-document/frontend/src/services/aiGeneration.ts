import api from './api';

// 字段类型枚举
export enum FieldType {
  CONFIGURED = 'configured',
  SMART = 'smart',
  DEFAULT = 'default'
}

// 生成上下文接口
export interface GenerationContext {
  category?: string;
  type?: string;
  content_type?: string;
  title?: string;
  keywords?: string;
  content?: string;
  reason?: string;
  purpose?: string;
  template_type_id?: number;
  scenario_config_id?: number;
  extra_data?: Record<string, any>;
}

// 单个字段生成请求
export interface FieldGenerateRequest {
  field_key: string;
  field_name: string;
  field_type?: FieldType;
  agent_id?: number;
  user_input?: string;
  context?: Record<string, any>;
  max_length?: number;
  style?: string;
  temperature?: number;
}

// 单个字段生成响应
export interface FieldGenerateResponse {
  success: boolean;
  content?: string;
  error?: string;
  field_key: string;
  agent_used?: string;
  generation_time?: number;
  token_count?: number;
  quality_score?: number;
  confidence?: number;
}

// 批量生成请求
export interface BatchGenerateRequest {
  fields: FieldGenerateRequest[];
  global_context?: Record<string, any>;
  parallel?: boolean;
  stop_on_error?: boolean;
  max_concurrent?: number;
}

// 批量生成响应
export interface BatchGenerateResponse {
  success: boolean;
  results: FieldGenerateResponse[];
  success_count: number;
  total_count: number;
  total_time?: number;
  error?: string;
}

// 智能生成请求
export interface SmartGenerateRequest {
  prompt: string;
  context: GenerationContext;
  auto_select_agent?: boolean;
  optimize_prompt?: boolean;
  quality_threshold?: number;
  max_tokens?: number;
  target_length?: number;
  required_keywords?: string[];
}

// 智能生成响应
export interface SmartGenerateResponse {
  success: boolean;
  content?: string;
  error?: string;
  strategy_used: string;
  agent_used: string;
  confidence_score: number;
  generation_time: number;
  optimization_applied?: string[];
  quality_metrics?: Record<string, number>;
}

// 适合的智能体信息
export interface SuitableAgent {
  id: number;
  name: string;
  description?: string;
  suitability_score: number;
}

class AIGenerationService {
  /**
   * 生成单个字段内容
   */
  async generateField(request: FieldGenerateRequest): Promise<FieldGenerateResponse> {
    const response = await api.post('/ai-generation/field', request);
    return response.data;
  }

  /**
   * 批量生成多个字段内容
   */
  async generateBatch(request: BatchGenerateRequest): Promise<BatchGenerateResponse> {
    const response = await api.post('/ai-generation/batch', request);
    return response.data;
  }

  /**
   * 智能内容生成
   */
  async generateSmart(request: SmartGenerateRequest): Promise<SmartGenerateResponse> {
    const response = await api.post('/ai-generation/smart', request);
    return response.data;
  }

  /**
   * 获取适合特定字段类型的智能体列表
   */
  async getSuitableAgents(fieldType: string, contentType: string): Promise<{
    success: boolean;
    agents: SuitableAgent[];
    total_count: number;
    error?: string;
  }> {
    const response = await api.get('/ai-generation/agents/suitable', {
      params: { field_type: fieldType, content_type: contentType }
    });
    return response.data;
  }

  /**
   * 便捷方法：生成标题
   */
  async generateTitle(context: Record<string, any>, userInput?: string): Promise<FieldGenerateResponse> {
    return this.generateField({
      field_key: 'title',
      field_name: '标题',
      field_type: FieldType.SMART,
      context,
      user_input: userInput
    });
  }

  /**
   * 便捷方法：生成关键词
   */
  async generateKeywords(context: Record<string, any>, userInput?: string): Promise<FieldGenerateResponse> {
    return this.generateField({
      field_key: 'keywords',
      field_name: '关键词',
      field_type: FieldType.SMART,
      context,
      user_input: userInput
    });
  }

  /**
   * 便捷方法：生成主要内容
   */
  async generateContent(context: Record<string, any>, userInput?: string): Promise<FieldGenerateResponse> {
    return this.generateField({
      field_key: 'content',
      field_name: '主要内容',
      field_type: FieldType.SMART,
      context,
      user_input: userInput
    });
  }

  /**
   * 便捷方法：生成所有基础字段
   */
  async generateAllBasicFields(context: Record<string, any>): Promise<BatchGenerateResponse> {
    const fields: FieldGenerateRequest[] = [
      {
        field_key: 'title',
        field_name: '标题',
        field_type: FieldType.SMART,
        context
      },
      {
        field_key: 'keywords',
        field_name: '关键词',
        field_type: FieldType.SMART,
        context
      },
      {
        field_key: 'content',
        field_name: '主要内容',
        field_type: FieldType.SMART,
        context
      }
    ];

    return this.generateBatch({
      fields,
      global_context: context,
      parallel: false, // 按顺序生成，后面的字段可以利用前面生成的内容
      stop_on_error: false
    });
  }

  /**
   * 便捷方法：根据配置的智能体生成字段内容
   */
  async generateWithConfiguredAgent(
    fieldKey: string,
    fieldName: string,
    agentId: number,
    context: Record<string, any>,
    userInput?: string
  ): Promise<FieldGenerateResponse> {
    return this.generateField({
      field_key: fieldKey,
      field_name: fieldName,
      field_type: FieldType.CONFIGURED,
      agent_id: agentId,
      context,
      user_input: userInput
    });
  }

  /**
   * 便捷方法：构建生成上下文
   */
  buildContext(data: {
    category?: string;
    type?: string;
    title?: string;
    keywords?: string;
    content?: string;
    reason?: string;
    purpose?: string;
    templateTypeId?: number;
    scenarioConfigId?: number;
    extraData?: Record<string, any>;
  }): Record<string, any> {
    return {
      category: data.category,
      type: data.type,
      content_type: data.category && data.type ? `${data.category}-${data.type}` : undefined,
      title: data.title,
      keywords: data.keywords,
      content: data.content,
      reason: data.reason,
      purpose: data.purpose,
      template_type_id: data.templateTypeId,
      scenario_config_id: data.scenarioConfigId,
      extra_data: data.extraData || {}
    };
  }

  /**
   * 便捷方法：处理生成错误
   */
  handleGenerationError(error: any): string {
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    if (error.message) {
      return error.message;
    }
    return '生成失败，请重试';
  }

  /**
   * 便捷方法：检查生成结果质量
   */
  checkGenerationQuality(response: FieldGenerateResponse): {
    isGoodQuality: boolean;
    issues: string[];
    suggestions: string[];
  } {
    const issues: string[] = [];
    const suggestions: string[] = [];

    if (!response.success) {
      issues.push('生成失败');
      suggestions.push('请检查网络连接或重试');
      return { isGoodQuality: false, issues, suggestions };
    }

    if (!response.content || response.content.trim().length === 0) {
      issues.push('生成内容为空');
      suggestions.push('请调整提示词或上下文信息');
    }

    if (response.content && response.content.length < 10) {
      issues.push('生成内容过短');
      suggestions.push('请提供更多上下文信息');
    }

    if (response.quality_score && response.quality_score < 0.6) {
      issues.push('内容质量较低');
      suggestions.push('建议重新生成或手动调整');
    }

    if (response.confidence && response.confidence < 0.7) {
      issues.push('生成置信度较低');
      suggestions.push('建议提供更明确的要求');
    }

    return {
      isGoodQuality: issues.length === 0,
      issues,
      suggestions
    };
  }
}

export const aiGenerationService = new AIGenerationService();
