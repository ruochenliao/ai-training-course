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
}
