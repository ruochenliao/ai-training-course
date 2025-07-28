import type {GetSessionListVO, AvailableModelsResponse} from './types';
import {get} from '@/utils/request';

// 获取系统可用模型列表
export function getSystemAvailableModels() {
  return get<AvailableModelsResponse>('/api/v1/llm/available-models');
}

// 获取当前用户的模型列表（保留用于其他功能）
export function getModelList() {
  return get<GetSessionListVO[]>('/api/v1/llm/models');
}
