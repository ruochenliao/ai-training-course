// 查询用户模型列表返回的数据结构
export interface GetSessionListVO {
  id?: number;
  category?: string;
  model_name?: string;
  model_describe?: string;
  model_price?: number;
  model_type?: string;
  model_show?: string;
  system_prompt?: string;
  api_host?: string;
  api_key?: string;
  remark?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;

  // 新增字段，兼容新的LLM模型结构
  display_name?: string;
  description?: string;
  provider_id?: number;
  provider?: {
    id: number;
    name: string;
    display_name: string;
    base_url: string;
  };

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

  // 状态管理
  is_default?: boolean;
  sort_order?: number;
}
