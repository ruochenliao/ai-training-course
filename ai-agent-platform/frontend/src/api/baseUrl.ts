// API基础URL配置
const baseUrl: Record<string, string> = {
  development: 'http://localhost:8000',
  production: 'https://your-api-domain.com',
}

export const BASE_URL = baseUrl[import.meta.env.VITE_ENV] || baseUrl.development

// API路径常量
export const API_PATHS = {
  // 认证相关
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    REGISTER: '/api/v1/auth/register',
    PROFILE: '/api/v1/auth/profile',
  },
  
  // 用户管理
  USER: {
    LIST: '/api/v1/users',
    DETAIL: '/api/v1/users',
    CREATE: '/api/v1/users',
    UPDATE: '/api/v1/users',
    DELETE: '/api/v1/users',
  },
  
  // 智能体管理
  AGENT: {
    LIST: '/api/v1/agents',
    DETAIL: '/api/v1/agents',
    CREATE: '/api/v1/agents',
    UPDATE: '/api/v1/agents',
    DELETE: '/api/v1/agents',
    CHAT: '/api/v1/agents/chat',
  },
  
  // 知识库管理
  KNOWLEDGE: {
    LIST: '/api/v1/knowledge',
    DETAIL: '/api/v1/knowledge',
    CREATE: '/api/v1/knowledge',
    UPDATE: '/api/v1/knowledge',
    DELETE: '/api/v1/knowledge',
    UPLOAD: '/api/v1/knowledge/upload',
  },
  
  // 文件管理
  FILE: {
    UPLOAD: '/api/v1/files/upload',
    DOWNLOAD: '/api/v1/files/download',
    DELETE: '/api/v1/files',
  },
  
  // 系统管理
  SYSTEM: {
    HEALTH: '/health',
    INFO: '/api/v1/system/info',
    STATS: '/api/v1/system/stats',
  }
}

export default BASE_URL
