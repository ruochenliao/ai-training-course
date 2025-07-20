/**
 * 知识库管理相关API
 */
import {request} from '../request'

export interface KnowledgeBase {
  id?: number
  name: string
  description?: string
  knowledge_type: string
  is_public: boolean
  config?: Record<string, any>
  embedding_model?: string
  chunk_size?: number
  chunk_overlap?: number
  max_file_size?: number
  allowed_file_types?: string[]
  file_count?: number
  total_size?: number
  status?: string
  owner_id?: number
  created_at?: string
  updated_at?: string
  last_updated_at?: string
  status_stats?: Record<string, number>
}

export interface KnowledgeFile {
  id?: number
  name: string
  original_name: string
  file_path: string
  file_size: number
  file_type: string
  file_hash?: string
  knowledge_base_id: number
  embedding_status: string
  embedding_error?: string
  processed_at?: string
  chunk_count?: number
  vector_ids?: string[]
  is_deleted?: boolean
  deleted_at?: string
  created_at?: string
  updated_at?: string
}

export interface KnowledgeBaseListParams {
  page?: number
  page_size?: number
  knowledge_type?: string
  is_public?: boolean
  search?: string
}

export interface KnowledgeFileListParams {
  page?: number
  page_size?: number
  status?: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data: T
  msg: string
  total?: number
  page?: number
  page_size?: number
}

/**
 * 知识库管理API
 */
export const knowledgeApi = {
  // 知识库管理
  
  /**
   * 获取知识库列表
   */
  getKnowledgeBases(params?: KnowledgeBaseListParams): Promise<ApiResponse<KnowledgeBase[]>> {
    return request.get('/knowledge/bases/', { params })
  },

  /**
   * 获取知识库详情
   */
  getKnowledgeBase(id: number): Promise<ApiResponse<KnowledgeBase>> {
    return request.get(`/knowledge/bases/${id}`)
  },

  /**
   * 创建知识库
   */
  createKnowledgeBase(data: Partial<KnowledgeBase>): Promise<ApiResponse<KnowledgeBase>> {
    // 转换文件大小单位（MB -> 字节）
    const submitData = { ...data }
    if (submitData.max_file_size_mb) {
      submitData.max_file_size = submitData.max_file_size_mb * 1024 * 1024
      delete submitData.max_file_size_mb
    }
    return request.post('/knowledge/bases/', submitData)
  },

  /**
   * 更新知识库
   */
  updateKnowledgeBase(id: number, data: Partial<KnowledgeBase>): Promise<ApiResponse<KnowledgeBase>> {
    // 转换文件大小单位（MB -> 字节）
    const submitData = { ...data }
    if (submitData.max_file_size_mb) {
      submitData.max_file_size = submitData.max_file_size_mb * 1024 * 1024
      delete submitData.max_file_size_mb
    }
    return request.put(`/knowledge/bases/${id}`, submitData)
  },

  /**
   * 删除知识库
   */
  deleteKnowledgeBase(id: number): Promise<ApiResponse> {
    return request.delete(`/knowledge/bases/${id}`)
  },

  /**
   * 获取知识库类型列表
   */
  getKnowledgeTypes(): Promise<ApiResponse<Array<{ value: string; label: string }>>> {
    return request.get('/knowledge/bases/types')
  },

  /**
   * 获取知识库统计信息
   */
  getKnowledgeBaseStats(id: number): Promise<ApiResponse> {
    return request.get(`/knowledge/bases/${id}/stats`)
  },

  // 文件管理

  /**
   * 获取知识库文件列表
   */
  getKnowledgeFiles(kbId: number, params?: KnowledgeFileListParams): Promise<ApiResponse<KnowledgeFile[]>> {
    return request.get(`/knowledge/files/${kbId}/list`, { params })
  },

  /**
   * 获取文件详情
   */
  getKnowledgeFile(fileId: number): Promise<ApiResponse<KnowledgeFile>> {
    return request.get(`/knowledge/files/${fileId}/info`)
  },

  /**
   * 上传文件到知识库
   */
  uploadFile(kbId: number, file: File): Promise<ApiResponse<KnowledgeFile>> {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post(`/knowledge/files/${kbId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000 // 5分钟超时
    })
  },

  /**
   * 批量上传文件
   */
  batchUploadFiles(kbId: number, files: File[]): Promise<ApiResponse> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    return request.post(`/knowledge/files/batch-upload/${kbId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 600000 // 10分钟超时
    })
  },

  /**
   * 下载文件
   */
  downloadFile(fileId: number): Promise<Blob> {
    return request.get(`/knowledge/files/${fileId}/download`, {
      responseType: 'blob'
    })
  },

  /**
   * 删除文件
   */
  deleteFile(fileId: number): Promise<ApiResponse> {
    return request.delete(`/knowledge/files/${fileId}`)
  },

  /**
   * 重新处理文件
   */
  reprocessFile(fileId: number): Promise<ApiResponse> {
    return request.post(`/knowledge/files/${fileId}/reprocess`)
  },

  /**
   * 获取文件处理状态
   */
  getFileProcessingStatus(fileId: number): Promise<ApiResponse> {
    return request.get(`/knowledge/files/${fileId}/processing-status`)
  },

  // 搜索相关

  /**
   * 搜索知识库内容
   */
  searchKnowledge(params: {
    query: string
    knowledge_base_ids?: number[]
    limit?: number
    score_threshold?: number
  }): Promise<ApiResponse> {
    return request.post('/knowledge/search', params)
  }
}

