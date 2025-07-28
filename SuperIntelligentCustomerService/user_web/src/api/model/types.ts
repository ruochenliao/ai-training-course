// API响应的基础结构
export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

// 可用模型列表响应类型
export type AvailableModelsResponse = ApiResponse<GetSessionListVO[]>;

// 查询用户模型列表返回的数据结构（保留用于其他API）
export interface GetSessionListVO {
  id?: number;

  // 提供商信息
  provider_name?: string;
  provider_display_name?: string;
  base_url?: string;

  // 基本信息
  model_name?: string;
  display_name?: string;
  description?: string;
  category?: string;

  // 模型能力
  vision?: boolean;
  function_calling?: boolean;
  json_output?: boolean;
  structured_output?: boolean;
  multiple_system_messages?: boolean;
  model_family?: string;

  // 技术配置
  max_tokens?: number;
  temperature?: number;
  top_p?: number;

  // 定价信息
  input_price_per_1k?: number;
  output_price_per_1k?: number;

  // 系统配置
  system_prompt?: string;

  // 状态管理
  is_active?: boolean;
  is_default?: boolean;
  sort_order?: number;

  // 时间戳
  created_at?: string;
  updated_at?: string;

  // 兼容旧字段（保留用于向后兼容）
  model_describe?: string;
  model_price?: number;
  model_type?: string;
  model_show?: string;
  api_host?: string;
  api_key?: string;
  remark?: string;
  provider_id?: number;
  provider?: {
    id: number;
    name: string;
    display_name: string;
    base_url: string;
  };
}
