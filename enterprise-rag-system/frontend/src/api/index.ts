// API 统一导出文件

// 导出配置
export { simpleHttpClient as httpClient, API_CONFIG } from './simple-config'

// 导入各模块API
import { authApi } from './auth'
import { usersApi } from './users'
import { knowledgeApi } from './knowledge'
import { documentsApi } from './documents'
import { chatApi } from './chat'
import { searchApi } from './search'
import { systemApi } from './system'

// 重新导出各模块API
export { authApi, usersApi, knowledgeApi, documentsApi, chatApi, searchApi, systemApi }

// 导出类型定义
export type {
  // 认证相关
  LoginRequest,
  LoginResponse,
  UserInfo,
  RegisterRequest,
  RefreshTokenRequest,
} from './auth'

export type {
  // 用户相关
  User,
  UserCreateRequest,
  UserUpdateRequest,
  UserListParams,
  UserListResponse,
} from './users'

export type {
  // 知识库相关
  KnowledgeBase,
  KnowledgeBaseCreateRequest,
  KnowledgeBaseUpdateRequest,
  KnowledgeBaseListParams,
  KnowledgeBaseListResponse,
  KnowledgeBaseStats,
} from './knowledge'

export type {
  // 文档相关
  Document,
  DocumentUploadRequest,
  DocumentListParams,
  DocumentListResponse,
  DocumentProcessingStatus,
  DocumentChunk,
} from './documents'

export type {
  // 聊天相关
  ChatMessage,
  Conversation,
  ChatRequest,
  ChatResponse,
  SearchSource,
  AutoGenChatRequest,
  AutoGenChatResponse,
  ConversationListParams,
  ConversationListResponse,
} from './chat'

export type {
  // 搜索相关
  SearchRequest,
  SearchResult,
  SearchResponse,
  AdvancedSearchRequest,
  GraphSearchRequest,
  GraphSearchResult,
  GraphEntity,
  GraphRelation,
  GraphPath,
} from './search'

export type {
  // 系统相关
  SystemInfo,
  SystemStats,
  HealthCheck,
  MonitoringData,
  LogEntry,
  LogQueryParams,
} from './system'

// 创建统一的API对象
const createApi = () => {
  return {
    auth: authApi,
    users: usersApi,
    knowledge: knowledgeApi,
    documents: documentsApi,
    chat: chatApi,
    search: searchApi,
    system: systemApi,
  }
}

export const api = createApi()

// 默认导出
export default api
