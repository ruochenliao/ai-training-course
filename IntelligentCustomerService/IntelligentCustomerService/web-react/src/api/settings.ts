import {request} from '../utils/request';

// 系统设置接口
export interface SystemSettings {
  // 基础设置
  siteName: string;
  siteDescription: string;
  siteLogo: string;
  siteIcon: string;
  timezone: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
  
  // 安全设置
  passwordMinLength: number;
  passwordRequireSpecialChar: boolean;
  sessionTimeout: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
  enableTwoFactor: boolean;
  
  // 邮件设置
  emailProvider: 'smtp' | 'sendgrid' | 'aws';
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword: string;
  smtpEncryption: 'none' | 'tls' | 'ssl';
  emailFromAddress: string;
  emailFromName: string;
  
  // 消息设置
  enableSms: boolean;
  smsProvider: 'twilio' | 'aliyun' | 'tencent';
  smsApiKey: string;
  smsApiSecret: string;
  enablePush: boolean;
  pushProvider: 'firebase' | 'jpush';
  pushApiKey: string;
  
  // 存储设置
  storageProvider: 'local' | 'oss' | 's3' | 'cos';
  storageEndpoint: string;
  storageAccessKey: string;
  storageSecretKey: string;
  storageBucket: string;
  storageRegion: string;
  
  // 缓存设置
  cacheProvider: 'memory' | 'redis';
  redisHost: string;
  redisPort: number;
  redisPassword: string;
  redisDatabase: number;
  cacheTtl: number;
  
  // 日志设置
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  logRetentionDays: number;
  enableAccessLog: boolean;
  enableErrorLog: boolean;
  enableAuditLog: boolean;
}

// 系统状态接口
export interface SystemStatus {
  version: string;
  uptime: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  databaseStatus: 'connected' | 'disconnected';
  cacheStatus: 'connected' | 'disconnected';
  emailStatus: 'configured' | 'not_configured';
  storageStatus: 'configured' | 'not_configured';
}

// 系统日志接口
export interface SystemLog {
  id: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  context?: Record<string, any>;
  userId?: string;
  ip?: string;
  userAgent?: string;
  createdAt: string;
}

// 审计日志接口
export interface AuditLog {
  id: string;
  action: string;
  resource: string;
  resourceId?: string;
  userId: string;
  username: string;
  ip: string;
  userAgent: string;
  details?: Record<string, any>;
  result: 'success' | 'failure';
  createdAt: string;
}

// 邮件测试参数
export interface EmailTestParams {
  email: string;
  subject: string;
  content: string;
}

