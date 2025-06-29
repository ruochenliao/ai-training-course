// 企业级RAG系统 - TypeScript 类型定义

// 基础类型
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  code?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 用户相关类型
export interface User extends BaseEntity {
  username: string
  email: string
  full_name: string
  avatar?: string
  is_active: boolean
  is_superuser: boolean
  department?: string
  role?: string
  last_login?: string
}

export interface UserProfile {
  user: User
  preferences: UserPreferences
  permissions: string[]
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string
  notifications: NotificationSettings
}

export interface NotificationSettings {
  email: boolean
  push: boolean
  desktop: boolean
}

// 认证相关类型
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name: string
  department?: string
}

// 知识库相关类型
export interface KnowledgeBase extends BaseEntity {
  name: string
  description: string
  owner_id: string
  owner: User
  is_public: boolean
  document_count: number
  size: number
  tags: string[]
  status: 'active' | 'inactive' | 'processing'
}

export interface CreateKnowledgeBaseRequest {
  name: string
  description: string
  is_public?: boolean
  tags?: string[]
}

// 文档相关类型
export interface Document extends BaseEntity {
  title: string
  filename: string
  file_path: string
  file_size: number
  file_type: string
  content?: string
  summary?: string
  knowledge_base_id: string
  knowledge_base: KnowledgeBase
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  processing_progress?: number
  metadata: DocumentMetadata
}

export interface DocumentMetadata {
  author?: string
  created_date?: string
  modified_date?: string
  page_count?: number
  word_count?: number
  language?: string
  tags?: string[]
}

export interface UploadDocumentRequest {
  file: File
  knowledge_base_id: string
  title?: string
  tags?: string[]
}

// 对话相关类型
export interface Conversation extends BaseEntity {
  title: string
  user_id: string
  user: User
  knowledge_base_ids: string[]
  knowledge_bases: KnowledgeBase[]
  message_count: number
  last_message_at?: string
  is_archived: boolean
}

export interface Message extends BaseEntity {
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: MessageMetadata
  sources?: MessageSource[]
  feedback?: MessageFeedback
}

export interface MessageMetadata {
  model?: string
  temperature?: number
  max_tokens?: number
  search_mode?: string
  processing_time?: number
  token_usage?: TokenUsage
}

export interface MessageSource {
  document_id: string
  document_title: string
  chunk_id: string
  content: string
  score: number
  page?: number
}

export interface MessageFeedback {
  rating: 1 | 2 | 3 | 4 | 5
  comment?: string
  created_at: string
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

// 聊天相关类型
export interface ChatRequest {
  message: string
  conversation_id?: string
  knowledge_base_ids?: string[]
  search_mode?: 'semantic' | 'keyword' | 'hybrid' | 'autogen'
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

export interface ChatResponse {
  message: Message
  conversation_id: string
  sources?: MessageSource[]
  suggestions?: string[]
}

// 搜索相关类型
export interface SearchRequest {
  query: string
  knowledge_base_ids?: string[]
  search_type?: 'semantic' | 'keyword' | 'hybrid'
  limit?: number
  threshold?: number
}

export interface SearchResult {
  document_id: string
  document_title: string
  chunk_id: string
  content: string
  score: number
  highlights?: string[]
  metadata?: Record<string, any>
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
  search_type: string
  processing_time: number
}

// AutoGen 相关类型
export interface AutoGenAgent {
  name: string
  role: string
  description: string
  system_message: string
  is_active: boolean
}

export interface AutoGenChatRequest {
  query: string
  knowledge_base_ids?: string[]
  conversation_id?: string
  agents?: string[]
  temperature?: number
  max_tokens?: number
}

export interface AutoGenChatResponse {
  conversation_id: string
  messages: AutoGenMessage[]
  final_answer: string
  agents_used: string[]
  processing_time: number
}

export interface AutoGenMessage {
  agent: string
  role: string
  content: string
  timestamp: string
}

// 权限相关类型
export interface Role extends BaseEntity {
  name: string
  description: string
  permissions: Permission[]
  is_system: boolean
}

export interface Permission extends BaseEntity {
  name: string
  description: string
  resource: string
  action: string
}

export interface Department extends BaseEntity {
  name: string
  description: string
  parent_id?: string
  parent?: Department
  children?: Department[]
  users: User[]
}

// 系统相关类型
export interface SystemInfo {
  version: string
  environment: string
  uptime: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_users: number
  total_documents: number
  total_conversations: number
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error'
  services: ServiceHealth[]
  last_check: string
}

export interface ServiceHealth {
  name: string
  status: 'up' | 'down' | 'degraded'
  response_time?: number
  error_message?: string
}

// 通用工具类型
export type Theme = 'light' | 'dark' | 'auto'
export type Language = 'zh-CN' | 'en-US'
export type Status = 'loading' | 'success' | 'error' | 'idle'

// 表单相关类型
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'file'
  required?: boolean
  placeholder?: string
  options?: { label: string; value: any }[]
  validation?: {
    pattern?: RegExp
    min?: number
    max?: number
    message?: string
  }
}

// 路由相关类型
export interface RouteConfig {
  path: string
  component: React.ComponentType
  title: string
  icon?: string
  children?: RouteConfig[]
  permissions?: string[]
  hidden?: boolean
}

// 事件类型
export interface AppEvent {
  type: string
  payload?: any
  timestamp: number
}

// 错误类型
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: number
}

// 导出所有类型
export * from './api'
export * from './components'
