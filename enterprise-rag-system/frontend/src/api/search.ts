// 搜索相关API

import { simpleHttpClient as httpClient } from './simple-config'
import type { ApiResponseData } from '@/types/api'

// 搜索相关类型定义
export interface SearchRequest {
  query: string
  knowledge_base_ids?: number[]
  search_mode?: 'vector' | 'hybrid' | 'graph' | 'keyword'
  top_k?: number
  score_threshold?: number
  filters?: Record<string, any>
}

export interface SearchResult {
  id: string
  content: string
  score: number
  document_id: number
  document_name: string
  chunk_id?: number
  metadata: Record<string, any>
  highlight?: string[]
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  total: number
  search_mode: string
  processing_time: number
  metadata: Record<string, any>
}

export interface AdvancedSearchRequest {
  query: string
  knowledge_base_ids?: number[]
  filters?: {
    document_types?: string[]
    date_range?: {
      start: string
      end: string
    }
    authors?: string[]
    tags?: string[]
  }
  search_options?: {
    include_metadata?: boolean
    include_chunks?: boolean
    rerank?: boolean
    expand_query?: boolean
  }
  pagination?: {
    page: number
    size: number
  }
}

export interface GraphSearchRequest {
  query: string
  knowledge_base_ids?: number[]
  entity_types?: string[]
  relation_types?: string[]
  max_depth?: number
  min_score?: number
}

export interface GraphSearchResult {
  entities: GraphEntity[]
  relations: GraphRelation[]
  paths: GraphPath[]
  metadata: Record<string, any>
}

export interface GraphEntity {
  id: string
  name: string
  type: string
  properties: Record<string, any>
  score: number
}

export interface GraphRelation {
  id: string
  source: string
  target: string
  type: string
  properties: Record<string, any>
  score: number
}

export interface GraphPath {
  entities: string[]
  relations: string[]
  score: number
  length: number
}

// 搜索API接口
export const searchApi = {
  // 基础搜索
  search: (data: SearchRequest): Promise<ApiResponseData<SearchResponse>> => {
    return httpClient.post('/search', data)
  },

  // 向量搜索
  vectorSearch: (data: SearchRequest): Promise<ApiResponseData<SearchResponse>> => {
    return httpClient.post('/search/vector', data)
  },

  // 混合搜索
  hybridSearch: (data: SearchRequest): Promise<ApiResponseData<SearchResponse>> => {
    return httpClient.post('/search/hybrid', data)
  },

  // 关键词搜索
  keywordSearch: (data: SearchRequest): Promise<ApiResponseData<SearchResponse>> => {
    return httpClient.post('/search/keyword', data)
  },

  // 高级搜索
  advancedSearch: (data: AdvancedSearchRequest): Promise<ApiResponseData<SearchResponse>> => {
    return httpClient.post('/advanced-search', data)
  },

  // 图谱搜索
  graphSearch: (data: GraphSearchRequest): Promise<ApiResponseData<GraphSearchResult>> => {
    return httpClient.post('/search/graph', data)
  },

  // 获取搜索建议
  getSearchSuggestions: (query: string, knowledge_base_ids?: number[]): Promise<ApiResponseData<string[]>> => {
    return httpClient.get('/search/suggestions', {
      params: { query, knowledge_base_ids },
    })
  },

  // 获取热门搜索
  getPopularSearches: (knowledge_base_ids?: number[]): Promise<ApiResponseData<string[]>> => {
    return httpClient.get('/search/popular', {
      params: { knowledge_base_ids },
    })
  },

  // 获取搜索历史
  getSearchHistory: (page?: number, size?: number): Promise<ApiResponseData<any[]>> => {
    return httpClient.get('/search/history', {
      params: { page, size },
    })
  },

  // 清空搜索历史
  clearSearchHistory: (): Promise<ApiResponseData<any>> => {
    return httpClient.delete('/search/history')
  },

  // 保存搜索
  saveSearch: (data: { query: string; results: SearchResult[] }): Promise<ApiResponseData<any>> => {
    return httpClient.post('/search/save', data)
  },

  // 获取保存的搜索
  getSavedSearches: (page?: number, size?: number): Promise<ApiResponseData<any[]>> => {
    return httpClient.get('/search/saved', {
      params: { page, size },
    })
  },
}