// 日志查询参数
export interface LogQueryParams {
  page?: number;
  pageSize?: number;
  level?: string;
  keyword?: string;
  userId?: string;
  startDate?: string;
  endDate?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
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

export const settingsApi = {
  // 获取系统设置
  getSettings: (): Promise<SystemSettings> => {
    return request.get('/api/settings');
  },

  // 更新系统设置
  updateSettings: (data: Partial<SystemSettings>): Promise<SystemSettings> => {
    return request.put('/api/settings', data);
  },

  // 重置系统设置
  resetSettings: (): Promise<SystemSettings> => {
    return request.post('/api/settings/reset');
  },

  // 获取系统状态
  getSystemStatus: (): Promise<SystemStatus> => {
    return request.get('/api/system/status');
  },

  // 测试邮件配置
  testEmailConfig: (params: EmailTestParams): Promise<void> => {
    return request.post('/api/settings/test-email', params);
  },

  // 测试存储配置
  testStorageConfig: (): Promise<void> => {
    return request.post('/api/settings/test-storage');
  },

  // 测试缓存配置
  testCacheConfig: (): Promise<void> => {
    return request.post('/api/settings/test-cache');
  },

  // 清理缓存
  clearCache: (type?: 'all' | 'user' | 'permission' | 'config'): Promise<void> => {
    return request.post('/api/system/clear-cache', { type });
  },

  // 重启系统
  restartSystem: (): Promise<void> => {
    return request.post('/api/system/restart');
  },

  // 获取系统日志
  getSystemLogs: (params?: LogQueryParams): Promise<PaginatedResponse<SystemLog>> => {
    return request.get('/api/system/logs', { params });
  },

  // 获取审计日志
  getAuditLogs: (params?: LogQueryParams): Promise<PaginatedResponse<AuditLog>> => {
    return request.get('/api/system/audit-logs', { params });
  },

  // 清理日志
  clearLogs: (type: 'system' | 'audit', beforeDate?: string): Promise<void> => {
    return request.delete('/api/system/logs', {
      data: { type, beforeDate },
    });
  },

  // 导出日志
  exportLogs: (type: 'system' | 'audit', params?: LogQueryParams): Promise<Blob> => {
    return request.get(`/api/system/logs/export`, {
      params: { type, ...params },
      responseType: 'blob',
    });
  },

  // 获取系统信息
  getSystemInfo: (): Promise<{
    version: string;
    buildTime: string;
    gitCommit: string;
    nodeVersion: string;
    platform: string;
    arch: string;
    uptime: number;
    environment: string;
  }> => {
    return request.get('/api/system/info');
  },

  // 获取数据库信息
  getDatabaseInfo: (): Promise<{
    type: string;
    version: string;
    size: number;
    tables: number;
    connections: number;
    status: string;
  }> => {
    return request.get('/api/system/database-info');
  },

  // 备份数据库
  backupDatabase: (): Promise<{
    filename: string;
    size: number;
    downloadUrl: string;
  }> => {
    return request.post('/api/system/backup');
  },

  // 恢复数据库
  restoreDatabase: (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    return request.post('/api/system/restore', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 获取备份列表
  getBackupList: (): Promise<Array<{
    filename: string;
    size: number;
    createdAt: string;
    downloadUrl: string;
  }>> => {
    return request.get('/api/system/backups');
  },

  // 删除备份
  deleteBackup: (filename: string): Promise<void> => {
    return request.delete(`/api/system/backups/${filename}`);
  },

  // 获取系统配置模板
  getConfigTemplate: (type: 'email' | 'storage' | 'cache'): Promise<Record<string, any>> => {
    return request.get(`/api/settings/template/${type}`);
  },

  // 验证配置
  validateConfig: (type: string, config: Record<string, any>): Promise<{
    valid: boolean;
    errors: string[];
  }> => {
    return request.post('/api/settings/validate', { type, config });
  },

  // 获取系统健康检查
  getHealthCheck: (): Promise<{
    status: 'healthy' | 'warning' | 'error';
    checks: Array<{
      name: string;
      status: 'pass' | 'fail' | 'warn';
      message?: string;
      duration: number;
    }>;
  }> => {
    return request.get('/api/system/health');
  },

  // 获取系统指标
  getSystemMetrics: (timeRange?: '1h' | '6h' | '24h' | '7d'): Promise<{
    cpu: Array<{ timestamp: number; value: number }>;
    memory: Array<{ timestamp: number; value: number }>;
    disk: Array<{ timestamp: number; value: number }>;
    network: Array<{ timestamp: number; in: number; out: number }>;
    requests: Array<{ timestamp: number; count: number; avgResponseTime: number }>;
  }> => {
    return request.get('/api/system/metrics', {
      params: { timeRange },
    });
  },

  // 设置系统维护模式
  setMaintenanceMode: (enabled: boolean, message?: string): Promise<void> => {
    return request.post('/api/system/maintenance', {
      enabled,
      message,
    });
  },

  // 获取系统维护状态
  getMaintenanceStatus: (): Promise<{
    enabled: boolean;
    message?: string;
    startTime?: string;
  }> => {
    return request.get('/api/system/maintenance');
  },

  // 发送系统通知
  sendSystemNotification: (data: {
    title: string;
    content: string;
    type: 'info' | 'warning' | 'error';
    targets: 'all' | 'admins' | string[];
  }): Promise<void> => {
    return request.post('/api/system/notification', data);
  },
};