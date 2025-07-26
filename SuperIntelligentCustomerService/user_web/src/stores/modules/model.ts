import type {GetSessionListVO} from '@/api/model/types';
import {defineStore} from 'pinia';
import {getSystemAvailableModels} from '@/api';

// 模型显示名称映射
const MODEL_DISPLAY_NAMES: Record<string, string> = {
  'deepseek-chat': 'DeepSeek Chat',
  'deepseek-reasoner': 'DeepSeek Reasoner',
  'qwen-vl-plus': '通义千问 VL Plus',
};

// 模型描述映射
const MODEL_DESCRIPTIONS: Record<string, string> = {
  'deepseek-chat': '强大的对话模型，支持多轮对话和复杂推理',
  'deepseek-reasoner': '专业的推理模型，擅长逻辑分析和问题解决',
  'qwen-vl-plus': '多模态模型，支持图像理解和视觉问答',
};

// 将字符串数组转换为组件需要的格式
function adaptModelsToLegacyFormat(models: string[]): GetSessionListVO[] {
  return models.map((modelName, index) => ({
    id: index + 1,
    model_name: modelName,
    model_show: MODEL_DISPLAY_NAMES[modelName] || modelName,
    display_name: MODEL_DISPLAY_NAMES[modelName] || modelName,
    remark: MODEL_DESCRIPTIONS[modelName] || `${modelName} 模型`,
    is_active: true,
    is_default: index === 0, // 第一个模型设为默认
  }));
}

// 模型管理
export const useModelStore = defineStore('model', () => {
  // 当前模型
  const currentModelInfo = ref<GetSessionListVO>({});

  // 设置当前模型
  const setCurrentModelInfo = (modelInfo: GetSessionListVO) => {
    currentModelInfo.value = modelInfo;
  };

  // 模型菜单列表
  const modelList = ref<GetSessionListVO[]>([]);

  // 请求模型菜单列表
  const requestModelList = async () => {
    try {
      const res = await getSystemAvailableModels();
      if (res.code === 200 && Array.isArray(res.data)) {
        // 将字符串数组转换为组件需要的格式
        modelList.value = adaptModelsToLegacyFormat(res.data);
      } else {
        console.error('获取模型列表失败:', res.msg);
        modelList.value = [];
      }
    }
    catch (error) {
      console.error('requestModelList错误', error);
      modelList.value = [];
    }
  };

  return {
    currentModelInfo,
    setCurrentModelInfo,
    modelList,
    requestModelList,
  };
});
