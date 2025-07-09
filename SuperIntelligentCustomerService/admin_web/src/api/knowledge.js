/**
 * 知识库管理API接口
 */
import { request } from '@/utils/http'

// 知识库管理API
export const knowledgeBaseApi = {
  // 获取知识库列表
  getList(params = {}) {
    return request.get('/knowledge/bases', { params })
  },

  // 获取知识库详情
  getDetail(id) {
    return request.get(`/knowledge/bases/${id}`)
  },

  // 创建知识库
  create(data) {
    return request.post('/knowledge/bases', data)
  },

  // 更新知识库
  update(id, data) {
    return request.put(`/knowledge/bases/${id}`, data)
  },

  // 删除知识库
  delete(id) {
    return request.delete(`/knowledge/bases/${id}`)
  },

  // 获取知识库类型
  getTypes() {
    return request.get('/knowledge/bases/types')
  },

  // 获取用户统计信息
  getStatistics() {
    return request.get('/knowledge/bases/statistics')
  }
}

// 知识文件管理API
export const knowledgeFileApi = {
  // 获取文件列表
  getList(kbId, params = {}) {
    return request.get(`/knowledge/files/${kbId}`, { params })
  },

  // 获取文件详情
  getDetail(fileId) {
    return request.get(`/knowledge/files/detail/${fileId}`)
  },

  // 上传文件
  upload(kbId, file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post(`/knowledge/files/${kbId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    })
  },

  // 删除文件
  delete(fileId) {
    return request.delete(`/knowledge/files/${fileId}`)
  },

  // 重试处理
  retry(fileId) {
    return request.post(`/knowledge/files/${fileId}/retry`)
  },

  // 获取处理统计
  getStatistics(kbId) {
    return request.get(`/knowledge/files/${kbId}/statistics`)
  },

  // 获取支持的文件类型
  getTypes() {
    return request.get('/knowledge/files/types')
  }
}

// 导出默认对象
export default {
  knowledgeBase: knowledgeBaseApi,
  knowledgeFile: knowledgeFileApi
}
