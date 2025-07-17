/**
 * 写作主题管理服务
 */
import api from './api';

// 类型定义
export interface ThemeField {
  id?: number;
  field_key: string;
  field_label: string;
  field_type: string;
  placeholder?: string;
  default_value?: string;
  is_required: boolean;
  max_length?: number;
  min_length?: number;
  options?: Record<string, any>;
  validation_rules?: Record<string, any>;
  sort_order: number;
  is_visible: boolean;
  help_text?: string;
}

export interface PromptTemplate {
  id?: number;
  template_name: string;
  template_type: string;
  system_prompt?: string;
  user_prompt_template: string;
  variables?: Record<string, any>;
  ai_model?: string;
  temperature?: string;
  max_tokens?: number;
  is_active: boolean;
  version: string;
  usage_count?: number;
  success_rate?: string;
}

export interface WritingTheme {
  id?: number;
  name: string;
  description?: string;
  category: string;
  icon?: string;
  theme_key: string;
  is_active: boolean;
  sort_order: number;
  fields: ThemeField[];
  prompt_templates: PromptTemplate[];
  created_at?: string;
  updated_at?: string;
}

export interface WritingThemeSimple {
  id: number;
  name: string;
  description?: string;
  category: string;
  icon?: string;
  theme_key: string;
  is_active: boolean;
  sort_order: number;
  field_count: number;
  template_count: number;
  created_at: string;
}

export interface ThemeCategory {
  id?: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_active: boolean;
  sort_order: number;
}

export interface TemplatePreviewRequest {
  template_id: number;
  field_values: Record<string, any>;
}

export interface TemplatePreviewResponse {
  rendered_prompt: string;
  variables_used: string[];
  estimated_tokens?: number;
}

class WritingThemeService {
  private baseUrl = '/writing-themes';

  // ==================== 主题管理 ====================
  
  /**
   * 获取写作主题列表
   */
  async getThemes(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<WritingTheme[]> {
    const response = await api.get(`${this.baseUrl}/themes`, { params });
    return response.data;
  }

  /**
   * 获取简化的主题列表
   */
  async getThemesSimple(params?: {
    category?: string;
    is_active?: boolean;
  }): Promise<WritingThemeSimple[]> {
    const response = await api.get(`${this.baseUrl}/themes/simple`, { params });
    return response.data;
  }

  /**
   * 获取单个主题详情
   */
  async getTheme(themeId: number): Promise<WritingTheme> {
    const response = await api.get(`${this.baseUrl}/themes/${themeId}`);
    return response.data;
  }

  /**
   * 创建写作主题
   */
  async createTheme(themeData: Omit<WritingTheme, 'id' | 'created_at' | 'updated_at'>): Promise<WritingTheme> {
    const response = await api.post(`${this.baseUrl}/themes`, themeData);
    return response.data;
  }

  /**
   * 更新写作主题
   */
  async updateTheme(themeId: number, themeData: Partial<WritingTheme>): Promise<WritingTheme> {
    const response = await api.put(`${this.baseUrl}/themes/${themeId}`, themeData);
    return response.data;
  }

  /**
   * 删除写作主题
   */
  async deleteTheme(themeId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/themes/${themeId}`);
  }

  // ==================== 字段管理 ====================

  /**
   * 获取主题字段列表
   */
  async getThemeFields(themeId: number): Promise<ThemeField[]> {
    const response = await api.get(`${this.baseUrl}/themes/${themeId}/fields`);
    return response.data;
  }

  /**
   * 创建主题字段
   */
  async createThemeField(themeId: number, fieldData: Omit<ThemeField, 'id'>): Promise<ThemeField> {
    const response = await api.post(`${this.baseUrl}/themes/${themeId}/fields`, fieldData);
    return response.data;
  }

  /**
   * 更新主题字段
   */
  async updateThemeField(fieldId: number, fieldData: Partial<ThemeField>): Promise<ThemeField> {
    const response = await api.put(`${this.baseUrl}/fields/${fieldId}`, fieldData);
    return response.data;
  }

  /**
   * 删除主题字段
   */
  async deleteThemeField(fieldId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/fields/${fieldId}`);
  }

