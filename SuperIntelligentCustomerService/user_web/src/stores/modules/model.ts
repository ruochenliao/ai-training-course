import type {GetSessionListVO} from '@/api/model/types';
import {defineStore} from 'pinia';
import {ref} from 'vue';
import {getSystemAvailableModels} from '@/api';

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
        // 直接使用后端返回的完整模型数据
        modelList.value = res.data.map((model, index) => ({
          ...model,
          // 确保向后兼容的字段映射
          model_show: model.display_name || model.model_name,
          remark: model.description || `${model.model_name} 模型`,
          // 如果没有设置默认模型，将第一个设为默认
          is_default: model.is_default || (index === 0 && !res.data.some(m => m.is_default))
        }));
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
