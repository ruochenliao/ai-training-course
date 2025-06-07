import {request} from '../utils/request';

// 会话状态枚举
export enum SessionStatus {
  WAITING = 'waiting',
  ACTIVE = 'active',
  CLOSED = 'closed',
  TRANSFERRED = 'transferred',
}

// 消息类型枚举
export enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  FILE = 'file',
  VOICE = 'voice',
  VIDEO = 'video',
  SYSTEM = 'system',
}

// 发送者类型枚举
export enum SenderType {
  USER = 'user',
  AGENT = 'agent',
  SYSTEM = 'system',
  BOT = 'bot',
}

// 会话优先级枚举
export enum SessionPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

// 用户信息接口
export interface UserInfo {
  id: string;
  username: string;
  nickname: string;
  avatar: string;
  email: string;
  phone: string;
  vipLevel: number;
  registeredAt: string;
  lastActiveAt: string;
  totalSessions: number;
  tags: string[];
  customFields: Record<string, any>;
}

// 客服信息接口
export interface AgentInfo {
  id: string;
  username: string;
  nickname: string;
  avatar: string;
  email: string;
  phone: string;
  department: string;
  status: 'online' | 'busy' | 'away' | 'offline';
  maxSessions: number;
  currentSessions: number;
  skills: string[];
  rating: number;
  totalSessions: number;
  resolvedSessions: number;
  avgResponseTime: number;
  lastActiveAt: string;
}

// 消息接口
export interface Message {
  id: string;
  sessionId: string;
  type: MessageType;
  content: string;
  sender: SenderType;
  senderId: string;
  senderName: string;
  senderAvatar: string;
  timestamp: string;
  isRead: boolean;
  metadata?: {
    fileName?: string;
    fileSize?: number;
    fileUrl?: string;
    duration?: number;
    thumbnail?: string;
    [key: string]: any;
  };
}

// 会话接口
export interface Session {
  id: string;
  userId: string;
  userInfo: UserInfo;
  agentId?: string;
  agentInfo?: AgentInfo;
  status: SessionStatus;
  priority: SessionPriority;
  title: string;
  tags: string[];
  source: 'web' | 'mobile' | 'wechat' | 'qq' | 'email';
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  lastMessage?: Message;
  unreadCount: number;
  waitingTime?: number;
  responseTime?: number;
  satisfaction?: number;
  feedback?: string;
  transferReason?: string;
  customFields: Record<string, any>;
}

// 快捷回复接口
export interface QuickReply {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  isPublic: boolean;
  createdBy: string;
  usageCount: number;
  createdAt: string;
  updatedAt: string;
}

// 知识库文章接口
export interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  isPublished: boolean;
  viewCount: number;
  likeCount: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

