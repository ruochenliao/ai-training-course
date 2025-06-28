'use client';

import React, { ReactNode } from 'react';
import { usePermissions } from '@/contexts/PermissionContext';
import { useAuth } from '@/contexts/AuthContext';
import { Result, Spin } from 'antd';
import { LockOutlined } from '@ant-design/icons';

interface PermissionGuardProps {
  children: ReactNode;
  permission?: string | string[];
  role?: string | string[];
  requireAll?: boolean; // 是否需要所有权限/角色，默认false（任意一个即可）
  fallback?: ReactNode; // 无权限时显示的内容
  loading?: ReactNode; // 加载时显示的内容
  showFallback?: boolean; // 是否显示无权限提示，默认true
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  permission,
  role,
  requireAll = false,
  fallback,
  loading,
  showFallback = true,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { hasPermission, hasRole, hasAnyPermission, hasAllPermissions } = usePermissions();

  // 如果用户未登录，不显示内容
  if (!isAuthenticated || !user) {
    return loading || <Spin size="small" />;
  }

  // 超级用户拥有所有权限
  if (user.is_superuser) {
    return <>{children}</>;
  }

  // 检查权限
  let hasRequiredPermission = true;
  if (permission) {
    if (typeof permission === 'string') {
      hasRequiredPermission = hasPermission(permission);
    } else {
      hasRequiredPermission = requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
  }

  // 检查角色
  let hasRequiredRole = true;
  if (role) {
    if (typeof role === 'string') {
      hasRequiredRole = hasRole(role);
    } else {
      hasRequiredRole = requireAll
        ? role.every(r => hasRole(r))
        : role.some(r => hasRole(r));
    }
  }

  // 如果有权限和角色，显示内容
  if (hasRequiredPermission && hasRequiredRole) {
    return <>{children}</>;
  }

  // 无权限时的处理
  if (fallback) {
    return <>{fallback}</>;
  }

  if (!showFallback) {
    return null;
  }

  return (
    <Result
      status="403"
      title="403"
      subTitle="抱歉，您没有权限访问此页面。"
      icon={<LockOutlined />}
    />
  );
};

// 权限按钮组件
interface PermissionButtonProps {
  children: ReactNode;
  permission?: string | string[];
  role?: string | string[];
  requireAll?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const PermissionButton: React.FC<PermissionButtonProps> = ({
  children,
  permission,
  role,
  requireAll = false,
  disabled = false,
  onClick,
  className,
  style,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { hasPermission, hasRole, hasAnyPermission, hasAllPermissions } = usePermissions();

  // 如果用户未登录，禁用按钮
  if (!isAuthenticated || !user) {
    return null;
  }

  // 超级用户拥有所有权限
  if (user.is_superuser) {
    return (
      <button
        disabled={disabled}
        onClick={onClick}
        className={className}
        style={style}
      >
        {children}
      </button>
    );
  }

  // 检查权限
  let hasRequiredPermission = true;
  if (permission) {
    if (typeof permission === 'string') {
      hasRequiredPermission = hasPermission(permission);
    } else {
      hasRequiredPermission = requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
  }

  // 检查角色
  let hasRequiredRole = true;
  if (role) {
    if (typeof role === 'string') {
      hasRequiredRole = hasRole(role);
    } else {
      hasRequiredRole = requireAll
        ? role.every(r => hasRole(r))
        : role.some(r => hasRole(r));
    }
  }

  // 如果没有权限，不显示按钮
  if (!hasRequiredPermission || !hasRequiredRole) {
    return null;
  }

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={className}
      style={style}
    >
      {children}
    </button>
  );
};

// 权限链接组件
interface PermissionLinkProps {
  children: ReactNode;
  href: string;
  permission?: string | string[];
  role?: string | string[];
  requireAll?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const PermissionLink: React.FC<PermissionLinkProps> = ({
  children,
  href,
  permission,
  role,
  requireAll = false,
  className,
  style,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { hasPermission, hasRole, hasAnyPermission, hasAllPermissions } = usePermissions();

  // 如果用户未登录，不显示链接
  if (!isAuthenticated || !user) {
    return null;
  }

  // 超级用户拥有所有权限
  if (user.is_superuser) {
    return (
      <a href={href} className={className} style={style}>
        {children}
      </a>
    );
  }

  // 检查权限
  let hasRequiredPermission = true;
  if (permission) {
    if (typeof permission === 'string') {
      hasRequiredPermission = hasPermission(permission);
    } else {
      hasRequiredPermission = requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
  }

  // 检查角色
  let hasRequiredRole = true;
  if (role) {
    if (typeof role === 'string') {
      hasRequiredRole = hasRole(role);
    } else {
      hasRequiredRole = requireAll
        ? role.every(r => hasRole(r))
        : role.some(r => hasRole(r));
    }
  }

  // 如果没有权限，不显示链接
  if (!hasRequiredPermission || !hasRequiredRole) {
    return null;
  }

  return (
    <a href={href} className={className} style={style}>
      {children}
    </a>
  );
};

// 权限文本组件（用于条件显示文本）
interface PermissionTextProps {
  children: ReactNode;
  permission?: string | string[];
  role?: string | string[];
  requireAll?: boolean;
  fallback?: ReactNode;
}

export const PermissionText: React.FC<PermissionTextProps> = ({
  children,
  permission,
  role,
  requireAll = false,
  fallback = null,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { hasPermission, hasRole, hasAnyPermission, hasAllPermissions } = usePermissions();

  // 如果用户未登录，显示fallback
  if (!isAuthenticated || !user) {
    return <>{fallback}</>;
  }

  // 超级用户拥有所有权限
  if (user.is_superuser) {
    return <>{children}</>;
  }

  // 检查权限
  let hasRequiredPermission = true;
  if (permission) {
    if (typeof permission === 'string') {
      hasRequiredPermission = hasPermission(permission);
    } else {
      hasRequiredPermission = requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
  }

  // 检查角色
  let hasRequiredRole = true;
  if (role) {
    if (typeof role === 'string') {
      hasRequiredRole = hasRole(role);
    } else {
      hasRequiredRole = requireAll
        ? role.every(r => hasRole(r))
        : role.some(r => hasRole(r));
    }
  }

  // 如果有权限，显示内容，否则显示fallback
  return <>{hasRequiredPermission && hasRequiredRole ? children : fallback}</>;
};
