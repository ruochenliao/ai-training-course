import { request } from '../utils/request';

// 角色接口
export interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  status: 'active' | 'inactive';
  permissions: string[];
  userCount: number;
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

// 权限接口
export interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: 'menu' | 'button' | 'api';
  parentId?: string;
  children?: Permission[];
}

// 角色查询参数
export interface RoleQueryParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  status?: 'active' | 'inactive';
  isSystem?: boolean;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 角色创建/更新参数
export interface RoleFormData {
  name: string;
  displayName: string;
  description?: string;
  status: 'active' | 'inactive';
  permissions?: string[];
}

// 分页响应
export interface PaginatedResponse<T> {
  list: T[];
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

export const roleApi = {
  // 获取角色列表
  getRoles: (params?: RoleQueryParams): Promise<PaginatedResponse<Role>> => {
    return request.get('/api/roles', { params });
  },

  // 获取角色详情
  getRoleById: (id: string): Promise<Role> => {
    return request.get(`/api/roles/${id}`);
  },

  // 创建角色
  createRole: (data: RoleFormData): Promise<Role> => {
    return request.post('/api/roles', data);
  },

  // 更新角色
  updateRole: (id: string, data: Partial<RoleFormData>): Promise<Role> => {
    return request.put(`/api/roles/${id}`, data);
  },

  // 删除角色
  deleteRole: (id: string): Promise<void> => {
    return request.delete(`/api/roles/${id}`);
  },

  // 批量删除角色
  batchDeleteRoles: (ids: string[]): Promise<void> => {
    return request.delete('/api/roles/batch', { data: { ids } });
  },

  // 切换角色状态
  toggleRoleStatus: (id: string, status: 'active' | 'inactive'): Promise<Role> => {
    return request.patch(`/api/roles/${id}/status`, { status });
  },

  // 复制角色
  copyRole: (id: string): Promise<Role> => {
    return request.post(`/api/roles/${id}/copy`);
  },

  // 获取权限列表
  getPermissions: (): Promise<Permission[]> => {
    return request.get('/api/permissions/tree');
  },

  // 获取角色权限
  getRolePermissions: (id: string): Promise<string[]> => {
    return request.get(`/api/roles/${id}/permissions`);
  },

  // 更新角色权限
  updateRolePermissions: (id: string, permissions: string[]): Promise<void> => {
    return request.put(`/api/roles/${id}/permissions`, { permissions });
  },

  // 获取角色用户列表
  getRoleUsers: (id: string, params?: { page?: number; pageSize?: number }): Promise<PaginatedResponse<any>> => {
    return request.get(`/api/roles/${id}/users`, { params });
  },

  // 分配用户到角色
  assignUsersToRole: (id: string, userIds: string[]): Promise<void> => {
    return request.post(`/api/roles/${id}/users`, { userIds });
  },

  // 从角色移除用户
  removeUsersFromRole: (id: string, userIds: string[]): Promise<void> => {
    return request.delete(`/api/roles/${id}/users`, { data: { userIds } });
  },

  // 检查角色名称是否可用
  checkRoleName: (name: string, excludeId?: string): Promise<{ available: boolean }> => {
    return request.get('/api/roles/check-name', {
      params: { name, excludeId },
    });
  },

  // 获取角色统计信息
  getRoleStats: (): Promise<{
    totalRoles: number;
    activeRoles: number;
    systemRoles: number;
    customRoles: number;
  }> => {
    return request.get('/api/roles/stats');
  },

  // 导出角色
  exportRoles: (params?: RoleQueryParams): Promise<Blob> => {
    return request.get('/api/roles/export', {
      params,
      responseType: 'blob',
    });
  },

  // 导入角色
  importRoles: (file: File): Promise<{
    success: number;
    failed: number;
    errors: string[];
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    return request.post('/api/roles/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};