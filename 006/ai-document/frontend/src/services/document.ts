import api from './api';
import { Document, DocumentList, DocumentCreate, DocumentUpdate } from '@/types';

export const documentService = {
  // 创建文档
  async createDocument(data: DocumentCreate): Promise<Document> {
    const response = await api.post<Document>('/documents/', data);
    return response.data;
  },

  // 获取文档列表
  async getDocuments(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<DocumentList[]> {
    const response = await api.get<DocumentList[]>('/documents/', { params });
    return response.data;
  },

  // 获取单个文档
  async getDocument(id: number): Promise<Document> {
    const response = await api.get<Document>(`/documents/${id}`);
    return response.data;
  },

  // 更新文档
  async updateDocument(id: number, data: DocumentUpdate): Promise<Document> {
    const response = await api.put<Document>(`/documents/${id}`, data);
    return response.data;
  },

  // 删除文档
  async deleteDocument(id: number): Promise<void> {
    await api.delete(`/documents/${id}`);
  },

  // 搜索文档
  async searchDocuments(query: string, params?: {
    skip?: number;
    limit?: number;
  }): Promise<DocumentList[]> {
    const response = await api.get<DocumentList[]>('/documents/', {
      params: { ...params, search: query }
    });
    return response.data;
  },
};
