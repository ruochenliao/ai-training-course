import {request} from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // models
  getModelList: (params = {}) => request.get('/system/model/list', { params }),
  getModelById: (params = {}) => request.get('/system/model/get', { params }),
  createModel: (data = {}) => request.post('/system/model/create', data),
  updateModel: (data = {}) => request.post('/system/model/update', data),
  deleteModel: (params = {}) => request.delete('/system/model/delete', { params }),

  // knowledge base
  getKnowledgeBaseList: (params = {}) => request.get('/knowledge/', { params }),
  getKnowledgeBaseById: (id) => request.get(`/knowledge/${id}`),
  createKnowledgeBase: (data = {}) => request.post('/knowledge/', data),
  updateKnowledgeBase: (id, data = {}) => request.put(`/knowledge/${id}`, data),
  deleteKnowledgeBase: (id) => request.delete(`/knowledge/${id}`),
  getKnowledgeTypes: () => request.get('/knowledge/types'),

  // knowledge bases
  getKnowledgeBases: (params = {}) => request.get('/knowledge/bases/', { params }),
  getKnowledgeBase: (id) => request.get(`/knowledge/bases/${id}`),
  createKnowledgeBase: (data = {}) => {
    // 转换文件大小单位（MB -> 字节）
    const submitData = { ...data }
    if (submitData.max_file_size_mb) {
      submitData.max_file_size = submitData.max_file_size_mb * 1024 * 1024
      delete submitData.max_file_size_mb
    }
    return request.post('/knowledge/bases/', submitData)
  },
  updateKnowledgeBase: (id, data = {}) => {
    // 转换文件大小单位（MB -> 字节）
    const submitData = { ...data }
    if (submitData.max_file_size_mb) {
      submitData.max_file_size = submitData.max_file_size_mb * 1024 * 1024
      delete submitData.max_file_size_mb
    }
    return request.put(`/knowledge/bases/${id}`, submitData)
  },
  deleteKnowledgeBase: (id) => request.delete(`/knowledge/bases/${id}`),
  getKnowledgeTypes: () => request.get('/knowledge/bases/types'),
  getKnowledgeBaseStats: (id) => request.get(`/knowledge/bases/${id}/stats`),

  // knowledge files
  getKnowledgeFiles: (kbId, params = {}) => request.get(`/knowledge/files/${kbId}/list`, { params }),
  getKnowledgeFile: (fileId) => request.get(`/knowledge/files/${fileId}/info`),
  uploadFile: (kbId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/knowledge/files/${kbId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000 // 5分钟超时
    })
  },
  batchUploadFiles: (kbId, files) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return request.post(`/knowledge/files/batch-upload/${kbId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000 // 10分钟超时
    })
  },
  downloadFile: (fileId) => request.get(`/knowledge/files/${fileId}/download`, { responseType: 'blob' }),
  deleteFile: (fileId) => request.delete(`/knowledge/files/${fileId}`),
  reprocessFile: (fileId) => request.post(`/knowledge/files/${fileId}/reprocess`),
  getFileProcessingStatus: (fileId) => request.get(`/knowledge/files/${fileId}/processing-status`),

  // knowledge search
  searchKnowledge: (params = {}) => request.post('/knowledge/search', params),
  getSearchableKnowledgeBases: () => request.get('/knowledge/knowledge-bases'),
  searchSimilarContent: (params = {}) => request.post('/knowledge/similar', params),
  getSearchStats: () => request.get('/knowledge/stats'),

  // 兼容旧API
  getKnowledgeFileList: (kbId, params = {}) => request.get(`/knowledge/files/${kbId}/list`, { params }),
  uploadKnowledgeFile: (kbId, data = {}) => request.post(`/knowledge/files/${kbId}/upload`, data),
  deleteKnowledgeFile: (fileId) => request.delete(`/knowledge/files/${fileId}`),
  getKnowledgeFileStatistics: (kbId) => request.get(`/knowledge/bases/${kbId}/stats`),
  retryKnowledgeFile: (kbId, fileId) => request.post(`/knowledge/files/${fileId}/reprocess`),

}
