// 基础类型
export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at: string;
}

// 用户相关类型
export interface User extends BaseEntity {
  username: string;
  email: string;
  full_name?: string;
  is_superuser: boolean;
  is_active: boolean;
  avatar_url?: string;
  last_login?: string;
  login_count?: number;
}

export interface UserProfile extends User {
  bio?: string;
  phone?: string;
  department?: string;
  position?: string;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  notifications: NotificationSettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  chat: boolean;
  system: boolean;
}

// 认证相关类型
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

// 知识库相关类型
export interface KnowledgeBase extends BaseEntity {
  name: string;
  description?: string;
  knowledge_type: KnowledgeBaseType;
  visibility: 'public' | 'private' | 'shared';
  owner_id: number;
  owner?: User;
  document_count: number;
  chunk_count: number;
  size: number;
  tags?: string[];
  settings?: KnowledgeBaseSettings;
  is_deleted: boolean;
}

export type KnowledgeBaseType = 'general' | 'technical' | 'business' | 'academic' | 'legal' | 'medical';

export interface KnowledgeBaseSettings {
  chunk_size: number;
  chunk_overlap: number;
  embedding_model: string;
  language: string;
  auto_process: boolean;
}

export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
  knowledge_type?: KnowledgeBaseType;
  visibility?: 'public' | 'private' | 'shared';
  settings?: Partial<KnowledgeBaseSettings>;
}

// 文档相关类型
export interface Document extends BaseEntity {
  title: string;
  file_name: string;
  file_type: string;
  file_size: number;
  file_path: string;
  knowledge_base_id: number;
  knowledge_base?: KnowledgeBase;
  processing_status: ProcessingStatus;
  language: string;
  chunk_count: number;
  metadata?: DocumentMetadata;
  tags?: string[];
  is_deleted: boolean;
}

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface DocumentMetadata {
  author?: string;
  subject?: string;
  keywords?: string[];
  page_count?: number;
  word_count?: number;
  character_count?: number;
  extracted_text_length?: number;
}

export interface DocumentChunk extends BaseEntity {
  document_id: number;
  content: string;
  chunk_index: number;
  start_char: number;
  end_char: number;
  metadata?: ChunkMetadata;
  embedding?: number[];
}

export interface ChunkMetadata {
  page_number?: number;
  section?: string;
  heading?: string;
  confidence?: number;
}

export interface UploadDocumentRequest {
  file: File;
  knowledge_base_id: number;
  description?: string;
  language?: string;
  chunk_strategy?: 'semantic' | 'fixed' | 'paragraph';
  tags?: string[];
}

// 对话相关类型
export interface Conversation extends BaseEntity {
  title: string;
  user_id: number;
  user?: User;
  message_count: number;
  last_message_at?: string;
  metadata?: ConversationMetadata;
  is_deleted: boolean;
}

export interface ConversationMetadata {
  knowledge_base_ids?: number[];
  model_settings?: ModelSettings;
  context_length?: number;
}

export interface Message extends BaseEntity {
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: MessageMetadata;
  parent_id?: number;
  children?: Message[];
}

