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

  // knowledge files
  getKnowledgeFileList: (kbId, params = {}) => request.get(`/knowledge/${kbId}/files`, { params }),
  uploadKnowledgeFile: (kbId, data = {}) => request.post(`/knowledge/${kbId}/files`, data),
  deleteKnowledgeFile: (fileId) => request.delete(`/knowledge/files/${fileId}`),
  getKnowledgeFileStatistics: (kbId) => request.get(`/knowledge/${kbId}/files/statistics`),

}
