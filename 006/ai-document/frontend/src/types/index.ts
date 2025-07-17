// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at?: string;
}

export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// 文档相关类型
export interface Document {
  id: number;
  title: string;
  content: string;
  summary?: string;
  word_count: number;
  user_id: number;
  is_public: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string;
}

export interface DocumentList {
  id: number;
  title: string;
  summary?: string;
  word_count: number;
  is_public: boolean;
  created_at: string;
  updated_at?: string;
}

export interface DocumentCreate {
  title: string;
  content?: string;
  summary?: string;
  is_public?: boolean;
}

export interface DocumentUpdate {
  title?: string;
  content?: string;
  summary?: string;
  is_public?: boolean;
}

// AI相关类型
export interface AIRequest {
  ai_type: string;
  prompt: string;
  document_id?: number;
  context?: string;
  metadata?: Record<string, any>;
}

export interface AIResponse {
  session_id: string;
  status: string;
  response?: string;
  error?: string;
}

export interface AISession {
  id: number;
  session_id: string;
  user_id: number;
  document_id?: number;
  ai_type: string;
  prompt: string;
  response?: string;
  status: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface AIStreamResponse {
  session_id: string;
  content: string;
  is_complete: boolean;
  error?: string;
}

// AI工具类型
export type AIToolType = 'ai_writer' | 'ai_polish' | 'deepseek' | 'ai_outline' | 'ai_collaborative' | 'ai_review' | 'ai_research';

export interface AITool {
  type: AIToolType;
  name: string;
  description: string;
  icon: string;
}

// AI写作向导相关类型
export interface WritingTemplate {
  category: string;
  type: string;
  name: string;
  description: string;
}

export interface WritingScenario {
  step: number;
  category?: string;
  type?: string;
  title?: string;
  keywords?: string;
  reason?: string;
  content?: string;
  purpose?: string;
  contentReference?: string;
  dataReference?: string;
  templateFormat?: string;
}

export interface WritingWizardRequest {
  scenario: WritingScenario;
  ai_type: string;
  prompt: string;
  context?: string;
  metadata?: Record<string, any>;
}

// 模板管理相关类型
export interface TemplateCategory {
  id: number;
  name: string;
  description?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TemplateType {
  id: number;
  category_id: number;
  name: string;
  description?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  category?: TemplateCategory;
}

export interface TemplateFile {
  id: number;
  template_type_id: number;
  name: string;
  description?: string;
  file_path?: string;
  file_size?: number;
  file_type?: string;
  content?: string;
  is_default: boolean;
  is_active: boolean;
  usage_count: number;
  created_by?: number;
  created_at: string;
  updated_at?: string;
  template_type?: TemplateType;
}

export interface TemplateTreeNode {
  id: number;
  name: string;
  type: 'category' | 'type' | 'file';
  description?: string;
  children: TemplateTreeNode[];
  is_active: boolean;
  sort_order: number;
}

// 智能体配置相关类型
export interface AgentConfig {
  id: number;
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
  created_at: string;
  updated_at?: string;
}

export interface AgentTool {
  id: number;
  name: string;
  description?: string;
  function_name: string;
  parameters_schema?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AgentModel {
  id: number;
  name: string;
  display_name: string;
  provider: string;
  api_base?: string;
  max_tokens: number;
  supports_tools: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// 写作场景配置相关类型
export interface WritingFieldConfig {
  id?: number;
  scenario_config_id?: number;
  field_name: string;      // 字段显示名称
  field_key: string;       // 字段键名
  field_type: 'text' | 'textarea' | 'select';  // 字段类型
  required: boolean;       // 是否必填
  ai_enabled: boolean;     // 是否支持AI生成
  doc_enabled: boolean;    // 是否支持选择文档
  placeholder?: string;    // 占位符
  options?: string[];      // 选择项（用于select类型）
  sort_order?: number;     // 排序
  agent_config_id?: number; // 关联的智能体配置ID
  agent_config?: AgentConfig; // 关联的智能体配置
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface WritingScenarioConfig {
  id: number;
  template_type_id: number;
  config_name: string;
  description?: string;
  field_configs: WritingFieldConfig[];
  default_config?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface WritingScenarioConfigCreate {
  template_type_id: number;
  config_name: string;
  description?: string;
  field_configs: WritingFieldConfig[];
  default_config?: Record<string, any>;
  is_active?: boolean;
}

export interface WritingScenarioConfigUpdate {
  template_type_id?: number;
  config_name?: string;
  description?: string;
  field_configs?: WritingFieldConfig[];
  default_config?: Record<string, any>;
  is_active?: boolean;
}

export interface TemplateCategoryWithTypes extends TemplateCategory {
  template_types: TemplateType[];
}

// 模板创建和更新类型
export interface TemplateCategoryCreate {
  name: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface TemplateTypeCreate {
  category_id: number;
  name: string;
  description?: string;
  sort_order?: number;
  is_active?: boolean;
}

export interface TemplateFileCreate {
  template_type_id: number;
  name: string;
  description?: string;
  content?: string;
  is_default?: boolean;
  is_active?: boolean;
}
