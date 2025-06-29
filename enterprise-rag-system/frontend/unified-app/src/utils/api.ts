import axios, {AxiosError, AxiosInstance, AxiosResponse} from 'axios';

// API 响应类型
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_superuser: boolean;
  is_active: boolean;
  avatar_url?: string;
  created_at: string;
  last_login?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// 知识库相关类型
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  knowledge_type: string;
  visibility: string;
  owner_id: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}

// 文档相关类型
export interface Document {
  id: number;
  title: string;
  file_name: string;
  file_type: string;
  file_size: number;
  knowledge_base_id: number;
  processing_status: string;
  language: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

// 对话相关类型
export interface Conversation {
  id: number;
  title: string;
  user_id: number;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
  created_at: string;
}

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.token = null;
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
  }

  // 通用请求方法
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }

  async upload<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // 认证相关
  async login(username: string, password: string): Promise<LoginResponse> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.client.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  async loginJson(username: string, password: string): Promise<LoginResponse> {
    return this.post('/api/v1/auth/login/json', { username, password });
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }): Promise<User> {
    return this.post('/api/v1/auth/register', userData);
  }

  async logout(): Promise<void> {
    return this.post('/api/v1/auth/logout');
  }

  async getCurrentUser(): Promise<User> {
    return this.get('/api/v1/auth/me');
  }

  async refreshToken(): Promise<LoginResponse> {
    return this.post('/api/v1/auth/refresh');
  }

  // 用户管理
  async getUsers(params?: { page?: number; size?: number; search?: string }): Promise<{ users: User[]; total: number; page: number; size: number; pages: number }> {
    return this.get('/api/v1/users', params);
  }

  async createUser(userData: Partial<User>): Promise<User> {
    return this.post('/api/v1/users', userData);
  }

  async updateUser(userId: number, userData: Partial<User>): Promise<User> {
    return this.put(`/api/v1/users/${userId}`, userData);
  }

  async deleteUser(userId: number): Promise<void> {
    return this.delete(`/api/v1/users/${userId}`);
  }

  // 知识库管理
  async getKnowledgeBases(params?: { 
    page?: number; 
    size?: number; 
    search?: string; 
    knowledge_type?: string; 
  }): Promise<{ items: KnowledgeBase[]; total: number }> {
    return this.get('/api/v1/knowledge-bases', params);
  }

  async getKnowledgeBase(id: number): Promise<KnowledgeBase> {
    return this.get(`/api/v1/knowledge-bases/${id}`);
  }

  async createKnowledgeBase(data: {
    name: string;
    description?: string;
    knowledge_type?: string;
    visibility?: string;
  }): Promise<KnowledgeBase> {
    return this.post('/api/v1/knowledge-bases', data);
  }

  async updateKnowledgeBase(id: number, data: Partial<KnowledgeBase>): Promise<KnowledgeBase> {
    return this.put(`/api/v1/knowledge-bases/${id}`, data);
  }

  async deleteKnowledgeBase(id: number): Promise<void> {
    return this.delete(`/api/v1/knowledge-bases/${id}`);
  }

  // 文档管理
  async getDocuments(params?: {
    page?: number;
    size?: number;
    knowledge_base_id?: number;
    processing_status?: string;
    file_type?: string;
    search?: string;
  }): Promise<{ items: Document[]; total: number }> {
    return this.get('/api/v1/documents', params);
  }

  async getDocument(id: number): Promise<Document> {
    return this.get(`/api/v1/documents/${id}`);
  }

  async uploadDocument(formData: FormData): Promise<Document> {
    return this.upload('/api/v1/documents/upload', formData);
  }

  async deleteDocument(id: number): Promise<void> {
    return this.delete(`/api/v1/documents/${id}`);
  }

  async getDocumentChunks(id: number): Promise<any[]> {
    return this.get(`/api/v1/documents/${id}/chunks`);
  }

  async batchProcessDocuments(data: {
    document_ids: number[];
    operation: string;
    parameters?: any;
  }): Promise<any> {
    return this.post('/api/v1/documents/batch-process', data);
  }

  async searchDocuments(params: {
    query: string;
    knowledge_base_id?: number;
    file_type?: string;
    processing_status?: string;
  }): Promise<{ items: Document[]; total: number }> {
    return this.post('/api/v1/documents/search', params);
  }

  // 对话管理
  async getConversations(params?: { page?: number; size?: number }): Promise<{ items: Conversation[]; total: number }> {
    return this.get('/api/v1/conversations', params);
  }

  async getConversation(id: number): Promise<Conversation> {
    return this.get(`/api/v1/conversations/${id}`);
  }

  async getMessages(conversationId: number): Promise<Message[]> {
    return this.get(`/api/v1/conversations/${conversationId}/messages`);
  }

  async deleteConversation(id: number): Promise<void> {
    return this.delete(`/api/v1/conversations/${id}`);
  }

  // 聊天功能
  async sendChatMessage(data: {
    message: string;
    conversation_id?: number;
    knowledge_base_ids?: number[];
    stream?: boolean;
    temperature?: number;
    max_tokens?: number;
  }): Promise<{
    message: string;
    conversation_id: number;
    message_id: number;
    sources: any[];
    metadata: any;
  }> {
    return this.post('/api/v1/chat/', data);
  }

  async streamChatMessage(data: {
    message: string;
    conversation_id?: number;
    knowledge_base_ids?: number[];
    temperature?: number;
    max_tokens?: number;
  }): Promise<ReadableStream> {
    const response = await this.client.post('/api/v1/chat/stream', data, {
      responseType: 'stream',
      headers: {
        'Accept': 'text/event-stream',
      },
    });
    return response.data;
  }

  // 搜索功能
  async vectorSearch(params: {
    query: string;
    knowledge_base_ids?: number[];
    top_k?: number;
    score_threshold?: number;
  }): Promise<{
    query: string;
    results: any[];
    total: number;
    search_type: string;
    processing_time: number;
  }> {
    return this.post('/api/v1/search/vector', params);
  }

  async graphSearch(params: {
    query: string;
    knowledge_base_ids?: number[];
    top_k?: number;
    score_threshold?: number;
  }): Promise<{
    query: string;
    results: any[];
    total: number;
    search_type: string;
    processing_time: number;
  }> {
    return this.post('/api/v1/search/graph', params);
  }

  async hybridSearch(params: {
    query: string;
    knowledge_base_ids?: number[];
    top_k?: number;
    score_threshold?: number;
  }): Promise<{
    query: string;
    results: any[];
    total: number;
    search_type: string;
    processing_time: number;
  }> {
    return this.post('/api/v1/search/hybrid', params);
  }

  async advancedSearch(params: {
    query: string;
    knowledge_base_ids?: number[];
    search_type?: 'vector' | 'graph' | 'hybrid';
    filters?: any;
    top_k?: number;
  }): Promise<any> {
    return this.post('/api/v1/advanced-search/', params);
  }

  // 系统管理
  async getSystemHealth(): Promise<{ status: string }> {
    return this.get('/health');
  }

  async getSystemInfo(): Promise<any> {
    return this.get('/api/v1/system/info');
  }

  async getSystemStats(): Promise<any> {
    return this.get('/api/v1/admin/stats');
  }

  async getSystemLogs(): Promise<any> {
    return this.get('/api/v1/admin/logs');
  }

  // 知识图谱可视化
  async getKnowledgeGraph(params: {
    knowledge_base_id?: number;
    entity_type?: string;
    depth?: number;
  }): Promise<any> {
    return this.get('/api/v1/graph/visualize', params);
  }

  async getGraphEntities(params: {
    knowledge_base_id?: number;
    entity_type?: string;
    limit?: number;
  }): Promise<any> {
    return this.get('/api/v1/graph/entities', params);
  }

  async getGraphRelations(params: {
    knowledge_base_id?: number;
    relation_type?: string;
    limit?: number;
  }): Promise<any> {
    return this.get('/api/v1/graph/relations', params);
  }

  // AutoGen多智能体协作
  async autoGenChat(data: {
    query: string;
    knowledge_base_ids?: number[];
    conversation_id?: number;
    temperature?: number;
    max_tokens?: number;
  }): Promise<{
    query: string;
    answer: string;
    sources: any[];
    confidence: number;
    processing_time: number;
    conversation_id?: number;
    agent_results: any;
    metadata: any;
  }> {
    return this.post('/api/v1/autogen/chat', data);
  }

  async getAutoGenAgentsStatus(): Promise<{
    initialized: boolean;
    agents: Array<{
      name: string;
      description: string;
      status: string;
    }>;
    llm_config: any;
  }> {
    return this.get('/api/v1/autogen/agents/status');
  }

  // RBAC权限管理
  // 部门管理
  async getDepartments(): Promise<{ departments: any[]; total: number }> {
    return this.get('/api/v1/rbac/departments');
  }

  async createDepartment(data: any): Promise<any> {
    return this.post('/api/v1/rbac/departments', data);
  }

  async updateDepartment(id: number, data: any): Promise<any> {
    return this.put(`/api/v1/rbac/departments/${id}`, data);
  }

  async deleteDepartment(id: number): Promise<void> {
    return this.delete(`/api/v1/rbac/departments/${id}`);
  }

  // 角色管理
  async getRoles(params?: any): Promise<{ roles: any[]; total: number; page: number; size: number; pages: number }> {
    return this.get('/api/v1/rbac/roles', params);
  }

  async createRole(data: any): Promise<any> {
    return this.post('/api/v1/rbac/roles', data);
  }

  async updateRole(id: number, data: any): Promise<any> {
    return this.put(`/api/v1/rbac/roles/${id}`, data);
  }

  async deleteRole(id: number): Promise<void> {
    return this.delete(`/api/v1/rbac/roles/${id}`);
  }

  // 权限管理
  async getPermissions(params?: any): Promise<{ permissions: any[]; total: number; page: number; size: number; pages: number }> {
    return this.get('/api/v1/rbac/permissions', params);
  }

  async createPermission(data: any): Promise<any> {
    return this.post('/api/v1/rbac/permissions', data);
  }

  async updatePermission(id: number, data: any): Promise<any> {
    return this.put(`/api/v1/rbac/permissions/${id}`, data);
  }

  async deletePermission(id: number): Promise<void> {
    return this.delete(`/api/v1/rbac/permissions/${id}`);
  }

  // 用户角色分配
  async assignUserRoles(data: any): Promise<any[]> {
    return this.post('/api/v1/rbac/user-roles', data);
  }

  async getUserRoles(userId: number): Promise<any[]> {
    return this.get(`/api/v1/rbac/users/${userId}/roles`);
  }

  // 权限检查
  async checkPermissions(data: { user_id: number; permission_codes: string[] }): Promise<{ user_id: number; permissions: Record<string, boolean> }> {
    return this.post('/api/v1/rbac/check-permissions', data);
  }

  // 菜单树
  async getMenuTree(): Promise<any[]> {
    return this.get('/api/v1/rbac/menu-tree');
  }
}

// 创建并导出 API 客户端实例
export const apiClient = new ApiClient();

// 为了向后兼容，也导出为 api
export const api = apiClient;

// 导出类型
export type { ApiResponse, ApiError };