  // ==================== 提示词模板管理 ====================

  /**
   * 获取主题提示词模板列表
   */
  async getThemeTemplates(themeId: number): Promise<PromptTemplate[]> {
    const response = await api.get(`${this.baseUrl}/themes/${themeId}/templates`);
    return response.data;
  }

  /**
   * 获取单个提示词模板
   */
  async getTemplate(templateId: number): Promise<PromptTemplate> {
    const response = await api.get(`${this.baseUrl}/templates/${templateId}`);
    return response.data;
  }

  /**
   * 创建提示词模板
   */
  async createTemplate(themeId: number, templateData: Omit<PromptTemplate, 'id' | 'usage_count' | 'success_rate'>): Promise<PromptTemplate> {
    const response = await api.post(`${this.baseUrl}/themes/${themeId}/templates`, templateData);
    return response.data;
  }

  /**
   * 更新提示词模板
   */
  async updateTemplate(templateId: number, templateData: Partial<PromptTemplate>): Promise<PromptTemplate> {
    const response = await api.put(`${this.baseUrl}/templates/${templateId}`, templateData);
    return response.data;
  }

  /**
   * 删除提示词模板
   */
  async deleteTemplate(templateId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/templates/${templateId}`);
  }

  // ==================== 分类管理 ====================

  /**
   * 获取主题分类列表
   */
  async getCategories(): Promise<ThemeCategory[]> {
    const response = await api.get(`${this.baseUrl}/categories`);
    return response.data;
  }

  /**
   * 创建主题分类
   */
  async createCategory(categoryData: Omit<ThemeCategory, 'id'>): Promise<ThemeCategory> {
    const response = await api.post(`${this.baseUrl}/categories`, categoryData);
    return response.data;
  }

  // ==================== 模板预览和测试 ====================

  /**
   * 预览提示词模板
   */
  async previewTemplate(previewData: TemplatePreviewRequest): Promise<TemplatePreviewResponse> {
    const response = await api.post(`${this.baseUrl}/templates/${previewData.template_id}/preview`, previewData);
    return response.data;
  }

  // ==================== 统计信息 ====================

  /**
   * 获取主题统计信息
   */
  async getStatistics(): Promise<any> {
    const response = await api.get(`${this.baseUrl}/statistics`);
    return response.data;
  }

  // ==================== 字段类型选项 ====================

  /**
   * 获取字段类型选项
   */
  getFieldTypeOptions() {
    return [
      { value: 'text', label: '单行文本' },
      { value: 'textarea', label: '多行文本' },
      { value: 'number', label: '数字' },
      { value: 'select', label: '下拉选择' },
      { value: 'radio', label: '单选按钮' },
      { value: 'checkbox', label: '复选框' },
      { value: 'date', label: '日期' },
      { value: 'datetime', label: '日期时间' },
      { value: 'email', label: '邮箱' },
      { value: 'url', label: '网址' },
      { value: 'file', label: '文件上传' }
    ];
  }

  /**
   * 获取模板类型选项
   */
  getTemplateTypeOptions() {
    return [
      { value: 'main', label: '主模板' },
      { value: 'alternative', label: '备用模板' },
      { value: 'simple', label: '简化模板' },
      { value: 'detailed', label: '详细模板' },
      { value: 'formal', label: '正式模板' },
      { value: 'casual', label: '非正式模板' }
    ];
  }

  /**
   * 获取AI模型选项
   */
  getAIModelOptions() {
    return [
      { value: 'deepseek-chat', label: 'DeepSeek Chat' },
      { value: 'deepseek-coder', label: 'DeepSeek Coder' },
      { value: 'gpt-4', label: 'GPT-4' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
      { value: 'claude-3', label: 'Claude 3' }
    ];
  }
}

export const writingThemeService = new WritingThemeService();
export default writingThemeService;