// 导出默认API对象，兼容现有代码
export default {
  // 知识库管理
  getKnowledgeBases: knowledgeApi.getKnowledgeBases,
  getKnowledgeBase: knowledgeApi.getKnowledgeBase,
  createKnowledgeBase: knowledgeApi.createKnowledgeBase,
  updateKnowledgeBase: knowledgeApi.updateKnowledgeBase,
  deleteKnowledgeBase: knowledgeApi.deleteKnowledgeBase,
  getKnowledgeTypes: knowledgeApi.getKnowledgeTypes,
  getKnowledgeBaseStats: knowledgeApi.getKnowledgeBaseStats,

  // 文件管理
  getKnowledgeFiles: knowledgeApi.getKnowledgeFiles,
  getKnowledgeFile: knowledgeApi.getKnowledgeFile,
  uploadFile: knowledgeApi.uploadFile,
  batchUploadFiles: knowledgeApi.batchUploadFiles,
  downloadFile: knowledgeApi.downloadFile,
  deleteFile: knowledgeApi.deleteFile,
  reprocessFile: knowledgeApi.reprocessFile,
  getFileProcessingStatus: knowledgeApi.getFileProcessingStatus,

  // 搜索
  searchKnowledge: knowledgeApi.searchKnowledge
}

/**
 * 文件大小格式化工具函数
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 文件类型图标映射
 */
export const getFileTypeIcon = (fileType: string): string => {
  const typeMap: Record<string, string> = {
    'pdf': 'mdi:file-pdf-box',
    'docx': 'mdi:file-word-box',
    'doc': 'mdi:file-word-box',
    'txt': 'mdi:file-document-outline',
    'md': 'mdi:language-markdown',
    'xlsx': 'mdi:file-excel-box',
    'xls': 'mdi:file-excel-box',
    'pptx': 'mdi:file-powerpoint-box',
    'ppt': 'mdi:file-powerpoint-box'
  }
  
  const ext = fileType.toLowerCase().replace('.', '')
  return typeMap[ext] || 'mdi:file-outline'
}

/**
 * 处理状态颜色映射
 */
export const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    'pending': 'warning',
    'processing': 'info',
    'completed': 'success',
    'failed': 'error'
  }
  return colorMap[status] || 'default'
}

/**
 * 处理状态文本映射
 */
export const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    'pending': '等待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '处理失败'
  }
  return textMap[status] || status
}