// 会话查询参数
export interface SessionQueryParams {
  page?: number;
  pageSize?: number;
  status?: SessionStatus;
  priority?: SessionPriority;
  agentId?: string;
  userId?: string;
  source?: string;
  keyword?: string;
  startDate?: string;
  endDate?: string;
  tags?: string[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 消息查询参数
export interface MessageQueryParams {
  sessionId: string;
  page?: number;
  pageSize?: number;
  type?: MessageType;
  sender?: SenderType;
  keyword?: string;
  startDate?: string;
  endDate?: string;
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

// 会话统计
export interface SessionStats {
  total: number;
  waiting: number;
  active: number;
  closed: number;
  transferred: number;
  avgWaitingTime: number;
  avgResponseTime: number;
  avgSessionDuration: number;
  satisfactionRate: number;
}

// 客服统计
export interface AgentStats {
  agentId: string;
  agentName: string;
  totalSessions: number;
  activeSessions: number;
  resolvedSessions: number;
  avgResponseTime: number;
  avgSessionDuration: number;
  satisfactionRate: number;
  onlineTime: number;
}

export const customerServiceApi = {
  // 会话管理
  getSessions: (params?: SessionQueryParams): Promise<PaginatedResponse<Session>> => {
    return request.get('/api/sessions', { params });
  },

  getSession: (id: string): Promise<Session> => {
    return request.get(`/api/sessions/${id}`);
  },

  createSession: (data: {
    userId: string;
    title: string;
    priority?: SessionPriority;
    source?: string;
    tags?: string[];
  }): Promise<Session> => {
    return request.post('/api/sessions', data);
  },

  updateSession: (id: string, data: Partial<Session>): Promise<Session> => {
    return request.put(`/api/sessions/${id}`, data);
  },

  closeSession: (id: string, data: {
    reason?: string;
    satisfaction?: number;
    feedback?: string;
  }): Promise<void> => {
    return request.post(`/api/sessions/${id}/close`, data);
  },

  transferSession: (id: string, data: {
    agentId: string;
    reason: string;
  }): Promise<void> => {
    return request.post(`/api/sessions/${id}/transfer`, data);
  },

  assignSession: (id: string, agentId: string): Promise<void> => {
    return request.post(`/api/sessions/${id}/assign`, { agentId });
  },

  // 消息管理
  getMessages: (params: MessageQueryParams): Promise<PaginatedResponse<Message>> => {
    return request.get('/api/messages', { params });
  },

  sendMessage: (data: {
    sessionId: string;
    type: MessageType;
    content: string;
    metadata?: Record<string, any>;
  }): Promise<Message> => {
    return request.post('/api/messages', data);
  },

  markMessageAsRead: (messageId: string): Promise<void> => {
    return request.post(`/api/messages/${messageId}/read`);
  },

  markSessionAsRead: (sessionId: string): Promise<void> => {
    return request.post(`/api/sessions/${sessionId}/read`);
  },

  // 文件上传
  uploadFile: (file: File, sessionId: string): Promise<{
    url: string;
    filename: string;
    size: number;
    type: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sessionId', sessionId);
    return request.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 用户管理
  getUsers: (params?: {
    page?: number;
    pageSize?: number;
    keyword?: string;
    vipLevel?: number;
    tags?: string[];
  }): Promise<PaginatedResponse<UserInfo>> => {
    return request.get('/api/users', { params });
  },

  getUser: (id: string): Promise<UserInfo> => {
    return request.get(`/api/users/${id}`);
  },

  updateUser: (id: string, data: Partial<UserInfo>): Promise<UserInfo> => {
    return request.put(`/api/users/${id}`, data);
  },

  getUserSessions: (userId: string, params?: {
    page?: number;
    pageSize?: number;
    status?: SessionStatus;
  }): Promise<PaginatedResponse<Session>> => {
    return request.get(`/api/users/${userId}/sessions`, { params });
  },

  // 客服管理
  getAgents: (params?: {
    page?: number;
    pageSize?: number;
    status?: string;
    department?: string;
    skills?: string[];
  }): Promise<PaginatedResponse<AgentInfo>> => {
    return request.get('/api/agents', { params });
  },

  getAgent: (id: string): Promise<AgentInfo> => {
    return request.get(`/api/agents/${id}`);
  },

  updateAgentStatus: (id: string, status: AgentInfo['status']): Promise<void> => {
    return request.post(`/api/agents/${id}/status`, { status });
  },

  getAgentSessions: (agentId: string, params?: {
    page?: number;
    pageSize?: number;
    status?: SessionStatus;
  }): Promise<PaginatedResponse<Session>> => {
    return request.get(`/api/agents/${agentId}/sessions`, { params });
  },

  // 快捷回复
  getQuickReplies: (params?: {
    page?: number;
    pageSize?: number;
    category?: string;
    keyword?: string;
    isPublic?: boolean;
  }): Promise<PaginatedResponse<QuickReply>> => {
    return request.get('/api/quick-replies', { params });
  },

  createQuickReply: (data: Omit<QuickReply, 'id' | 'createdBy' | 'usageCount' | 'createdAt' | 'updatedAt'>): Promise<QuickReply> => {
    return request.post('/api/quick-replies', data);
  },

  updateQuickReply: (id: string, data: Partial<QuickReply>): Promise<QuickReply> => {
    return request.put(`/api/quick-replies/${id}`, data);
  },

  deleteQuickReply: (id: string): Promise<void> => {
    return request.delete(`/api/quick-replies/${id}`);
  },

  useQuickReply: (id: string): Promise<void> => {
    return request.post(`/api/quick-replies/${id}/use`);
  },

  // 知识库
  getKnowledgeArticles: (params?: {
    page?: number;
    pageSize?: number;
    category?: string;
    keyword?: string;
    isPublished?: boolean;
  }): Promise<PaginatedResponse<KnowledgeArticle>> => {
    return request.get('/api/knowledge', { params });
  },

  getKnowledgeArticle: (id: string): Promise<KnowledgeArticle> => {
    return request.get(`/api/knowledge/${id}`);
  },

  searchKnowledge: (keyword: string): Promise<KnowledgeArticle[]> => {
    return request.get('/api/knowledge/search', {
      params: { keyword },
    });
  },

  // 统计数据
  getSessionStats: (params?: {
    startDate?: string;
    endDate?: string;
    agentId?: string;
    department?: string;
  }): Promise<SessionStats> => {
    return request.get('/api/stats/sessions', { params });
  },

  getAgentStats: (params?: {
    startDate?: string;
    endDate?: string;
    department?: string;
  }): Promise<AgentStats[]> => {
    return request.get('/api/stats/agents', { params });
  },

  getDashboardData: (): Promise<{
    sessionStats: SessionStats;
    recentSessions: Session[];
    agentStats: AgentStats[];
    popularQuestions: Array<{
      question: string;
      count: number;
    }>;
  }> => {
    return request.get('/api/dashboard');
  },

  // 实时通信
  connectWebSocket: (token: string): WebSocket => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';
    const ws = new WebSocket(`${wsUrl}/ws?token=${token}`);
    return ws;
  },

  // 通知管理
  getNotifications: (params?: {
    page?: number;
    pageSize?: number;
    type?: string;
    isRead?: boolean;
  }): Promise<PaginatedResponse<{
    id: string;
    type: string;
    title: string;
    content: string;
    isRead: boolean;
    createdAt: string;
    data?: Record<string, any>;
  }>> => {
    return request.get('/api/notifications', { params });
  },

  markNotificationAsRead: (id: string): Promise<void> => {
    return request.post(`/api/notifications/${id}/read`);
  },

  markAllNotificationsAsRead: (): Promise<void> => {
    return request.post('/api/notifications/read-all');
  },

  // 自动回复
  getAutoReplies: (): Promise<Array<{
    id: string;
    trigger: string;
    response: string;
    isEnabled: boolean;
    priority: number;
  }>> => {
    return request.get('/api/auto-replies');
  },

  updateAutoReply: (id: string, data: {
    trigger?: string;
    response?: string;
    isEnabled?: boolean;
    priority?: number;
  }): Promise<void> => {
    return request.put(`/api/auto-replies/${id}`, data);
  },

  // 会话评价
  submitFeedback: (sessionId: string, data: {
    satisfaction: number;
    feedback?: string;
    tags?: string[];
  }): Promise<void> => {
    return request.post(`/api/sessions/${sessionId}/feedback`, data);
  },

  // 导出数据
  exportSessions: (params?: SessionQueryParams): Promise<Blob> => {
    return request.get('/api/sessions/export', {
      params,
      responseType: 'blob',
    });
  },

  exportMessages: (sessionId: string): Promise<Blob> => {
    return request.get(`/api/sessions/${sessionId}/export`, {
      responseType: 'blob',
    });
  },
};