export interface MessageMetadata {
  sources?: SourceReference[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  processing_time?: number;
  token_count?: number;
}

export interface SourceReference {
  document_id: number;
  document_title: string;
  chunk_id: number;
  content: string;
  relevance_score: number;
  page_number?: number;
}

export interface ModelSettings {
  model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
}

// 聊天相关类型
export interface ChatRequest {
  message: string;
  conversation_id?: number;
  knowledge_base_ids?: number[];
  stream?: boolean;
  model_settings?: Partial<ModelSettings>;
}

export interface ChatResponse {
  message: string;
  conversation_id: number;
  message_id: number;
  sources: SourceReference[];
  metadata: MessageMetadata;
}

// 搜索相关类型
export interface SearchRequest {
  query: string;
  knowledge_base_ids?: number[];
  search_type: 'semantic' | 'keyword' | 'hybrid';
  limit?: number;
  filters?: SearchFilters;
}

export interface SearchFilters {
  file_types?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  tags?: string[];
  min_relevance?: number;
}

export interface SearchResult {
  id: number;
  document_id: number;
  document_title: string;
  content: string;
  relevance_score: number;
  metadata: ChunkMetadata;
  highlights?: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query_time: number;
  suggestions?: string[];
}

// 系统相关类型
export interface SystemStats {
  users: {
    total: number;
    active: number;
    new_today: number;
  };
  knowledge_bases: {
    total: number;
    public: number;
    private: number;
  };
  documents: {
    total: number;
    processing: number;
    completed: number;
    failed: number;
    total_size: number;
  };
  conversations: {
    total: number;
    today: number;
    this_week: number;
  };
  system: {
    uptime: number;
    memory_usage: number;
    cpu_usage: number;
    disk_usage: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  services: ServiceStatus[];
  last_check: string;
}

export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time?: number;
  error_message?: string;
}

// 分页相关类型
export interface PaginationParams {
  page?: number;
  size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 表单相关类型
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'file' | 'checkbox';
  required?: boolean;
  placeholder?: string;
  options?: { label: string; value: any }[];
  validation?: ValidationRule[];
}

export interface ValidationRule {
  type: 'required' | 'email' | 'min' | 'max' | 'pattern';
  value?: any;
  message: string;
}

// 通知相关类型
export interface Notification extends BaseEntity {
  title: string;
  content: string;
  type: 'info' | 'success' | 'warning' | 'error';
  user_id: number;
  is_read: boolean;
  action_url?: string;
  metadata?: any;
}

// 主题相关类型
export type Theme = 'light' | 'dark';

export interface ThemeConfig {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  border: string;
}

// 路由相关类型
export interface RouteConfig {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  protected?: boolean;
  adminOnly?: boolean;
  permissions?: string[];
  title?: string;
  icon?: React.ComponentType;
}

// RBAC权限相关类型
export interface Department extends BaseEntity {
  name: string;
  code: string;
  description?: string;
  parent_id?: number;
  level: number;
  sort_order: number;
  manager_id?: number;
  status: string;
  children?: Department[];
  parent?: Department;
  manager_name?: string;
}

export interface Role extends BaseEntity {
  name: string;
  code: string;
  description?: string;
  parent_id?: number;
  level: number;
  sort_order: number;
  role_type: string;
  data_scope: string;
  status: string;
  permissions?: Permission[];
  children?: Role[];
  parent?: Role;
  user_count?: number;
}

export interface Permission extends BaseEntity {
  name: string;
  code: string;
  description?: string;
  group: string;
  resource: string;
  action: string;
  permission_type: string;
  menu_path?: string;
  menu_component?: string;
  menu_icon?: string;
  parent_id?: number;
  sort_order: number;
  status: string;
  children?: Permission[];
  parent?: Permission;
}

export interface UserRole extends BaseEntity {
  user_id: number;
  role_id: number;
  granted_by: number;
  granted_at: string;
  expires_at?: string;
  dept_ids: number[];
  role?: Role;
}

export interface UserPermission extends BaseEntity {
  user_id: number;
  permission_id: number;
  granted_by: number;
  granted_at: string;
  expires_at?: string;
  permission_type: string;
  permission?: Permission;
}

// RBAC请求类型
export interface CreateDepartmentRequest {
  name: string;
  code: string;
  description?: string;
  parent_id?: number;
  sort_order?: number;
  manager_id?: number;
}

export interface UpdateDepartmentRequest {
  name?: string;
  description?: string;
  parent_id?: number;
  sort_order?: number;
  manager_id?: number;
  status?: string;
}

export interface CreateRoleRequest {
  name: string;
  code: string;
  description?: string;
  parent_id?: number;
  sort_order?: number;
  role_type?: string;
  data_scope?: string;
  permission_ids?: number[];
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  parent_id?: number;
  sort_order?: number;
  data_scope?: string;
  status?: string;
  permission_ids?: number[];
}

export interface CreatePermissionRequest {
  name: string;
  code: string;
  description?: string;
  group: string;
  resource: string;
  action: string;
  permission_type?: string;
  menu_path?: string;
  menu_component?: string;
  menu_icon?: string;
  parent_id?: number;
  sort_order?: number;
}

export interface UpdatePermissionRequest {
  name?: string;
  description?: string;
  group?: string;
  resource?: string;
  action?: string;
  permission_type?: string;
  menu_path?: string;
  menu_component?: string;
  menu_icon?: string;
  parent_id?: number;
  sort_order?: number;
  status?: string;
}

export interface AssignUserRolesRequest {
  user_id: number;
  role_ids: number[];
  expires_at?: string;
  dept_ids?: number[];
}

export interface AssignUserPermissionsRequest {
  user_id: number;
  permission_ids: number[];
  permission_type?: string;
  expires_at?: string;
}

export interface PermissionCheckRequest {
  user_id: number;
  permission_codes: string[];
}

export interface PermissionCheckResponse {
  user_id: number;
  permissions: Record<string, boolean>;
}

// 菜单树类型
export interface MenuTree {
  id: number;
  name: string;
  code: string;
  path?: string;
  component?: string;
  icon?: string;
  sort_order: number;
  children?: MenuTree[];
}

// 权限上下文类型
export interface PermissionContextType {
  permissions: string[];
  roles: string[];
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  checkPermissions: (permissionCodes: string[]) => Promise<Record<string, boolean>>;
  refreshPermissions: () => Promise<void>;
}
