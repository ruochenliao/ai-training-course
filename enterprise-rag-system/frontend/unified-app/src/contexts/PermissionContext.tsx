'use client';

import React, {createContext, ReactNode, useContext, useEffect, useState} from 'react';
import {useAuth} from './AuthContext';
import {Permission, PermissionCheckResponse, PermissionContextType, UserRole} from '@/types';
import {api} from '@/utils/api';

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

interface PermissionProviderProps {
  children: ReactNode;
}

export const PermissionProvider: React.FC<PermissionProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [permissions, setPermissions] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // 获取用户权限和角色
  const fetchUserPermissions = async () => {
    if (!user || !isAuthenticated) {
      setPermissions([]);
      setRoles([]);
      return;
    }

    try {
      setLoading(true);

      // 获取用户角色
      const userRolesResponse = await api.get<UserRole[]>(`/rbac/users/${user.id}/roles`);
      const userRoles = userRolesResponse.data;
      const roleNames = userRoles.map(ur => ur.role?.code || '').filter(Boolean);
      setRoles(roleNames);

      // 获取用户权限（通过角色和直接权限）
      const userPermissions: string[] = [];
      
      // 从角色获取权限
      for (const userRole of userRoles) {
        if (userRole.role?.permissions) {
          userRole.role.permissions.forEach(permission => {
            if (!userPermissions.includes(permission.code)) {
              userPermissions.push(permission.code);
            }
          });
        }
      }

      // 获取直接权限（如果有API）
      try {
        const directPermissionsResponse = await api.get<Permission[]>(`/users/${user.id}/permissions`);
        directPermissionsResponse.data.forEach(permission => {
          if (!userPermissions.includes(permission.code)) {
            userPermissions.push(permission.code);
          }
        });
      } catch (error) {
        // 直接权限API可能不存在，忽略错误
        console.debug('Direct permissions API not available');
      }

      setPermissions(userPermissions);
    } catch (error) {
      console.error('Failed to fetch user permissions:', error);
      setPermissions([]);
      setRoles([]);
    } finally {
      setLoading(false);
    }
  };

  // 检查单个权限
  const hasPermission = (permission: string): boolean => {
    if (!user || !isAuthenticated) return false;
    if (user.is_superuser) return true;
    return permissions.includes(permission);
  };

  // 检查单个角色
  const hasRole = (role: string): boolean => {
    if (!user || !isAuthenticated) return false;
    if (user.is_superuser) return true;
    return roles.includes(role);
  };

  // 检查是否有任意一个权限
  const hasAnyPermission = (permissionList: string[]): boolean => {
    if (!user || !isAuthenticated) return false;
    if (user.is_superuser) return true;
    return permissionList.some(permission => permissions.includes(permission));
  };

  // 检查是否有所有权限
  const hasAllPermissions = (permissionList: string[]): boolean => {
    if (!user || !isAuthenticated) return false;
    if (user.is_superuser) return true;
    return permissionList.every(permission => permissions.includes(permission));
  };

  // 批量检查权限
  const checkPermissions = async (permissionCodes: string[]): Promise<Record<string, boolean>> => {
    if (!user || !isAuthenticated) {
      return permissionCodes.reduce((acc, code) => ({ ...acc, [code]: false }), {});
    }

    if (user.is_superuser) {
      return permissionCodes.reduce((acc, code) => ({ ...acc, [code]: true }), {});
    }

    try {
      const response = await api.post<PermissionCheckResponse>('/rbac/check-permissions', {
        user_id: user.id,
        permission_codes: permissionCodes
      });
      return response.data.permissions;
    } catch (error) {
      console.error('Failed to check permissions:', error);
      // 降级到本地检查
      return permissionCodes.reduce((acc, code) => ({
        ...acc,
        [code]: permissions.includes(code)
      }), {});
    }
  };

  // 刷新权限
  const refreshPermissions = async () => {
    await fetchUserPermissions();
  };

  // 当用户状态变化时重新获取权限
  useEffect(() => {
    fetchUserPermissions();
  }, [user, isAuthenticated]);

  const value: PermissionContextType = {
    permissions,
    roles,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    checkPermissions,
    refreshPermissions,
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = (): PermissionContextType => {
  const context = useContext(PermissionContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

// 权限检查Hook
export const usePermissionCheck = (permission: string | string[]) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermissions();

  if (typeof permission === 'string') {
    return hasPermission(permission);
  }

  return {
    hasAny: hasAnyPermission(permission),
    hasAll: hasAllPermissions(permission),
  };
};

// 角色检查Hook
export const useRoleCheck = (role: string | string[]) => {
  const { hasRole, roles } = usePermissions();

  if (typeof role === 'string') {
    return hasRole(role);
  }

  return {
    hasAny: role.some(r => hasRole(r)),
    hasAll: role.every(r => hasRole(r)),
    userRoles: roles,
  };
};
