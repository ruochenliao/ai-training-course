import api from './api';
import {
  TemplateCategory,
  TemplateType,
  TemplateFile,
  TemplateTreeNode,
  TemplateCategoryWithTypes,
  TemplateCategoryCreate,
  TemplateTypeCreate,
  TemplateFileCreate,
  WritingScenarioConfig,
  WritingScenarioConfigCreate,
  WritingScenarioConfigUpdate
} from '@/types';

export const templateService = {
  // 模板分类相关
  async getCategories(): Promise<TemplateCategory[]> {
    const response = await api.get<TemplateCategory[]>('/templates/categories');
    return response.data;
  },

  async getCategory(id: number): Promise<TemplateCategory> {
    const response = await api.get<TemplateCategory>(`/templates/categories/${id}`);
    return response.data;
  },

  async createCategory(data: TemplateCategoryCreate): Promise<TemplateCategory> {
    const response = await api.post<TemplateCategory>('/templates/categories', data);
    return response.data;
  },

  async updateCategory(id: number, data: Partial<TemplateCategoryCreate>): Promise<TemplateCategory> {
    const response = await api.put<TemplateCategory>(`/templates/categories/${id}`, data);
    return response.data;
  },

  async deleteCategory(id: number): Promise<void> {
    await api.delete(`/templates/categories/${id}`);
  },

  // 模板类型相关
  async getTypesByCategory(categoryId: number): Promise<TemplateType[]> {
    const response = await api.get<TemplateType[]>(`/templates/categories/${categoryId}/types`);
    return response.data;
  },

  async getType(id: number): Promise<TemplateType> {
    const response = await api.get<TemplateType>(`/templates/types/${id}`);
    return response.data;
  },

  async createType(data: TemplateTypeCreate): Promise<TemplateType> {
    const response = await api.post<TemplateType>('/templates/types', data);
    return response.data;
  },

  async updateType(id: number, data: Partial<TemplateTypeCreate>): Promise<TemplateType> {
    const response = await api.put<TemplateType>(`/templates/types/${id}`, data);
    return response.data;
  },

  async deleteType(id: number): Promise<void> {
    await api.delete(`/templates/types/${id}`);
  },

  // 模板文件相关
  async getFilesByType(typeId: number): Promise<TemplateFile[]> {
    const response = await api.get<TemplateFile[]>(`/templates/types/${typeId}/files`);
    return response.data;
  },

  async getFile(id: number): Promise<TemplateFile> {
    const response = await api.get<TemplateFile>(`/templates/files/${id}`);
    return response.data;
  },

  async createFile(data: TemplateFileCreate): Promise<TemplateFile> {
    const response = await api.post<TemplateFile>('/templates/files', data);
    return response.data;
  },

  async updateFile(id: number, data: Partial<TemplateFileCreate>): Promise<TemplateFile> {
    const response = await api.put<TemplateFile>(`/templates/files/${id}`, data);
    return response.data;
  },

  async deleteFile(id: number): Promise<void> {
    await api.delete(`/templates/files/${id}`);
  },

  async useTemplateFile(id: number): Promise<void> {
    await api.post(`/templates/files/${id}/use`);
  },

  // 文件上传
  async uploadTemplateFile(
    file: File,
    typeId: number,
    name?: string,
    description?: string
  ): Promise<TemplateFile> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type_id', typeId.toString());
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);

    const response = await api.post<TemplateFile>('/templates/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 综合查询
  async getTemplateTree(): Promise<TemplateTreeNode[]> {
    const response = await api.get<TemplateTreeNode[]>('/templates/tree');
    return response.data;
  },

  async getCategoriesWithTypes(): Promise<TemplateCategoryWithTypes[]> {
    const response = await api.get<TemplateCategoryWithTypes[]>('/templates/categories-with-types');
    return response.data;
  },

  async searchTemplates(keyword: string): Promise<any> {
    const response = await api.get(`/templates/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  // 数据初始化
  async initTemplateData(): Promise<any> {
    const response = await api.post('/templates/init');
    return response.data;
  },

  async resetTemplateData(): Promise<any> {
    const response = await api.post('/templates/reset');
    return response.data;
  },

  async getTemplateStatistics(): Promise<any> {
    const response = await api.get('/templates/statistics');
    return response.data;
  },

  // 写作场景配置相关
  async getWritingScenarioConfig(typeId: number): Promise<WritingScenarioConfig> {
    const response = await api.get<WritingScenarioConfig>(`/templates/types/${typeId}/writing-scenario`);
    return response.data;
  },

  async createWritingScenarioConfig(typeId: number, data: WritingScenarioConfigCreate): Promise<WritingScenarioConfig> {
    const response = await api.post<WritingScenarioConfig>(`/templates/types/${typeId}/writing-scenario`, data);
    return response.data;
  },

  async updateWritingScenarioConfig(configId: number, data: WritingScenarioConfigUpdate): Promise<WritingScenarioConfig> {
    const response = await api.put<WritingScenarioConfig>(`/templates/writing-scenario/${configId}`, data);
    return response.data;
  },

  async deleteWritingScenarioConfig(configId: number): Promise<void> {
    await api.delete(`/templates/writing-scenario/${configId}`);
  },
};
